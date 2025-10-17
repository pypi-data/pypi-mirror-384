"""
Typing helpers.
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Annotated, Any, Literal, TypedDict, Union

if TYPE_CHECKING:
    import os

from collections.abc import Generator

if sys.version_info >= (3, 10):
    from typing import TypeAlias

    Dict = dict
    List = list
else:
    from typing_extensions import TypeAlias

if sys.version_info >= (3, 11):
    from typing import NotRequired
else:
    from typing_extensions import NotRequired

PathLike: TypeAlias = Union[str, "os.PathLike[str]"]
Layer: TypeAlias = Literal["R0", "R0.5", "L0", "L1", "L2", "L3", "L4"]
SerialNumber: TypeAlias = str
ChipType: TypeAlias = Literal["RD53B", "ITKPIXV2"]
TestType: TypeAlias = Literal[
    "",
    "ADC_CALIBRATION",
    "ANALOG_READBACK",
    "CUTTER_PCB_TAB",
    "DATA_TRANSMISSION",
    "INJECTION_CAPACITANCE",
    "IV_MEASURE",
    "LONG_TERM_STABILITY_DCS",
    "LP_MODE",
    "OVERVOLTAGE_PROTECTION",
    "SLDO",
    "UNDERSHUNT_PROTECTION",
    "VCAL_CALIBRATION",
]
SubTestType: TypeAlias = Literal[
    "",
    "AR_REGISTER",
    "AR_TEMP",
    "AR_VDD",
    "AR_VMEAS",
    "VCAL_HIGH",
    "VCAL_HIGH_SMALL_RANGE",
    "VCAL_MED",
    "VCAL_MED_SMALL_RANGE",
    "DT_EYE",
    "DT_MERGE",
]

ParamLeaf: TypeAlias = Union[float, list[float]]
ParamValue: TypeAlias = Union[ParamLeaf, dict[str, ParamLeaf]]


class QCDict(TypedDict):
    DCSdata: dict[str, Any]
    Measurements: dict[str, Any]
    Metadata: dict[str, Any]
    comment: str
    metadata: NotRequired[dict[str, Any]]
    parameter: dict[str, Any]
    property: dict[str, Any]


class OutputQCDict(TypedDict):
    serialNumber: str
    testType: TestType
    subtestType: NotRequired[SubTestType]
    runNumber: str
    passed: NotRequired[bool]
    results: dict[str, Any]


__all__ = (
    "Annotated",
    "Generator",
    "Layer",
    "PathLike",
    "QCDict",
    "SerialNumber",
    "TestType",
    "TypeAlias",
)
