import hashlib
from typing import Callable, Iterator, Mapping, Optional, Union

import msgspec.json
import polars as pl
from polars._typing import ParallelStrategy
from polars.io.plugins import register_io_source
from ulid import ULID

from polars_pf._polars_pf import PyPFrame, canonicalize, map_predicate
from polars_pf.json.filter import PTableRecordFilter
from polars_pf.json.join import CreateTableRequest
from polars_pf.json.spec import (
    AxisId,
    AxisSpec,
    AxisType,
    ColumnType,
    PTableColumnId,
    PTableColumnIdAxis,
    PTableColumnIdColumn,
    PTableColumnSpec,
    PTableColumnSpecAxis,
    PTableColumnSpecs,
)
from polars_pf.log import Logger, LogLevel
from polars_pf.perf_timer import PerfTimer


def pframes_to_polars_type(type: Union[AxisType, ColumnType]) -> pl.DataType:
    match type:
        case AxisType.Int | ColumnType.Int:
            return pl.Int32
        case AxisType.Long | ColumnType.Long:
            return pl.Int64
        case ColumnType.Float:
            return pl.Float32
        case ColumnType.Double:
            return pl.Float64
        case AxisType.String | ColumnType.String:
            return pl.String


def axis_ref(spec: AxisSpec) -> str:
    return hashlib.sha256(
        canonicalize(AxisId(name=spec.name, type=spec.type, domain=spec.domain))
    ).hexdigest()


def column_ref(spec: PTableColumnSpec) -> str:
    if isinstance(spec, PTableColumnSpecAxis):
        return axis_ref(spec.spec)
    return spec.id


def pframe_source(
    input_path: str,
    request: CreateTableRequest,
    *,
    spill_path: Optional[str] = None,
    column_ref: Callable[[PTableColumnSpec], str] = column_ref,
    logger: Optional[Logger] = None,
    parallel: ParallelStrategy = "auto",
    low_memory: bool = False,
) -> pl.LazyFrame:
    """
    Create PTable and export it as Polars LazyFrame.

    Args:
        input_path: Path to the directory containing the frame data
        request: Table creation request
        column_ref: Function to generate column references
        logger: Optional logger function

    Returns:
        Polars LazyFrame representing the PTable data
    """
    pframe_id = str(ULID())

    logger and logger(
        LogLevel.Info,
        f"PFrame {pframe_id} registration as Polars source started, "
        f"input_path: {input_path}, "
        f"request: {msgspec.json.encode(request).decode()}",
    )
    timer: PerfTimer = PerfTimer.start()
    try:
        pframe = PyPFrame(input_path, spill_path, logger)

        column_refs: list[str] = []
        schema: Mapping[str, pl.DataType] = {}
        column_ref_to_field: Mapping[str, str] = {}
        column_ref_to_column_id: Mapping[str, PTableColumnId] = {}
        with pframe.create_table(request, str(ULID())) as temp_table:
            fields: list[str] = temp_table.get_fields()
            specs: PTableColumnSpecs = temp_table.get_spec()
            for field, spec_item in zip(fields, specs):
                ref: str = column_ref(spec_item)
                column_refs.append(ref)
                schema[ref] = pframes_to_polars_type(
                    spec_item.spec.type
                    if isinstance(spec_item, PTableColumnSpecAxis)
                    else spec_item.spec.value_type
                )
                column_ref_to_field[ref] = field
                column_ref_to_column_id[ref] = (
                    PTableColumnIdAxis(id=spec_item.id)
                    if isinstance(spec_item, PTableColumnSpecAxis)
                    else PTableColumnIdColumn(id=spec_item.id)
                )

        def source_generator(
            with_columns: Optional[list[str]],
            predicate: Optional[pl.Expr],
            n_rows: Optional[int],
            batch_size: Optional[int],
        ) -> Iterator[pl.DataFrame]:
            logger and logger(
                LogLevel.Info,
                f"PFrame {pframe_id} Polars source generator started, "
                f"with_columns: {with_columns}, "
                f"predicate: {predicate is not None}, "
                f"n_rows: {n_rows}, "
                f"batch_size: {batch_size}",
            )
            timer: PerfTimer = PerfTimer.start()
            try:
                pframe_filters: list[PTableRecordFilter] = []
                polars_filters: list[pl.Expr] = []
                if predicate is not None:
                    pframe_filter: PTableRecordFilter | None = map_predicate(
                        predicate, column_ref_to_column_id
                    )
                    if pframe_filter is not None:
                        pframe_filters.append(pframe_filter)
                    else:
                        polars_filters.append(predicate)

                new_request = CreateTableRequest(
                    src=request.src, filters=request.filters + pframe_filters
                )
                with pframe.create_table(new_request, str(ULID())) as ptable:
                    with_columns_set: set[str] = set(with_columns or [])
                    select_exprs: list[pl.Expr] = []
                    for col_ref, field in column_ref_to_field.items():
                        if not with_columns_set or col_ref in with_columns_set:
                            select_exprs.append(pl.col(field).alias(col_ref))

                    table_path: str = ptable.get_path()
                    logger and logger(
                        LogLevel.Info,
                        f"PFrame {pframe_id} Polars source generator got table path {table_path}, "
                        f"took {timer.elapsed()} (overall)",
                    )

                    lf: pl.LazyFrame = pl.scan_parquet(
                        table_path, parallel=parallel, low_memory=low_memory
                    ).select(select_exprs)
                    if polars_filters:
                        lf = lf.filter(polars_filters)
                    if n_rows is not None:
                        lf = lf.limit(n_rows)

                    if batch_size is not None:
                        sort_exprs: list[str] = []
                        for column_ref in column_refs:
                            if not with_columns_set or column_ref in with_columns_set:
                                sort_exprs.append(column_ref)
                        # slice without sort will return continuous row batches from random offsets
                        lf = lf.sort(sort_exprs, maintain_order=True)

                        offset = 0
                        while True:
                            batch_lf: pl.LazyFrame = lf.slice(offset, batch_size)
                            offset += batch_size

                            df_batch: pl.DataFrame = batch_lf.collect()
                            if len(df_batch) == 0:
                                break

                            yield df_batch
                    else:
                        yield lf.collect()

                logger and logger(
                    LogLevel.Info,
                    f"PFrame {pframe_id} Polars source generator finished, "
                    f"took {timer.elapsed()} (overall)",
                )
            except Exception as e:
                logger and logger(
                    LogLevel.Error,
                    f"PFrame {pframe_id} Polars source generator error: {e}",
                )
                raise
            finally:
                pframe.dispose()

        lf: pl.LazyFrame = register_io_source(source_generator, schema=schema)
        logger and logger(
            LogLevel.Info,
            f"PFrame {pframe_id} registration as Polars source finished, "
            f"took {timer.elapsed()} (overall), "
            f"schema: {schema}",
        )
        return lf
    except Exception as e:
        pframe.dispose()
        logger and logger(
            LogLevel.Error,
            f"PFrame {pframe_id} registration as Polars source error: {e}",
        )
        raise
