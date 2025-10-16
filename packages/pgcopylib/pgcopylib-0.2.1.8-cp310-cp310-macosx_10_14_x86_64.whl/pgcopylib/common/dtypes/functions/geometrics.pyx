from struct import (
    pack,
    unpack,
)


cpdef (double, double) read_point(
    bytes binary_data,
    object pgoid_function = None,
    object buffer_object = None,
    object pgoid = None,
):
    """Unpack point value."""

    return unpack("!2d", binary_data)


cpdef bytes write_point(
    (double, double) dtype_value,
    object pgoid_function = None,
    object buffer_object = None,
    object pgoid = None,
):
    """Pack point value."""

    return pack("!2d", *dtype_value)


cpdef (double, double, double) read_line(
    bytes binary_data,
    object pgoid_function = None,
    object buffer_object = None,
    object pgoid = None,
):
    """Unpack line value."""

    return unpack("!3d", binary_data)


cpdef bytes write_line(
    (double, double, double) dtype_value,
    object pgoid_function = None,
    object buffer_object = None,
    object pgoid = None,
):
    """Pack line value."""

    return pack("!3d", *dtype_value)


cpdef list read_lseg(
    bytes binary_data,
    object pgoid_function = None,
    object buffer_object = None,
    object pgoid = None,
):
    """Unpack lseg value."""

    cdef double x1, y1, x2, y2
    x1, y1, x2, y2 = unpack("!4d", binary_data)
    return [(x1, y1), (x2, y2)]


cpdef bytes write_lseg(
    list dtype_value,
    object pgoid_function = None,
    object buffer_object = None,
    object pgoid = None,
):
    """Pack lseg value."""

    return pack("!4d", *dtype_value[0], *dtype_value[1])


cpdef ((double, double), (double, double)) read_box(
    bytes binary_data,
    object pgoid_function = None,
    object buffer_object = None,
    object pgoid = None,
):
    """Unpack box value."""

    cdef double x1, y1, x2, y2
    x1, y1, x2, y2 = unpack("!4d", binary_data)
    return (x1, y1), (x2, y2)


cpdef bytes write_box(
    ((double, double), (double, double)) dtype_value,
    object pgoid_function = None,
    object buffer_object = None,
    object pgoid = None,
):
    """Pack box value."""

    return pack("!4d", *dtype_value[0], *dtype_value[1])


cpdef object read_path(
    bytes binary_data,
    object pgoid_function = None,
    object buffer_object = None,
    object pgoid = None,
):
    """Unpack path value."""

    cdef bint is_closed
    cdef int length
    cdef tuple coords_data
    cdef list path_data = []
    cdef long i

    is_closed = unpack("!?", binary_data[:1])[0]
    length = unpack("!l", binary_data[1:5])[0]

    cdef long coords_count = (len(binary_data) - 5) // 8
    coords_data = unpack(f"!{coords_count}d", binary_data[5:])

    for i in range(0, coords_count, 2):
        if i + 1 < coords_count:
            path_data.append((coords_data[i], coords_data[i + 1]))

    if is_closed:
        return tuple(path_data)
    return path_data


cpdef bytes write_path(
    object dtype_value,
    object pgoid_function = None,
    object buffer_object = None,
    object pgoid = None,
):
    """Pack path value."""

    cdef bint is_closed = isinstance(dtype_value, tuple)
    cdef short length = len(dtype_value)
    cdef list path_data = []
    cdef short i
    cdef object point

    for i in range(length):
        point = dtype_value[i]
        path_data.append(point[0])
        path_data.append(point[1])

    return pack(
        f"?l{len(path_data)}d",
        is_closed,
        length,
        *path_data
    )


cpdef tuple read_polygon(
    bytes binary_data,
    object pgoid_function = None,
    object buffer_object = None,
    object pgoid = None,
):
    """Unpack polygon value."""

    cdef int length
    cdef tuple coords_data
    cdef list points = []
    cdef short i
    length = unpack("!l", binary_data[:4])[0]
    cdef short coords_count = (len(binary_data) - 4) // 8
    coords_data = unpack(f"!{coords_count}d", binary_data[4:])

    for i in range(0, coords_count, 2):
        points.append((coords_data[i], coords_data[i + 1]))

    return tuple(points)


cpdef bytes write_polygon(
    tuple dtype_value,
    object pgoid_function = None,
    object buffer_object = None,
    object pgoid = None,
):
    """Pack polygon value."""

    cdef short length = len(dtype_value)
    cdef list path_data = []
    cdef short i
    cdef tuple point

    for i in range(length):
        point = dtype_value[i]
        path_data.extend(point)

    return pack(
        f"l{len(path_data)}d",
        length,
        *path_data
    )
