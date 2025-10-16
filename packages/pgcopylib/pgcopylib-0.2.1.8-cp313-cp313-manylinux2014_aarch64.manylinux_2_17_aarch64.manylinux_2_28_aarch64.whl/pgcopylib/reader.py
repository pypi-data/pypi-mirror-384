from io import (
    BufferedReader,
    BytesIO,
)
from typing import (
    Any,
    Generator,
    TYPE_CHECKING,
)
from struct import unpack

from .common import (
    ArrayOidToOid,
    PGOid,
    PGOidToDType,
    PGCopySignatureError,
)
from .common.base import (
    read_num_columns,
    read_record,
    skip_all,
)
from .common.dtypes import PostgreSQLDtype

if TYPE_CHECKING:
    from types import FunctionType


class PGCopyReader:
    """PGCopy dump reader."""

    def __init__(
        self,
        file: BufferedReader,
        pgtypes: list[PGOid] = [],
    ) -> None:
        """Class initialization."""

        self.file = file
        self.pgtypes = pgtypes

        self.header: bytes = self.file.read(11)

        if self.header != b"PGCOPY\n\xff\r\n\x00":
            msg = "PGCopy signature not match!"
            raise PGCopySignatureError(msg)

        self.flags_area: list[int] = [
            (byte >> i) & 1
            for byte in self.file.read(4)
            for i in range(7, -1, -1)
        ]
        self.is_oid_enable: bool = bool(self.flags_area[16])
        self.header_ext_length: int = unpack("!i", self.file.read(4))[0]

        if self.is_oid_enable:
            self.column_length: int = 6
        else:
            self.column_length: int = 2

        self.num_columns: int = read_num_columns(
            self.file,
            self.column_length,
        )
        self.num_rows: int = 0
        self.postgres_dtype: list[PostgreSQLDtype] = [
            PGOidToDType[self.pgtypes[column]]
            if self.pgtypes else PostgreSQLDtype.Bytes
            for column in range(self.num_columns)
        ]
        self.pgoid_functions: list[FunctionType] = [
            PGOidToDType[ArrayOidToOid[self.pgtypes[column]]].read
            if self.pgtypes and ArrayOidToOid.get(
                self.pgtypes[column]
            ) else None
            for column in range(self.num_columns)
        ]
        self.pgoid: list[int] = [
            ArrayOidToOid[self.pgtypes[column]].value
            if self.pgtypes and ArrayOidToOid.get(
                self.pgtypes[column]
            ) else 0
            for column in range(self.num_columns)
        ]
        self.buffer_object = BytesIO()

    def __count_rows(self) -> None:
        """Count rows."""

        if not self.num_rows:
            self.num_rows = skip_all(
                self.file,
                self.column_length,
                self.num_columns,
                self.num_rows,
            )

    def read_row(self) -> Generator[Any, None, None]:
        """Read single row."""

        for postgres_dtype, pgoid_function, pgoid in zip(
            self.postgres_dtype,
            self.pgoid_functions,
            self.pgoid,
        ):
            yield read_record(
                self.file,
                postgres_dtype.read,
                pgoid_function,
                self.buffer_object,
                pgoid,
            )

    def to_rows(self) -> Generator[list[Any], None, None]:
        """Read all rows."""

        columns = self.num_columns

        while columns != 0xffff:
            yield [*self.read_row()]
            self.num_rows += 1
            columns = read_num_columns(
                self.file,
                self.column_length,
            )

    def tell(self) -> int:
        """Return current position."""

        return self.file.tell()

    def close(self) -> None:
        """Close file object."""

        self.file.close()

    def __repr__(self) -> str:
        """PGCopy info in interpreter."""

        return self.__str__()

    def __str__(self) -> str:
        """PGCopy info."""

        self.__count_rows()

        if not self.pgtypes:
            self.pgtypes = [
                PGOid.bytea
                for _ in range(self.num_columns)
            ]

        def to_col(text: str) -> str:
            """Format string element."""

            text = text[:14] + "…" if len(text) > 15 else text
            return f" {text: <15} "

        empty_line = (
            "│-----------------+-----------------│"
        )
        end_line = (
            "└─────────────────┴─────────────────┘"
        )
        _str = [
            "<PGCopy dump reader>",
            "┌─────────────────┬─────────────────┐",
            "│ Column Number   │ PostgreSQL Type │",
            "╞═════════════════╪═════════════════╡",
        ]

        for column, pgtype in zip(range(self.num_columns), self.pgtypes):
            _str.append(
                f"│{to_col(f'Column_{column}')}│{to_col(pgtype.name)}│",
            )
            _str.append(empty_line)

        _str[-1] = end_line
        return "\n".join(_str) + f"""
Total columns: {self.num_columns}
Total rows: {self.num_rows}
"""
