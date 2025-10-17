import json
import logging
from pathlib import Path
from typing import Optional

import typer
from rich import print as rich_print

from module_qc_data_tools.cli.globals import (
    CONTEXT_SETTINGS,
    LogLevel,
)
from module_qc_data_tools.typing_compat import Annotated, TypeAlias
from module_qc_data_tools.utils import check_sn_format, validate_measurement

app = typer.Typer(context_settings=CONTEXT_SETTINGS)


def verbosity_callback(ctx: typer.Context, value: LogLevel) -> Optional[LogLevel]:
    if ctx.resilient_parsing:
        return None

    logging.getLogger(__name__).setLevel(value.value)
    return value


VERBOSITY_T: TypeAlias = Annotated[
    LogLevel,
    typer.Option(
        "-v",
        "--verbosity",
        help="Log level",
        callback=verbosity_callback,
    ),
]


@app.command()
def measurement(
    measurement_path: Annotated[
        Path,
        typer.Argument(
            help="measurement to validate",
            file_okay=True,
            readable=True,
            resolve_path=True,
        ),
    ],
    _verbosity: VERBOSITY_T = LogLevel.info,
) -> None:
    """
    Validate the provided measurement.
    """
    instance = json.loads(measurement_path.read_text(encoding="utf-8"))
    if not validate_measurement(instance):
        raise typer.Exit(1)

    rich_print(":white_check_mark: [green]Valid[/]")


@app.command()
def analysis(
    analysis_path: Annotated[
        Path,
        typer.Argument(
            help="analysis to validate",
            file_okay=True,
            readable=True,
            resolve_path=True,
        ),
    ],
    _verbosity: VERBOSITY_T = LogLevel.info,
) -> None:
    """
    Validate the provided analysis.
    """
    msg = f"not implemented yet. analysis_path='{analysis_path}'"
    raise NotImplementedError(msg)


@app.command()
def sn(
    serial_number: Annotated[str, typer.Argument(help="serial number to validate")],
    _verbosity: VERBOSITY_T = LogLevel.info,
) -> None:
    """
    Validate the provided serial number.
    """
    try:
        check_sn_format(serial_number)
    except ValueError as exc:
        rich_print(f":cross_mark: {exc}")
        raise typer.Exit(1) from exc
    rich_print(":white_check_mark: [green]Valid[/]")


if __name__ == "__main__":
    app()
