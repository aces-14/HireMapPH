"""
JSearch API via RapidAPI.
Docs: https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch
Legally aggregates Indeed data. Free tier: 200 requests/month.
"""

import hashlib
import os
from typing import Any

import requests

BASE_URL = "https://jsearch.p.rapidapi.com/search"

HEADERS = {
    "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
}

PH_QUERIES = [
    "jobs in Philippines",
    "software engineer Philippines",
    "data analyst Philippines",
    "marketing Philippines",
    "accounting Philippines",
]


def _make_id(title: str, company: str, posted: str) -> str:
    raw = f"jsearch|{title}|{company}|{posted}"
    return hashlib.md5(raw.encode()).hexdigest()


def fetch(queries: list[str] | None = None, num_pages: int = 1) -> list[dict[str, Any]]:
    """Fetch jobs from JSearch API and return raw job dicts."""
    api_key = os.getenv("RAPIDAPI_KEY")

    if not api_key:
        print("[JSearch] Missing RAPIDAPI_KEY — skipping")
        return []

    headers = {**HEADERS, "X-RapidAPI-Key": api_key}
    queries = queries or PH_QUERIES
    jobs: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for query in queries:
        for page in range(1, num_pages + 1):
            try:
                resp = requests.get(
                    BASE_URL,
                    headers=headers,
                    params={
                        "query": query,
                        "page": page,
                        "num_pages": 1,
                        "country": "ph",
                    },
                    timeout=15,
                )
                resp.raise_for_status()
            except requests.RequestException as e:
                print(f"[JSearch] Query '{query}' page {page} failed: {e}")
                continue

            data = resp.json()
            results = data.get("data", [])

            for r in results:
                title = r.get("job_title", "")
                company = r.get("employer_name", "")
                posted = r.get("job_posted_at_datetime_utc", "")
                job_id = _make_id(title, company, posted)

                if job_id in seen_ids:
                    continue
                seen_ids.add(job_id)

                salary_min = r.get("job_min_salary")
                salary_max = r.get("job_max_salary")
                salary_currency = r.get("job_salary_currency", "")
                salary_period = r.get("job_salary_period", "")

                jobs.append({
                    "job_id": job_id,
                    "title": title,
                    "company": company,
                    "location_raw": " ".join(filter(None, [
                        r.get("job_city"),
                        r.get("job_state"),
                        r.get("job_country"),
                    ])),
                    "description": r.get("job_description", ""),
                    "date_posted_raw": posted,
                    "salary_min_raw": salary_min,
                    "salary_max_raw": salary_max,
                    "salary_currency": salary_currency,
                    "salary_period": salary_period,
                    "remote": r.get("job_is_remote", False),
                    "apply_url": r.get("job_apply_link", ""),
                    "source": "jsearch",
                })

            print(f"[JSearch] '{query}' page {page}: {len(results)} listings")

    print(f"[JSearch] Total fetched: {len(jobs)}")
    return jobs
