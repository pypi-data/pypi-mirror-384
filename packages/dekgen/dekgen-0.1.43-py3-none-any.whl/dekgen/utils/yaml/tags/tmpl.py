from copy import deepcopy
from itertools import chain
from dektools.escape import str_escape_special
from dektools.dict import is_list, is_dict, merge_flex, assign_flex
from dektools.serializer.yaml.tags.base import TagBase
from ....tmpl.template import Template


class TemplateTmpl(Template):
    default_env_kwargs = dict(
        **Template.default_env_kwargs,
        variable_start_string='(-(',
        variable_end_string=')-)'
    )


class TmplBase:
    sep = '/'

    @classmethod
    def parse_args(cls, array):
        return dict()

    @classmethod
    def pkg(cls, exp, data):
        array = exp.lstrip(cls.sep).split(cls.sep) if exp else []
        return cls(**{'data': data, **cls.parse_args(array)})

    def __init__(self, data=None):
        self.data = data


class TmplPatch(TmplBase):
    sep_operation = ':'

    @classmethod
    def parse_args(cls, array):
        func = array[0]
        args = array[1:]
        array = func.split(cls.sep_operation)
        operation = None
        if len(array) > 1:
            operation = array[1]
        func = array[0]
        return dict(func=func, operation=operation, args=args)

    def __init__(self, func=None, operation=None, args=None, **kwargs):
        super().__init__(**kwargs)
        self.args = args
        self.func = func
        self.operation = operation  # merge_flex: _merge_options

    @staticmethod
    def walk_data(node, walk):
        if is_list(node):
            for key, value in enumerate(node):
                walk(node, key, value)
        elif is_dict(node):
            for key, value in node.items():
                walk(node, key, value)

    def combine_data(self, func):
        data = deepcopy(func.data)
        if not self.data:
            return data
        data2 = deepcopy(self.data)
        merge_flex(data, data2, self.operation)
        return data

    def invoke(self, ins, key, func):
        raise NotImplementedError()


class FuncTmpl(TmplBase):
    @classmethod
    def parse_args(cls, array):
        return dict(args=array)

    def __init__(self, args=None, **kwargs):
        super().__init__(**kwargs)
        self.args = args

    def get_context(self, args):
        context = {}
        for i, k in enumerate(self.args):
            kv = k.split('=')
            if len(kv) == 1:
                context[k] = args[i]
            else:
                k, v = kv
                if i < len(args):
                    v = args[i]
                context[k] = v
        return context


class CallTmpl(TmplPatch):
    def invoke(self, ins, key, func):
        if isinstance(key, str) and key.startswith('='):
            ins.pop(key)
            ins.update(self.invoke_inner(func))
        else:
            ins[str_escape_special(key) if isinstance(key, str) else key] = self.invoke_inner(func)

    def invoke_inner(self, func):
        def walk(node, key, value):
            self.walk_data(value, walk)
            if isinstance(key, str) or isinstance(value, str):
                replace_list.append(delay(node, key, value))

        def delay(ins, key, value):
            def wrapper():
                nonlocal key, value
                if isinstance(key, str):
                    ins.pop(key)
                    key = tt.render(key)
                if isinstance(value, str):
                    value = tt.render(value)
                ins[key] = value

            return wrapper

        tt = TemplateTmpl(func.get_context(self.args))
        replace_list = []
        data_total = self.combine_data(func)
        self.walk_data(data_total, walk)
        for c in replace_list:
            c()
        return data_total


class ExtendTmpl(TmplPatch):
    def invoke(self, ins, key, func):
        data = self.invoke_inner(func)
        if is_list(ins) or not is_dict(data):
            ins[key] = data
        else:
            temp = ins.__class__()
            combine = False
            for k, v in ins.items():
                if k == key:
                    combine = True
                    v = data
                if combine:
                    temp = assign_flex(temp, v)
                else:
                    temp[k] = v
            ins.clear()
            ins.update(temp)

    def invoke_inner(self, func):
        return self.combine_data(func)


def tmpl_data_final(data):
    def walk(node):
        if is_list(node):
            for key, value in enumerate(node):
                walk2(node, key, value)
        elif is_dict(node):
            for key, value in node.items():
                walk2(node, key, value)

    def walk2(node, key, value):
        walk(value)
        if isinstance(value, FuncTmpl):
            walk(value.data)
            func_map[key] = value
            func_list.append(lambda: node.pop(key))
        elif isinstance(value, ExtendTmpl):
            walk(value.data)
            extend_list.append(delay_patch(node, key, value))
        elif isinstance(value, CallTmpl):
            walk(value.data)
            call_list.append(delay_patch(node, key, value))

    def delay_patch(ins, key, patch):
        def wrapper():
            patch.invoke(ins, key, func_map[patch.func])

        return wrapper

    func_map = {}
    func_list = []
    extend_list = []
    call_list = []
    walk(data)
    for c in chain(func_list, extend_list, call_list):
        c()
    return data


class TmplTag(TagBase):
    yaml_tag_multi = True
    tmpl_cls = None

    @classmethod
    def from_yaml_multi(cls, loader, tag_suffix, node):
        return cls.tmpl_cls.pkg(tag_suffix, cls.node_to_data(loader, node))


class FuncTag(TmplTag):
    yaml_tag = '!f'
    tmpl_cls = FuncTmpl


class CallTag(TmplTag):
    yaml_tag = '!c'
    tmpl_cls = CallTmpl


class ExtendTag(TmplTag):
    yaml_tag = '!e'
    tmpl_cls = ExtendTmpl
