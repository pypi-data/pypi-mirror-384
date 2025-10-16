import os
import functools
from pathlib import Path
from dektools.str import tab_str
from dektools.collect import DictCollection, NamedListCollection, CollectionDataMixin
from .template import TemplateWide
from .part import Repr, ReprTuple


class Generator(CollectionDataMixin):
    TEMPLATE_DIR = None

    template_name = None
    template_cls = TemplateWide
    template_ext = '.tpl'

    Repr = Repr
    ReprTuple = ReprTuple

    env_default = {}

    def __init__(self, instance, kwargs=None):
        self.instance = instance
        self.parent = None
        self.kwargs = kwargs or {}

    def render(self):
        raise NotImplementedError

    def render_tpl(self, tpl, variables=None):
        return self.template_cls(self.normalize_variables(
            {**(self.variables if variables is None else variables), **self.kwargs}), self.env_default).render_string(
            str(Path(self.template_path) / (tpl + self.template_ext)))

    def normalize_variables(self, variables):
        return variables

    @functools.cached_property
    def template_path(self):
        return os.path.join(self.TEMPLATE_DIR, self.template_name) if self.template_name else str(self.TEMPLATE_DIR)

    @functools.cached_property
    def variables(self):
        return self._collect_data('variables', DictCollection)

    def get_variables(self, *args, **kwargs):
        return {
            **{k: self.variables[k] for k in args},
            **{k: self.variables[v] for k, v in kwargs.items()}
        }

    @staticmethod
    def tab_str(s, n, p=4, sl=False):  # s: list or str
        return tab_str(s, n, p, sl)

    @functools.cached_property
    def children(self):
        return self._collect_data('children', NamedListCollection)

    @functools.cached_property
    def parent_root(self):
        cursor = self.parent
        while cursor:
            if cursor.parent:
                cursor = cursor.parent
            else:
                return cursor
        return cursor

    def _post_collect_children(self, children):
        for lst in children.values():
            for child in lst:
                child.parent = self
        return children

    def _post_collect_variables(self, variables):
        children_data = {}
        all_filter_children = getattr(self, f'_filter_children___all__', lambda k, x, y: x)
        for key, array in self.children.items():
            r = self.tab_str([node.render() for node in array], 0)
            filter_children = getattr(self, f'_filter_children_{key}', None)
            if filter_children:
                children_data[key] = filter_children(r, array)
            else:
                children_data[key] = all_filter_children(key, r, array)
        return {
            **variables,
            **children_data,
        }


class GeneratorTpl(Generator):
    template_tpl = 'main'

    def render(self):
        return '' if self.template_tpl is None else self.render_tpl(self.template_tpl)


class GeneratorFiles(Generator):
    def __init__(self, target_dir, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target_dir = str(target_dir)

    def check(self):
        return self.instance is not None

    def action(self):
        if self.check():
            self.render()
            self.on_rendered()

    def on_rendered(self):
        pass

    def render(self):
        self.template_cls(
            self.normalize_variables({**self.variables, **self.kwargs}),
            env=self.env_default,
            multi=self.multi
        ).render_dir(self.target_dir, self.template_path)
        for generator_cls, ins_list in self.sibling.items():
            for ins in ins_list:
                generator_cls(self.target_dir, ins).action()

    @functools.cached_property
    def multi(self):
        return self._collect_data('multi', NamedListCollection)

    @functools.cached_property
    def sibling(self):
        return self._collect_data('sibling', DictCollection)
