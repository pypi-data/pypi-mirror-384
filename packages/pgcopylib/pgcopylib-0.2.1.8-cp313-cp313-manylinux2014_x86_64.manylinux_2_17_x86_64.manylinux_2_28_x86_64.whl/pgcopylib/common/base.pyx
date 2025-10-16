from cpython cimport PyBytes_AsString
from struct import pack


cdef bytes HEADER = b"PGCOPY\n\xff\r\n\x00\x00\x00\x00\x00\x00\x00\x00\x00"
cdef bytes FINALIZE = b"\xff\xff"
cdef bytes NULLABLE = b"\xff\xff\xff\xff"


cpdef long read_num_columns(
    object fileobj,
    long column_length,
):
    """Read one record to bytes."""

    cdef bytes _bytes = fileobj.read(column_length)
    cdef const unsigned char *buf = <const unsigned char*>PyBytes_AsString(
        _bytes
    )
    return (buf[0] << 8) | buf[1]


cpdef object read_record(
    object fileobj,
    object reader,
    object pgoid_function,
    object buffer_object,
    long pgoid,
):
    """Read one record to bytes."""

    cdef bytes _bytes = fileobj.read(4)
    cdef const unsigned char *buf = <const unsigned char*>PyBytes_AsString(
        _bytes
    )
    cdef int length = (buf[0] << 24) | (buf[1] << 16) | (buf[2] << 8) | buf[3]

    if length == 0xffffffff:
        return

    return reader(fileobj.read(length), pgoid_function, buffer_object, pgoid)


cpdef long long skip_all(
    object fileobj,
    long column_length,
    long num_columns,
    long long num_rows,
):
    """Skip all records."""

    cdef long columns = num_columns

    while columns != 0xffff:

        for _ in range(num_columns):
            skip_record(fileobj)

        num_rows += 1
        columns = read_num_columns(fileobj, column_length)

    return num_rows


cdef void skip_record(object fileobj):
    """Skip one record."""

    cdef bytes _bytes = fileobj.read(4)
    cdef const unsigned char *buf = <const unsigned char*>PyBytes_AsString(
        _bytes
    )
    cdef int length = (buf[0] << 24) | (buf[1] << 16) | (buf[2] << 8) | buf[3]
    fileobj.read(length)


cpdef long long writer(
    object fileobj,
    object write_row,
    object dtype_values,
    long num_columns,
):
    """Write pgcopy into fileobj."""

    cdef long long pos = 0

    for buffer_object in make_rows(write_row, dtype_values, num_columns):
        pos += fileobj.write(buffer_object)

    return pos


cpdef bytes nullable_writer(
    object write_dtype,
    object dtype_value,
    object pgoid_function,
    object buffer_object,
    long pgoid,
):
    """Function for write None value and data with length."""

    if dtype_value is None:
        return NULLABLE

    cdef bytes binary_data = write_dtype(
        dtype_value,
        pgoid_function,
        buffer_object,
        pgoid,
    )
    cdef int len_data = len(binary_data)
    return pack(f"!I{len_data}s", len_data, binary_data)


def make_rows(object write_row, object dtype_values, long num_columns):
    """Make pgcopy rows."""

    cdef list bytes_buffer = [HEADER]
    cdef bytes num_columns_bytes = bytes([
        (num_columns >> 8) & 0xFF,
        num_columns & 0xFF
    ])

    for dtype_value in dtype_values:
        bytes_buffer.append(num_columns_bytes)

        for row in write_row(dtype_value):
            bytes_buffer.append(row)

        if len(bytes_buffer) > 1024:
            yield b"".join(bytes_buffer)
            bytes_buffer.clear()

    bytes_buffer.append(FINALIZE)
    yield b"".join(bytes_buffer)
