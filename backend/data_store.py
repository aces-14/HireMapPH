"""
In-memory Parquet cache.

Loads latest.parquet and master.parquet once at startup.
Reloads automatically if the file has been modified (e.g. after a pipeline run).

Why in-memory: Parquet reads are fast but not instant. For a dashboard with
multiple concurrent API calls per page load, re-reading from disk on every
request would be slow. One read at startup, then serve from memory.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).parent.parent / "data"

_latest_df: pd.DataFrame = pd.DataFrame()
_master_df: pd.DataFrame = pd.DataFrame()
_latest_mtime: float = 0.0
_master_mtime: float = 0.0


def _deserialize(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "skills" in df.columns:
        df["skills"] = df["skills"].apply(
            lambda x: json.loads(x) if isinstance(x, str) else []
        )
    if "apply_urls" in df.columns:
        df["apply_urls"] = df["apply_urls"].apply(
            lambda x: json.loads(x) if isinstance(x, str) else []
        )
    return df


def _reload_if_stale(path: Path, cached_df: pd.DataFrame, cached_mtime: float):
    if not path.exists():
        return cached_df, cached_mtime
    mtime = path.stat().st_mtime
    if mtime > cached_mtime:
        df = _deserialize(pd.read_parquet(path, engine="pyarrow"))
        return df, mtime
    return cached_df, cached_mtime


def get_latest() -> pd.DataFrame:
    global _latest_df, _latest_mtime
    _latest_df, _latest_mtime = _reload_if_stale(
        DATA_DIR / "latest.parquet", _latest_df, _latest_mtime
    )
    return _latest_df


def get_master() -> pd.DataFrame:
    global _master_df, _master_mtime
    _master_df, _master_mtime = _reload_if_stale(
        DATA_DIR / "master.parquet", _master_df, _master_mtime
    )
    return _master_df


def get_insights() -> dict:
    path = DATA_DIR / "insights.json"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def last_updated() -> str | None:
    path = DATA_DIR / "latest.parquet"
    if not path.exists():
        return None
    mtime = path.stat().st_mtime
    from datetime import datetime, timezone
    return datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat()
