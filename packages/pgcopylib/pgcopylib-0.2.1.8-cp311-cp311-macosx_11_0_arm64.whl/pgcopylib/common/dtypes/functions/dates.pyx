from datetime import (
    date,
    datetime,
    time,
    timedelta,
    timezone,
)
from dateutil.relativedelta import relativedelta
from struct import (
    pack,
    unpack,
    unpack_from,
)


cdef object DEFAULT_DATE = date(2000, 1, 1)
cdef object DEFAULT_DATETIME = datetime(2000, 1, 1)
cdef long long MICROSECONDS_PER_SECOND = 1_000_000
cdef int SECONDS_PER_MINUTE = 60
cdef int HOURS_PER_DAY = 24
cdef int SECONDS_PER_HOUR = 3600


cpdef object read_date(
    bytes binary_data,
    object pgoid_function = None,
    object buffer_object = None,
    object pgoid = None,
):
    """Unpack date value."""

    return DEFAULT_DATE + timedelta(days=unpack("!i", binary_data)[0])


cpdef bytes write_date(
    object dtype_value,
    object pgoid_function = None,
    object buffer_object = None,
    object pgoid = None,
):
    """Pack date value."""

    if dtype_value.__class__.__name__ in ("Timestamp", "datetime"):
        dtype_value = dtype_value.date()

    cdef int days = (dtype_value - DEFAULT_DATE).days
    return pack("!i", days)


cpdef object read_timestamp(
    bytes binary_data,
    object pgoid_function = None,
    object buffer_object = None,
    object pgoid = None,
):
    """Unpack timestamp value."""

    return DEFAULT_DATETIME + timedelta(
        microseconds=unpack("!q", binary_data)[0]
    )


cpdef bytes write_timestamp(
    object dtype_value,
    object pgoid_function = None,
    object buffer_object = None,
    object pgoid = None,
):
    """Pack timestamp value."""

    if dtype_value.__class__.__name__ == "Timestamp":
        dtype_value = dtype_value.to_pydatetime()
    elif dtype_value.__class__ is date:
        dtype_value = datetime.combine(dtype_value, datetime.min.time())

    cdef long long seconds = (dtype_value - DEFAULT_DATETIME).total_seconds()
    cdef long long microseconds = seconds * MICROSECONDS_PER_SECOND
    return pack("!q", microseconds)


cpdef object read_timestamptz(
    bytes binary_data,
    object pgoid_function = None,
    object buffer_object = None,
    object pgoid = None,
):
    """Unpack timestamptz value."""

    return read_timestamp(binary_data).replace(tzinfo=timezone.utc)


cpdef bytes write_timestamptz(
    object dtype_value,
    object pgoid_function = None,
    object buffer_object = None,
    object pgoid = None,
):
    """Pack timestamptz value."""

    return write_timestamp(dtype_value.astimezone(timezone.utc))


cpdef object read_time(
    bytes binary_data,
    object pgoid_function = None,
    object buffer_object = None,
    object pgoid = None,
):
    """Unpack time value."""

    cdef long long microseconds, total_seconds, total_minutes
    cdef long long hours, minutes, seconds, microsecond

    microseconds = unpack_from("!q", binary_data)[0]
    total_seconds = microseconds // MICROSECONDS_PER_SECOND
    microsecond = microseconds % MICROSECONDS_PER_SECOND
    seconds = total_seconds % SECONDS_PER_MINUTE
    total_minutes = total_seconds // SECONDS_PER_MINUTE
    minutes = total_minutes % SECONDS_PER_MINUTE
    hours = total_minutes // SECONDS_PER_MINUTE
    hours = hours % HOURS_PER_DAY

    return time(hours, minutes, seconds, microsecond)


cpdef bytes write_time(
    object dtype_value,
    object pgoid_function = None,
    object buffer_object = None,
    object pgoid = None,
):
    """Pack time value."""

    cdef long long hour_per_microsecond = (
        dtype_value.hour * SECONDS_PER_HOUR * MICROSECONDS_PER_SECOND
    )
    cdef long long minute_per_microsecond = (
        dtype_value.minute * SECONDS_PER_MINUTE * MICROSECONDS_PER_SECOND
    )
    cdef long long second_per_microsecond = (
        dtype_value.second * MICROSECONDS_PER_SECOND
    )
    cdef long long total_microseconds = (
        hour_per_microsecond +
        minute_per_microsecond +
        second_per_microsecond +
        dtype_value.microsecond
    )
    return pack("!q", total_microseconds)


cpdef object read_timetz(
    bytes binary_data,
    object pgoid_function = None,
    object buffer_object = None,
    object pgoid = None,
):
    """Unpack timetz value."""

    cdef object time_notz = read_time(binary_data)
    cdef long tz_offset_sec = unpack("!i", binary_data[-4:])[0]
    cdef object tz_offset = timedelta(seconds=tz_offset_sec)
    return time_notz.replace(tzinfo=timezone(tz_offset))


cpdef bytes write_timetz(
    object dtype_value,
    object pgoid_function = None,
    object buffer_object = None,
    object pgoid = None,
):
    """Pack timetz value."""

    cdef long long hour_per_microsecond = (
        dtype_value.hour * SECONDS_PER_HOUR * MICROSECONDS_PER_SECOND
    )
    cdef long long minute_per_microsecond = (
        dtype_value.minute * SECONDS_PER_MINUTE * MICROSECONDS_PER_SECOND
    )
    cdef long long second_per_microsecond = (
        dtype_value.second * MICROSECONDS_PER_SECOND
    )
    cdef long long total_microseconds = (
        hour_per_microsecond +
        minute_per_microsecond +
        second_per_microsecond +
        dtype_value.microsecond
    )
    cdef object tz_offset = dtype_value.tzinfo.utcoffset(None)
    cdef int offset = tz_offset.total_seconds()
    return pack("!qi", total_microseconds, offset)


cpdef object read_interval(
    bytes binary_data,
    object pgoid_function = None,
    object buffer_object = None,
    object pgoid = None,
):
    """Unpack interval value."""

    cdef long long microseconds
    cdef int days, months
    microseconds, days, months = unpack("!qii", binary_data)
    return relativedelta(months=months, days=days, microseconds=microseconds)


cpdef bytes write_interval(
    object dtype_value,
    object pgoid_function = None,
    object buffer_object = None,
    object pgoid = None,
):
    """Pack interval value."""

    cdef long long days = dtype_value.days or 0
    cdef long long months = dtype_value.months or 0
    cdef long long hours = dtype_value.hours or 0
    cdef long long minutes = dtype_value.minutes or 0
    cdef long long seconds = dtype_value.seconds or 0
    cdef long long microseconds = dtype_value.microseconds or 0
    cdef long long hour_per_microsecond = (
        hours * SECONDS_PER_HOUR * MICROSECONDS_PER_SECOND
    )
    cdef long long minute_per_microsecond = (
        minutes * SECONDS_PER_MINUTE * MICROSECONDS_PER_SECOND
    )
    cdef long long second_per_microsecond = (
        seconds * MICROSECONDS_PER_SECOND
    )
    cdef long long total_microseconds = (
        hour_per_microsecond +
        minute_per_microsecond +
        second_per_microsecond +
        microseconds
    )
    return pack("!qii", total_microseconds, days, months)
