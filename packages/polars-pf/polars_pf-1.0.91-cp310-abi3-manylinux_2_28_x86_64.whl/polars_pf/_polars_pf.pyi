from types import TracebackType
from typing import Optional

import polars as pl
from msgspec import Struct

from polars_pf.json.filter import PTableRecordFilter
from polars_pf.json.join import CreateTableRequest
from polars_pf.json.spec import PTableColumnId, PTableColumnSpecs
from polars_pf.log import Logger

class PyPFrame:
    """
    Python wrapper for PFrame operations.

    Supports context manager protocol for automatic resource cleanup.
    """

    def __init__(
        self,
        dir_path: str,
        spill_path: Optional[str] = None,
        logger: Optional[Logger] = None,
    ) -> None:
        """
        Initialize a new PFrame from a directory path.

        Args:
            dir_path: Path to the directory containing frame data
            logger: Optional logger function for logging operations
        """
        ...

    def create_table(self, request: CreateTableRequest, id: str) -> "PyPTable":
        """
        Create a table from the frame using the provided request and ID.

        Args:
            request: CreateTableRequest object specifying the table to create
            id: Unique string identifier for the table

        Returns:
            PyPTable instance representing the created table
        """
        ...

    def dispose(self) -> None:
        """
        Dispose of the frame resources manually.
        Called automatically when exiting context manager.
        """
        ...

    def __enter__(self) -> "PyPFrame":
        """Context manager entry."""
        ...

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> bool:
        """Context manager exit with automatic disposal."""
        ...

class PyPTable:
    """
    Python wrapper for PTable operations.

    Supports context manager protocol for automatic resource cleanup.
    """

    def get_spec(self) -> PTableColumnSpecs:
        """
        Get the table specification.

        Returns:
            PTableColumnSpecs object containing the table's column specifications
        """
        ...

    def get_fields(self) -> list[str]:
        """
        Get the field names from the table.

        Returns:
            List of field names as strings
        """
        ...

    def get_path(self) -> str:
        """
        Get the path of the table.

        Returns:
            String path to the table parquet file
        """
        ...

    def dispose(self) -> None:
        """
        Dispose of the table resources manually.
        Called automatically when exiting context manager.
        """
        ...

    def __enter__(self) -> "PyPTable":
        """Context manager entry."""
        ...

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> bool:
        """Context manager exit with automatic disposal."""
        ...

def canonicalize(obj: Struct) -> bytes:
    """
    Encode a msgspec-serializable object to a canonical JSON representation.

    Args:
        obj: Any msgspec-serializable Python object

    Returns:
        Canonical JSON representation as bytes
    """
    ...

def map_predicate(
    predicate: pl.Expr,
    mapping: dict[str, PTableColumnId],
) -> Optional[PTableRecordFilter]:
    """
    Convert a Polars predicate expression to a PFrame record filter.

    Args:
        predicate: Polars expression representing the filter predicate
        mapping: Dictionary mapping column reference strings to PTableColumnId objects

    Returns:
        PTableRecordFilter if conversion is possible, None otherwise
    """
    ...
