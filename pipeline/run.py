"""
Main pipeline entry point.
Run: python -m pipeline.run
"""

from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

from pipeline.sources import dole, kalibrr, jsearch
from pipeline.cleaner import clean
from pipeline.writer import write, load_latest
from pipeline import insights


def run() -> None:
    print("=" * 50)
    print("HireMap PH — Data Pipeline")
    print("=" * 50)

    raw: list[dict] = []

    print("\n[Step 1/4] Fetching from DOLE Phil-JobNet...")
    raw += dole.fetch(max_pages=5)

    print("\n[Step 2/4] Fetching from Kalibrr...")
    raw += kalibrr.fetch(max_pages=5)

    print("\n[Step 3/4] Fetching from JSearch API...")
    raw += jsearch.fetch(num_pages=1)

    print(f"\n[Step 4/4] Cleaning and writing {len(raw)} raw jobs...")
    cleaned = clean(raw)

    if not cleaned:
        print("[Pipeline] No clean jobs produced — aborting write")
        sys.exit(1)

    write(cleaned)

    print("\n[Step 5/5] Generating AI market insights...")
    df = load_latest()
    insights.generate(df)

    print("\n" + "=" * 50)
    print(f"Pipeline complete. {len(cleaned)} jobs processed.")
    print("=" * 50)


if __name__ == "__main__":
    run()
