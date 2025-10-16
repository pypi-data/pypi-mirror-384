"""Metadata convert functions."""

from nativelib import Column
from pgcopylib import PGOid


def pgoid_from_metadata(metadata: bytes) -> list[PGOid]:
    """Convert PGPack metadata to PGCopy metadata."""

    ...


def columns_from_metadata(
    metadata: bytes,
    is_nullable: bool = True,
) -> list[Column]:
    """Convert PGPack metadata to Native column_list."""

    ...


def metadata_from_columns(column_list: list[Column]) -> bytes:
    """Convert Native column_list to PGPack metadata."""

    ...
