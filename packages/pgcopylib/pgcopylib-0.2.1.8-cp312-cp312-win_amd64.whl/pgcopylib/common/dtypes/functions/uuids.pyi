from uuid import UUID


def read_uuid(
    binary_data: bytes,
    pgoid_function: object | None = None,
    buffer_object: object | None = None,
    pgoid: int | None = None,
) -> UUID:
    """Unpack uuid value."""

    ...


def write_uuid(
    dtype_value: UUID,
    pgoid_function: object | None = None,
    buffer_object: object | None = None,
    pgoid: int | None = None,
) -> bytes:
    """Pack uuid value."""

    ...
