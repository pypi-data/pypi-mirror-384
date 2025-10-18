from enum import Enum
from typing import Any, Dict, List, Optional, Union

from msgspec import Struct


class AxisType(str, Enum):
    Int = "Int"
    Long = "Long"
    String = "String"


class AxisId(Struct, rename="camel", omit_defaults=True):
    name: str
    type: AxisType
    domain: Optional[Dict[str, str]] = None


class AxisSpec(AxisId, rename="camel", omit_defaults=True):
    annotations: Optional[Dict[str, Any]] = None
    parent_axes: Optional[List[int]] = None


class ColumnType(str, Enum):
    Int = "Int"
    Long = "Long"
    Float = "Float"
    Double = "Double"
    String = "String"


PObjectId = str


class PColumnSpec(
    Struct, rename="camel", tag_field="kind", tag="PColumn", omit_defaults=True
):
    name: str
    value_type: ColumnType
    axes_spec: List[AxisSpec]
    domain: Optional[Dict[str, str]] = None
    annotations: Optional[Dict[str, Any]] = None
    parent_axes: Optional[List[int]] = None


class PTableColumnIdAxis(Struct, rename="camel", tag="axis"):
    id: AxisId


class PTableColumnIdColumn(Struct, rename="camel", tag="column"):
    id: PObjectId


PTableColumnId = Union[PTableColumnIdAxis, PTableColumnIdColumn]


class PTableColumnSpecAxis(Struct, rename="camel", tag="axis"):
    id: AxisId
    spec: AxisSpec


class PTableColumnSpecColumn(Struct, rename="camel", tag="column"):
    id: PObjectId
    spec: PColumnSpec


PTableColumnSpec = Union[PTableColumnSpecAxis, PTableColumnSpecColumn]

PTableColumnSpecs = List[PTableColumnSpec]
