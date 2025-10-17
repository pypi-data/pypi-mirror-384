"""TimescaleDB-related metadata helpers."""

from __future__ import annotations

from typing import Any

from sqlalchemy.ext.declarative import DeclarativeMeta


def get_timescale_compress_after(model_cls: type[DeclarativeMeta]) -> str | None:
    """Return the Timescale compression window (compress_after) configured for a table."""
    if not hasattr(model_cls, "__table__"):
        raise TypeError("model_cls must be a SQLAlchemy declarative model with a __table__ attribute")

    table = model_cls.__table__
    info: dict[str, Any] = getattr(table, "info", {})
    timescale_cfg: dict[str, Any] = info.get("timescale", {})
    compression: dict[str, Any] | None = timescale_cfg.get("compression")
    if not compression:
        return None
    return compression.get("compress_after")

