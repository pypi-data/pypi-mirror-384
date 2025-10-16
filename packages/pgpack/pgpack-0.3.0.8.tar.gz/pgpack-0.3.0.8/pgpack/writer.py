from io import (
    BufferedReader,
    BufferedWriter,
)
from struct import pack
from typing import (
    Any,
    Iterable,
)
from zlib import (
    crc32,
    compress,
)

from light_compressor import (
    CompressionMethod,
    LZ4Compressor,
    ZSTDCompressor,
)
from pandas import DataFrame as PdFrame
from polars import DataFrame as PlFrame
from pgcopylib import (
    PGCopyWriter,
    PGOid,
)

from .common import (
    HEADER,
    metadata_from_frame,
    metadata_reader,
    PGPackMetadataCrcError,
    PGPackModeError,
    PGParam,
)


NAN2NONE = {float("nan"): None}


class PGPackWriter:
    """Class for write PGPack format."""

    fileobj: BufferedReader
    metadata: bytes | None
    columns: list[str]
    pgtypes: list[PGOid]
    pgparam: list[PGParam]
    pgcopy_compressed_length: int
    pgcopy_data_length: int
    compression_method: CompressionMethod
    pgcopy_start: int
    pgcopy: PGCopyWriter | None
    _str: str | None

    def __init__(
        self,
        fileobj: BufferedWriter,
        metadata: bytes | None = None,
        compression_method: CompressionMethod = CompressionMethod.ZSTD,
    ) -> None:
        """Class initialization."""

        self.fileobj = fileobj
        self.metadata = metadata
        self.columns = []
        self.pgtypes = []
        self.pgparam = []
        self.pgcopy_compressed_length = 0
        self.pgcopy_data_length = -1
        self.compression_method = compression_method
        self.pgcopy_start = self.fileobj.tell()
        self.pgcopy = None
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

    def __init_copy(self) -> None:
        """Initialize pgcopy from self.metadata."""

        (
            self.columns,
            self.pgtypes,
            self.pgparam,
        ) = metadata_reader(self.metadata)
        self.pgcopy = PGCopyWriter(None, self.pgtypes)

    def from_rows(
        self,
        dtype_values: Iterable[Any],
    ) -> str:
        """Convert python rows to pgpack format."""

        if not self.metadata:
            raise PGPackMetadataCrcError("Metadata error.")

        if not self.pgcopy:
            self.__init_copy()

        return self.from_bytes(self.pgcopy.from_rows(dtype_values))

    def from_pandas(
        self,
        data_frame: PdFrame,
    ) -> str:
        """Convert pandas.DataFrame to pgpack format."""

        if not self.metadata:
            self.metadata = metadata_from_frame(data_frame)

        return self.from_rows(iter(data_frame.values))

    def from_polars(
        self,
        data_frame: PlFrame,
    ) -> str:
        """Convert polars.DataFrame to pgpack format."""

        if not self.metadata:
            self.metadata = metadata_from_frame(data_frame)

        return self.from_rows(data_frame.iter_rows())

    def from_bytes(
        self,
        bytes_data: Iterable[bytes],
    ) -> str:
        """Convert pgcopy bytes to pgpack format."""

        if self.compression_method is CompressionMethod.NONE:
            compressor = None
        elif self.compression_method is CompressionMethod.LZ4:
            compressor = LZ4Compressor()
        elif self.compression_method is CompressionMethod.ZSTD:
            compressor = ZSTDCompressor()
        else:
            raise ValueError(
                f"Unsupported compression method {self.compression_method}"
            )

        if not self.fileobj:
            raise ValueError("Fileobject not define.")
        if not self.fileobj.writable():
            raise PGPackModeError("Fileobject don't support write.")
        if not self.metadata:
            raise PGPackMetadataCrcError("Metadata error.")

        if not self.pgcopy:
            self.__init_copy()

        metadata_zlib = compress(self.metadata)
        metadata_crc = pack("!L", crc32(metadata_zlib))
        metadata_length = pack("!L", len(metadata_zlib))
        compression_method = pack("!B", self.compression_method.value)

        for data in (
            HEADER,
            metadata_crc,
            metadata_length,
            metadata_zlib,
            compression_method,
            bytes(16),
        ):
            self.pgcopy_start += self.fileobj.write(data)

        if compressor:
            bytes_data = compressor.send_chunks(bytes_data)

        for data in bytes_data:
            self.fileobj.write(data)

        self.pgcopy_compressed_length = self.fileobj.tell() - self.pgcopy_start

        if compressor:
            self.pgcopy_data_length = compressor.decompressed_size
        else:
            self.pgcopy_data_length = self.pgcopy_compressed_length

        self.fileobj.seek(self.pgcopy_start - 16)
        self.fileobj.write(pack(
            "!2Q",
            self.pgcopy_compressed_length,
            self.pgcopy_data_length,
        ))
        self.fileobj.flush()
        self._str = None
        return self.__str__()

    def tell(self) -> int:
        """Return current position."""

        if self.pgcopy:
            return self.pgcopy.tell()

        return self.fileobj.tell()

    def close(self) -> None:
        """Close file object."""

        self.pgcopy.close()
        self.fileobj.close()
