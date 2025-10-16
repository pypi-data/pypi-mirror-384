import functools
from .imports import Imports, ImportsStatement
from .template import TemplateFormatted
from .template.env import env_extend
from ...tmpl.generator import GeneratorTpl, GeneratorFiles, Repr, DictCollection


class ReprTS(Repr):
    def final_value(self):
        return f'_({repr(self.value)})'


class CodeGeneratorMixin:
    ReprTS = ReprTS
    template_cls = TemplateFormatted
    _imports_cls = Imports
    _imports_statement_cls = ImportsStatement

    env_default = {**env_extend.context}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__imports_statement__ = None

    @functools.cached_property
    def iss(self):
        if self.parent_root:
            return self.parent_root.__imports_statement__
        else:
            _imports_core = getattr(self.__class__, '_imports_core', None)
            if _imports_core is None:
                _imports_core = self.__class__._imports_core = self._imports_cls()
            imports_core = _imports_core.derive()
            imports_core.update(self.walk_imports(self))
            self.__imports_statement__ = self._imports_statement_cls(imports_core)
            return self.__imports_statement__

    def _post_collect_variables(self, variables):
        variables = super()._post_collect_variables(variables)
        if self.parent_root:
            imports_data = {}
        else:
            imports_data = dict(
                imports=self.iss.as_statements()
            )
        return {
            **variables,
            **imports_data
        }

    @functools.cached_property
    def imports(self):
        return self._collect_data('imports', DictCollection)

    @classmethod
    def walk_imports(cls, node):
        imports = {}
        imports.update(node.imports)
        for children in node.children.values():
            for child in children:
                imports.update(cls.walk_imports(child))
        return imports


class CodeGeneratorTpl(CodeGeneratorMixin, GeneratorTpl):
    pass


class CodeGeneratorFiles(CodeGeneratorMixin, GeneratorFiles):
    pass
