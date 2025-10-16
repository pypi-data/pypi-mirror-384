from decimal import Decimal


def read_bool(
    binary_data: bytes,
    pgoid_function: object | None = None,
    buffer_object: object | None = None,
    pgoid: int | None = None,
) -> bool:
    """Unpack bool value."""

    ...


def write_bool(
    dtype_value: bool,
    pgoid_function: object | None = None,
    buffer_object: object | None = None,
    pgoid: int | None = None,
) -> bytes:
    """Pack bool value."""

    ...


def read_oid(
    binary_data: bytes,
    pgoid_function: object | None = None,
    buffer_object: object | None = None,
    pgoid: int | None = None,
) -> int:
    """Unpack oid value."""

    ...


def write_oid(
    dtype_value: int,
    pgoid_function: object | None = None,
    buffer_object: object | None = None,
    pgoid: int | None = None,
) -> bytes:
    """Pack oid value."""

    ...


def read_serial2(
    binary_data: bytes,
    pgoid_function: object | None = None,
    buffer_object: object | None = None,
    pgoid: int | None = None,
) -> int:
    """Unpack serial2 value."""

    ...


def write_serial2(
    dtype_value: int,
    pgoid_function: object | None = None,
    buffer_object: object | None = None,
    pgoid: int | None = None,
) -> bytes:
    """Pack serial2 value."""

    ...


def read_serial4(
    binary_data: bytes,
    pgoid_function: object | None = None,
    buffer_object: object | None = None,
    pgoid: int | None = None,
) -> int:
    """Unpack serial4 value."""

    ...


def write_serial4(
    dtype_value: int,
    pgoid_function: object | None = None,
    buffer_object: object | None = None,
    pgoid: int | None = None,
) -> bytes:
    """Pack serial4 value."""

    ...


def read_serial8(
    binary_data: bytes,
    pgoid_function: object | None = None,
    buffer_object: object | None = None,
    pgoid: int | None = None,
) -> int:
    """Unpack serial8 value."""

    ...


def write_serial8(
    dtype_value: int,
    pgoid_function: object | None = None,
    buffer_object: object | None = None,
    pgoid: int | None = None,
) -> bytes:
    """Pack serial8 value."""

    ...


def read_int2(
    binary_data: bytes,
    pgoid_function: object | None = None,
    buffer_object: object | None = None,
    pgoid: int | None = None,
) -> int:
    """Unpack int2 value."""

    ...


def write_int2(
    dtype_value: int,
    pgoid_function: object | None = None,
    buffer_object: object | None = None,
    pgoid: int | None = None,
) -> bytes:
    """Pack int2 value."""

    ...


def read_int4(
    binary_data: bytes,
    pgoid_function: object | None = None,
    buffer_object: object | None = None,
    pgoid: int | None = None,
) -> int:
    """Unpack int4 value."""

    ...


def write_int4(
    dtype_value: int,
    pgoid_function: object | None = None,
    buffer_object: object | None = None,
    pgoid: int | None = None,
) -> bytes:
    """Pack int4 value."""

    ...


def read_int8(
    binary_data: bytes,
    pgoid_function: object | None = None,
    buffer_object: object | None = None,
    pgoid: int | None = None,
) -> int:
    """Unpack int8 value."""

    ...


def write_int8(
    dtype_value: int,
    pgoid_function: object | None = None,
    buffer_object: object | None = None,
    pgoid: int | None = None,
) -> bytes:
    """Pack int8 value."""

    ...


def read_money(
    binary_data: bytes,
    pgoid_function: object | None = None,
    buffer_object: object | None = None,
    pgoid: int | None = None,
) -> float:
    """Unpack money value."""

    ...


def write_money(
    dtype_value: float,
    pgoid_function: object | None = None,
    buffer_object: object | None = None,
    pgoid: int | None = None,
) -> bytes:
    """Pack money value."""

    ...


def read_float4(
    binary_data: bytes,
    pgoid_function: object | None = None,
    buffer_object: object | None = None,
    pgoid: int | None = None,
) -> float:
    """Unpack float4 value."""

    ...


def write_float4(
    dtype_value: float,
    pgoid_function: object | None = None,
    buffer_object: object | None = None,
    pgoid: int | None = None,
) -> bytes:
    """Pack float4 value."""

    ...


def read_float8(
    binary_data: bytes,
    pgoid_function: object | None = None,
    buffer_object: object | None = None,
    pgoid: int | None = None,
) -> float:
    """Unpack float8 value."""

    ...


def write_float8(
    dtype_value: float,
    pgoid_function: object | None = None,
    buffer_object: object | None = None,
    pgoid: int | None = None,
) -> bytes:
    """Pack float8 value."""

    ...


def read_numeric(
    binary_data: bytes,
    pgoid_function: object | None = None,
    buffer_object: object | None = None,
    pgoid: int | None = None,
) -> Decimal:
    """Unpack numeric value."""

    ...


def write_numeric(
    dtype_value: Decimal,
    pgoid_function: object | None = None,
    buffer_object: object | None = None,
    pgoid: int | None = None,
) -> bytes:
    """Pack numeric value."""

    ...
