from collections.abc import Generator
from io import BufferedReader
from struct import unpack
from typing import (
    Any,
    Optional,
)
from zlib import (
    crc32,
    decompress,
)

from light_compressor import (
    CompressionMethod,
    define_reader,
)
from pandas import DataFrame as PdFrame
from pgcopylib import (
    PGCopyReader,
    PGOid,
)
from polars import DataFrame as PlFrame

from .common import (
    HEADER,
    metadata_reader,
    pandas_astype,
    PGPackHeaderError,
    PGPackMetadataCrcError,
    PGParam,
)


class PGPackReader:
    """Class for read PGPack format."""

    fileobj: BufferedReader
    metadata: bytes
    columns: list[str]
    pgtypes: list[PGOid]
    pgparam: list[PGParam]
    pgcopy_compressed_length: int
    pgcopy_data_length: int
    compression_method: CompressionMethod
    compression_stream: BufferedReader
    pgcopy_start: int
    pgcopy: PGCopyReader
    _str: Optional[str]

    def __init__(
        self,
        fileobj: BufferedReader,
    ) -> None:
        """Class initialization."""

        self.fileobj = fileobj

        header = self.fileobj.read(8)

        if header != HEADER:
            raise PGPackHeaderError()

        metadata_crc, metadata_length = unpack(
            "!2L",
            self.fileobj.read(8),
        )
        metadata_zlib = self.fileobj.read(metadata_length)

        if crc32(metadata_zlib) != metadata_crc:
            raise PGPackMetadataCrcError()

        self.metadata = decompress(metadata_zlib)
        (
            self.columns,
            self.pgtypes,
            self.pgparam,
        ) = metadata_reader(self.metadata)
        (
            compression_method,
            self.pgcopy_compressed_length,
            self.pgcopy_data_length,
        ) = unpack(
            "!B2Q",
            self.fileobj.read(17),
        )

        self.compression_method = CompressionMethod(compression_method)
        self.compression_stream = define_reader(
            self.fileobj,
            self.compression_method,
        )
        self.pgcopy_start = self.fileobj.tell()
        self.pgcopy = PGCopyReader(
            self.compression_stream,
            self.pgtypes,
        )
        self._str = None

    def __repr__(self) -> str:
        """String representation in interpreter."""

        return self.__str__()

    def __str__(self) -> str:
        """String representation of PGPackReader."""

        def to_col(text: str) -> str:
            """Format string element."""

            text = text[:14] + "…" if len(text) > 15 else text
            return f" {text: <15} "

        if not self._str:
            empty_line = (
                "│-----------------+-----------------│"
            )
            end_line = (
                "└─────────────────┴─────────────────┘"
            )
            _str = [
                "<PostgreSQL/GreenPlum compressed dump>",
                "┌─────────────────┬─────────────────┐",
                "│ Column Name     │ PostgreSQL Type │",
                "╞═════════════════╪═════════════════╡",
            ]

            for column, pgtype in zip(self.columns, self.pgtypes):
                _str.append(
                    f"│{to_col(column)}│{to_col(pgtype.name)}│",
                )
                _str.append(empty_line)

            _str[-1] = end_line
            self._str = "\n".join(_str) + f"""
Total columns: {len(self.columns)}
Compression method: {self.compression_method.name}
Unpacked size: {self.pgcopy_data_length} bytes
Compressed size: {self.pgcopy_compressed_length} bytes
Compression rate: {round(
    (self.pgcopy_compressed_length / self.pgcopy_data_length) * 100, 2
)} %
"""
        return self._str

    def to_rows(self) -> Generator[list[Any], None, None]:
        """Convert to python objects."""

        return self.pgcopy.to_rows()

    def to_pandas(self) -> PdFrame:
        """Convert to pandas.DataFrame."""

        return PdFrame(
            data=self.pgcopy.to_rows(),
            columns=self.columns,
        ).astype(pandas_astype(
            self.columns,
            self.pgcopy.postgres_dtype,
        ))

    def to_polars(self) -> PlFrame:
        """Convert to polars.DataFrame."""

        return PlFrame(
            data=self.pgcopy.to_rows(),
            schema=self.columns,
        )

    def to_bytes(self) -> Generator[bytes, None, None]:
        """Get raw unpacked pgcopy data."""

        if self.compression_method is CompressionMethod.NONE:
            self.fileobj.seek(self.pgcopy_start)
        else:
            self.compression_stream.seek(0)

        chunk_size = 65536
        read_size = 0

        while 1:
            chunk = self.compression_stream.read(chunk_size)
            read_size += len(chunk)

            if not chunk:
                break

            yield chunk

    def tell(self) -> int:
        """Return current position."""

        return self.pgcopy.tell()

    def close(self) -> None:
        """Close file object."""

        self.pgcopy.close()
        self.fileobj.close()
