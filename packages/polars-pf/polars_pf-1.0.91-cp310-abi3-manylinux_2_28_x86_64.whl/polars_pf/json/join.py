from typing import Dict, List, Union

from msgspec import Struct

from .filter import PTableRecordFilter
from .spec import PColumnSpec, PObjectId

PColumnValue = Union[None, int, float, str]


class JsonDataInfo(Struct, rename="camel", tag="Json"):
    key_length: int
    data: Dict[str, PColumnValue]


class ConstantAxisFilter(Struct, rename="camel", tag="constant"):
    axis_index: int
    constant: Union[int, float, str]


class ColumnJoinEntry(Struct, rename="camel", tag="column"):
    column_id: PObjectId


class SlicedColumnJoinEntry(Struct, rename="camel", tag="slicedColumn"):
    column_id: PObjectId
    new_id: PObjectId
    axis_filters: List[ConstantAxisFilter]


class ArtificialColumnJoinEntry(Struct, rename="camel", tag="artificialColumn"):
    column_id: PObjectId
    new_id: PObjectId
    axes_indices: List[int]


class InlineColumnJoinEntry(Struct, rename="camel", tag="inlineColumn"):
    new_id: PObjectId
    spec: PColumnSpec
    data_info: JsonDataInfo


class InnerJoin(Struct, rename="camel", tag="inner"):
    entries: List["JoinEntry"]


class FullJoin(Struct, rename="camel", tag="full"):
    entries: List["JoinEntry"]


class OuterJoin(Struct, rename="camel", tag="outer"):
    primary: "JoinEntry"
    secondary: List["JoinEntry"]


JoinEntry = Union[
    ColumnJoinEntry,
    SlicedColumnJoinEntry,
    ArtificialColumnJoinEntry,
    InlineColumnJoinEntry,
    InnerJoin,
    FullJoin,
    OuterJoin,
]


class CreateTableRequest(Struct, rename="camel", omit_defaults=True):
    src: JoinEntry
    filters: List[PTableRecordFilter]
