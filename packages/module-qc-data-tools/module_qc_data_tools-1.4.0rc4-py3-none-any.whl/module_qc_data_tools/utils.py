from __future__ import annotations

import json
import logging
import re

# see https://stackoverflow.com/a/15012814/355230
from _ctypes import PyObj_FromPtr  # pylint: disable=wrong-import-order
from importlib import resources
from pathlib import Path
from typing import Any, TypeVar

import itksn
from construct.core import ConstructError
from jsonschema import Draft202012Validator
from jsonschema.exceptions import best_match

from module_qc_data_tools.typing_compat import (
    ChipType,
    Generator,
    Layer,
    PathLike,
    SerialNumber,
)

datapath = resources.files("module_qc_data_tools") / "data"

log = logging.getLogger(__name__)


class MyEncoder(json.JSONEncoder):
    FORMAT_SPEC: str = "@@{}@@"  # Unique string pattern of NoIndent object ids.
    regex: re.Pattern[str] = re.compile(
        FORMAT_SPEC.format(r"(\d+)")
    )  # compile(r'@@(\d+)@@')

    def __init__(self, **kwargs: Any) -> None:
        # Keyword arguments to ignore when encoding NoIndent wrapped values.
        ignore = {"cls", "indent"}

        # Save copy of any keyword argument values needed for use here.
        self._kwargs: dict[str, Any] = {
            k: v for k, v in kwargs.items() if k not in ignore
        }
        super().__init__(**kwargs)

    def default(self, o: Any) -> Any:
        return (
            self.FORMAT_SPEC.format(id(o))
            if isinstance(o, list)
            else super().default(o)
        )

    def iterencode(self, o: Any, _one_shot: bool = False) -> Generator[str, None, None]:
        format_spec = self.FORMAT_SPEC  # Local var to expedite access.

        # Replace any marked-up NoIndent wrapped values in the JSON repr
        # with the json.dumps() of the corresponding wrapped Python object.
        for encoded in super().iterencode(o, _one_shot):
            match = self.regex.search(encoded)
            new_encoded = encoded
            if match:
                the_id = int(match.group(1))
                no_indent = PyObj_FromPtr(the_id)
                json_repr = json.dumps(no_indent.value, **self._kwargs)
                new_encoded = encoded.replace(
                    f'"{format_spec.format(the_id)}"', json_repr
                )

            yield new_encoded


def save_dict_list(path: PathLike, output: list[dict[str, Any]]) -> None:
    serial_numbers: list[SerialNumber] = []

    passed_values = [out.get("passed") for out in output]
    all_none = all(v is None for v in passed_values)
    all_not_none = all(v is not None for v in passed_values)

    if not (all_none or all_not_none):
        log.error(
            "List of dictionaries being saved to output contain both measurement and output formats. Please fix."
        )
        return

    analysis_output: list[dict[str, Any]] = []
    measurement_output: list[list[dict[str, Any]]] = []

    # Separate into separate lists for each chip if saving measurement output
    if all_not_none:
        analysis_output = [*output]
    else:
        # For measurement, group by serialNumber
        measurement_output = []
        for out in output:
            serial_number = out["serialNumber"]

            if serial_number in serial_numbers:
                measurement_output[serial_numbers.index(serial_number)].append(out)
            else:
                serial_numbers.append(serial_number)
                measurement_output.append([out])

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="UTF-8") as fp:
        json.dump(analysis_output or measurement_output, fp, cls=MyEncoder, indent=4)


def convert_name_to_serial(chip_name: str) -> str:
    serialPrefix = "20UPGFC"  # This will change to 20UPGFW for real wafers
    try:
        chip_number = str(int(chip_name, base=16))
        # Add preceding zeros
        while len(chip_number) < 7:
            chip_number = "0" + chip_number
        return serialPrefix + str(chip_number)
    except Exception:
        msg = f"Can't convert chip name ({chip_name}) into serial number, setting serial number to {chip_name}"
        log.warning(msg)
        return chip_name


def convert_serial_to_name(serial_number: str) -> str:
    # Assumes prefix is of length 7 (i.e. "20UPGFC")
    try:
        # Remove prefix and preceding 0's
        chip_name = hex(int(serial_number[7:].lstrip("0")))
    except Exception:
        chip_name = serial_number
        msg = f"Can't convert chip serial number ({serial_number}) into name, setting chip name to {serial_number}"
        log.warning(msg)
    return chip_name


def get_nominal_current(
    meas_config: dict[str, Any],
    layer: Layer,
    chip_type: ChipType,
    BOM_type: str,
    n_chips_input: int = 0,
) -> float:
    default_n_chips_in_module = get_n_chips(layer)

    if n_chips_input > default_n_chips_in_module:
        msg = f"Invalid input: input n chips ({n_chips_input}) is higher than the default n chips for the given module type ({default_n_chips_in_module})"
        log.error(msg)
        raise ValueError(msg)

    chip_type_bom = str(chip_type)
    if chip_type == "ITKPIXV2":
        if BOM_type in ["_V1bom", "_V2bom"]:
            chip_type_bom += BOM_type
        else:
            msg = f"Invalid BOM type ({BOM_type}) for {chip_type} chip"
            log.error(msg)
            raise ValueError(msg)

    try:
        nom_current: float = (
            meas_config["tasks"]["GENERAL"]["i_config"][chip_type_bom][layer]
            / default_n_chips_in_module
        )
        msg = f"Retrieved the nominal chip current for ChipType {chip_type_bom} and layer {layer} as {nom_current} A"
        log.debug(msg)
    except KeyError:
        log.exception("Missing key in configuration")
        raise
    except ZeroDivisionError:
        log.exception("Division by zero")
        raise
    except TypeError:
        log.error("Invalid JSON structure")
        raise
    except Exception:
        log.exception("Cannot retrieve nominal current from meas_config")
        raise

    n_chips = default_n_chips_in_module
    if n_chips_input not in {0, default_n_chips_in_module}:
        log.warning(
            "Overwriting default number of chips (%s) with manual input (%s)!",
            default_n_chips_in_module,
            n_chips_input,
        )
        n_chips = n_chips_input

    current = nom_current * n_chips
    msg = f"With {n_chips} of {default_n_chips_in_module} chips enabled, the nominal PS current is {current} A"
    log.debug(msg)

    return current


def get_n_chips(layer: Layer) -> int:
    chips_per_layer = {"L0": 3, "L1": 4, "L2": 4}
    return chips_per_layer.get(layer, 0)


# Returns module type component code, given module serial number
def get_type_from_sn(module_serial_number: SerialNumber) -> str:
    module_types = {
        "PI": {
            "MS": "TRIPLET_L0_STAVE_MODULE",
            "M0": "TRIPLET_L0_RING0_MODULE",
            "M5": "TRIPLET_L0_RING0.5_MODULE",
            "M1": "L1_QUAD_MODULE",
            "R6": "DIGITAL_TRIPLET_L0_STAVE_MODULE",
            "R7": "DIGITAL_TRIPLET_L0_RING0_MODULE",
            "R8": "DIGITAL_TRIPLET_L0_RING0.5_MODULE",
            "RB": "DIGITAL_L1_QUAD_MODULE",
            "RT": "DUMMY_TRIPLET_L0_STAVE_MODULE",
            "RU": "DUMMY_TRIPLET_L0_RING0_MODULE",
            "RV": "DUMMY_TRIPLET_L0_RING0.5_MODULE",
        },
        "PG": {
            "M2": "OUTER_SYSTEM_QUAD_MODULE",
            "R0": "SINGLE_CHIP_MODULE",
            "R2": "DUAL_CHIP_MODULE",
            "R9": "DIGITAL_QUAD_MODULE",
            "RQ": "DUMMY_QUAD_MODULE",
            "RR": "DUMMY_L1_QUAD_MODULE",
            "XM": "TUTORIAL_MODULE",
        },
    }

    try:
        return module_types[module_serial_number[3:5]][module_serial_number[5:7]]
    except Exception:
        msg = f"Unknown module type ({module_serial_number}) - will not separate inner from outer pixels in disconnected bump analysis"
        log.warning(msg)
        return "unknown"


def get_sensor_type_from_sn(sensor_serial_number: SerialNumber) -> str:
    sensor_types = {
        "S0": "L0_INNER_PIXEL_3D_SENSOR_TILE_25",
        "S1": "L0_INNER_PIXEL_3D_SENSOR_TILE_50",
        "S2": "L1_INNER_PIXEL_QUAD_SENSOR_TILE",
        "S3": "OUTER_PIXEL_QUAD_SENSOR_TILE",
    }
    try:
        return sensor_types[sensor_serial_number[5:7]]
    except KeyError as exc:
        msg = f"Unknown sensor type for serial number: {sensor_serial_number}"
        raise ValueError(msg) from exc


def get_sensor_type_from_layer(layer: Layer) -> str:
    sensor_type: dict[Layer, str] = {
        "R0": "3D",
        "R0.5": "3D",
        "L0": "3D",
        "L1": "L1_INNER_PIXEL_QUAD_SENSOR_TILE",
        "L2": "OUTER_PIXEL_QUAD_SENSOR_TILE",
        "L3": "OUTER_PIXEL_QUAD_SENSOR_TILE",
        "L4": "OUTER_PIXEL_QUAD_SENSOR_TILE",
    }
    try:
        return sensor_type[layer]
    except KeyError as exc:
        msg = f"Layer {layer} invalid!"
        raise ValueError(msg) from exc


# requires the connectivity file name to be "<SerialNumber>_<layer>_<suffix>.json" as output from the database tool
def get_sn_from_connectivity(path: PathLike) -> SerialNumber:
    try:
        module_serial_number = Path(path).stem.split("_")[0]
        check_sn_format(module_serial_number)
    except Exception as exc:
        msg = f"Cannot extract module serial number from path ({path})"
        log.exception(msg)
        raise ValueError(msg) from exc
    return module_serial_number


def get_layer_from_sn(serial_number: SerialNumber, for_analysis: bool = True) -> Layer:
    check_sn_format(serial_number)

    parsed = itksn.parse(serial_number.encode("utf-8"))

    if parsed.component_code.bytevalue in [b"B1", b"FC"]:
        return (
            "L2"  # Doesn't look like there is anything dependent on SCC vs module flex
        )

    if parsed.project_code == "pixel":
        if parsed.subproject_code == "inner_pixel":
            if parsed.component_code.bytevalue in [b"MS", b"R6"]:
                return "L0"

            if parsed.component_code.bytevalue in [b"M0", b"R7"]:
                return "R0" if not for_analysis else "L0"

            if parsed.component_code.bytevalue in [b"M5", b"R8"]:
                return "R0.5" if not for_analysis else "L0"

            if parsed.component_code.bytevalue in [b"M1", b"RB"]:
                return "L1"
        elif parsed.subproject_code in ["pixel_general", "outer_pixel_barrel"]:
            return "L2"

    msg = f"Cannot recognise {serial_number}, not a valid module serial number."
    log.error(msg)
    raise ValueError(msg)


def get_nlanes_from_sn(serial_number: SerialNumber) -> int:
    check_sn_format(serial_number)
    if "PIMS" in serial_number or "PIR6" in serial_number:
        return 4  # L0

    if "PIM0" in serial_number or "PIR7" in serial_number:
        return 3  # R0

    if "PIM5" in serial_number or "PIR8" in serial_number:
        return 2  # R0.5

    if "PIM1" in serial_number or "PIRB" in serial_number:
        return 1  # L1

    if "PG" in serial_number:
        return 1  # L2-L4

    msg = f"Cannot get the number of lanes from this serial number: {serial_number} \U0001f937"
    log.error(msg)
    raise ValueError(msg)


def check_sn_format(serial_number: SerialNumber) -> bool:
    """
    Checks if the serial number is a valid ATLAS Serial Number.

    Example:

    ```pycon
    >>> import module_qc_data_tools
    >>> module_qc_data_tools.utils.check_sn_format("20UPGM23310161")
    True
    >>> module_qc_data_tools.utils.chip_serial_number_to_uid("fake")
    Traceback (most recent call last):
    ...
    ValueError: Cannot recognize ATLAS serial number ...
    ```
    """
    try:
        itksn.parse(serial_number.encode("utf-8"))
    except ConstructError as exc:
        msg = f"Cannot recognise ATLAS serial number {serial_number}. Please enter a valid ATLAS serial number."
        raise ValueError(msg) from exc

    return True


def chip_serial_number_to_uid(serial_number: SerialNumber) -> str:
    """
    Convert chip serial number to hexadecimal UID.

    ```pycon
    >>> import module_qc_data_tools
    >>> module_qc_data_tools.utils.chip_serial_number_to_uid("20UPGM23310161")
    Traceback (most recent call last):
    ...
    AssertionError: Serial number must be for a valid RD53 chip
    >>> module_qc_data_tools.utils.chip_serial_number_to_uid("20UPGFC3310161")
    '0x328251'
    ```
    """
    parsed = itksn.parse(serial_number.encode("utf-8"))

    assert parsed.component_code.bytevalue == b"FC", (
        "Serial number must be for a valid RD53 chip"
    )
    return hex(int(parsed.identifier.number))


def chip_uid_to_serial_number(uid: str) -> SerialNumber:
    """
    Convert chip hexadecimal UID to serial number.

    Example:

    ```pycon
    >>> import module_qc_data_tools
    >>> module_qc_data_tools.utils.chip_uid_to_serial_number("0x328251")
    '20UPGFC3310161'
    ```
    """
    try:
        data = {
            "atlas_project": "atlas_detector",
            "system_code": "phaseII_upgrade",
            "project_code": "pixel",
            "subproject_code": "pixel_general",
            "component_code": "FE_chip",
            "identifier": {"number": f"{int(uid, 16):07}".encode()},
        }
    except TypeError as e:
        msg = f"uid is {uid}"
        raise TypeError(msg) from e
    return itksn.build(data).decode("utf-8")


def get_chip_type_from_serial_number(serial_number: SerialNumber) -> ChipType:
    """
    Convert module SN or chip SN to chip type

    Example:

    ```pycon
    >>> import module_qc_data_tools
    >>> module_qc_data_tools.utils.get_chip_type_from_serial_number("20UPIM14602031")
    'ITKPIXV2'
    ```

    """

    msg = f"Invalid serial number: {serial_number}"

    parsed = itksn.parse(serial_number.encode("utf-8"))

    if parsed.component_code.bytevalue == b"FC":
        if parsed.identifier.batch == "ITkpix_v2":
            return "ITKPIXV2"
        if parsed.identifier.batch == "ITkpix_v1":
            return "RD53B"

        raise ValueError(msg)

    if parsed.identifier.FE_chip_version.startswith("ITkpix_v2"):
        return "ITKPIXV2"

    if parsed.identifier.FE_chip_version in ["ITkpix_v1", "ITkpix_v1p1"]:
        return "RD53B"

    raise ValueError(msg)


def get_chip_type_from_config(config: dict[str, Any]) -> ChipType:
    """
    Get chip type from keyword in chip config
    """
    chiptype = ""
    try:
        chiptype = next(iter(config.keys()))
    except IndexError:
        log.error("One of your chip configuration files is empty")

    if chiptype not in {"RD53B", "ITKPIXV2"}:
        msg = f"Chip name in configuration not one of expected chip names (RD53B or ITKPIXV2). Got {chiptype}."
        raise ValueError(msg)
    return chiptype  # type: ignore[return-value]


def get_config_type_from_connectivity_path(connectivity: PathLike) -> str:
    """
    Returns measurement type e.g. "L2_warm" from the module connectivity file name ("<some path>/<modulesn>/<modulesn>_L2_warm.json").
    """
    return Path(connectivity).stem.split("_", maxsplit=1)[-1]


T = TypeVar("T")


def chunks(lst: list[T], n: int) -> Generator[list[T], None, None]:
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def validate_measurement(spec: list[list[dict[str, Any]]]) -> bool:
    schema = json.loads(
        (datapath / "schema_measurement.json").read_text(encoding="utf-8")
    )
    validator = Draft202012Validator(
        schema, format_checker=Draft202012Validator.FORMAT_CHECKER
    )

    errors = list(validator.iter_errors(spec))

    if not errors:
        return True

    # Pick the most relevant error
    best = best_match(errors)
    path = ".".join(str(p) for p in best.absolute_path) or "<root>"
    log.error("❌ Validation error at `%s`: %s", path, best.message)

    # Optional: show context if it's an anyOf/oneOf failure
    if best.context:
        log.error("→ Schema matching failed against multiple options:")
        for index, suberror in enumerate(best.context, 1):
            sub_path = ".".join(str(p) for p in suberror.absolute_path) or "<root>"
            log.error("   %d. `%s`: %s", index, sub_path, suberror.message)

    return False


def check_hw_config(spec: dict[str, Any]) -> bool:
    schema = json.loads(
        (datapath / "schema_hw_config.json").read_text(encoding="utf-8")
    )

    validator = Draft202012Validator(
        schema, format_checker=Draft202012Validator.FORMAT_CHECKER
    )

    errors = list(validator.iter_errors(spec))

    if not errors:
        return True

    # Pick the most relevant error
    best = best_match(errors)
    path = ".".join(str(p) for p in best.absolute_path) or "<root>"
    log.error("❌ Validation error at `%s`: %s", path, best.message)

    # Optional: show context if it's an anyOf/oneOf failure
    if best.context:
        log.error("→ Schema matching failed against multiple options:")
        for index, suberror in enumerate(best.context, 1):
            sub_path = ".".join(str(p) for p in suberror.absolute_path) or "<root>"
            log.error("   %d. `%s`: %s", index, sub_path, suberror.message)

    msg = "Input hardware config fails schema check"
    raise RuntimeError(msg)


def load_hw_config(config_path: PathLike) -> Any:
    with resources.as_file(Path(config_path)) as path:
        config = json.loads(path.read_text(encoding="utf-8"))

    # check if config is in the old format
    if "tasks" in config and "yarr" in config:
        log.error(
            "%s has both measurement and hardware configs in it. This config structure is now deprecated. You can generate a new config by calling the following:",
            config_path,
        )
        log.error("mqt split-old-config -c %s", config_path)

    check_hw_config(config)
    log.info("Using %s for hardware config", config_path)
    return config


__all__ = (
    "check_sn_format",
    "chip_serial_number_to_uid",
    "chip_uid_to_serial_number",
    "convert_name_to_serial",
    "convert_serial_to_name",
    "datapath",
    "get_chip_type_from_config",
    "get_chip_type_from_serial_number",
    "get_config_type_from_connectivity_path",
    "get_layer_from_sn",
    "get_n_chips",
    "get_nlanes_from_sn",
    "get_nominal_current",
    "get_sensor_type_from_layer",
    "get_sensor_type_from_sn",
    "get_sn_from_connectivity",
    "get_type_from_sn",
    "save_dict_list",
    "validate_measurement",
)
