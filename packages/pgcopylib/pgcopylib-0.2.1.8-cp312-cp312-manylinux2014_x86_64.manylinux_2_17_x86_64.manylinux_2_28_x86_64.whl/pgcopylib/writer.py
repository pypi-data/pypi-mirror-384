from io import (
    BytesIO,
    BufferedWriter,
)
from typing import (
    Any,
    Generator,
    TYPE_CHECKING,
)

from .common import (
    ArrayOidToOid,
    PGOid,
    PGCopyRecordError,
    PGOidToDType,
)
from .common.base import (
    make_rows,
    nullable_writer,
    writer,
)

if TYPE_CHECKING:
    from types import FunctionType
    from .common.dtypes import PostgreSQLDtype


class PGCopyWriter:
    """PGCopy dump writer."""

    def __init__(
        self,
        file: BufferedWriter | None,
        pgtypes: list[PGOid],
    ) -> None:
        """Class initialization."""

        if not pgtypes:
            raise PGCopyRecordError("PGOids not defined!")

        self.file = file
        self.pgtypes = pgtypes
        self.num_columns = len(pgtypes)
        self.num_rows = 0
        self.pos = 0
        self.postgres_dtype: list[PostgreSQLDtype] = [
            PGOidToDType[pgtype]
            for pgtype in pgtypes
        ]
        self.pgoid_functions: list[FunctionType] = [
            PGOidToDType[ArrayOidToOid[self.pgtypes[column]]].write
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

    def write_row(self, dtype_values: Any) -> Generator[Any, None, None]:
        """Write single row."""

        for postgres_dtype, dtype_value, pgoid_function, pgoid in zip(
            self.postgres_dtype,
            dtype_values,
            self.pgoid_functions,
            self.pgoid,
        ):
            yield nullable_writer(
                postgres_dtype.write,
                dtype_value,
                pgoid_function,
                self.buffer_object,
                pgoid,
            )
        self.num_rows += 1

    def from_rows(self, dtype_values: list[Any]) -> Generator[
        bytes,
        None,
        None,
    ]:
        """Write all rows."""

        return make_rows(self.write_row, dtype_values, self.num_columns)

    def write(self, dtype_values: list[Any]) -> None:
        """Write all rows into file."""

        if self.file is None:
            raise PGCopyRecordError("File not defined!")

        self.pos = writer(
            self.file,
            self.write_row,
            dtype_values,
            self.num_columns,
        )

    def tell(self) -> int:
        """Return current position."""

        return self.pos

    def close(self) -> None:
        """Close file object."""

        if self.file:
            self.file.close()

    def __repr__(self) -> str:
        """PGCopy info in interpreter."""

        return self.__str__()

    def __str__(self) -> str:
        """PGCopy info."""

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
            "<PGCopy dump writer>",
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
