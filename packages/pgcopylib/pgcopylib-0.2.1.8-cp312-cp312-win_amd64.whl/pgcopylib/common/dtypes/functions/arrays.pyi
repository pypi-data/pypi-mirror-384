from typing import Any


def read_array(
    binary_data: bytes,
    pgoid_function: object,
    buffer_object: object,
    pgoid: int,
) -> list[Any]:
    """Unpack array values."""

    ...


def write_array(
    dtype_value: list[Any],
    pgoid_function: object,
    buffer_object: object,
    pgoid: int,
) -> bytes:
    """Pack array values."""

    ...
