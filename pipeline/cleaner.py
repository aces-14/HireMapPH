"""
Data cleaner and normalizer.
Takes raw job dicts from any source and outputs the unified schema.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Any, Optional

from pipeline.geocoder import geocode

KNOWN_SKILLS: list[str] = [
    # Languages
    "python", "javascript", "typescript", "java", "php", "c#", "c++", "golang",
    "ruby", "swift", "kotlin", "r", "matlab", "scala", "rust",
    # Web
    "react", "vue", "angular", "nextjs", "html", "css", "tailwind", "bootstrap",
    "nodejs", "express", "django", "flask", "fastapi", "laravel", "spring",
    # Data
    "sql", "mysql", "postgresql", "mongodb", "redis", "elasticsearch",
    "pandas", "numpy", "spark", "hadoop", "tableau", "power bi", "excel",
    # Cloud / Infra
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "linux",
    "git", "ci/cd", "jenkins", "github actions",
    # AI / ML
    "machine learning", "deep learning", "tensorflow", "pytorch", "scikit-learn",
    "nlp", "llm", "computer vision", "data science",
    # Other
    "sap", "salesforce", "jira", "agile", "scrum",
]

EXPERIENCE_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\bentry[\s-]?level\b|\bfresh\s*grad\b|\bjunior\b|\bjr\.?\b", re.I), "entry"),
    (re.compile(r"\bmid[\s-]?level\b|\bintermediate\b|\b[2-5]\s*years?\b", re.I), "mid"),
    (re.compile(r"\bsenior\b|\bsr\.?\b|\blead\b|\bmanager\b|\b[5-9]\+?\s*years?\b|\b10\+", re.I), "senior"),
]

REMOTE_PATTERNS = re.compile(
    r"\bremote\b|\bwork[\s-]?from[\s-]?home\b|\bwfh\b|\bhybrid\b", re.I
)

SALARY_PATTERNS = [
    # ₱30,000 – ₱55,000 or PHP 30000-55000
    re.compile(
        r"(?:₱|php|peso)\s*([\d,]+)\s*(?:–|-|to)\s*(?:₱|php|peso)?\s*([\d,]+)",
        re.I,
    ),
    # 30,000 - 55,000
    re.compile(r"([\d,]{5,})\s*(?:–|-|to)\s*([\d,]{5,})"),
]


def _clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _parse_salary(raw_min, raw_max, description: str) -> tuple[Optional[int], Optional[int]]:
    # Use explicit values if provided by the API
    if raw_min is not None and raw_max is not None:
        try:
            return int(float(raw_min)), int(float(raw_max))
        except (ValueError, TypeError):
            pass

    # Try extracting from description text
    for pattern in SALARY_PATTERNS:
        match = pattern.search(description)
        if match:
            try:
                low = int(match.group(1).replace(",", ""))
                high = int(match.group(2).replace(",", ""))
                # Sanity check: monthly PH salary range (₱5k–₱500k)
                if 5_000 <= low <= 500_000 and 5_000 <= high <= 500_000:
                    return low, high
            except (ValueError, IndexError):
                continue

    return None, None


def _parse_date(raw: str) -> Optional[date]:
    if not raw:
        return None
    # Try each format against the full string, not a slice
    # (len(fmt) is wrong — "%Y-%m-%d" is 8 chars but represents 10)
    for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(raw.strip(), fmt).date()
        except (ValueError, TypeError):
            continue
    # Fallback: try just the first 10 chars (handles ISO datetime strings)
    try:
        return datetime.strptime(raw[:10], "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def _extract_skills(description: str) -> list[str]:
    desc_lower = description.lower()
    return [skill for skill in KNOWN_SKILLS if re.search(rf"\b{re.escape(skill)}\b", desc_lower)]


def _detect_experience(title: str, description: str) -> Optional[str]:
    text = f"{title} {description}"
    for pattern, level in EXPERIENCE_PATTERNS:
        if pattern.search(text):
            return level
    return None


def _detect_remote(title: str, location_raw: str, description: str) -> bool:
    return bool(REMOTE_PATTERNS.search(f"{title} {location_raw} {description}"))


def normalize(raw: dict[str, Any]) -> dict[str, Any]:
    """Convert a raw job dict (any source) to the unified schema."""
    title = _clean_text(raw.get("title", ""))
    company = _clean_text(raw.get("company", ""))
    location_raw = _clean_text(raw.get("location_raw", ""))
    description = _clean_text(raw.get("description", ""))
    date_posted_raw = raw.get("date_posted_raw", "")

    geo = geocode(location_raw)
    salary_min, salary_max = _parse_salary(
        raw.get("salary_min_raw"),
        raw.get("salary_max_raw"),
        description,
    )

    return {
        "job_id": raw.get("job_id", ""),
        "title": title,
        "company": company,
        "location_raw": location_raw,
        "city": geo["city"],
        "region": geo["region"],
        "lat": geo["lat"],
        "lng": geo["lng"],
        "remote": raw.get("remote") or _detect_remote(title, location_raw, description),
        "salary_min": salary_min,
        "salary_max": salary_max,
        "experience_level": _detect_experience(title, description),
        "skills": _extract_skills(description),
        "description": description,
        "date_posted": _parse_date(date_posted_raw),
        "source": raw.get("source", "unknown"),
        "apply_url": raw.get("apply_url", ""),
    }


# Lower index = higher priority. When the same job appears on multiple boards,
# we keep the version from the highest-priority source (most metadata).
_SOURCE_PRIORITY: dict[str, int] = {"jsearch": 0, "dole": 1, "kalibrr": 2}


def clean(raw_jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalize a list of raw jobs, drop invalid ones, deduplicate by job_id,
    then cross-source deduplicate by (title, company) keeping the best-sourced version."""
    seen_ids: set[str] = set()
    candidates: list[dict[str, Any]] = []

    for raw in raw_jobs:
        try:
            job = normalize(raw)
        except Exception as e:
            print(f"[Cleaner] Skipping job due to error: {e}")
            continue

        if not job["title"] or not job["company"]:
            continue
        if job["job_id"] in seen_ids:
            continue
        seen_ids.add(job["job_id"])
        candidates.append(job)

    # Sort so higher-priority sources come first.
    # Same job on Kalibrr AND JSearch → keep JSearch as the primary record (more metadata).
    candidates.sort(key=lambda j: _SOURCE_PRIORITY.get(j["source"], 99))

    tc_to_idx: dict[tuple, int] = {}   # (title, company) → index in cleaned
    cleaned: list[dict[str, Any]] = []
    merged = 0

    for job in candidates:
        key = (job["title"].lower().strip(), job["company"].lower().strip())

        if key not in tc_to_idx:
            # First occurrence — seed apply_urls with this job's own link
            job["apply_urls"] = (
                [{"url": job["apply_url"], "source": job["source"]}]
                if job.get("apply_url") else []
            )
            tc_to_idx[key] = len(cleaned)
            cleaned.append(job)
        else:
            # Duplicate from a different source — merge its apply link in
            url = job.get("apply_url", "")
            if url:
                existing = cleaned[tc_to_idx[key]]
                existing_urls = [u["url"] for u in existing["apply_urls"]]
                if url not in existing_urls:
                    existing["apply_urls"].append({"url": url, "source": job["source"]})
            merged += 1

    if merged:
        print(f"[Cleaner] Merged {merged} cross-source duplicates (links combined on one card)")
    print(f"[Cleaner] {len(cleaned)} clean jobs from {len(raw_jobs)} raw")
    return cleaned
