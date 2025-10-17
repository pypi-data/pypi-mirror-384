"""Utilities for translating SQLAlchemy column metadata into Polars dtypes."""

from __future__ import annotations

import polars as pl
from sqlalchemy.sql.schema import Column
from sqlalchemy.sql.sqltypes import (
    BigInteger,
    Boolean,
    Date,
    DateTime,
    DECIMAL,
    Float,
    Integer,
    Numeric,
    REAL,
    SmallInteger,
    String,
    Text,
    Time,
    Unicode,
    UnicodeText,
)

__all__ = ["sa_column_to_polars_dtype"]


def sa_column_to_polars_dtype(col: Column) -> pl.datatypes.DataType:
    """Best-effort mapping from a SQLAlchemy column type to a Polars dtype."""
    tpe = col.type

    # Integer types map to a nullable 64-bit integer column
    if isinstance(tpe, (Integer, BigInteger, SmallInteger)):
        return pl.Int64

    # Text-oriented types use Polars' string representation
    if isinstance(tpe, (String, Text, Unicode, UnicodeText)):
        return pl.Utf8

    # Floating point types
    if isinstance(tpe, (Float, REAL)):
        return pl.Float64

    # Numeric / Decimal: use Polars Decimal iff precision/scale present
    if isinstance(tpe, (Numeric, DECIMAL)):
        precision = getattr(tpe, "precision", None)
        scale = getattr(tpe, "scale", None)
        if precision is not None and scale is not None:
            return pl.Decimal(precision=precision, scale=scale)
        return pl.Float64

    # Temporal types
    if isinstance(tpe, Date):
        return pl.Date
    if isinstance(tpe, DateTime):
        return pl.Datetime("us")
    if isinstance(tpe, Time):
        return pl.Time

    # Boolean
    if isinstance(tpe, Boolean):
        return pl.Boolean

    # Fail fast on unknown types so mappings remain explicit
    msg = f"Unsupported SQLAlchemy type for Polars conversion: {type(tpe).__name__}"
    raise ValueError(msg)
