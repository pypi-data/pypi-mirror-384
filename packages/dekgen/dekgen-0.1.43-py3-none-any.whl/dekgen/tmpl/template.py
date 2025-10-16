import os
import json
import datetime
from jinja2 import Environment
from jinja2.exceptions import TemplateError
from dektools.common import classproperty
from dektools.file import read_text, read_file, write_file, list_dir, list_relative_path, FileHitChecker, normal_path
from dektools.module import ModuleProxy
from dektools.time import TZ_CURRENT
from dektools.output import obj2str
from .exceptions import RenderException


class ModuleProxyTemplate(ModuleProxy):
    def __call__(self, obj, attrs, *args, **kwargs):
        return self[attrs](obj, *args, **kwargs)

    def __getattr__(self, item):
        if item == 'jinja_pass_arg':
            raise AttributeError(item)
        return super().__getattr__(item)


class Template:
    template_bin_suffix = '-tpl-bin'
    template_suffix = '-tpl'
    target_suffix = None

    file_ignore_name = ''

    _file_ignore_tpl = ['.ignoretpl', '.ignoretpl.tpl']
    _file_ignore_override = ['.ignoreor', '.ignoreor.tpl']
    _file_ignore = ['.ignore', '.ignore.tpl']

    default_env_kwargs = dict(
        autoescape=False
    )

    @classmethod
    def get_file_ignore(cls, name):
        return cls.file_ignore_name + name

    @classproperty
    def file_ignore_tpl(self):
        return [self.get_file_ignore(x) for x in self._file_ignore_tpl]

    @classproperty
    def file_ignore_override(self):
        return [self.get_file_ignore(x) for x in self._file_ignore_override]

    @classproperty
    def file_ignore(self):
        return [self.get_file_ignore(x) for x in self._file_ignore]

    @classproperty
    def files_of_ignore(self):
        return {*self.file_ignore, *self.file_ignore_override, *self.file_ignore_tpl}

    def __init__(self, variables, env=None, filters=None, multi=None, **kwargs):
        self._copy_things = [variables, env, filters, kwargs]
        self.multi = multi or {}
        self.env = Environment(**{
            **self.default_env_kwargs,
            **kwargs
        })
        self.env.filters.update(dict(
            mp=ModuleProxyTemplate()
        ))
        if filters:
            self.env.filters.update(filters)
        self.variables = {
            **{
                'now': datetime.datetime.now(tz=TZ_CURRENT),
                '_virtual_': '__virtual__',
                '_multi_': '__multi__'
            },
            **variables
        }
        if env:
            for k, data in env.items():
                getattr(self.env, k).update(data)

    def copy(
            self,
            variables=None,
            loss_vars=False,
            loss_env=False,
            loss_filters=False,
            loss_multi=False,
            loss_kwargs=False
    ):
        return self.__class__(
            {**({} if loss_vars else self._copy_things[0]), **(variables or {})},
            env=None if loss_env else self._copy_things[1],
            filters=None if loss_filters else self._copy_things[2],
            multi=None if loss_multi else self.multi,
            **({} if loss_kwargs else self._copy_things[3])
        )

    def render(self, content):
        return self.env.from_string(content).render(self.variables)

    @classmethod
    def render_circle(cls, data, **kwargs):
        def to_string(d):
            return json.dumps(d, sort_keys=True)

        def to_data(s):
            return json.loads(s)

        cursor_data = data
        cursor_str = to_string(cursor_data)
        while True:
            prev_str = cursor_str
            cursor_str = cls(cursor_data, **kwargs).render(cursor_str)
            if cursor_str == prev_str:
                return cursor_data
            cursor_data = to_data(cursor_str)

    def render_string(self, template_file, close_tpl=False):
        if close_tpl:
            return read_file(template_file)
        else:
            content = read_text(template_file)
            try:
                return self.render(content)
            except TemplateError as e:
                raise RenderException(f'Render error: {template_file}: {e} ==>:\n{obj2str(self.variables)}')

    def render_file(self, target_file, template_file, close_tpl=False):
        content = self.render_string(template_file, close_tpl)
        write_file(target_file, sb=content)
        return content

    def render_dir(self, path_target, path_template, force_close_tpl=False, open_ignore_override=True):
        files_of_ignore = self.files_of_ignore
        ignore_tpl = FileHitChecker(
            path_template,
            self.file_ignore_tpl[0],
            lines=self.get_hit_rules(path_template, self.file_ignore_tpl[1])
        )
        ignore_override = FileHitChecker(
            path_template,
            self.file_ignore_override[0],
            lines=self.get_hit_rules(path_template, self.file_ignore_override[1])
        )
        ignore = FileHitChecker(
            path_template,
            self.file_ignore[0],
            lines=[
                *self.get_hit_rules(path_template, self.file_ignore[1]),
                *[f'/{item}' for item in [*self.file_ignore_tpl, *self.file_ignore_override, *self.file_ignore]]
            ]
        )

        path_virtual = os.path.join(path_template, '__virtual__')
        variables_virtual = {}
        for rp, fp in list_relative_path(path_virtual).items():
            variables_virtual[rp.replace('\\', '/').replace('/', '__')] = self.render_string(fp)
        self.variables['__virtual__'] = variables_virtual

        path_multi = os.path.join(path_template, '__multi__')
        for fp, name in list_dir(path_multi, True):
            list_variables = self.multi.get(name)
            if list_variables:
                for variables in list_variables:
                    tmpl = self.copy(variables, loss_vars=True, loss_multi=True)
                    tmpl.render_dir(path_target, os.path.join(path_multi, name), force_close_tpl, open_ignore_override)

        for root, _, files in os.walk(path_template):
            if any(root.startswith(x + os.path.sep) for x in [path_virtual, path_multi]):
                continue
            for f in files:
                if f in files_of_ignore and root == path_template:
                    continue
                fp = os.path.join(root, f)
                if ignore.match(fp):
                    continue
                fp_ = fp
                is_bin = False
                if fp_.endswith(self.template_bin_suffix):
                    fp_ = fp_[:len(fp_) - len(self.template_bin_suffix)]
                    is_bin = True
                elif fp_.endswith(self.template_suffix):
                    fp_ = fp_[:len(fp_) - len(self.template_suffix)]
                rp = fp_[len(path_template):]
                target_file = path_target + self.render(rp)
                if open_ignore_override and os.path.exists(target_file) and ignore_override.match(fp):
                    continue
                if is_bin:
                    write_file(target_file, sb=self.variables[self.render(read_text(fp)).strip()])
                else:
                    self.render_file(target_file, fp, force_close_tpl or ignore_tpl.match(fp))

    def get_hit_rules(self, path_template, filepath):
        ignore_file = normal_path(os.path.join(path_template, filepath))
        if os.path.exists(ignore_file):
            content = self.render_string(ignore_file)
            return [line for line in content.split('\n') if line]
        else:
            return []


class TemplateWide(Template):
    default_env_kwargs = dict(
        **Template.default_env_kwargs,
        variable_start_string='(=(',
        variable_end_string=')=)'
    )
