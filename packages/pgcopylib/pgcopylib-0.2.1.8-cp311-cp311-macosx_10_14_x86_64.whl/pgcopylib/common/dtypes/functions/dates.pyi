from datetime import (
    date,
    datetime,
    time,
)
from dateutil.relativedelta import relativedelta


def read_date(
    binary_data: bytes,
    pgoid_function: object | None = None,
    buffer_object: object | None = None,
    pgoid: int | None = None,
) -> date:
    """Unpack date value."""

    ...


def write_date(
    dtype_value: date,
    pgoid_function: object | None = None,
    buffer_object: object | None = None,
    pgoid: int | None = None,
) -> bytes:
    """Pack date value."""

    ...


def read_timestamp(
    binary_data: bytes,
    pgoid_function: object | None = None,
    buffer_object: object | None = None,
    pgoid: int | None = None,
) -> datetime:
    """Unpack timestamp value."""

    ...


def write_timestamp(
    dtype_value: datetime,
    pgoid_function: object | None = None,
    buffer_object: object | None = None,
    pgoid: int | None = None,
) -> bytes:
    """Pack timestamp value."""

    ...


def read_timestamptz(
    binary_data: bytes,
    pgoid_function: object | None = None,
    buffer_object: object | None = None,
    pgoid: int | None = None,
) -> datetime:
    """Unpack timestamptz value."""

    ...


def write_timestamptz(
    dtype_value: datetime,
    pgoid_function: object | None = None,
    buffer_object: object | None = None,
    pgoid: int | None = None,
) -> bytes:
    """Pack timestamptz value."""

    ...


def read_time(
    binary_data: bytes,
    pgoid_function: object | None = None,
    buffer_object: object | None = None,
    pgoid: int | None = None,
) -> time:
    """Unpack time value."""

    ...


def write_time(
    dtype_value: time,
    pgoid_function: object | None = None,
    buffer_object: object | None = None,
    pgoid: int | None = None,
) -> bytes:
    """Pack time value."""

    ...


def read_timetz(
    binary_data: bytes,
    pgoid_function: object | None = None,
    buffer_object: object | None = None,
    pgoid: int | None = None,
) -> time:
    """Unpack timetz value."""

    ...


def write_timetz(
    dtype_value: time,
    pgoid_function: object | None = None,
    buffer_object: object | None = None,
    pgoid: int | None = None,
) -> bytes:
    """Pack timetz value."""

    ...


def read_interval(
    binary_data: bytes,
    pgoid_function: object | None = None,
    buffer_object: object | None = None,
    pgoid: int | None = None,
) -> relativedelta:
    """Unpack interval value."""

    ...


def write_interval(
    dtype_value: relativedelta,
    pgoid_function: object | None = None,
    buffer_object: object | None = None,
    pgoid: int | None = None,
) -> bytes:
    """Pack interval value."""

    ...
