def read_text(
    binary_data: bytes,
    pgoid_function: object | None = None,
    buffer_object: object | None = None,
    pgoid: int | None = None,
) -> str:
    """Unpack text value."""

    ...


def write_text(
    dtype_value: str,
    pgoid_function: object | None = None,
    buffer_object: object | None = None,
    pgoid: int | None = None,
) -> bytes:
    """Pack text value."""

    ...


def read_macaddr(
    binary_data: bytes,
    pgoid_function: object | None = None,
    buffer_object: object | None = None,
    pgoid: int | None = None,
) -> str:
    """Unpack macaddr and macaddr8 value."""

    ...


def write_macaddr(
    dtype_value: str,
    pgoid_function: object | None = None,
    buffer_object: object | None = None,
    pgoid: int | None = None,
) -> bytes:
    """Pack macaddr and macaddr8 value."""

    ...


def read_bits(
    binary_data: bytes,
    pgoid_function: object | None = None,
    buffer_object: object | None = None,
    pgoid: int | None = None,
) -> str:
    """Unpack bit and varbit value."""

    ...


def write_bits(
    dtype_value: str,
    pgoid_function: object | None = None,
    buffer_object: object | None = None,
    pgoid: int | None = None,
) -> bytes:
    """Pack bit and varbit value."""

    ...


def read_bytea(
    binary_data: bytes,
    pgoid_function: object | None = None,
    buffer_object: object | None = None,
    pgoid: int | None = None,
) -> bytes:
    """Unpack bytea value."""

    ...


def write_bytea(
    dtype_value: bytes,
    pgoid_function: object | None = None,
    buffer_object: object | None = None,
    pgoid: int | None = None,
) -> bytes:
    """Pack bytea value."""

    ...
