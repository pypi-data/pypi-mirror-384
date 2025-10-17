from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from enum import Enum, IntEnum
from functools import lru_cache
from pathlib import Path
from typing import ClassVar, Literal, Optional, overload
from urllib.parse import urljoin

import itksn
import requests
from packaging.version import Version
from rich.console import Console
from rich.highlighter import RegexHighlighter
from rich.style import Style
from rich.theme import Theme

from module_qc_database_tools.typing_compat import Annotated, Dict, ModuleType

log = logging.getLogger(__name__)


class ComponentType(IntEnum):
    """
    An enum for component types.
    """

    SensorTile: Annotated[int, "SensorTile"] = 0
    FeChip: Annotated[int, "FeChip"] = 1
    BareModule: Annotated[int, "BareModule"] = 2
    TripletModule: Annotated[int, "TripletModule"] = 3
    QuadModule: Annotated[int, "QuadModule"] = 4


class DataMergingMode(str, Enum):
    """
    Enum for data merging modes.
    """

    FourToOne = "4-to-1"
    TwoToOne = "2-to-1"


class DPPort(str, Enum):
    """
    Enum for DP Port labeling on PCIe cards.
    """

    A = "A"
    B = "B"
    C = "C"
    D = "D"


@dataclass(frozen=True)
class BOM:
    """
    BOM dataclass to store version, RExtA and RExtD information
    """

    version: str
    rext_a: int
    rext_d: int


class BOMLookupTable:
    """
    BOM LookupTable using a dataclass for structured data.
    """

    _table: ClassVar[Dict[str, BOM]] = {
        "09": BOM("_V1bom", 0, 0),
        "10": BOM("_V1bom", 511, 407),
        "11": BOM("_V1bom", 732, 549),
        "12": BOM("_V1bom", 866, 590),
        "20": BOM("_V2bom", 475, 383),
        "21": BOM("_V2bom", 715, 576),
        "22": BOM("_V2bom", 845, 576),
    }

    @classmethod
    def get_bom_data(cls, bom_code: str) -> BOM:
        """Retrieves BOM dataclass instance, or None if not found."""
        return cls._table.get(bom_code, BOM("Unknown", -1, -1))

    @classmethod
    def get_rext_a(cls, bom_code: str) -> int:
        """Retrieves RExtA for a given BOM code."""
        if cls.check_key(bom_code):
            return cls.get_bom_data(bom_code).rext_a

        msg = f"The BOM code '{bom_code}' is not supported for now"
        raise ValueError(msg)

    @classmethod
    def get_rext_d(cls, bom_code: str) -> int:
        """Retrieves RExtD for a given BOM code."""
        if cls.check_key(bom_code):
            return cls.get_bom_data(bom_code).rext_d

        msg = f"The BOM code '{bom_code}' is not supported for now"
        raise ValueError(msg)

    @classmethod
    def get_version(cls, bom_code: str) -> str:
        """Retrieves the BOM version string"""
        if cls.check_key(bom_code):
            return cls.get_bom_data(bom_code).version

        msg = f"The BOM code '{bom_code}' is not supported for now"
        raise ValueError(msg)

    @classmethod
    def check_key(cls, key: str) -> bool:
        """Check if key is in the BOM table"""
        return key in cls._table


def default_BOMCode_from_layer(layer: str):
    """
    Return BOMCode for V1.1 version, with appropriate layer information
    """
    bom_code = "09"
    try:
        layer_number = int(layer[1:2])  # Extract number from "L1", "L2", etc.
        bom_code = f"1{layer_number}"
    except IndexError as e:
        msg = f"The layer {layer} string does not have the assumed format. Something is very wrong."
        raise IndexError(msg) from e

    return bom_code


def get_BOMCode_from_file(fpath: Path, layer: str):
    """
    Return the BOM code from the SN_info.json file
    If the file with the extra information is not available, or has the wrong format, an exception is raised
    If the code in prodDB is not set, it gets set to "09". This functions update it accordingly to the layer information, and assume it's V1.1
    """

    file_path = Path(fpath)

    if not file_path.exists():
        msg = f"The module_info.json file is not present locally. Please pull the chip config again, the file '{file_path}' will be generated."
        raise FileNotFoundError(msg)

    try:
        extra_info_file = json.loads(file_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        msg = f"Error decoding JSON from '{file_path}': {e}"
        log.error(msg)
        raise json.JSONDecodeError from e

    # set the BOM code to the default value
    bom_code_from_file = "09"

    try:
        bom_code_from_file = extra_info_file["PCB_BOM_VERSION"]["code"]
    except KeyError as e:
        msg = "The info.json file that contains the BOM information does not have the correct format"
        raise KeyError(msg) from e

    if bom_code_from_file in ("09", "Unknown"):
        msg = f"The information on the BOM version was not saved in prodDB '{bom_code_from_file}'. Will assume V1.1 BOM"
        log.warning(msg)
        bom_code_from_file = default_BOMCode_from_layer(layer)

    return bom_code_from_file


def get_cutFile_suffix(BOMcode):
    """
    Return the suffix for the mqat cut file associated with the BOM version
    """
    return BOMLookupTable.get_version(BOMcode)


def get_nominal_Rext(rail, BOMcode):
    """
    Return the value of the external resistors associated with a given layer and BOM
    """

    if BOMcode == "09":
        msg = f"The BOMcode has value '{BOMcode}', which is associated with RextA=RextD=0. This should never happen."
        raise ValueError(msg)

    Rext = 0
    if rail == "A":
        Rext = BOMLookupTable.get_rext_a(BOMcode)

    if rail == "D":
        Rext = BOMLookupTable.get_rext_d(BOMcode)

    return Rext


def get_component_type(serial_number: str) -> ComponentType:
    """
    Returns component type for the serial number.
    """
    info = itksn.parse(serial_number.encode("utf-8"))

    assert "pixel" in info.project_code.title().lower(), (
        "This is not a pixel project component."
    )

    if "sensor_tile" in info.component_code.title().lower():
        return ComponentType.SensorTile

    if "fe_chip" in info.component_code.title().lower():
        return ComponentType.FeChip

    if "bare_module" in info.component_code.title().lower():
        return ComponentType.BareModule

    if (
        "triplet" in info.component_code.title().lower()
        and "module" in info.component_code.title().lower()
    ):
        return ComponentType.TripletModule

    if "quad_module" in info.component_code.title().lower():
        return ComponentType.QuadModule

    msg = (
        f"{serial_number} does not correspond to a sensor tile, bare module, or module."
    )
    raise ValueError(msg)


@overload
def get_chip_connectivity(
    dp_port: DPPort,
    chip_index: Literal[0, 1, 2],
    module_type: Literal["triplet"],
    reverse: bool,
    data_merging: DataMergingMode,
): ...


@overload
def get_chip_connectivity(
    dp_port: DPPort,
    chip_index: Literal[0, 1, 2, 3],
    module_type: Literal["quad"],
    reverse: bool,
    data_merging: DataMergingMode,
): ...


def get_chip_connectivity(
    dp_port: DPPort,
    chip_index: int,
    module_type: ModuleType = "quad",
    reverse: bool = False,
    data_merging: Optional[DataMergingMode] = None,  # noqa: UP045
):
    """
    Get chip connectivity information for a chip on a triplet or quad module.

    Triplets use 4x4 firmware:

    - tx = 0 fixed by data adapter card,
    - rx = 0, 1, 2, 3

    Quads use 16x1 firmware:

    - tx = 0, 1, 2, 3
    - rx is one of the following depending on the DP port used

       - `A`: 0, 1, 2, 3
       - `B`: 4, 5, 6, 7
       - `C`: 8, 9, 10, 11
       - `D`: 12, 13, 14, 15

    """
    if module_type == "single":
        ports = [port.value for port in DPPort]
        if dp_port in ports:
            tx = ports.index(dp_port)
            rx = tx * 4
        else:
            msg = "could not determine rx/tx settings"
            raise RuntimeError(msg)
    elif module_type == "triplet":
        tx = 0
        rx = [2, 1, 0][chip_index] if reverse else [0, 1, 2][chip_index]
    else:
        ports = [port.value for port in DPPort]
        if dp_port in ports:
            tx = ports.index(dp_port)
            if data_merging == DataMergingMode.TwoToOne:
                rx = [3 + tx * 4, 1 + tx * 4, 1 + tx * 4, 3 + tx * 4][chip_index]
            elif data_merging == DataMergingMode.FourToOne:
                rx = [3 + tx * 4, 3 + tx * 4, 3 + tx * 4, 3 + tx * 4][chip_index]
            else:
                rx = [2 + tx * 4, 1 + tx * 4, 0 + tx * 4, 3 + tx * 4][chip_index]
        else:
            msg = "could not determine rx/tx settings"
            raise RuntimeError(msg)
    return tx, rx


@lru_cache
def get_localdb_versions(localdb_uri: str):
    """
    Get the tool versions of the localDB server.
    """
    response = requests.get(
        urljoin(localdb_uri, "version"),
        timeout=10,
        headers={"Accept": "application/json"},
    )
    try:
        return response.json()
    except ValueError:
        return {
            "python": "0.0.0",
            "localdb": "0.0.0",
            "itkdb": "0.0.0",
            "mqat": "0.0.0",
            "mqdbt": "0.0.0",
        }


def check_localdb_version(localdb_uri: str, required: str = "2.4.0"):
    """
    Check the localdb version is at least the required version specified.
    """
    versions = get_localdb_versions(localdb_uri)
    localdb_version = versions["localdb"]
    if Version(localdb_version) < Version(required):
        msg = f"localDB version {localdb_version} < {required}. Please update your localDB."
        raise RuntimeError(msg)


class ATLASHighlighter(RegexHighlighter):
    """Apply style to anything that looks like:

    - ATLAS Serial Number
    - Stage
    """

    base_style: ClassVar[str] = "atlas."
    highlights: ClassVar[list[str]] = [
        r"(?P<sn_atlas_project>\d{2})(?P<sn_system_code>[A-Z])(?P<sn_project_code>[A-Z])(?P<sn_subproject_code>[A-Z])(?P<sn_component_code>[A-Z0-9]{2})(?P<sn_identifier>[A-Z0-9]{7})",
        r"(?P<stage_component>[A-Z]+)(?P<stage_separator>/)(?P<stage_name>[A-Z_]+)",
    ]


theme = Theme(
    {
        "atlas.sn_atlas_project": Style(color="bright_black"),
        "atlas.sn_system_code": Style(color="bright_black"),
        "atlas.sn_project_code": Style(color="bright_yellow"),
        "atlas.sn_subproject_code": Style(color="bright_yellow"),
        "atlas.sn_component_code": Style(color="bright_red"),
        "atlas.sn_identifier": Style(color="yellow"),
        "atlas.stage_component": Style(color="cyan"),
        "atlas.stage_separator": Style(color="bright_black"),
        "atlas.stage_name": Style(color="green"),
        "atlas.test_name": Style(color="green"),
    }
)

console = Console(highlighter=ATLASHighlighter(), theme=theme)
