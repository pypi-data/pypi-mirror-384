import os
import black
from black.parsing import InvalidInput
from dektools.file.operation import write_file
from ....tmpl.template import TemplateWide


class TemplateException(Exception):
    pass


class FormatException(Exception):
    pass


def py_formatted(s):
    if not isinstance(s, str):
        s = s.decode('utf-8')
    try:
        return black.format_str(s, mode=black.Mode(line_length=120, string_normalization=False))
    except InvalidInput:
        raise FormatException()


class TemplateFormatted(TemplateWide):
    format_ext_map = {
        '.py': py_formatted
    }

    def render_file(self, target_file, template_file, close_tpl=False):
        content = self.render_string(template_file, close_tpl)
        formatted = self.format_ext_map.get(os.path.splitext(target_file)[-1], default_formatted)
        try:
            content = formatted(content)
            errors = False
        except FormatException:
            errors = True
        write_file(target_file, sb=content)
        if errors:
            raise TemplateException(f'format error, please check the target file: {template_file} , {target_file}')
        return content


def default_formatted(s):
    return s
