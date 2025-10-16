cpdef list read_array(
    bytes binary_data,
    object pgoid_function,
    object buffer_object,
    long pgoid,
)
cpdef bytes write_array(
    list dtype_value,
    object pgoid_function,
    object buffer_object,
    long pgoid,
)
