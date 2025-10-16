cpdef str read_text(
    bytes binary_data,
    object pgoid_function=*,
    object buffer_object=*,
    object pgoid=*,
)
cpdef bytes write_text(
    str dtype_value,
    object pgoid_function=*,
    object buffer_object=*,
    object pgoid=*,
)
cpdef str read_macaddr(
    bytes binary_data,
    object pgoid_function=*,
    object buffer_object=*,
    object pgoid=*,
)
cpdef bytes write_macaddr(
    str dtype_value,
    object pgoid_function=*,
    object buffer_object=*,
    object pgoid=*,
)
cpdef str read_bits(
    bytes binary_data,
    object pgoid_function=*,
    object buffer_object=*,
    object pgoid=*,
)
cpdef bytes write_bits(
    str dtype_value,
    object pgoid_function=*,
    object buffer_object=*,
    object pgoid=*,
)
cpdef bytes read_bytea(
    bytes binary_data,
    object pgoid_function=*,
    object buffer_object=*,
    object pgoid=*,
)
cpdef bytes write_bytea(
    bytes dtype_value,
    object pgoid_function=*,
    object buffer_object=*,
    object pgoid=*,
)
