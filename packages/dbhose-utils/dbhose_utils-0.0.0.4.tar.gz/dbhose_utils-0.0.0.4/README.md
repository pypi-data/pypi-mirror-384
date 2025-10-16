# DBHouse Utils

Dump convertor utility

## Enums

### CompressionMethod

Enum for select current compression method

* NONE - without compression
* LZ4 - lz4 compression
* ZSTD - zstd compression

### DumpType

Enum for dump class classification

* NATIVE - Clickhouse native
* PGCOPY - Postgres/Greenplum pgcopy
* PGPACK - Postgres/Greenplum pgpack container with metadata and pgcopy

### DumpClass

NamedTuple object for DumpType value

* name: str
* reader: object
* writer: object
* have_compress: bool

## Cython functions

### columns_from_metadata

Function for convert pgpack metadata to native column list

### metadata_from_columns

Function for convert native column list to pgpack metadata

### pgoid_from_metadata

Function for convert pgpack metadata to pgcopy oid list

## Python functions

### chunk_fileobj

Function for make iterable bytes chunks from file

### dump_convertor

Function for convert dump to another dump

A dump in Native format can be converted to PGPack or PGCopy, or you can leave it in Native format but change the compression codec.
A dump in PGPack format can be converted to Native or PGCopy, or you can leave it in PGPack format but change the compression codec.
A dump in PGCopy format cannot be converted to other formats due to its storage characteristics (no metadata),
but you can change the compression codec for compact storage of the dump on disk.

Example

```python
from dbhose_utils import dump_convertor

source = "path_to_source_dump"
destination = "path_to_output_dump"
dump_type = "native"  # Native, PGPack or PGCopy output format
compression_method = "lz4"  # lz4, zstd or none

dump_convertor(
    source=source,
    destination=destination,
    dump_type=dump_type,
    compression_method=compression_method,
)
```

### dump_detective

Function for auto detect dump type and compression method

Make current reader object from dump

## Installation

From pip

```bash
pip install dbhose-utils
```

From local directory

```bash
pip install .
```

From git

```bash
pip install git+https://github.com/0xMihalich/dbhose_utils
```
