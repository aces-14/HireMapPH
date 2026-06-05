"""
Adzuna API integration.
Docs: https://developer.adzuna.com/docs/search
Free tier: no rate limit issues at daily scrape frequency.
Philippines country code: ph
"""

import hashlib
import os
from typing import Any

import requests

BASE_URL = "https://api.adzuna.com/v1/api/jobs/ph/search"

HEADERS = {"Content-Type": "application/json"}


def _make_id(title: str, company: str, created: str) -> str:
    raw = f"adzuna|{title}|{company}|{created}"
    return hashlib.md5(raw.encode()).hexdigest()


def fetch(max_pages: int = 5, results_per_page: int = 50) -> list[dict[str, Any]]:
    """Fetch jobs from Adzuna PH API and return raw job dicts."""
    app_id = os.getenv("ADZUNA_APP_ID")
    app_key = os.getenv("ADZUNA_APP_KEY")

    if not app_id or not app_key:
        print("[Adzuna] Missing ADZUNA_APP_ID or ADZUNA_APP_KEY — skipping")
        return []

    jobs: list[dict[str, Any]] = []

    for page in range(1, max_pages + 1):
        try:
            resp = requests.get(
                f"{BASE_URL}/{page}",
                params={
                    "app_id": app_id,
                    "app_key": app_key,
                    "results_per_page": results_per_page,
                    "content-type": "application/json",
                },
                headers=HEADERS,
                timeout=15,
            )
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"[Adzuna] Page {page} failed: {e}")
            break

        data = resp.json()
        results = data.get("results", [])

        if not results:
            print(f"[Adzuna] No results on page {page} — stopping")
            break

        for r in results:
            company = r.get("company", {}).get("display_name", "")
            location = r.get("location", {}).get("display_name", "")
            salary_min = r.get("salary_min")
            salary_max = r.get("salary_max")
            title = r.get("title", "")
            created = r.get("created", "")

            jobs.append({
                "job_id": _make_id(title, company, created),
                "title": title,
                "company": company,
                "location_raw": location,
                "description": r.get("description", ""),
                "date_posted_raw": created,
                "salary_min_raw": salary_min,
                "salary_max_raw": salary_max,
                "apply_url": r.get("redirect_url", ""),
                "source": "adzuna",
            })

        print(f"[Adzuna] Page {page}: {len(results)} listings")

    print(f"[Adzuna] Total fetched: {len(jobs)}")
    return jobs
