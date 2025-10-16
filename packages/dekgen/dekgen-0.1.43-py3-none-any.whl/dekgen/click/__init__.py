import typer
from typing import Optional, List
from typing_extensions import Annotated
from dektools.typer import multi_options_to_dict
from ..tmpl.render import render_path

app = typer.Typer(add_completion=False)


@app.command()
def render(
        dest,
        src,
        vss=None,
        ves=None,
        files: Annotated[Optional[List[str]], typer.Option('--file')] = None,
        _set: Annotated[Optional[List[str]], typer.Option('--set')] = None
):
    if vss and ves:
        kwargs = dict(
            variable_start_string=vss,
            variable_end_string=ves
        )
    else:
        kwargs = {}
    render_path(dest, src, files, multi_options_to_dict(_set), **kwargs)


@app.callback()
def callback():
    pass
