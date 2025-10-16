"""DBHose dumps convertors utility."""

from light_compressor import CompressionMethod

from .common import (
    columns_from_metadata,
    metadata_from_columns,
    pgoid_from_metadata,
)
from .convertor import (
    DumpClass,
    DumpType,
    chunk_fileobj,
    dump_convertor,
)
from .detective import dump_detective


__all__ = (
    "CompressionMethod",
    "DumpClass",
    "DumpType",
    "chunk_fileobj",
    "columns_from_metadata",
    "dump_convertor",
    "dump_detective",
    "metadata_from_columns",
    "pgoid_from_metadata",
)
__author__ = "0xMihalich"
__version__ = "0.0.0.4"
