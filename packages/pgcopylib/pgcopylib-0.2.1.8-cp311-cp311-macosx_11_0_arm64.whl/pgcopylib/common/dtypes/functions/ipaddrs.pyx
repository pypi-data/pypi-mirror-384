from ipaddress import (
    IPv4Address,
    IPv4Network,
    IPv6Address,
    IPv6Network,
)
from struct import (
    pack,
    unpack,
)


cdef dict IpAddr = {
    2: IPv4Address,
    3: IPv6Address,
    IPv4Address: 2,
    IPv4Network: 2,
    IPv6Network: 3,
    IPv6Address: 3,
}
cdef dict IpNet = {
    IPv4Address: IPv4Network,
    IPv6Address: IPv6Network,
}


cpdef object read_network(
    bytes binary_data,
    object pgoid_function = None,
    object buffer_object = None,
    object pgoid = None,
):
    """Unpack inet or cidr value."""

    cdef int binary_length = len(binary_data) - 4
    cdef unsigned char ip_family, ip_netmask, is_cidr, ip_length
    cdef bytes ip_data
    ip_family, ip_netmask, is_cidr, ip_length, ip_data = unpack(
        f"!4B{binary_length}s",
        binary_data,
    )

    cdef object ip_addr = IpAddr[ip_family](ip_data)

    if is_cidr:
        return IpNet[ip_addr.__class__](
            f"{ip_addr}/{ip_netmask}",
            strict=False,
        )

    return ip_addr


cpdef bytes write_network(
    object dtype_value,
    object pgoid_function = None,
    object buffer_object = None,
    object pgoid = None,
):
    """Pack inet or cidr value."""

    cdef unsigned char ip_family, ip_netmask, is_cidr, ip_length
    cdef bytes ip_addr

    if isinstance(dtype_value, IPv4Address | IPv6Address):
        ip_addr = dtype_value.packed
        ip_netmask = dtype_value.max_prefixlen
        is_cidr = 0
    elif isinstance(dtype_value, IPv4Network | IPv6Network):
        ip_addr = dtype_value.network_address.packed
        ip_netmask = dtype_value._prefixlen
        is_cidr = 1

    ip_family = IpAddr[dtype_value]
    ip_length = len(ip_addr)

    return pack(
        f"!4B{ip_length}s",
        ip_family,
        ip_netmask,
        is_cidr,
        ip_length,
        ip_addr,
    )
