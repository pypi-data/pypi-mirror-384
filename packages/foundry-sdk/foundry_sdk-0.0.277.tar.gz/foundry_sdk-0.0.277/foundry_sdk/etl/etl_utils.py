"""Utility helpers for ETL operations."""

from __future__ import annotations

import logging
import re
from datetime import date, datetime, timedelta

import polars as pl
from sqlalchemy import func, select
from sqlalchemy.ext.declarative import DeclarativeMeta

from foundry_sdk.db_mgmt import SQLAlchemyDatabase
from foundry_sdk.db_mgmt.utils import get_timescale_compress_after

from .constants import TimeDataStrategy


logger = logging.getLogger(__name__)


def get_time_data_strategy(strategy_str: str) -> TimeDataStrategy:
    """Convert a configuration string into the matching TimeDataStrategy."""
    if isinstance(strategy_str, TimeDataStrategy):
        return strategy_str

    if not isinstance(strategy_str, str):
        raise TypeError("time data strategy must be provided as a string")

    normalized_value = strategy_str.strip().lower()
    try:
        return TimeDataStrategy(normalized_value)
    except ValueError as exc:  # pragma: no cover - defensive message clarity
        valid = ", ".join(strategy.value for strategy in TimeDataStrategy)
        raise ValueError(
            f"Invalid time data strategy '{strategy_str}'. Expected one of: {valid}."
        ) from exc


def get_table_max_date(
    db: SQLAlchemyDatabase,
    model_cls: type[DeclarativeMeta],
    *,
    time_column: str | None = None,
):
    """Return the maximum timestamp present in the target Timescale table."""

    column_name = time_column or _get_timescale_time_column(model_cls)
    table = model_cls.__table__
    if not hasattr(table.c, column_name):
        raise ValueError(f"Time column '{column_name}' not found on table '{table.name}'.")

    time_col = getattr(table.c, column_name)
    stmt = select(func.max(time_col))

    with db.engine.begin() as conn:
        return conn.execute(stmt).scalar()


def _validate_append_mode(
    db: SQLAlchemyDatabase,
    model_cls: type[DeclarativeMeta],
    df: pl.DataFrame,
    *,
    time_column: str | None = None,
    hot_window_days: int | None = None,
) -> bool:
    """Check whether APPEND mode is safe for the incoming dataframe."""

    if df.height == 0:
        logger.debug("Append validation short-circuited due to empty dataframe for %s", model_cls.__name__)
        return True

    column_name = time_column or _get_timescale_time_column(model_cls)
    if column_name not in df.columns:
        raise ValueError(
            f"Incoming dataframe is missing required time column '{column_name}' for table '{model_cls.__name__}'."
        )

    table_max = get_table_max_date(db, model_cls, time_column=column_name)
    if table_max is None:
        return True  # empty table

    incoming_min = df.select(pl.col(column_name).min()).item()
    if incoming_min is None:
        return True

    parsed_table_max = _normalize_date_like(table_max)
    parsed_incoming_min = _normalize_date_like(incoming_min)

    window_days = hot_window_days
    if window_days is None:
        compress_after = get_timescale_compress_after(model_cls)
        window_days = _parse_compress_after_to_days(compress_after)

    if window_days is None:
        logger.warning(
            "Could not derive hot window for %s. Falling back to UPDATE mode.",
            model_cls.__name__,
        )
        return False

    hot_window = timedelta(days=window_days)
    threshold = parsed_table_max - hot_window
    return parsed_incoming_min > threshold


def _get_timescale_time_column(model_cls: type[DeclarativeMeta]) -> str:
    table = model_cls.__table__
    info = getattr(table, "info", {})
    timescale_cfg = info.get("timescale", {})
    time_column = timescale_cfg.get("time_column")
    if not time_column:
        raise ValueError(f"Timescale metadata for '{model_cls.__name__}' must define a time_column")
    return time_column


def _parse_compress_after_to_days(compress_after: str | None) -> int | None:
    if compress_after is None:
        return None
    match = re.search(r"(\d+)", str(compress_after))
    if not match:
        return None
    return int(match.group(1))


def _normalize_date_like(value: date | datetime) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    raise TypeError(f"Unsupported date-like value: {value!r}")
