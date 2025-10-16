from ipaddress import (
    IPv4Address,
    IPv4Network,
    IPv6Address,
    IPv6Network,
)


def read_network(
    binary_data: bytes,
    pgoid_function: object | None = None,
    buffer_object: object | None = None,
    pgoid: int | None = None,
) -> IPv4Address | IPv4Network | IPv6Address | IPv6Network:
    """Unpack inet or cidr value."""

    ...


def write_network(
    dtype_value: IPv4Address | IPv4Network | IPv6Address | IPv6Network,
    pgoid_function: object | None = None,
    buffer_object: object | None = None,
    pgoid: int | None = None,
) -> bytes:
    """Pack inet or cidr value."""

    ...
