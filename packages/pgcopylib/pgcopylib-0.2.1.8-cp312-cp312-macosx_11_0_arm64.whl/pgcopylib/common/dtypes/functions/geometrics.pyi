def read_point(
    binary_data: bytes,
    pgoid_function: object | None = None,
    buffer_object: object | None = None,
    pgoid: int | None = None,
) -> tuple[float, float]:
    """Unpack point value."""

    ...


def write_point(
    dtype_value: tuple[float, float],
    pgoid_function: object | None = None,
    buffer_object: object | None = None,
    pgoid: int | None = None,
) -> bytes:
    """Pack point value."""

    ...


def read_line(
    binary_data: bytes,
    pgoid_function: object | None = None,
    buffer_object: object | None = None,
    pgoid: int | None = None,
) -> tuple[float, float, float]:
    """Unpack line value."""

    ...


def write_line(
    dtype_value: tuple[float, float, float],
    pgoid_function: object | None = None,
    buffer_object: object | None = None,
    pgoid: int | None = None,
) -> bytes:
    """Pack line value."""

    ...


def read_lseg(
    binary_data: bytes,
    pgoid_function: object | None = None,
    buffer_object: object | None = None,
    pgoid: int | None = None,
) -> list[tuple[float, float], tuple[float, float]]:
    """Unpack lseg value."""

    ...


def write_lseg(
    dtype_value: list[tuple[float, float], tuple[float, float]],
    pgoid_function: object | None = None,
    buffer_object: object | None = None,
    pgoid: int | None = None,
) -> bytes:
    """Pack lseg value."""

    ...


def read_box(
    binary_data: bytes,
    pgoid_function: object | None = None,
    buffer_object: object | None = None,
    pgoid: int | None = None,
) -> tuple[tuple[float, float], tuple[float, float]]:
    """Unpack box value."""

    ...


def write_box(
    dtype_value: tuple[tuple[float, float], tuple[float, float]],
    pgoid_function: object | None = None,
    buffer_object: object | None = None,
    pgoid: int | None = None,
) -> bytes:
    """Pack box value."""

    ...


def read_path(
    binary_data: bytes,
    pgoid_function: object | None = None,
    buffer_object: object | None = None,
    pgoid: int | None = None,
) -> list[tuple[float, ...]] | tuple[tuple[float, ...]]:
    """Unpack path value."""

    ...


def write_path(
    dtype_value: list[tuple[float, ...]] | tuple[tuple[float, ...]],
    pgoid_function: object | None = None,
    buffer_object: object | None = None,
    pgoid: int | None = None,
) -> bytes:
    """Pack path value."""

    ...


def read_polygon(
    binary_data: bytes,
    pgoid_function: object | None = None,
    buffer_object: object | None = None,
    pgoid: int | None = None,
) -> tuple[float, ...]:
    """Unpack polygon value."""

    ...


def write_polygon(
    dtype_value: tuple[float, ...],
    pgoid_function: object | None = None,
    buffer_object: object | None = None,
    pgoid: int | None = None,
) -> bytes:
    """Pack polygon value."""

    ...
