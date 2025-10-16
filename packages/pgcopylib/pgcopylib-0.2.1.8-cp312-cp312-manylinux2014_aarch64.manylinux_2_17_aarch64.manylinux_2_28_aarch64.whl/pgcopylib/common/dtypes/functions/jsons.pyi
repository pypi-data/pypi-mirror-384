def read_json(
    binary_data: bytes,
    pgoid_function: object | None = None,
    buffer_object: object | None = None,
    pgoid: int | None = None,
) -> dict:
    """Unpack json value."""

    ...


def write_json(
    dtype_value: dict,
    pgoid_function: object | None = None,
    buffer_object: object | None = None,
    pgoid: int | None = None,
) -> bytes:
    """Pack json value."""

    ...
