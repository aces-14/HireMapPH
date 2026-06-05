"""
Parquet writer with cross-day deduplication.

Strategy: master.parquet is the full historical record.
Each run upserts today's jobs — updating last_seen for known jobs,
adding first_seen/last_seen for new ones.

latest.parquet  = jobs seen within the last ACTIVE_WINDOW_DAYS (active listings)
master.parquet  = all jobs ever seen with first_seen + last_seen dates (trends)

Why this matters: JSearch and Kalibrr return currently active listings regardless
of post date. Without cross-day tracking, the same job appears in every daily
snapshot, making trend analysis (e.g. "demand up 40% this month") meaningless.
first_seen is the signal — it marks when a new job actually entered the market.
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

DATA_DIR = Path(__file__).parent.parent / "data"
ACTIVE_WINDOW_DAYS = 30


def _serialize(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare DataFrame for Parquet — lists to JSON strings, types enforced."""
    df = df.copy()
    df["skills"] = df["skills"].apply(
        lambda x: json.dumps(x) if isinstance(x, list) else (x if isinstance(x, str) else "[]")
    )
    if "apply_urls" in df.columns:
        df["apply_urls"] = df["apply_urls"].apply(
            lambda x: json.dumps(x) if isinstance(x, list) else (x if isinstance(x, str) else "[]")
        )
    df["salary_min"] = pd.to_numeric(df["salary_min"], errors="coerce").astype("Int64")
    df["salary_max"] = pd.to_numeric(df["salary_max"], errors="coerce").astype("Int64")
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lng"] = pd.to_numeric(df["lng"], errors="coerce")
    df["remote"] = df["remote"].fillna(False).astype(bool)
    return df


def _deserialize(df: pd.DataFrame) -> pd.DataFrame:
    """Restore list columns after reading from Parquet."""
    df = df.copy()
    df["skills"] = df["skills"].apply(
        lambda x: json.loads(x) if isinstance(x, str) else []
    )
    if "apply_urls" in df.columns:
        df["apply_urls"] = df["apply_urls"].apply(
            lambda x: json.loads(x) if isinstance(x, str) else []
        )
    return df


def _load_master() -> pd.DataFrame:
    path = DATA_DIR / "master.parquet"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_parquet(path, engine="pyarrow")


def write(jobs: list[dict[str, Any]]) -> Path:
    """
    Upsert today's jobs into master.parquet.
    Returns the path to master.parquet.
    """
    DATA_DIR.mkdir(exist_ok=True)
    today = date.today()
    today_str = today.isoformat()

    today_df = pd.DataFrame(jobs)
    today_df["date_posted"] = pd.to_datetime(
        today_df["date_posted"], errors="coerce"
    ).dt.date

    master = _load_master()
    new_count = 0
    updated_count = 0

    if master.empty:
        # First ever run — everything is new
        today_df["first_seen"] = today_str
        today_df["last_seen"] = today_str
        master = today_df
        new_count = len(master)
    else:
        existing_ids = set(master["job_id"])
        today_ids = set(today_df["job_id"])

        # Update last_seen for jobs we've seen before
        mask = master["job_id"].isin(today_ids)
        master.loc[mask, "last_seen"] = today_str
        updated_count = mask.sum()

        # Add genuinely new jobs
        new_ids = today_ids - existing_ids
        if new_ids:
            new_rows = today_df[today_df["job_id"].isin(new_ids)].copy()
            new_rows["first_seen"] = today_str
            new_rows["last_seen"] = today_str
            master = pd.concat([master, new_rows], ignore_index=True)
            new_count = len(new_rows)

    # Write master (full history)
    master_path = DATA_DIR / "master.parquet"
    _serialize(master).to_parquet(master_path, index=False, engine="pyarrow")

    # Write latest (active listings only — seen within the window)
    cutoff = (today - timedelta(days=ACTIVE_WINDOW_DAYS)).isoformat()
    active = master[master["last_seen"] >= cutoff].copy()
    latest_path = DATA_DIR / "latest.parquet"
    _serialize(active).to_parquet(latest_path, index=False, engine="pyarrow")

    print(f"[Writer] New jobs today: {new_count} | Updated last_seen: {updated_count}")
    print(f"[Writer] Master: {len(master)} total | Latest (active): {len(active)} jobs")
    print(f"[Writer] Written -> master.parquet, latest.parquet")
    return master_path


def load_latest() -> pd.DataFrame:
    """Load active job listings. Returns empty DataFrame if none exists."""
    path = DATA_DIR / "latest.parquet"
    if not path.exists():
        files = sorted(DATA_DIR.glob("master.parquet"), reverse=True)
        if not files:
            return pd.DataFrame()
        path = files[0]
    return _deserialize(pd.read_parquet(path, engine="pyarrow"))


def load_master() -> pd.DataFrame:
    """Load full job history for trend analysis."""
    path = DATA_DIR / "master.parquet"
    if not path.exists():
        return pd.DataFrame()
    return _deserialize(pd.read_parquet(path, engine="pyarrow"))
