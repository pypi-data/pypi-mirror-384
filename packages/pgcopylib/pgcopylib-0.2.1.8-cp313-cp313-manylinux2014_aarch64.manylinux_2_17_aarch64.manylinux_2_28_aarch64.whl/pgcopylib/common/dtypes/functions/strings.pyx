cpdef str read_text(
    bytes binary_data,
    object pgoid_function = None,
    object buffer_object = None,
    object pgoid = None,
):
    """Unpack text value."""

    return binary_data.decode("utf-8", errors="replace")


cpdef bytes write_text(
    str dtype_value,
    object pgoid_function = None,
    object buffer_object = None,
    object pgoid = None,
):
    """Pack text value."""

    return str(dtype_value).encode("utf-8")


cpdef str read_macaddr(
    bytes binary_data,
    object pgoid_function = None,
    object buffer_object = None,
    object pgoid = None,
):
    """Unpack macaddr and macaddr8 value."""

    cdef long i
    cdef long data_len = len(binary_data)
    cdef const unsigned char[:] view = binary_data
    cdef list parts = []

    parts.reserve(data_len)

    for i in range(data_len):
        parts.append(f"{view[i]:02x}")

    return ":".join(parts).upper()


cpdef bytes write_macaddr(
    str dtype_value,
    object pgoid_function = None,
    object buffer_object = None,
    object pgoid = None,
):
    """Pack macaddr and macaddr8 value."""

    return bytes.fromhex(dtype_value.replace(":", ""))


cpdef str read_bits(
    bytes binary_data,
    object pgoid_function = None,
    object buffer_object = None,
    object pgoid = None,
):
    """Unpack bit and varbit value."""

    cdef unsigned int length
    cdef const unsigned char[:] view = binary_data
    cdef long data_len = len(binary_data)
    cdef long bit_data_len = data_len - 4
    cdef list bits = []
    cdef short i, j
    cdef unsigned char byte_val

    length = (view[0] << 24) | (view[1] << 16) | (view[2] << 8) | view[3]
    bits.reserve(bit_data_len * 8)

    for i in range(4, data_len):
        byte_val = view[i]
        for j in range(7, -1, -1):
            bits.append(str((byte_val >> j) & 1))

    return "".join(bits)[:length]


cpdef bytes write_bits(
    str dtype_value,
    object pgoid_function = None,
    object buffer_object = None,
    object pgoid = None,
):
    """Pack bit and varbit value."""

    cdef long bit_length = len(dtype_value)
    cdef long byte_length = (bit_length + 7) // 8
    cdef int int_value = int(dtype_value, 2)

    return int_value.to_bytes(byte_length, "big")


cpdef bytes read_bytea(
    bytes binary_data,
    object pgoid_function = None,
    object buffer_object = None,
    object pgoid = None,
):
    """Unpack bytea value."""

    return binary_data


cpdef bytes write_bytea(
    bytes dtype_value,
    object pgoid_function = None,
    object buffer_object = None,
    object pgoid = None,
):
    """Pack bytea value."""

    return dtype_value
