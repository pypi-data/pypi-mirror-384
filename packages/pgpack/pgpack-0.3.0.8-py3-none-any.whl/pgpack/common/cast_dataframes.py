from datetime import date
from types import NoneType

from pgcopylib.common.dtypes.dtype import PostgreSQLDtype


PANDAS_TYPE: dict[type, str] = {
    NoneType: "nan",
    bool: "?",
    date: "datetime64[ns]",
    float: "float64",
    int: "int64",
    str: "string",
}


def pandas_astype(
    columns: list[str],
    postgres_dtype: list[PostgreSQLDtype],
) -> dict[str, str]:
    """Make pandas dtypes from columns."""

    astype: dict[str, str] = {}

    for column, pgtype in zip(columns, postgres_dtype):
        astype[column] = PANDAS_TYPE.get(pgtype.pytype)

    return astype
