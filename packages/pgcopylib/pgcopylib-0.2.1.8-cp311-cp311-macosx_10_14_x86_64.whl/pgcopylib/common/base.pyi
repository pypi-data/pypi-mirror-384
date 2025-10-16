from collections.abc import Generator
from io import BufferedReader
from typing import Any


def read_num_columns(
    fileobj: BufferedReader,
    column_length: int,
) -> int:
    """Read column count."""

    ...


def read_record(
    fileobj: BufferedReader,
    reader: object,
    pgoid_function: object,
    buffer_object: object,
    pgoid: int,
) -> Any:
    """Read one record."""

    ...


def skip_all(
    fileobj: BufferedReader,
    column_length: int,
    num_columns: int,
    num_rows: int,
) -> int:
    """Skip all records."""

    ...


def writer(
    fileobj: BufferedReader,
    write_row: object,
    dtype_values: Any,
    num_columns: int,
) -> int:
    """Write pgcopy into fileobj."""

    ...


def nullable_writer(
    write_dtype: object,
    dtype_value: Any,
    pgoid_function: object,
    buffer_object: object,
    pgoid: int,
) -> bytes:
    """Function for write None value and data with length."""

    ...


def make_rows(
    write_row: object,
    dtype_values: Any,
    num_columns: int,
) -> Generator[bytes, None, None]:
    """Make pgcopy rows."""

    ...
