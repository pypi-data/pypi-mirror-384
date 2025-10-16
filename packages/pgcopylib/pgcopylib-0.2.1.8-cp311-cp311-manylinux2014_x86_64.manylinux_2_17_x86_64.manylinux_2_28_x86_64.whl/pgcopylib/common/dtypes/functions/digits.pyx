from decimal import (
    ROUND_HALF_UP,
    Decimal,
)
from libc.math cimport round
from struct import (
    pack,
    unpack,
    unpack_from,
)


cpdef object read_bool(
    bytes binary_data,
    object pgoid_function = None,
    object buffer_object = None,
    object pgoid = None,
):
    """Unpack bool value."""

    return unpack("!?", binary_data)[0]


cpdef bytes write_bool(
    object dtype_value,
    object pgoid_function = None,
    object buffer_object = None,
    object pgoid = None,
):
    """Pack bool value."""

    return pack("!?", bool(dtype_value))


cpdef unsigned long read_oid(
    bytes binary_data,
    object pgoid_function = None,
    object buffer_object = None,
    object pgoid = None,
):
    """Unpack oid value."""

    return unpack("!I", binary_data)[0]


cpdef bytes write_oid(
    object dtype_value,
    object pgoid_function = None,
    object buffer_object = None,
    object pgoid = None,
):
    """Pack oid value."""

    return pack("!I", <unsigned long>dtype_value)


cpdef unsigned short read_serial2(
    bytes binary_data,
    object pgoid_function = None,
    object buffer_object = None,
    object pgoid = None,
):
    """Unpack serial2 value."""

    return unpack("!H", binary_data)[0]


cpdef bytes write_serial2(
    object dtype_value,
    object pgoid_function = None,
    object buffer_object = None,
    object pgoid = None,
):
    """Pack serial2 value."""

    return pack("!H", <unsigned short>dtype_value)


cpdef unsigned long read_serial4(
    bytes binary_data,
    object pgoid_function = None,
    object buffer_object = None,
    object pgoid = None,
):
    """Unpack serial4 value."""

    return unpack("!L", binary_data)[0]


cpdef bytes write_serial4(
    object dtype_value,
    object pgoid_function = None,
    object buffer_object = None,
    object pgoid = None,
):
    """Pack serial4 value."""

    return pack("!L", <unsigned long>dtype_value)


cpdef unsigned long long read_serial8(
    bytes binary_data,
    object pgoid_function = None,
    object buffer_object = None,
    object pgoid = None,
):
    """Unpack serial8 value."""

    return unpack("!Q", binary_data)[0]


cpdef bytes write_serial8(
    object dtype_value,
    object pgoid_function = None,
    object buffer_object = None,
    object pgoid = None,
):
    """Pack serial8 value."""

    return pack("!Q", <unsigned long long>dtype_value)


cpdef short read_int2(
    bytes binary_data,
    object pgoid_function = None,
    object buffer_object = None,
    object pgoid = None,
):
    """Unpack int2 value."""

    return unpack("!h", binary_data)[0]


cpdef bytes write_int2(
    object dtype_value,
    object pgoid_function = None,
    object buffer_object = None,
    object pgoid = None,
):
    """Pack int2 value."""

    return pack("!h", <short>dtype_value)


cpdef long read_int4(
    bytes binary_data,
    object pgoid_function = None,
    object buffer_object = None,
    object pgoid = None,
):
    """Unpack int4 value."""

    return unpack("!l", binary_data)[0]


cpdef bytes write_int4(
    object dtype_value,
    object pgoid_function = None,
    object buffer_object = None,
    object pgoid = None,
):
    """Pack int4 value."""

    return pack("!l", <long>dtype_value)


cpdef long long read_int8(
    bytes binary_data,
    object pgoid_function = None,
    object buffer_object = None,
    object pgoid = None,
):
    """Unpack int8 value."""

    return unpack("!q", binary_data)[0]


cpdef bytes write_int8(
    object dtype_value,
    object pgoid_function = None,
    object buffer_object = None,
    object pgoid = None,
):
    """Pack int8 value."""

    return pack("!q", <long long>dtype_value)


cpdef double read_money(
    bytes binary_data,
    object pgoid_function = None,
    object buffer_object = None,
    object pgoid = None,
):
    """Unpack money value."""

    return read_int8(binary_data) * 0.01


cpdef bytes write_money(
    object dtype_value,
    object pgoid_function = None,
    object buffer_object = None,
    object pgoid = None,
):
    """Pack money value."""

    return write_int8(<long long>round(dtype_value / 0.01))


cpdef float read_float4(
    bytes binary_data,
    object pgoid_function = None,
    object buffer_object = None,
    object pgoid = None,
):
    """Unpack float4 value."""

    return unpack("!f", binary_data)[0]


cpdef bytes write_float4(
    object dtype_value,
    object pgoid_function = None,
    object buffer_object = None,
    object pgoid = None,
):
    """Pack float4 value."""

    return pack("!f", <float>dtype_value)


cpdef double read_float8(
    bytes binary_data,
    object pgoid_function = None,
    object buffer_object = None,
    object pgoid = None,
):
    """Unpack float8 value."""

    return unpack("!d", binary_data)[0]


cpdef bytes write_float8(
    object dtype_value,
    object pgoid_function = None,
    object buffer_object = None,
    object pgoid = None,
):
    """Pack float8 value."""

    return pack("!d", <double>dtype_value)


cpdef object read_numeric(
    bytes binary_data,
    object pgoid_function = None,
    object buffer_object = None,
    object pgoid = None,
):
    """Unpack numeric value."""

    cdef:
        int ndigits, weight, sign, dscale
        int i, pos
        bint is_negative
        list digits = []
        object numeric, scale, power, term
        short digit

    ndigits, weight, sign, dscale = unpack_from("!hhhh", binary_data)

    if sign == 0xc000:
        return Decimal("nan")

    is_negative = (sign == 0x4000)

    cdef int data_len = len(binary_data)

    for i in range(8, 8 + ndigits * 2, 2):
        if i + 1 < data_len:
            digit = unpack_from("!h", binary_data, i)[0]
            digits.append(digit)

    numeric = Decimal(0)
    scale = Decimal(10) ** -dscale

    cdef object weight_dec = Decimal(weight)
    cdef object ten = Decimal(10)
    cdef object four = Decimal(4)

    for pos, digit in enumerate(digits):
        power = four * (weight_dec - Decimal(pos))
        term = Decimal(digit) * (ten ** power)
        numeric += term

    if is_negative:
        numeric *= -1

    return numeric.quantize(scale)


cpdef bytes write_numeric(
    object dtype_value,
    object pgoid_function = None,
    object buffer_object = None,
    object pgoid = None,
):
    """Pack numeric value."""

    cdef bint is_negative
    cdef int sign, dscale, ndigits, weight, digit
    cdef object abs_value, scaled_value, int_value
    cdef list digits = []
    cdef list digit_bytes_list = []
    cdef bytes header, digits_data

    dtype_value = Decimal(dtype_value)

    if dtype_value.is_nan():
        return pack("!hhhh", 0, 0, 0xc000, 0)

    is_negative = dtype_value < 0
    sign = 0x4000 if is_negative else 0x0000

    if dtype_value == 0:
        return pack("!hhhh", 0, 0, sign, 0)

    abs_value = abs(dtype_value)
    as_tuple = abs_value.as_tuple()
    dscale = abs(as_tuple.exponent) if as_tuple.exponent < 0 else 0
    scaled_value = abs_value * (Decimal(10) ** dscale)
    int_value = int(scaled_value.to_integral_value(rounding=ROUND_HALF_UP))
    temp = int_value
    base = 10000

    while temp > 0:
        digits.append(temp % base)
        temp //= base

    if not digits:
        digits = [0]
    else:
        digits.reverse()

    ndigits = len(digits)

    if int_value == 0:
        weight = 0
    else:
        integer_digits = len(str(int(abs_value)))
        weight = (integer_digits - 1) // 4

    header = pack("!hhhh", ndigits, weight, sign, dscale)

    for digit in digits:
        digit_bytes_list.append(pack("!h", digit))

    digits_data = b''.join(digit_bytes_list)

    return header + digits_data
