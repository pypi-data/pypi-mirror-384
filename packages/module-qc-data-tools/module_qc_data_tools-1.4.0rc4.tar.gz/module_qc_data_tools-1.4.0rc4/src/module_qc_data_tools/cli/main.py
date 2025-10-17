"""
Top-level entrypoint for the command line interface.
"""

import typer

import module_qc_data_tools
from module_qc_data_tools.cli.globals import CONTEXT_SETTINGS
from module_qc_data_tools.cli.validate import app as app_validate
from module_qc_data_tools.typing_compat import Annotated
from module_qc_data_tools.utils import datapath

# subcommands
app = typer.Typer(context_settings=CONTEXT_SETTINGS)
app.add_typer(app_validate, name="validate")


@app.callback(invoke_without_command=True)
def main(
    version: Annotated[
        bool, typer.Option("--version", help="Print the current version.")
    ] = False,
    prefix: Annotated[
        bool, typer.Option("--prefix", help="Print the path prefix for data files.")
    ] = False,
) -> None:
    """
    Manage top-level options
    """
    if version:
        typer.echo(f"module-qc-data-tools v{module_qc_data_tools.__version__}")
        raise typer.Exit()
    if prefix:
        typer.echo(datapath)
        raise typer.Exit()


# for generating documentation using mkdocs-click
typer_click_object = typer.main.get_command(app)
