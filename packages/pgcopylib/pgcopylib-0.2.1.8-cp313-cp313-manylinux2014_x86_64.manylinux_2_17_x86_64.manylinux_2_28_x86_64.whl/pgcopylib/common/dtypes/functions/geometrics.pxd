cpdef (double, double) read_point(
    bytes binary_data,
    object pgoid_function=*,
    object buffer_object=*,
    object pgoid=*,
)
cpdef bytes write_point(
    (double, double) dtype_value,
    object pgoid_function=*,
    object buffer_object=*,
    object pgoid=*,
)
cpdef (double, double, double) read_line(
    bytes binary_data,
    object pgoid_function=*,
    object buffer_object=*,
    object pgoid=*,
)
cpdef bytes write_line(
    (double, double, double) dtype_value,
    object pgoid_function=*,
    object buffer_object=*,
    object pgoid=*,
)
cpdef list read_lseg(
    bytes binary_data,
    object pgoid_function=*,
    object buffer_object=*,
    object pgoid=*,
)
cpdef bytes write_lseg(
    list dtype_value,
    object pgoid_function=*,
    object buffer_object=*,
    object pgoid=*,
)
cpdef ((double, double), (double, double)) read_box(
    bytes binary_data,
    object pgoid_function=*,
    object buffer_object=*,
    object pgoid=*,
)
cpdef bytes write_box(
    ((double, double), (double, double)) dtype_value,
    object pgoid_function=*,
    object buffer_object=*,
    object pgoid=*,
)
cpdef object read_path(
    bytes binary_data,
    object pgoid_function=*,
    object buffer_object=*,
    object pgoid=*,
)
cpdef bytes write_path(
    object dtype_value,
    object pgoid_function=*,
    object buffer_object=*,
    object pgoid=*,
)
cpdef tuple read_polygon(
    bytes binary_data,
    object pgoid_function=*,
    object buffer_object=*,
    object pgoid=*,
)
cpdef bytes write_polygon(
    tuple dtype_value,
    object pgoid_function=*,
    object buffer_object=*,
    object pgoid=*,
)
