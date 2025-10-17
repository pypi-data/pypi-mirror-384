from __future__ import annotations

import json
import logging
from contextlib import suppress
from itertools import zip_longest
from pathlib import Path
from typing import Any, cast

import bson
import numpy as np
from rich.console import Console, ConsoleOptions, Group, RenderableType, RenderResult
from rich.panel import Panel
from rich.pretty import Pretty
from rich.table import Table
from tabulate import tabulate

from module_qc_data_tools.typing_compat import (
    Generator,
    OutputQCDict,
    ParamLeaf,
    ParamValue,
    PathLike,
    QCDict,
    SerialNumber,
    SubTestType,
    TestType,
)
from module_qc_data_tools.utils import (
    MyEncoder,
    chunks,
    convert_name_to_serial,
)

log = logging.getLogger(__name__)
log.setLevel("INFO")


class qcDataFrame:
    """
    The QC data frame which stores meta data and task data.
    """

    def __init__(
        self,
        columns: list[str] | None = None,
        units: list[str] | None = None,
        x: list[bool] | None = None,
        _dict: QCDict | None = None,
    ) -> None:
        self._identifiers: dict[str, Any] = {}
        self._meta_data: dict[str, Any] = {}
        self._dcs_data: dict[str, Any] = {}
        self._data: dict[str, Any] = {}
        self._property: dict[str, Any] = {}
        self._parameter: dict[str, ParamValue] = {}
        self._comment: str = ""
        if _dict:
            self.from_dict(_dict)
            return

        columns = columns or []

        for i, column in enumerate(columns):
            self._data[column] = {
                "X": x[i] if x else False,
                "Unit": units[i] if units else None,
                "Values": [],
            }

    def add_meta_data(self, key: str, value: Any) -> None:
        self._meta_data[key] = value

    @property
    def dcs_data(self) -> dict[str, Any]:
        """
        Unifies add_dcs_data and get_dcs_data
        add: `df.dcs_data[key] = value`
        get: `df.dcs_data`
        """
        return self._dcs_data

    def add_data(self, data: dict[str, Any]) -> None:
        for key, value in data.items():
            self._data[key]["Values"] += list(value)

    def add_column(
        self, column: str, unit: str = "", x: bool = False, data: Any = None
    ) -> None:
        data = data or []
        if column in self._data:
            msg = f"column {column} already exists! Will overwrite."
            log.warning(msg)
        self._data[column] = {"X": x, "Unit": unit, "Values": list(data)}

    def add_property(
        self, key: str, value: float | list[float], precision: int = -1
    ) -> None:
        if key in self._property:
            msg = f"property {key} already exists! Will overwrite."
            log.warning(msg)
        if precision != -1:
            with suppress(Exception):
                value = self._round(key, value, precision)
        self._property[key] = value

    def add_parameter(
        self,
        key: str,
        value: ParamValue,
        precision: int = -1,
    ) -> None:
        if key in self._parameter:
            msg = f"parameter {key} already exists! Will overwrite."
            log.warning(msg)

        if precision != -1:
            if isinstance(value, dict):
                value = {k: self._round(k, v, precision) for k, v in value.items()}
            else:
                value = self._round(key, value, precision)
        self._parameter[key] = value

    def _round(self, key: str, value: float | list[float], precision: int) -> ParamLeaf:
        try:
            if isinstance(value, list):
                value = np.around(value, precision).tolist()
            else:
                value = round(value, precision)
        except Exception:
            msg = f"Unable to round value stored in output file for {key}."
            log.warning(msg)
        return value

    def add_comment(self, comment: str, override: bool = False) -> None:
        if override or self._comment == "":
            self._comment = comment
        else:
            self._comment += ". " + str(comment)

    def __getitem__(self, column: str) -> Any:
        return np.array(self._data[column]["Values"])

    def set_unit(self, column: str, unit: str) -> None:
        self._data[column]["Unit"] = unit

    def get_unit(self, column: str) -> str:
        return cast(str, self._data[column]["Unit"])

    def set_x(self, column: str, x: bool) -> None:
        self._data[column]["X"] = x

    def get_x(self, column: str) -> bool:
        return cast(bool, self._data[column]["X"])

    def __len__(self) -> int:
        return max(len(value["Values"]) for value in self._data.values())

    def get_meta_data(self) -> dict[str, Any]:
        return self._meta_data

    def get_identifiers(self) -> dict[str, Any]:
        return {
            k: self._meta_data.get(k)
            for k in (
                "ChipID",
                "Name",
                "ModuleSN",
                "Institution",
                "TestType",
                "TimeStart",
                "TimeEnd",
            )
        }

    def get_properties(self) -> dict[str, Any]:
        return self._property

    def get_comment(self) -> str:
        return self._comment

    def __str__(self) -> str:
        text = "Identifiers:\n"
        text += str(json.dumps(self.get_identifiers(), cls=MyEncoder, indent=4))
        text += "\n"
        # text += "Meta data:\n"
        # text += str(json.dumps(self._meta_data, cls=MyEncoder, indent=4))
        # text += "\n"
        table = []
        for key, value in self._data.items():
            table.append(
                [key + (f" [{value['Unit']}]" if value["Unit"] else "")]
                + value["Values"]
            )
        text += tabulate(table, floatfmt=".3f")
        return text

    def __rich_identifiers__(self) -> RenderableType:
        pretty = Pretty(self.get_identifiers())
        return Panel(pretty)

    def __rich_data__(self) -> Generator[RenderableType]:
        for chunk in chunks(list(self._data.items()), 10):
            table = Table()
            ## to identify columns with small values like sensor leakage current (sigma)
            smallvalues = False
            data = []
            for key, column in chunk:
                unit = f"({column['Unit']})" if column["Unit"] else ""
                identifier = f"{key} {unit}" if column["Unit"] else key
                table.add_column(
                    identifier, justify="right", style="cyan" if column["X"] else None
                )
                data.append(column["Values"])
                ## only for sensor leakage current (and sigma) with 100uA as current compliance
                if "current" in key and np.average(column["Values"]) < 100e-6:
                    smallvalues = True
            if smallvalues:
                for row in list(zip_longest(*data, fillvalue=np.nan)):
                    table.add_row(
                        *[f"{x:0.4e}" if 0 < x < 100e-6 else f"{x:0.2f}" for x in row]
                    )
            else:
                for row in list(zip_longest(*data, fillvalue=np.nan)):
                    table.add_row(*[f"{x:0.2f}" for x in row])

            yield table

    def __rich_console__(
        self, _console: Console, _options: ConsoleOptions
    ) -> RenderResult:
        yield self.__rich_identifiers__()
        yield Group(*list(self.__rich_data__()))

    def to_dict(self) -> QCDict:
        return {
            "property": self._property,
            "parameter": self._parameter,
            "comment": self._comment,
            "Measurements": self._data,
            "Metadata": self._meta_data,
            "DCSdata": self._dcs_data,
        }

    def from_dict(self, _dict: QCDict) -> None:
        self._meta_data = _dict.get("metadata", {}) or _dict["Metadata"]
        self._dcs_data = _dict.get("DCSdata", {})
        self._identifiers = self.get_identifiers()
        self._data = _dict["Measurements"]
        self._property = _dict["property"]
        self._comment = _dict["comment"]

    def to_json(self) -> str:
        _dict = self.to_dict()
        return json.dumps(_dict, cls=MyEncoder, indent=4)

    def save_json(self, path: PathLike) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        _dict = self.to_dict()
        with Path(path).open("w", encoding="UTF-8") as fp:
            json.dump(_dict, fp, cls=MyEncoder, indent=4)


class outputDataFrame:
    """
    The output file format, designed to work well with localDB and prodDB
    """

    def __init__(self, _dict: OutputQCDict | None = None) -> None:
        self._serialNumber: SerialNumber = "Unknown"
        self._testType: TestType = ""
        self._subtestType: SubTestType = ""
        self._results: qcDataFrame = qcDataFrame()  # holds qcDataFrame
        self._passed: bool = False
        self._runNumber: bson.ObjectId | None = None
        if _dict:
            self.from_dict(_dict)

    def set_serial_num(self, serial_num: SerialNumber | None = None) -> None:
        if serial_num is not None:
            self._serialNumber = serial_num
        else:
            try:
                chipName = self._results.get_meta_data()["Name"]
            except Exception:
                log.warning("Can't find chip name for serial number conversion")
                return
            self._serialNumber = convert_name_to_serial(chipName)

    @property
    def run_number(self) -> bson.ObjectId:
        if not self._runNumber or bson.ObjectId.is_valid(self._runNumber):
            self._runNumber = bson.ObjectId()
        return self._runNumber

    @property
    def passed(self) -> bool:
        return self._passed

    def set_test_type(self, test_type: TestType | None = None) -> None:
        if test_type is not None:
            self._testType = test_type
        else:
            self._testType = ""

    def set_subtest_type(self, subtest_type: SubTestType | None = None) -> None:
        if subtest_type is not None:
            self._subtestType = subtest_type
        else:
            self._subtestType = ""

    def set_pass_flag(self, passed: bool = False) -> None:
        self._passed = passed

    def set_results(self, results: qcDataFrame | None = None) -> None:
        if results is not None:
            self._results = results
        else:
            self._results = qcDataFrame()
        if self._serialNumber == "Unknown":
            self.set_serial_num()

    def get_results(self) -> qcDataFrame:
        return self._results

    def to_dict(self, forAnalysis: bool = False) -> OutputQCDict:
        _dict: OutputQCDict = {
            "serialNumber": self._serialNumber,
            "testType": self._testType,
            "runNumber": str(self.run_number),
            "results": {},
        }
        if not forAnalysis:
            _dict.update({"subtestType": self._subtestType})
        all_results = self.get_results().to_dict()

        _dict["results"]["DCSdata"] = all_results["DCSdata"]
        all_results_metadata = (
            all_results.get("metadata", {}) or all_results["Metadata"]
        )

        # Write out different information, depending on if we are in measurement or analysis step
        if not forAnalysis:
            _dict["results"]["Measurements"] = all_results["Measurements"]
            _dict["results"]["Metadata"] = all_results_metadata
            _dict["results"]["comment"] = all_results["comment"]
        else:
            metadata_keep = [
                "MEASUREMENT_VERSION",
                "YARR_VERSION",
                "MEASUREMENT_DATE",
                "QC_LAYER",
                "INSTITUTION",
                "MODULE_SN",
            ]  # Metadata we want to write out
            _dict["results"]["Metadata"] = {
                k: v for k, v in all_results_metadata.items() if k in metadata_keep
            }
            _dict["results"].update(all_results["parameter"])
            _dict["passed"] = self._passed

        _dict["results"]["property"] = all_results["property"]

        return _dict

    def save_json(self, path: PathLike, forAnalysis: bool = False) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        _dict = self.to_dict(forAnalysis)
        with Path(path).open("w", encoding="UTF-8") as fp:
            json.dump(_dict, fp, cls=MyEncoder, indent=4)

    def from_dict(self, _dict: OutputQCDict) -> None:
        self._serialNumber = _dict["serialNumber"]
        self._testType = _dict["testType"]
        self._subtestType = _dict.get("subtestType", "")
        self._runNumber = (
            bson.ObjectId(_dict["runNumber"])
            if bson.ObjectId.is_valid(_dict.get("runNumber"))
            else bson.ObjectId()
        )
        self._passed = _dict.get("passed", False)
        try:
            self._results = qcDataFrame(_dict=_dict.get("results"))  # type: ignore[arg-type]
        except Exception:
            self._results = _dict.get("results")  # type: ignore[assignment]
