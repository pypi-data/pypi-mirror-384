from enum import Enum
from typing import Optional

import typer

from module_qc_data_tools import check_sn_format
from module_qc_data_tools.typing_compat import Annotated

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


class LogLevel(str, Enum):
    debug = "DEBUG"
    info = "INFO"
    warning = "WARNING"
    error = "ERROR"


def sn_callback(ctx: typer.Context, value: str) -> Optional[str]:
    if ctx.resilient_parsing:
        return None

    if value:
        try:
            check_sn_format(value)
        except SystemExit as e:
            msg = f"Invalid serial number format: {value}"
            raise typer.BadParameter(msg) from e
    return value


OPTION_serial_number = Annotated[
    str,
    typer.Option(
        "--sn",
        "--serial-number",
        help="Module serial number",
        callback=sn_callback,
    ),
]
