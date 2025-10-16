"""Metadata convert functions."""

from json import dumps

from pgcopylib import PGOid
from pgcopylib.common import ArrayOidToOid
from pgpack import metadata_reader

from nativelib import Column


cdef dict DTYPE2OID = {
    "BFloat16": PGOid.float4,
    "Bool": PGOid.bool,
    "Date": PGOid.date,
    "Date32": PGOid.date,
    "DateTime": PGOid.timestamp,
    "DateTime64": PGOid.timestamptz,
    "Decimal": PGOid.numeric,
    "Enum8": PGOid.varchar,
    "Enum16": PGOid.varchar,
    "FixedString": PGOid.bpchar,
    "Float32": PGOid.float4,
    "Float64": PGOid.float8,
    "IPv4": PGOid.inet,
    "IPv6": PGOid.inet,
    "Int128": PGOid.int8,
    "Int16": PGOid.int2,
    "Int256": PGOid.int8,
    "Int32": PGOid.int4,
    "Int64": PGOid.int8,
    "Int8": PGOid.int2,
    "String": PGOid.varchar,
    "Time": PGOid.time,
    "Time64": PGOid.timetz,
    "UInt128": PGOid.int8,
    "UInt16": PGOid.int4,
    "UInt256": PGOid.int8,
    "UInt32": PGOid.int8,
    "UInt64": PGOid.int8,
    "UInt8": PGOid.int2,
    "UUID": PGOid.uuid,
}
cdef dict OID2ARRAY = {
    PGOid.bit: PGOid._bit,
    PGOid.bool: PGOid._bool,
    PGOid.box: PGOid._box,
    PGOid.bpchar: PGOid._bpchar,
    PGOid.bytea: PGOid._bytea,
    PGOid.char: PGOid._char,
    PGOid.cidr: PGOid._cidr,
    PGOid.circle: PGOid._circle,
    PGOid.date: PGOid._date,
    PGOid.float4: PGOid._float4,
    PGOid.float8: PGOid._float8,
    PGOid.inet: PGOid._inet,
    PGOid.int2: PGOid._int2,
    PGOid.int4: PGOid._int4,
    PGOid.int8: PGOid._int8,
    PGOid.interval: PGOid._interval,
    PGOid.json: PGOid._json,
    PGOid.jsonb: PGOid._jsonb,
    PGOid.line: PGOid._line,
    PGOid.lseg: PGOid._lseg,
    PGOid.macaddr: PGOid._macaddr,
    PGOid.macaddr8: PGOid._macaddr8,
    PGOid.money: PGOid._money,
    PGOid.numeric: PGOid._numeric,
    PGOid.oid: PGOid._oid,
    PGOid.path: PGOid._path,
    PGOid.point: PGOid._point,
    PGOid.polygon: PGOid._polygon,
    PGOid.text: PGOid._text,
    PGOid.time: PGOid._time,
    PGOid.timestamp: PGOid._timestamp,
    PGOid.timestamptz: PGOid._timestamptz,
    PGOid.timetz: PGOid._timetz,
    PGOid.uuid: PGOid._uuid,
    PGOid.varbit: PGOid._varbit,
    PGOid.varchar: PGOid._varchar,
    PGOid.xml: PGOid._xml,
}
cdef dict OID2DTYPE = {
    PGOid.bit: "String",
    PGOid.bool: "Bool",
    # PGOid.box: 603,
    PGOid.bpchar: "FixedString",
    # PGOid.bytea: 17,
    PGOid.char: "String",
    # PGOid.cidr: 650,
    # PGOid.circle: 718,
    PGOid.date: "Date",
    PGOid.float4: "Float32",
    PGOid.float8: "Float64",
    PGOid.inet: "IPv4",
    PGOid.int2: "Int16",
    PGOid.int4: "Int32",
    PGOid.int8: "Int64",
    PGOid.interval: "IntervalSecond",
    PGOid.json: "JSON",
    PGOid.jsonb: "JSON",
    # PGOid.line: 628,
    # PGOid.lseg: 601,
    PGOid.macaddr: "String",
    PGOid.macaddr8: "String",
    PGOid.money: "Float64",
    PGOid.numeric: "Decimal",
    PGOid.oid: "UInt32",
    # PGOid.path: 602,
    PGOid.point: "Point",
    PGOid.polygon: "Polygon",
    PGOid.text: "String",
    PGOid.time: "Time",
    PGOid.timestamp: "DateTime",
    PGOid.timestamptz: "DateTime64",
    PGOid.timetz: "Time64",
    PGOid.uuid: "UUID",
    PGOid.varbit: "String",
    PGOid.varchar: "String",
    PGOid.xml: "String",
}
cdef dict PGLENGTH = {
    PGOid.bool: 1,
    PGOid.box: 32,
    PGOid.circle: 24,
    PGOid.date: 4,
    PGOid.float4: 4,
    PGOid.float8: 8,
    PGOid.int2: 2,
    PGOid.int4: 4,
    PGOid.int8: 8,
    PGOid.interval: 16,
    PGOid.line: 24,
    PGOid.lseg: 32,
    PGOid.macaddr8: 8,
    PGOid.macaddr: 6,
    PGOid.oid: 4,
    PGOid.point: 16,
    PGOid.time: 8,
    PGOid.timestamp: 8,
    PGOid.timestamptz: 8,
    PGOid.timetz: 12,
    PGOid.uuid: 16,
}


cpdef list pgoid_from_metadata(bytes metadata):
    """Convert PGPack metadata to PGCopy metadata."""

    return metadata_reader(metadata)[1]


cpdef list columns_from_metadata(
    bytes metadata,
    object is_nullable = True,
):
    """Convert PGPack metadata to Native column_list."""

    cdef int _i
    cdef str column, dtype
    cdef object pgoid, pgparam
    cdef list column_list = []

    for column, pgoid, pgparam in zip(*metadata_reader(metadata)):

        if pgparam.nested:
            pgoid = ArrayOidToOid[pgoid]

        dtype = OID2DTYPE[pgoid]

        if dtype in ("DateTime64", "Time64"):
            dtype += "(3)"
        elif dtype == "Decimal":
            dtype += f"({pgparam.length}, {pgparam.scale})"
        elif dtype == "FixedString":
            dtype += f"({pgparam.length})"

        if is_nullable:
            dtype = f"Nullable({dtype})"

        for _i in range(pgparam.nested):
            dtype = f"Array({dtype})"

        column_list.append(Column(column, dtype))

    return column_list


cpdef bytes metadata_from_columns(list column_list):
    """Convert Native column_list to PGPack metadata."""

    cdef list pg_column_info, column_info, metadata = []
    cdef int number, lengths, scale, nested
    cdef object column, info, oid
    cdef str name, dtype, json_metadata

    for number, column in enumerate(column_list, 1):
        info = column.info
        name = info.column
        dtype = info.dtype.name
        oid = DTYPE2OID[dtype]

        if oid is PGOid.bpchar:
            lengths = info.length
        elif oid is PGOid.numeric:
            lengths = info.precission
        else:
            lengths = PGLENGTH.get(oid, -1)

        scale = info.scale or 0
        nested = info.nested

        if info.is_array:
            oid = OID2ARRAY[oid]

        pg_column_info = [name, oid.value, lengths, scale, nested]
        column_info = [number, pg_column_info]
        metadata.append(column_info)

    json_metadata = dumps(metadata, ensure_ascii=False)
    return json_metadata.encode("utf-8")
