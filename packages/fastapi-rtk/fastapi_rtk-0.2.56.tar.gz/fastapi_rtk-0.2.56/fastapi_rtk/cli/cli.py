from pathlib import Path
from typing import Annotated, Union

import typer

app = typer.Typer(rich_markup_mode="rich")
from .commands import path_callback, version_callback  # noqa: E402


@app.callback()
def callback(
    version: Annotated[
        Union[bool, None],
        typer.Option(
            "--version", help="Show the version and exit.", callback=version_callback
        ),
    ] = None,
    path: Annotated[
        Union[Path, None],
        typer.Option(
            help="A path to a Python file or package directory (with [blue]__init__.py[/blue] files) containing a [bold]FastAPI[/bold] app. If not provided, a default set of paths will be tried.",
            callback=path_callback,
        ),
    ] = None,
) -> None:
    """
    FastAPI RTK CLI - The [bold]fastapi-rtk[/bold] command line app. 😎

    Manage your [bold]FastAPI React Toolkit[/bold] projects.
    """


def main():
    app()
