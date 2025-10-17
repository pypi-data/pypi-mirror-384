from __future__ import annotations

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

from module_qc_data_tools.qcDataFrame import outputDataFrame, qcDataFrame
from module_qc_data_tools.typing_compat import (
    PathLike,
    TestType,
)

log = logging.getLogger(__name__)
log.setLevel("INFO")


def load_json(path: PathLike) -> list[outputDataFrame]:
    with Path(path).open(encoding="UTF-8") as serialized:
        inputdata = json.load(serialized)
    alldf = []
    # Can read measurement jsons (nested list) or analysis jsons (1D list)
    for chip in inputdata:
        if isinstance(chip, list):
            for _dict in chip:
                alldf += [outputDataFrame(_dict=_dict)]
        else:
            alldf += [outputDataFrame(_dict=chip)]
    return alldf


def load_iv_alt(
    path: PathLike, test_type: TestType, input_vdepl: float | None
) -> list[outputDataFrame] | None:
    ## loads data from sensor IV json format [1], input into non-electric-GUI [2] and output from non-electric-GUI [3]
    ## [1] https://gitlab.cern.ch/atlas-itk/sw/db/production_database_scripts/-/blob/pixel_preproduction_GUI/pixels/sensors_prototype/data/IV_DATA_TILE.json
    ## [2] https://gitlab.cern.ch/atlas-itk/pixel/module/module-qc-tools/uploads/b0c6d5edde5514865e27574810a3a449/ivcurve_result_20230403_235249.json
    ## [3] https://gitlab.cern.ch/atlas-itk/pixel/module/module-qc-tools/uploads/8dbdc2f81ff479343318dfe25e6ae96d/20UPGXM2000013_MODULE__INITIAL_WARM_IV_MEASURE_2023Y03m27d__04_49_56+0000.json

    qchelper = False
    timestart: str | float | None = None

    with Path(path).open(encoding="utf-8") as serialized:
        if "QCHELPER" in serialized.read():
            qchelper = True
        serialized.seek(0)  ## move cursur back to the beginning of file
        inputdata = json.load(serialized)

    alldf = []
    # Can read one IV measurement in sensor json format at a time
    if not isinstance(inputdata, list):
        inputdata = [inputdata]
        log.info("Found data for one measurement.")
    else:
        log.info("Found data for {%i} measurement(s).", len(inputdata))
        if qchelper:
            log.info("Output format from QC helper/non-electric GUI detected.")

    for item in inputdata:
        module_sn = ""
        test = ""
        institution = ""
        date = ""
        prefix = None
        vdepl: float = 0
        IV_ARRAY: dict[str, Any] = {}

        iv_array = {}

        keys = {
            "component": module_sn,
            "test": test,
            "institution": institution,
            "date": date,
            "prefix": prefix,
            "depletion_voltage": vdepl,
            "IV_ARRAY": IV_ARRAY,
        }

        for key in keys:
            if key not in item and not qchelper:
                log.warning("Key {%s} is missing in the input file!", key)
        if not qchelper:
            if item["component"]:
                module_sn = item["component"]
            else:
                log.error("No module SN found.")
                return None

            if "iv" not in item["test"].lower():
                log.error("No test type found.")
                return None

            try:
                institution = item["institution"]
            except Exception:
                log.warning("No institution found in measurement file!")
                institution = ""

            try:
                if item["date"]:
                    try:
                        timestart = time.mktime(
                            datetime.strptime(
                                item["date"], "%d.%m.%Y %H:%M"
                            ).timetuple()
                        )
                    except Exception:
                        log.warning("Cannot decode time stamp format {err}")
                        timestart = item["date"]
            except Exception:
                log.warning("No measurement time found.")
                timestart = datetime.now().strftime("%Y-%m-%d_%H%M%S")

            try:
                vdepl = item["depletion_voltage"]
            except Exception:
                if input_vdepl is not None:
                    vdepl = input_vdepl
                    log.warning(
                        "No depletion voltage found, using manual input via --vdepl."
                    )
                else:
                    log.warning(
                        "No depletion voltage found! Will use database or default value."
                    )
            if item["IV_ARRAY"]:
                iv_array = item["IV_ARRAY"]
            else:
                log.error("No measurement data found!")
                return None
            current_unit = "uA"
            try:
                if item["prefix"] and "A" in item["prefix"]:
                    current_unit = item["prefix"]
            except Exception:
                log.warning(
                    "No prefix found. Assuming default current unit {%s}!", current_unit
                )
        else:
            if len(item) == 1:
                jtem = item[0]
            else:
                log.error("Unknown format.")
                return None

            metadata = jtem["results"].get("Metadata") or jtem["results"].get(
                "metadata"
            )

            if jtem["serialNumber"] == metadata["MODULE_SN"]:
                module_sn = jtem["serialNumber"]
            elif not jtem["serialNumber"] and metadata["MODULE_SN"]:
                module_sn = metadata["MODULE_SN"]
            elif jtem["serialNumber"] and not metadata["MODULE_SN"]:
                module_sn = jtem["serialNumber"]
            else:
                log.error("'serialNumber' and 'MODULE_SN' are inconsistent or missing!")
                return None

            if "IV_MEASURE" not in jtem["testType"]:
                log.error("No test type found.")
                return None

            ## not there by default
            try:
                institution = jtem["institution"]
            except Exception:
                log.warning("No institution found in measurement file!")
                institution = ""

            try:
                if jtem["date"]:
                    try:
                        timestart = time.mktime(
                            datetime.strptime(
                                jtem["date"], "%d.%m.%Y %H:%M"
                            ).timetuple()
                        )
                    except Exception as err:
                        log.warning("Cannot decode time stamp format {%s}", err)
                        timestart = jtem["date"]
            except Exception:
                log.warning("No measurement time found, using current time.")
                timestart = datetime.now().strftime("%Y-%m-%d_%H%M%S")

            try:
                vdepl = jtem["depletion_voltage"]
            except Exception:
                if input_vdepl is not None:
                    vdepl = input_vdepl
                    log.warning(
                        "No depletion voltage found, using manual input via --vdepl ."
                    )
                else:
                    log.warning(
                        "No depletion voltage found! Will use database or default value."
                    )
            if jtem["results"]["IV_ARRAY"]:
                iv_array = jtem["results"]["IV_ARRAY"]
            else:
                log.error("No measurement data found!")
                return None

            current_unit = "uA"
            try:
                if jtem["prefix"] and "A" in jtem["prefix"]:
                    current_unit = jtem["prefix"]
            except Exception:
                log.warning(
                    "No prefix found. Assuming default current unit {%s}!", current_unit
                )

        data = qcDataFrame(
            columns=[
                "time",
                "voltage",
                "current",
                "sigma current",
                "temperature",
                "humidity",
            ],
            units=["s", "V", current_unit, current_unit, "C", "%"],
        )

        data.set_x("voltage", True)
        data.add_data(iv_array)
        data.add_meta_data("Institution", institution)
        data.add_meta_data("ModuleSN", module_sn)
        data.add_meta_data("TimeStart", timestart)
        data.add_meta_data("DepletionVoltage", vdepl)
        data.add_meta_data("AverageTemperature", np.average(data["temperature"]))
        outputDF = outputDataFrame()
        outputDF.set_test_type(test_type)
        outputDF.set_results(data)
        alldf.append(outputDF)
    return alldf
