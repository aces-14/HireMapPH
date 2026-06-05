"""
DOLE Phil-JobNet scraper.
URL: https://www.phil-jobnet.dol.gov.ph
Government site — no auth, no rate limiting, stable HTML.
"""

import hashlib
from datetime import date
from typing import Any

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.phil-jobnet.dol.gov.ph"
SEARCH_URL = f"{BASE_URL}/jobpost/searchjobpost"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def _make_id(title: str, company: str, url: str = "") -> str:
    # Use job URL if available — it's stable across runs.
    # Avoid including the date (scraped as "2 days ago" etc) which changes daily.
    raw = f"dole|url|{url}" if url else f"dole|{title}|{company}"
    return hashlib.md5(raw.encode()).hexdigest()


def fetch(max_pages: int = 5) -> list[dict[str, Any]]:
    """Scrape DOLE Phil-JobNet and return raw job dicts."""
    jobs: list[dict[str, Any]] = []
    session = requests.Session()
    session.headers.update(HEADERS)

    for page in range(1, max_pages + 1):
        try:
            resp = session.get(
                SEARCH_URL,
                params={"page": page},
                timeout=15,
            )
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"[DOLE] Page {page} failed: {e}")
            break

        soup = BeautifulSoup(resp.text, "lxml")
        cards = soup.select(".job-listing, .job-post, article.job")

        if not cards:
            print(f"[DOLE] No cards found on page {page} — stopping")
            break

        for card in cards:
            title = (card.select_one(".job-title, h3, h2") or {}).get_text(strip=True)
            company = (card.select_one(".company-name, .employer") or {}).get_text(strip=True)
            location = (card.select_one(".location, .job-location") or {}).get_text(strip=True)
            description = (card.select_one(".description, .job-description, p") or {}).get_text(strip=True)
            posted = (card.select_one(".date-posted, time") or {}).get_text(strip=True)
            link_tag = card.select_one("a[href]")
            url = BASE_URL + link_tag["href"] if link_tag else ""

            if not title:
                continue

            jobs.append({
                "job_id": _make_id(title, company, url),
                "title": title,
                "company": company,
                "location_raw": location,
                "description": description,
                "date_posted_raw": posted,
                "apply_url": url,
                "source": "dole",
            })

        print(f"[DOLE] Page {page}: {len(cards)} listings")

    print(f"[DOLE] Total fetched: {len(jobs)}")
    return jobs
