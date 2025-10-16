from uuid import UUID


cpdef object read_uuid(
    bytes binary_data,
    object pgoid_function = None,
    object buffer_object = None,
    object pgoid = None,
):
    """Unpack uuid value."""

    return UUID(bytes=binary_data)


cpdef bytes write_uuid(
    object dtype_value,
    object pgoid_function = None,
    object buffer_object = None,
    object pgoid = None,
):
    """Pack uuid value."""

    return dtype_value.bytes
