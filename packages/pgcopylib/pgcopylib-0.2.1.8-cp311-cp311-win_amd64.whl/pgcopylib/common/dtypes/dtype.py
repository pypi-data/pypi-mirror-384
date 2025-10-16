"""Convert between bytes and data types functions."""

from datetime import (
    date,
    datetime as dt,
    time,
)
from dateutil.relativedelta import relativedelta as rd
from enum import Enum
from ipaddress import (
    IPv4Address as IP4A,
    IPv4Network as IP4N,
    IPv6Address as IP6A,
    IPv6Network as IP6N,
)
from typing import NamedTuple
from types import FunctionType

from .functions import (
    read_array,
    read_bits,
    read_bool,
    read_box,
    read_bytea,
    read_date,
    read_float4,
    read_float8,
    read_int2,
    read_int4,
    read_int8,
    read_interval,
    read_json,
    read_line,
    read_lseg,
    read_macaddr,
    read_money,
    read_network,
    read_numeric,
    read_oid,
    read_path,
    read_point,
    read_polygon,
    read_serial2,
    read_serial4,
    read_serial8,
    read_text,
    read_time,
    read_timestamp,
    read_timestamptz as read_stamptz,
    read_timetz,
    read_uuid,
    write_array,
    write_bits,
    write_bool,
    write_box,
    write_bytea,
    write_date,
    write_float4,
    write_float8,
    write_int2,
    write_int4,
    write_int8,
    write_interval,
    write_json,
    write_line,
    write_lseg,
    write_macaddr,
    write_money,
    write_network,
    write_numeric,
    write_oid,
    write_path,
    write_point,
    write_polygon,
    write_serial2,
    write_serial4,
    write_serial8,
    write_text,
    write_time,
    write_timestamp,
    write_timestamptz as write_stamptz,
    write_timetz,
    write_uuid,
)


class PGTypeFunc(NamedTuple):
    """Class for associate read and write functions."""

    name: str
    pytype: type
    length: int
    read: FunctionType
    write: FunctionType


class PostgreSQLDtype(PGTypeFunc, Enum):
    """Associate read and write functions with postgres data type."""

    Array = PGTypeFunc("Array", list, -1, read_array, write_array)
    Bit = PGTypeFunc("Bit", str, -1, read_bits, write_bits)
    Bool = PGTypeFunc("Bool", bool, 1, read_bool, write_bool)
    Box = PGTypeFunc("Box", tuple, 32, read_box, write_box)
    Bytes = PGTypeFunc("Bytes", bytes, -1, read_bytea, write_bytea)
    Cidr = PGTypeFunc("Cidr", IP4N | IP6N, -1, read_network, write_network)
    Circle = PGTypeFunc("Circle", tuple, 24, read_line, write_line)
    Date = PGTypeFunc("Date", date, 4, read_date, write_date)
    Float4 = PGTypeFunc("Float4", float, 4, read_float4, write_float4)
    Float8 = PGTypeFunc("Float8", float, 8, read_float8, write_float8)
    Inet = PGTypeFunc("Inet", IP4A | IP6A, -1, read_network, write_network)
    Int2 = PGTypeFunc("Int2", int, 2, read_int2, write_int2)
    Int4 = PGTypeFunc("Int4", int, 4, read_int4, write_int4)
    Int8 = PGTypeFunc("Int8", int, 8, read_int8, write_int8)
    Interval = PGTypeFunc("Interval", rd, 16, read_interval, write_interval)
    Json = PGTypeFunc("Json", dict, -1, read_json, write_json)
    Line = PGTypeFunc("Line", tuple, 24, read_line, write_line)
    Lseg = PGTypeFunc("Lseg", list, 32, read_lseg, write_lseg)
    Macaddr8 = PGTypeFunc("Macaddr8", str, 8, read_macaddr, write_macaddr)
    Macaddr = PGTypeFunc("Macaddr", str, 6, read_macaddr, write_macaddr)
    Money = PGTypeFunc("Money", float, -1, read_money, write_money)
    Numeric = PGTypeFunc("Numeric", object, -1, read_numeric, write_numeric)
    Oid = PGTypeFunc("Oid", int, 4, read_oid, write_oid)
    Path = PGTypeFunc("Path", tuple | list, -1, read_path, write_path)
    Point = PGTypeFunc("Point", tuple, 16, read_point, write_point)
    Polygon = PGTypeFunc("Polygon", tuple, -1, read_polygon, write_polygon)
    Serial2 = PGTypeFunc("Serial2", int, 2, read_serial2, write_serial2)
    Serial4 = PGTypeFunc("Serial4", int, 4, read_serial4, write_serial4)
    Serial8 = PGTypeFunc("Serial8", int, 8, read_serial8, write_serial8)
    Text = PGTypeFunc("Text", str, -1, read_text, write_text)
    Time = PGTypeFunc("Time", time, 8, read_time, write_time)
    Timestamp = PGTypeFunc("Timestamp", dt, 8, read_timestamp, write_timestamp)
    Timestamptz = PGTypeFunc("Timestamptz", dt, 8, read_stamptz, write_stamptz)
    Timetz = PGTypeFunc("Timetz", time, 12, read_timetz, write_timetz)
    Uuid = PGTypeFunc("Uuid", object, 16, read_uuid, write_uuid)
