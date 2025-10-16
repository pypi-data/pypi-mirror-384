from cpython cimport PyBytes_AsString
from struct import (
    pack,
    unpack,
)


cdef bytes NULLABLE = b"\xff\xff\xff\xff"


cdef list recursive_elements(list elements, list array_struct):
    """Recursive unpack array struct."""

    cdef long chunk, num_chunks
    cdef long _i, start, end
    cdef long elements_len = len(elements)
    cdef list result = []

    if not array_struct:
        return elements

    chunk = array_struct.pop()

    if elements_len == chunk:
        return recursive_elements(elements, array_struct)
    
    num_chunks = (elements_len + chunk - 1) // chunk

    for _i in range(num_chunks):
        start = _i * chunk
        end = start + chunk

        if end > elements_len:
            end = elements_len
        result.append(elements[start:end])

    return recursive_elements(result, array_struct)


cdef list get_num_dim(object type_values):
    """Get list of num dim."""

    cdef list num_dim = []
    cdef object current = type_values

    while current.__class__ is list and len(current) > 0:
        num_dim.append(len(current))
        current = current[0]

    return num_dim


cdef long prod(list iterable):
    """Cython math.prod."""

    cdef long result, item

    for item in iterable:
        result *= item

    return result


cdef object _reader(object buffer_object, object pgoid_function):
    """Read array record."""

    cdef bytes _bytes = buffer_object.read(4)
    cdef const unsigned char *buf = <const unsigned char*>PyBytes_AsString(
        _bytes
    )
    cdef int length = (buf[0] << 24) | (buf[1] << 16) | (buf[2] << 8) | buf[3]

    if length == 0xffffffff:
        return

    return pgoid_function(buffer_object.read(length))


cpdef list read_array(
    bytes binary_data,
    object pgoid_function,
    object buffer_object,
    long pgoid,
):
    """Unpack array values."""

    cdef unsigned int num_dim, _, oid
    cdef list array_struct = []
    cdef list array_elements = []

    buffer_object.write(binary_data)
    buffer_object.seek(0)
    num_dim, _, oid = unpack("!3I", buffer_object.read(12))

    for _ in range(num_dim):
        array_struct.append(unpack("!2I", buffer_object.read(8))[0])

    for _ in range(prod(array_struct)):
        array_elements.append(_reader(buffer_object, pgoid_function))

    buffer_object.seek(0)
    buffer_object.truncate()
    return recursive_elements(array_elements, array_struct)


cpdef bytes write_array(
    list dtype_value,
    object pgoid_function,
    object buffer_object,
    long pgoid,
):
    """Pack array values."""

    cdef list num_dim = get_num_dim(dtype_value)
    cdef short is_nullable, dim, dim_length = len(num_dim)
    cdef list expand_values, dimensions = []
    cdef object value
    cdef short length_dimensions
    cdef bytes binary_data
    cdef bint has_list = True

    while has_list:
        has_list = False
        expand_values = []

        for value in dtype_value:
            if isinstance(value, list):
                has_list = True
                expand_values.extend(value)
            else:
                expand_values.append(value)

        dtype_value = expand_values

    is_nullable = False
    for value in dtype_value:
        if value is None:
            is_nullable = True
            break

    for dim in num_dim:
        dimensions.extend([dim, 1])

    length_dimensions = len(dimensions)

    buffer_object.write(pack("!3I", dim_length, is_nullable, pgoid))
    buffer_object.write(pack("!%dI" % length_dimensions, *dimensions))

    for value in dtype_value:
        if value is None:
            buffer_object.write(NULLABLE)
        else:
            binary_data = pgoid_function(value)
            buffer_object.write(pack("!I", len(binary_data)))
            buffer_object.write(binary_data)

    binary_data = buffer_object.getvalue()
    buffer_object.seek(0)
    buffer_object.truncate()
    return binary_data
