# PGPack format

Storage format for PGCopy dump packed into LZ4, ZSTD or uncompressed with meta data information packed into zlib

## PGPack structure

- header b"PGPACK\n\x00" 8 bytes
- unsigned long integer zlib.crc32 for packed metadata 4 bytes
- unsigned long integer zlib packed metadata length 4 bytes
- zlib packed metadata
- unsigned char compression method 1 byte
- unsigned long long integer packed pgcopy data length 8 bytes
- unsigned long long integer unpacked pgcopy data length 8 bytes
- packed pgcopy data

## Installation

### From pip

```bash
pip install pgpack
```

### From local directory

```bash
pip install .
```

### From git

```bash
pip install git+https://github.com/0xMihalich/pgpack
```

## Metadata format

Metadata for PGCopy dump contained Column names and OID Types

### Decompressed metadata structure

```
list[
    list[
        column number int,
        list[
            column name str,
            column oid int,
            column lengths int,
            column scale int,
            column nested int,
        ]
    ]
]
```

## Compression methods

- NONE (value = 0x02) PGCopy dump without compression
- LZ4 (value = 0x82) PGCopy dump with lz4 compression
- ZSTD (value = 0x90) PGCopy dump with zstd compression

### Get ENUM for set compression method

```python
from pgpack import CompressionMethod

compression_method = CompressionMethod.NONE  # no compression
compression_method = CompressionMethod.LZ4  # lz4 compression
compression_method = CompressionMethod.ZSTD  # zstd compression (default)
```

## Class PGPackReader

Initialization parameters

- fileobj - BufferedReader object (file, BytesIO e t.c)

Methods and attributes

- metadata - metadata in bytes
- columns - List columns names
- pgtypes - List PGOid for all columns
- pgparam - List PGParam for all columns
- pgcopy_compressed_length - integer packed pgcopy data length
- pgcopy_data_length - integer unpacked pgcopy data length
- compression_method - CompressionMethod object
- compression_stream - BufferedReader object for decompress data
- pgcopy_start - integer offset for start pgcopy compressed data
- pgcopy - PGCopyReader object
- to_rows() - Method for reading uncompressed PGCopy data as generator python objects
- to_pandas() - Method for reading uncompressed PGCopy data as pandas.DataFrame
- to_polars() - Method for reading uncompressed PGCopy data as polars.DataFrame
- to_bytes() - Method for reading uncompressed PGCopy data as generator bytes

## Class PGPackWriter

Initialization parameters

- fileobj - BufferedWriter object (file, BytesIO e t.c)
- metadata - metadata in bytes (default is None)
- compression_method - CompressionMethod object (default is CompressionMethod.ZSTD)

Methods and attributes

- columns - List columns names
- pgtypes - List PGOid for all columns
- pgparam - List PGParam for all columns
- pgcopy_compressed_length - integer packed pgcopy data length set to 0 as initialized
- pgcopy_data_length - integer unpacked pgcopy data length set to -1 as initialized
- pgcopy_start - integer offset for start pgcopy compressed data set to current offset as initialized
- pgcopy - PGCopyWriter object
- from_rows(dtype_data) - Write PGPack file from python objects. Parameter: dtype_data as python iterable object
- from_pandas(data_frame) - Write PGPack file from pandas.DataFrame. Parameter: data_frame as pandas.DataFrame
- from_polars(data_frame) - Write PGPack file from polars.DataFrame. Parameter: data_frame as polars.DataFrame
- from_bytes(bytes_data) - Write PGPack file from bytes. Parameter: bytes_data as bytes iterable object

## Errors

- PGPackError - Base PGPack error
- PGPackHeaderError - Error header signature
- PGPackMetadataCrcError - Error metadata crc32
- PGPackModeError - Error fileobject mode
