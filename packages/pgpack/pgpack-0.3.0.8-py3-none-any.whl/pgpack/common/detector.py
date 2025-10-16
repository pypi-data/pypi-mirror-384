from datetime import (
    date,
    datetime,
    time,
)
from dateutil.relativedelta import relativedelta
from decimal import Decimal
from ipaddress import (
    IPv4Address,
    IPv4Network,
    IPv6Address,
    IPv6Network,
)
from typing import Any
from types import NoneType
from uuid import UUID

from pandas import Timestamp
from numpy import (
    float64,
    int64,
    str_,
)


AssociatePyType: dict[Any, tuple[int, ...]] = {
    Decimal: (1700, 1231, -1, 0),
    IPv4Address: (869, 1041, -1, 0),
    IPv4Network: (650, 651, -1, 0),
    IPv6Address: (869, 1041, -1, 0),
    IPv6Network: (650, 651, -1, 0),
    Timestamp: (1114, 1115, 8, 0),
    UUID: (2950, 2951, 16, 0),
    bool: (16, 1000, 1, 0),
    bytes: (17, 1001, -1, 0),
    date: (1082, 1182, 4, 0),
    datetime: (1114, 1115, 8, 0),
    dict: (114, 199, -1, 0),
    float64: (701, 1022, 8, 0),
    float: (701, 1022, 8, 0),
    int64: (20, 1016, 8, 0),
    int: (20, 1016, 8, 0),
    relativedelta: (1186, 1187, -1, 0),
    str: (25, 1009, -1, 0),
    str_: (25, 1009, -1, 0),
    time: (1083, 1183, 8, 0),
}


def detect_oid(
    data_values: Any,
    is_array: bool = False,
    nested: int = 0,
) -> tuple[int, ...]:
    """Associate python type with postgres type."""

    for value in data_values:
        if isinstance(value, list | tuple):
            pg_type = detect_oid(value, True, nested + 1)
            if pg_type:
                return pg_type
            continue
        if not isinstance(value, NoneType):
            pg_oid: tuple[int] = AssociatePyType[value.__class__]
            if is_array:
                return pg_oid[1], *pg_oid[2:], nested
            return pg_oid[0], *pg_oid[2:], nested
