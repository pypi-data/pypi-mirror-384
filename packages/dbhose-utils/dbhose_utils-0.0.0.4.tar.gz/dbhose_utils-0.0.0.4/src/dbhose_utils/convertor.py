"""Dump convert functions."""

from collections.abc import Generator
from enum import Enum
from io import BufferedReader
from itertools import chain
from typing import NamedTuple

from light_compressor import (
    CompressionMethod,
    define_reader,
    define_writer,
)
from nativelib import (
    NativeReader,
    NativeWriter,
)
from pgcopylib import (
    PGCopyReader,
    PGCopyWriter,
)
from pgpack import (
    PGPackReader,
    PGPackWriter,
)

from .common import (
    columns_from_metadata,
    metadata_from_columns,
    pgoid_from_metadata,
)
from .detective import dump_detective as detective


CHUNK_SIZE = 1_048_576


class DumpClass(NamedTuple):
    """Class for reader/writer implementations."""

    name: str
    reader: object
    writer: object
    have_compress: bool


class DumpType(DumpClass, Enum):
    """Dump type enum."""

    NATIVE = DumpClass("native", NativeReader, NativeWriter, False)
    PGCOPY = DumpClass("pgcopy", PGCopyReader, PGCopyWriter, False)
    PGPACK = DumpClass("pgpack", PGPackReader, PGPackWriter, True)


def chunk_fileobj(fileobj: BufferedReader) -> Generator[bytes, None, None]:
    """Chunk fileobject to bytes generator."""

    while chunk := fileobj.read(CHUNK_SIZE):
        yield chunk

    fileobj.close()


def dump_convertor(
    source: str,
    destination: str,
    dump_type: DumpType | str,
    compression_method: CompressionMethod | str = CompressionMethod.NONE,
) -> None:
    """Convert dumps function."""

    if dump_type.__class__ is str:
        dump_type = DumpType[dump_type.upper()]

    if compression_method.__class__ is str:
        compression_method = CompressionMethod[compression_method.upper()]

    reader: NativeReader | PGCopyReader | PGPackReader = detective(source)

    if reader.__class__ is PGCopyReader and dump_type is not DumpType.PGCOPY:
        raise TypeError(
            "PGCopy dump don't support convert to any other types."
        )
    if source == destination:
        raise ValueError("Files path is not different.")

    if reader.__class__ is dump_type.reader:
        if dump_type.reader in (NativeReader, PGCopyReader):
            reader.close()
            source_obj = define_reader(open(source, "rb"))
            writer = define_writer(
                chunk_fileobj(source_obj),
                compression_method,
            )

            with open(destination, "wb") as fileobj:
                for bytes_data in writer:
                    fileobj.write(bytes_data)

        elif dump_type.reader is PGPackReader:
            metadata = reader.metadata
            bytes_data = reader.to_bytes()
            fileobj = open(destination, "wb")
            writer = PGPackWriter(fileobj, metadata, compression_method)
            writer.from_bytes(bytes_data)
            writer.close()
    else:
        if reader.__class__ is NativeReader:
            dtype_values = chain(reader.block_reader.read(), reader.to_rows())
            column_list = reader.block_reader.column_list
            metadata = metadata_from_columns(column_list)
            fileobj = open(destination, "wb")

            if dump_type.writer is PGCopyWriter:
                pgtypes = pgoid_from_metadata(metadata)
                writer = PGCopyWriter(None, pgtypes)
                bytes_data = writer.from_rows(reader.to_rows())

                with fileobj:
                    for data in define_writer(
                        bytes_data,
                        compression_method,
                    ):
                        fileobj.write(data)

            elif dump_type.writer is PGPackWriter:
                writer = PGPackWriter(fileobj, metadata, compression_method)
                writer.from_rows(dtype_values)
                writer.close()
        elif reader.__class__ is PGPackReader:
            if dump_type.writer is NativeWriter:
                column_list = columns_from_metadata(reader.metadata)
                writer = NativeWriter(column_list)
                bytes_data = writer.from_rows(reader.to_rows())
            elif dump_type.writer is PGCopyWriter:
                bytes_data = reader.to_bytes()

            with open(destination, "wb") as fileobj:
                for data in define_writer(
                    bytes_data,
                    compression_method,
                ):
                    fileobj.write(data)

    reader.close()
