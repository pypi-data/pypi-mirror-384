import re
from collections import OrderedDict
from dektools.dict import assign


class ImportsException(Exception):
    pass


class Imports:
    def __init__(self, parents=None, data=None):
        self.parents = parents or []
        self.data = data or {}
        self.data_formatted = {}
        self.data_primary = OrderedDict()
        self.data_shortcut = {}
        self.update(self.data)

    def derive(self):
        return self.__class__([self])

    def dependency(self):
        self.parents = []

    def add_shortcut(self, typed, key, value):
        self.data_shortcut.setdefault(typed, {})[key] = value

    def add_primary(self, key, value):
        self.data_primary[key] = value

    def add_item(self, name, data):
        self.data[name] = assign(self.data.get(name) or {}, data)
        last_name = None
        for x in reversed(name.split('.')):
            if last_name is None:
                label = x
            else:
                label = f'{x}.{last_name}'
            last_name = label
            self.data_formatted.setdefault(label, set()).add(name)

    def update(self, data):
        for k, v in data.items():
            self.add_item(k, v)

    def get_item(self, key, bases=None):
        bases = bases or ()
        if not isinstance(bases, (list, tuple)):
            bases = [bases]
        label_set = self.get_label_formatted_set(key)
        self.validate(label_set, key, True)
        label_primary = self.get_label_primary(key)
        if label_primary and label_primary in label_set:
            return label_primary
        if len(label_set) > 1:
            label_set = self.checkout_hits(label_set, bases)
            self.validate(label_set, key, False)
        if key in label_set:
            return key
        return next(iter(label_set))

    @staticmethod
    def validate(label_set, key, allow_multiple):
        if not label_set:
            raise ImportsException(f'Can not find module by [ {key} ]')
        elif len(label_set) > 1:
            if key not in label_set:
                if not allow_multiple:
                    raise ImportsException(f'Check out multiple module [{label_set}] by [ {key} ]')

    def get_label_formatted_set(self, key):
        if key in self.data_formatted:
            return self.data_formatted[key]
        for parent in self.parents:
            value = parent.get_label_formatted_set(key)
            if value is not None:
                return value

    def get_key_by_shortcut(self, key, typed):
        mt = self.data_shortcut.get(typed)
        if mt:
            return mt.get(key)
        for parent in self.parents:
            value = parent.get_key_by_shortcut(key, typed)
            if value is not None:
                return value

    def get_label_primary(self, key):
        for query, label in self.data_primary.items():
            m = re.search(query, key)
            if m:
                label_primary = label.format(*m.groups())
                if self.get_label_data(label_primary):
                    return label_primary
        for parent in self.parents:
            value = parent.get_label_primary(key)
            if value is not None:
                return value

    def get_label_data(self, label):
        if label in self.data:
            return self.data[label]
        for parent in self.parents:
            value = parent.get_label_data(label)
            if value is not None:
                return value

    def checkout_hits(self, label_set, bases):
        result = set()
        for label in label_set:
            for base in bases:
                if not self.is_hit(label, base):
                    break
            else:
                result.add(label)
        return result

    def is_hit(self, label, key):
        data = self.get_label_data(label)
        if data:
            value = data.get('value')
            bases = data.get('bases') or []
            lists = ([value] if value else []) + bases
            for item in lists:
                if key == item or item.endswith(f'.{key}'):
                    return True
            for item in lists:
                if self.is_hit(item, key):
                    return True
        return False


class ImportsStatement:
    def __init__(self, imports: Imports):
        self.imports = imports
        self.statements = {}

    def as_statements(self):
        return '\n'.join(sorted(self.statements.values()))

    def var(self, module_guss, bases=None, alias=None):
        module = self.imports.get_item(module_guss, bases)
        _, variable = self.get_sv(module, alias)
        return variable

    def get_sv(self, module, alias):
        def walk(index):
            ml = module.split('.')
            m, vd = '.'.join(ml[:index]), ml[index]
            statement = f'from {m} import {vd}' + s_addition
            ml[index] = alias or ml[index]
            variable = '.'.join(ml[index:])
            return statement, variable, alias or vd

        def conflict(v, s, ss):
            raise ValueError(f'Conflicts with statement: {v} , {s} , {ss}')

        def directly(vv):
            s, v = f'import {module}' + s_addition, module
            ss = self.statements.get(vv)
            if ss is None:
                self.statements[vv] = s
            elif ss != s:
                conflict(v, s, ss)
            return s, v

        s_addition = f' as {alias}' if alias else ''
        s, v, vv = walk(-1)
        if '.' not in module:
            return directly(vv)
        ss = self.statements.get(vv)
        if ss is None:
            self.statements[vv] = s
        elif ss != s:
            s, v, vv = walk(-2)
            ss = self.statements.get(vv)
            if ss is None:
                self.statements[vv] = s
            elif s != s:
                if module.startswith('.'):
                    conflict(v, s, ss)
                vv = alias or module
                return directly(vv)
        return s, v
