from importlib.metadata import PackageNotFoundError, version

import typer

try:
    __version__ = version("dns-archiver")
except PackageNotFoundError:
    __version__ = "dev"


def version_callback(value: bool):
    if value:
        print(__version__)
        raise typer.Exit()
