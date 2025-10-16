"""Auto detect dump type and compression method."""

from io import BufferedReader
from pathlib import Path

from light_compressor import define_reader
from nativelib import NativeReader
from pgcopylib import PGCopyReader
from pgpack import PGPackReader
from pgpack.common import HEADER


PGCOPY_HEADER = b"PGCOPY\n\xff"


def dump_detective(
    file: str | Path | BufferedReader
) -> PGCopyReader | PGPackReader | NativeReader:
    """Auto detect dump type and return reader."""

    if isinstance(file, str | Path):
        fileobj = open(file, "rb")
    elif hasattr(file, "read"):
        fileobj = file
    else:
        raise ValueError(
            "File type must be str, Path, BytesIO or "
            f"BufferedReader not {file.__class__}"
        )

    buffer_obj = define_reader(fileobj)
    pos = buffer_obj.tell()
    header = buffer_obj.read(8)
    buffer_obj.seek(pos)

    if header == HEADER:
        return PGPackReader(buffer_obj)
    if header == PGCOPY_HEADER:
        return PGCopyReader(buffer_obj)

    return NativeReader(buffer_obj)
