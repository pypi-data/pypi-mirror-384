cpdef long read_num_columns(
    object fileobj,
    long column_length,
)
cpdef object read_record(
    object fileobj,
    object reader,
    object pgoid_function,
    object buffer_object,
    long pgoid,
)
cpdef long long skip_all(
    object fileobj,
    long column_length,
    long num_columns,
    long long num_rows,
)
cdef void skip_record(object fileobj)
cpdef long long writer(
    object fileobj,
    object write_row,
    object dtype_values,
    long num_columns,
)
cpdef bytes nullable_writer(
    object write_dtype,
    object dtype_value,
    object pgoid_function,
    object buffer_object,
    long pgoid,
)
