from enum import Enum

from .dtypes import PostgreSQLDtype


class PGOid(Enum):
    """PGCopy OID Identifiers."""

    _bit = 1561
    _bool = 1000
    _box = 1020
    _bpchar = 1014
    _bytea = 1001
    _char = 1002
    _cidr = 651
    _circle = 719
    _date = 1182
    _float4 = 1021
    _float8 = 1022
    _inet = 1041
    _int2 = 1005
    _int4 = 1007
    _int8 = 1016
    _interval = 1187
    _json = 199
    _jsonb = 3807
    _line = 629
    _lseg = 1018
    _macaddr = 1040
    _macaddr8 = 775
    _money = 791
    _numeric = 1231
    _oid = 1028
    _path = 1019
    _point = 1017
    _polygon = 1027
    _text = 1009
    _time = 1183
    _timestamp = 1115
    _timestamptz = 1185
    _timetz = 1270
    _tsquery = 3645
    _tsvector = 3643
    _uuid = 2951
    _varbit = 1563
    _varchar = 1015
    _xml = 143
    bit = 1560
    bool = 16
    box = 603
    bpchar = 1042
    bytea = 17
    char = 18
    cidr = 650
    circle = 718
    date = 1082
    float4 = 700
    float8 = 701
    inet = 869
    int2 = 21
    int4 = 23
    int8 = 20
    interval = 1186
    json = 114
    jsonb = 3802
    line = 628
    lseg = 601
    macaddr = 829
    macaddr8 = 774
    money = 790
    numeric = 1700
    oid = 26
    path = 602
    point = 600
    polygon = 604
    text = 25
    time = 1083
    timestamp = 1114
    timestamptz = 1184
    timetz = 1266
    tsquery = 3615
    tsvector = 3614
    uuid = 2950
    varbit = 1562
    varchar = 1043
    xml = 142


ArrayOidToOid: dict[PGOid, PGOid] = {
    PGOid._bit: PGOid.bit,
    PGOid._bool: PGOid.bool,
    PGOid._box: PGOid.box,
    PGOid._bpchar: PGOid.bpchar,
    PGOid._bytea: PGOid.bytea,
    PGOid._char: PGOid.char,
    PGOid._cidr: PGOid.cidr,
    PGOid._circle: PGOid.circle,
    PGOid._date: PGOid.date,
    PGOid._float4: PGOid.float4,
    PGOid._float8: PGOid.float8,
    PGOid._inet: PGOid.inet,
    PGOid._int2: PGOid.int2,
    PGOid._int4: PGOid.int4,
    PGOid._int8: PGOid.int8,
    PGOid._interval: PGOid.interval,
    PGOid._json: PGOid.json,
    PGOid._jsonb: PGOid.jsonb,
    PGOid._line: PGOid.line,
    PGOid._lseg: PGOid.lseg,
    PGOid._macaddr: PGOid.macaddr,
    PGOid._macaddr8: PGOid.macaddr8,
    PGOid._money: PGOid.money,
    PGOid._numeric: PGOid.numeric,
    PGOid._oid: PGOid.oid,
    PGOid._path: PGOid.path,
    PGOid._point: PGOid.point,
    PGOid._polygon: PGOid.polygon,
    PGOid._text: PGOid.text,
    PGOid._time: PGOid.time,
    PGOid._timestamp: PGOid.timestamp,
    PGOid._timestamptz: PGOid.timestamptz,
    PGOid._timetz: PGOid.timetz,
    PGOid._uuid: PGOid.uuid,
    PGOid._varbit: PGOid.varbit,
    PGOid._varchar: PGOid.varchar,
    PGOid._xml: PGOid.xml,
}


PGOidToDType: dict[PGOid, PostgreSQLDtype] = {
    # Associate oid with data type.
    PGOid._bit: PostgreSQLDtype.Array,
    PGOid._bool: PostgreSQLDtype.Array,
    PGOid._box: PostgreSQLDtype.Array,
    PGOid._bpchar: PostgreSQLDtype.Array,
    PGOid._bytea: PostgreSQLDtype.Array,
    PGOid._char: PostgreSQLDtype.Array,
    PGOid._cidr: PostgreSQLDtype.Array,
    PGOid._circle: PostgreSQLDtype.Array,
    PGOid._date: PostgreSQLDtype.Array,
    PGOid._float4: PostgreSQLDtype.Array,
    PGOid._float8: PostgreSQLDtype.Array,
    PGOid._inet: PostgreSQLDtype.Array,
    PGOid._int2: PostgreSQLDtype.Array,
    PGOid._int4: PostgreSQLDtype.Array,
    PGOid._int8: PostgreSQLDtype.Array,
    PGOid._interval: PostgreSQLDtype.Array,
    PGOid._json: PostgreSQLDtype.Array,
    PGOid._jsonb: PostgreSQLDtype.Array,
    PGOid._line: PostgreSQLDtype.Array,
    PGOid._lseg: PostgreSQLDtype.Array,
    PGOid._macaddr: PostgreSQLDtype.Array,
    PGOid._macaddr8: PostgreSQLDtype.Array,
    PGOid._money: PostgreSQLDtype.Array,
    PGOid._numeric: PostgreSQLDtype.Array,
    PGOid._oid: PostgreSQLDtype.Array,
    PGOid._path: PostgreSQLDtype.Array,
    PGOid._point: PostgreSQLDtype.Array,
    PGOid._polygon: PostgreSQLDtype.Array,
    PGOid._text: PostgreSQLDtype.Array,
    PGOid._time: PostgreSQLDtype.Array,
    PGOid._timestamp: PostgreSQLDtype.Array,
    PGOid._timestamptz: PostgreSQLDtype.Array,
    PGOid._timetz: PostgreSQLDtype.Array,
    PGOid._uuid: PostgreSQLDtype.Array,
    PGOid._varbit: PostgreSQLDtype.Array,
    PGOid._varchar: PostgreSQLDtype.Array,
    PGOid._xml: PostgreSQLDtype.Array,
    PGOid.bit: PostgreSQLDtype.Bit,
    PGOid.bool: PostgreSQLDtype.Bool,
    PGOid.box: PostgreSQLDtype.Box,
    PGOid.bpchar: PostgreSQLDtype.Text,
    PGOid.bytea: PostgreSQLDtype.Bytes,
    PGOid.char: PostgreSQLDtype.Text,
    PGOid.cidr: PostgreSQLDtype.Cidr,
    PGOid.circle: PostgreSQLDtype.Circle,
    PGOid.date: PostgreSQLDtype.Date,
    PGOid.float4: PostgreSQLDtype.Float4,
    PGOid.float8: PostgreSQLDtype.Float8,
    PGOid.inet: PostgreSQLDtype.Inet,
    PGOid.int2: PostgreSQLDtype.Int2,
    PGOid.int4: PostgreSQLDtype.Int4,
    PGOid.int8: PostgreSQLDtype.Int8,
    PGOid.interval: PostgreSQLDtype.Interval,
    PGOid.json: PostgreSQLDtype.Json,
    PGOid.jsonb: PostgreSQLDtype.Json,
    PGOid.line: PostgreSQLDtype.Line,
    PGOid.lseg: PostgreSQLDtype.Lseg,
    PGOid.macaddr: PostgreSQLDtype.Macaddr,
    PGOid.macaddr8: PostgreSQLDtype.Macaddr8,
    PGOid.money: PostgreSQLDtype.Money,
    PGOid.numeric: PostgreSQLDtype.Numeric,
    PGOid.oid: PostgreSQLDtype.Oid,
    PGOid.path: PostgreSQLDtype.Path,
    PGOid.point: PostgreSQLDtype.Point,
    PGOid.polygon: PostgreSQLDtype.Polygon,
    PGOid.text: PostgreSQLDtype.Text,
    PGOid.time: PostgreSQLDtype.Time,
    PGOid.timestamp: PostgreSQLDtype.Timestamp,
    PGOid.timestamptz: PostgreSQLDtype.Timestamptz,
    PGOid.timetz: PostgreSQLDtype.Timetz,
    PGOid.uuid: PostgreSQLDtype.Uuid,
    PGOid.varbit: PostgreSQLDtype.Bit,
    PGOid.varchar: PostgreSQLDtype.Text,
    PGOid.xml: PostgreSQLDtype.Text,
}
