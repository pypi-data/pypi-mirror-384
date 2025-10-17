"""
PFrames: Python Polars extensions
"""

from importlib.metadata import version

__version__ = version("polars_pf")

from polars_pf._polars_pf import canonicalize

# Expressions module exports
from polars_pf.expressions import Expr, PFramesExpressionsNamespace

# IO module exports
from polars_pf.io_source import axis_ref, column_ref, pframe_source

# JSON module exports - Filter related
from polars_pf.json.filter import (
    PTableRecordFilter,
    SingleValueAndPredicate,
    SingleValueEqualPredicate,
    SingleValueGreaterOrEqualPredicate,
    SingleValueGreaterPredicate,
    SingleValueIEqualPredicate,
    SingleValueInSetPredicate,
    SingleValueIsNAPredicate,
    SingleValueLessOrEqualPredicate,
    SingleValueLessPredicate,
    SingleValueMatchesPredicate,
    SingleValueNotPredicate,
    SingleValueOrPredicate,
    SingleValuePredicate,
    SingleValueStringContainsFuzzyPredicate,
    SingleValueStringContainsPredicate,
    SingleValueStringIContainsFuzzyPredicate,
    SingleValueStringIContainsPredicate,
)

# JSON module exports - Join related
from polars_pf.json.join import (
    ArtificialColumnJoinEntry,
    ColumnJoinEntry,
    ConstantAxisFilter,
    CreateTableRequest,
    FullJoin,
    InlineColumnJoinEntry,
    InnerJoin,
    JoinEntry,
    JsonDataInfo,
    OuterJoin,
    PColumnValue,
    SlicedColumnJoinEntry,
)

# JSON module exports - Spec related
from polars_pf.json.spec import (
    AxisId,
    AxisSpec,
    AxisType,
    ColumnType,
    PColumnSpec,
    PObjectId,
    PTableColumnId,
    PTableColumnIdAxis,
    PTableColumnIdColumn,
    PTableColumnSpec,
    PTableColumnSpecAxis,
    PTableColumnSpecColumn,
    PTableColumnSpecs,
)

# Log module exports
from polars_pf.log import Logger, LogLevel, logger

# Perf timer module exports
from polars_pf.perf_timer import PerfTimer

__all__ = [
    "__version__",
    "canonicalize",
    # Expressions module exports
    "Expr",
    "PFramesExpressionsNamespace",
    # IO module exports
    "axis_ref",
    "column_ref",
    "pframe_source",
    # Filter module exports
    "PTableRecordFilter",
    "SingleValueAndPredicate",
    "SingleValueEqualPredicate",
    "SingleValueGreaterOrEqualPredicate",
    "SingleValueGreaterPredicate",
    "SingleValueIEqualPredicate",
    "SingleValueInSetPredicate",
    "SingleValueIsNAPredicate",
    "SingleValueLessOrEqualPredicate",
    "SingleValueLessPredicate",
    "SingleValueMatchesPredicate",
    "SingleValueNotPredicate",
    "SingleValueOrPredicate",
    "SingleValuePredicate",
    "SingleValueStringContainsFuzzyPredicate",
    "SingleValueStringContainsPredicate",
    "SingleValueStringIContainsFuzzyPredicate",
    "SingleValueStringIContainsPredicate",
    # Join module exports
    "ArtificialColumnJoinEntry",
    "ColumnJoinEntry",
    "ConstantAxisFilter",
    "CreateTableRequest",
    "FullJoin",
    "InlineColumnJoinEntry",
    "InnerJoin",
    "JoinEntry",
    "JsonDataInfo",
    "OuterJoin",
    "PColumnValue",
    "SlicedColumnJoinEntry",
    # Spec module exports
    "AxisId",
    "AxisSpec",
    "AxisType",
    "ColumnType",
    "PColumnSpec",
    "PObjectId",
    "PTableColumnId",
    "PTableColumnIdAxis",
    "PTableColumnIdColumn",
    "PTableColumnSpec",
    "PTableColumnSpecAxis",
    "PTableColumnSpecColumn",
    "PTableColumnSpecs",
    # Log module exports
    "Logger",
    "LogLevel",
    "logger",
    # Perf timer module exports
    "PerfTimer",
]
