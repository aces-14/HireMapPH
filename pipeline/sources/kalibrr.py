"""
Kalibrr scraper.
URL: https://www.kalibrr.com/job-board/te/philippines/p/{page}
Philippine-native job board. Server-rendered HTML — no JS wall.
"""

from __future__ import annotations

import hashlib
import re
import time
from datetime import date
from typing import Any

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.kalibrr.com"
LISTING_URL = BASE_URL + "/job-board/te/philippines/p/{page}"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

# Job link pattern: /c/{company-slug}/jobs/{id}/{job-slug}
JOB_LINK_RE = re.compile(r"/c/[^/]+/jobs/\d+/")


def _make_id(title: str, company: str) -> str:
    raw = f"kalibrr|{title}|{company}"
    return hashlib.md5(raw.encode()).hexdigest()


def _parse_card(h2_tag) -> dict[str, Any] | None:
    """Extract a job dict from the card rooted at h2.parent.parent.parent."""
    title = h2_tag.get_text(strip=True)
    if not title:
        return None

    card_root = h2_tag.parent.parent.parent

    # Company name is in a <span class="k-inline-flex ...">
    company_el = card_root.select_one("span.k-inline-flex")
    company = company_el.get_text(strip=True) if company_el else ""

    # Direct job URL: anchor whose href matches /c/{slug}/jobs/{id}/
    job_url = ""
    for a in card_root.find_all("a", href=True):
        if JOB_LINK_RE.search(a["href"]):
            job_url = BASE_URL + a["href"]
            break

    # All span texts for metadata (deduplicated, preserving order)
    seen: set[str] = set()
    meta: list[str] = []
    for span in card_root.select("span, p"):
        txt = span.get_text(strip=True)
        if txt and txt not in seen and txt != company:
            seen.add(txt)
            meta.append(txt)

    # Location: first span containing "Philippines" or a city name
    location_raw = ""
    for m in meta:
        if "Philippines" in m or re.search(r"\b(Manila|Cebu|Davao|Makati|BGC|Quezon|Pasig|Taguig)\b", m, re.I):
            location_raw = m.replace(", Philippines", "").strip()
            break

    # Experience level
    exp_raw = ""
    for m in meta:
        if re.search(r"level|senior|junior|associate|supervisor|manager|intern|executive", m, re.I):
            exp_raw = m
            break

    return {
        "job_id": _make_id(title, company),
        "title": title,
        "company": company,
        "location_raw": location_raw,
        "description": "",
        "date_posted_raw": date.today().isoformat(),
        "salary_min_raw": None,
        "salary_max_raw": None,
        "remote": bool(re.search(r"\bremote\b|\bwfh\b|\bwork.from.home\b", " ".join(meta), re.I)),
        "apply_url": job_url,
        "source": "kalibrr",
        "_experience_raw": exp_raw,
    }


def fetch(max_pages: int = 5) -> list[dict[str, Any]]:
    """Scrape Kalibrr PH job listings. Returns raw job dicts."""
    jobs: list[dict[str, Any]] = []
    session = requests.Session()
    session.headers.update(HEADERS)

    for page in range(1, max_pages + 1):
        url = LISTING_URL.format(page=page)
        try:
            resp = session.get(url, timeout=15)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"[Kalibrr] Page {page} failed: {e}")
            break

        soup = BeautifulSoup(resp.text, "lxml")
        headings = soup.find_all("h2")

        if not headings:
            print(f"[Kalibrr] No job headings on page {page} — stopping")
            break

        page_count = 0
        for h2 in headings:
            job = _parse_card(h2)
            if job:
                jobs.append(job)
                page_count += 1

        print(f"[Kalibrr] Page {page}: {page_count} listings")

        # Polite delay between pages
        if page < max_pages:
            time.sleep(1)

    print(f"[Kalibrr] Total fetched: {len(jobs)}")
    return jobs
