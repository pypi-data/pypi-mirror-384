from __future__ import annotations

import logging
import logging.config
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler

from module_qc_data_tools._version import __version__
from module_qc_data_tools.loaders import load_iv_alt, load_json
from module_qc_data_tools.qcDataFrame import (
    outputDataFrame,
    qcDataFrame,
)
from module_qc_data_tools.utils import (
    check_sn_format,
    convert_name_to_serial,
    convert_serial_to_name,
    get_layer_from_sn,
    get_n_chips,
    get_nlanes_from_sn,
    get_nominal_current,
    get_sensor_type_from_layer,
    get_sensor_type_from_sn,
    get_sn_from_connectivity,
    get_type_from_sn,
    save_dict_list,
)


class AppFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.filenameStem = Path(record.filename).stem
        return True


def rich_handler_factory() -> RichHandler:
    return RichHandler(
        console=Console(width=160),
        rich_tracebacks=True,
        tracebacks_suppress=[],
        markup=True,
    )


LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": True,
    "filters": {
        "appfilter": {
            "()": AppFilter,
        }
    },
    "formatters": {
        "standard": {"format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s"},
        "pretty": {"format": "[[yellow]%(filenameStem)s[/]] %(message)s"},
    },
    "handlers": {
        "default": {
            "formatter": "standard",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",  # Default is stderr
        },
        "rich": {
            "()": rich_handler_factory,
            "formatter": "pretty",
            "filters": ["appfilter"],
        },
    },
    "loggers": {
        "": {
            "handlers": [],
            "level": "WARNING",
            "propagate": False,
        },
        "module_qc_data_tools": {
            "handlers": ["rich"],
            "level": "INFO",
            "propagate": True,
        },
    },
}

logging.config.dictConfig(LOGGING_CONFIG)

__all__ = (
    "__version__",
    "check_sn_format",
    "convert_name_to_serial",
    "convert_serial_to_name",
    "get_layer_from_sn",
    "get_n_chips",
    "get_nlanes_from_sn",
    "get_nominal_current",
    "get_sensor_type_from_layer",
    "get_sensor_type_from_sn",
    "get_sn_from_connectivity",
    "get_type_from_sn",
    "load_iv_alt",
    "load_json",
    "outputDataFrame",
    "qcDataFrame",
    "save_dict_list",
)
