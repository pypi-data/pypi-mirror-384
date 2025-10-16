import os
from dektools.serializer.yaml import yaml
from dektools.dict import dict_merge
from dektools.typer import load_yaml_files
from .template import TemplateWide


class RenderTemplate(TemplateWide):
    file_ignore_tpl = [f"../{x}" for x in TemplateWide.file_ignore_tpl]
    file_ignore_override = [f"../{x}" for x in TemplateWide.file_ignore_override]
    file_ignore = [f"../{x}" for x in TemplateWide.file_ignore]


def render_path(dest, src, files=None, updated=None, **kwargs):
    data = {}
    path_values = os.path.join(src, 'values.yaml')
    if os.path.isfile(path_values):
        data = dict(Values=yaml.load(path_values) or {})
    dict_merge(data, dict(Values=load_yaml_files(files)))
    if updated:
        dict_merge(data, updated)
    if os.path.isdir(dest) or os.path.isdir(src):
        RenderTemplate(data, **kwargs).render_dir(dest, os.path.join(src, 'templates'))
    elif os.path.isfile(src):
        RenderTemplate(data, **kwargs).render_file(dest, src)
