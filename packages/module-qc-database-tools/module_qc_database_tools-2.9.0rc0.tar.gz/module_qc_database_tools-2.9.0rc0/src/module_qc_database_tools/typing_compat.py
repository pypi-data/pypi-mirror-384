"""
Typing helpers.
"""

from __future__ import annotations

import sys
from typing import Annotated, Any, Callable, Literal, Union

Dict = dict
Tuple = tuple
Set = set

if sys.version_info >= (3, 10):
    from typing import TypeAlias
else:
    from typing_extensions import TypeAlias

LocalDBComponent: TypeAlias = Dict[str, Any]
ProdDBComponent: TypeAlias = Dict[str, Any]
ProdDBTestRun: TypeAlias = Dict[str, Any]
ModuleType: TypeAlias = Literal["single", "quad", "triplet"]
CheckFunction: TypeAlias = Callable[..., Union[bool, str, None]]
CheckResult: TypeAlias = Dict[str, Union[Tuple[Any, ...], bool, str]]

InstitutionCode: TypeAlias = Annotated[str, "institution code"]
StageCode: TypeAlias = Annotated[str, "stage code"]
TestTypeCode: TypeAlias = Annotated[str, "test type code"]

__all__ = (
    "Annotated",
    "CheckFunction",
    "CheckResult",
    "Dict",
    "InstitutionCode",
    "LocalDBComponent",
    "ModuleType",
    "ProdDBComponent",
    "ProdDBTestRun",
    "Set",
    "StageCode",
    "TestTypeCode",
    "Tuple",
    "TypeAlias",
)
