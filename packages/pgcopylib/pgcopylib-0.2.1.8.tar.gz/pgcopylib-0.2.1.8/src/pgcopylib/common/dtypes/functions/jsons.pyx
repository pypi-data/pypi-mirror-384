from json import (
    dumps,
    loads,
)


cpdef object read_json(
    bytes binary_data,
    object pgoid_function = None,
    object buffer_object = None,
    object pgoid = None,
):
    """Unpack json value."""

    return loads(binary_data)


cpdef bytes write_json(
    object dtype_value,
    object pgoid_function = None,
    object buffer_object = None,
    object pgoid = None,
):
    """Pack json value."""

    return dumps(dtype_value, ensure_ascii=False).encode("utf-8")
