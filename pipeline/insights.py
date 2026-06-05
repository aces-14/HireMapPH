"""
Daily AI insights generator.
Called once at the end of the pipeline run.
Sends aggregated job stats to Groq → structured JSON → saved to data/insights.json.

One call per day. Zero per-user cost. FastAPI serves the cached file from GET /insights.
"""

from __future__ import annotations

import json
import os

# Python 3.13 + Windows 11 WMI regression: platform.win32_ver() raises OSError
# when WMI class WBEM_E_INVALID_CLASS is missing. Groq SDK calls platform.system()
# while building request headers, which triggers this crash. Patch it here before
# the SDK is used so it returns empty strings instead of raising.
import platform as _platform
_orig_win32_ver = _platform.win32_ver
def _safe_win32_ver(release="", version="", csd="", ptype=""):
    try:
        return _orig_win32_ver(release, version, csd, ptype)
    except OSError:
        return (release, version, csd, ptype)
_platform.win32_ver = _safe_win32_ver
from collections import Counter
from datetime import date
from pathlib import Path

from groq import Groq

DATA_DIR = Path(__file__).parent.parent / "data"
OUT = DATA_DIR / "insights.json"


def _build_context(df) -> str:
    """Summarize the Parquet data into a compact text block for the prompt."""
    import pandas as pd

    total = len(df)
    today = date.today().isoformat()

    # Top cities by job count
    city_counts = df[df["city"].notna()]["city"].value_counts().head(8)
    cities_str = ", ".join(f"{c} ({n})" for c, n in city_counts.items())

    # Top skills across all postings
    all_skills = [s for skills in df["skills"] for s in (skills if isinstance(skills, list) else [])]
    skill_counts = Counter(all_skills).most_common(12)
    skills_str = ", ".join(f"{s} ({n})" for s, n in skill_counts)

    # Top job titles
    title_counts = df["title"].value_counts().head(8)
    titles_str = ", ".join(f"{t} ({n})" for t, n in title_counts.items())

    # Remote vs onsite
    remote_pct = int(df["remote"].mean() * 100) if len(df) else 0

    # Experience level breakdown
    exp_counts = df["experience_level"].value_counts().to_dict()
    exp_str = ", ".join(f"{k}: {v}" for k, v in exp_counts.items() if k)

    # Salary data (sparse but include if available)
    has_salary = df["salary_min"].notna().sum()
    salary_str = ""
    if has_salary > 0:
        median_min = int(df["salary_min"].median())
        median_max = int(df["salary_max"].median())
        salary_str = f"Salary data available for {has_salary} postings. Median range: PHP {median_min:,}–{median_max:,}/month."

    # Day-over-day role trend from master.parquet
    trend_str = ""
    try:
        master_path = DATA_DIR / "master.parquet"
        if master_path.exists():
            master = pd.read_parquet(master_path, engine="pyarrow")
            if "first_seen" in master.columns:
                from datetime import timedelta
                yesterday = (date.today() - timedelta(days=1)).isoformat()
                today_new   = master[master["first_seen"] == today]["title"].value_counts().head(8)
                yest_new    = master[master["first_seen"] == yesterday]["title"].value_counts().head(8)
                if not yest_new.empty or not today_new.empty:
                    lines = []
                    for title in dict.fromkeys(list(today_new.index) + list(yest_new.index)):
                        t = int(today_new.get(title, 0))
                        y = int(yest_new.get(title, 0))
                        if y > 0:
                            pct = round((t - y) / y * 100)
                            lines.append(f"  {title}: {t} today vs {y} yesterday ({pct:+d}%)")
                        elif t > 0:
                            lines.append(f"  {title}: {t} today vs 0 yesterday (new)")
                    if lines:
                        trend_str = "Role volume (today vs yesterday):\n" + "\n".join(lines[:8])
    except Exception:
        pass

    return f"""Philippine Job Market Data — {today}
Total active listings: {total}
Top hiring cities: {cities_str}
Most in-demand skills: {skills_str}
Most common roles: {titles_str}
Remote listings: {remote_pct}%
Experience levels: {exp_str}
{salary_str}
{trend_str}
Sources: DOLE Phil-JobNet, Kalibrr, JSearch (via Indeed)"""


PROMPT_SYSTEM = """You are a Philippine job market analyst. You receive aggregated job posting data and produce a structured JSON market intelligence report. Be specific, data-driven, and concise. Only reference information present in the data. Respond with a valid JSON object only — no markdown fences, no explanation."""

PROMPT_USER = """Based on the following Philippine job market data, produce a JSON object with exactly this structure. Do not include any text outside the JSON.

{context}

Required JSON structure:
{{
  "generated_at": "YYYY-MM-DD",
  "fastest_growing_roles": [
    {{"role": "string", "change_pct": number, "city": "string"}}
  ],
  "most_in_demand_skills": ["string", ...],
  "top_hiring_cities": [
    {{"city": "string", "count": number, "change_pct": number}}
  ],
  "notable_shifts": ["string", ...],
  "salary_highlights": [
    {{"role": "string", "city": "string", "min": number, "max": number, "n": number}}
  ],
  "summary_text": "string"
}}

Rules:
- fastest_growing_roles: list 4-6 roles with estimated growth % based on volume and recency. Use the city where demand is highest.
- most_in_demand_skills: ordered by frequency, list 8-12 skills
- top_hiring_cities: list top 5 cities with job counts from the data
- notable_shifts: 2-4 plain English observations about what changed or stands out
- salary_highlights: only include if salary data was provided; leave as empty array if not
- summary_text: 2-3 sentence plain English summary of the current PH job market
- All strings must be in English
- change_pct for cities: use 0 if no historical comparison available
"""




def _generate_local(df) -> dict:
    """Pure-Python fallback: builds the same JSON schema from data analysis, no LLM needed."""
    from collections import Counter

    today = date.today().isoformat()

    city_counts = df["city"].value_counts().head(5)
    top_cities = [{"city": c, "count": int(n), "change_pct": 0} for c, n in city_counts.items()]

    all_skills = [s for skills in df["skills"] for s in (skills if isinstance(skills, list) else [])]
    top_skills = [s for s, _ in Counter(all_skills).most_common(10)]

    title_counts = df["title"].value_counts().head(6)
    top_city = city_counts.index[0] if len(city_counts) else "Manila"
    growing_roles = [{"role": t, "change_pct": 0, "city": top_city} for t in title_counts.index]

    remote_pct = int(df["remote"].mean() * 100) if len(df) else 0

    salary_highlights = []
    if df["salary_min"].notna().sum() > 0:
        for title in title_counts.index[:3]:
            s = df[df["title"] == title][["salary_min", "salary_max"]].dropna()
            if len(s):
                salary_highlights.append({
                    "role": title, "city": "Multiple",
                    "min": int(s["salary_min"].median()),
                    "max": int(s["salary_max"].median()),
                    "n": len(s),
                })

    top_skill = top_skills[0] if top_skills else "technical skills"
    notable = [
        f"{top_city} leads hiring with {int(city_counts.iloc[0])} active listings.",
        f"{top_skill} is the most in-demand skill across all postings.",
        f"{remote_pct}% of listings offer remote or hybrid work.",
    ]
    if df["salary_min"].notna().sum() > 0:
        notable.append(
            f"Median advertised salary: PHP {int(df['salary_min'].median()):,}–"
            f"{int(df['salary_max'].median()):,}/month."
        )

    total = len(df)
    return {
        "generated_at": today,
        "fastest_growing_roles": growing_roles,
        "most_in_demand_skills": top_skills,
        "top_hiring_cities": top_cities,
        "notable_shifts": notable,
        "salary_highlights": salary_highlights,
        "summary_text": (
            f"The Philippine job market currently has {total} active listings. "
            f"{top_city} dominates with the most openings, while {top_skill} remains "
            f"the most sought-after skill. {remote_pct}% of roles offer remote flexibility."
        ),
    }


def generate(df) -> dict | None:
    """Generate insights from the jobs DataFrame. Returns the insights dict or None on error."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("[Insights] GROQ_API_KEY not set — generating insights locally")
        data = _generate_local(df)
        OUT.parent.mkdir(exist_ok=True)
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"[Insights] Local insights saved -> {OUT}")
        return data

    # No hard timeout — let Groq take as long as it needs.
    # The pipeline runs daily and isn't time-sensitive; 2-3 min is fine.
    client = Groq(api_key=api_key)
    context = _build_context(df)

    import time
    response = None
    for attempt in range(1, 4):
        try:
            print(f"[Insights] Calling Groq (llama-3.1-8b-instant)... attempt {attempt}")
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": PROMPT_SYSTEM},
                    {"role": "user",   "content": PROMPT_USER.format(context=context)},
                ],
                temperature=0,
                max_tokens=1200,
            )
            print("[Insights] Groq succeeded")
            break
        except Exception as e:
            err = str(e)
            print(f"[Insights] Attempt {attempt} failed: {err[:120]}")
            if attempt < 3:
                delay = 30 if ("429" in err or "rate_limit" in err.lower()) else 10
                print(f"[Insights] Retrying in {delay}s")
                time.sleep(delay)

    if response is None:
        print("[Insights] All Groq attempts failed — generating insights locally")
        data = _generate_local(df)
        data["generated_at"] = date.today().isoformat()
        OUT.parent.mkdir(exist_ok=True)
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"[Insights] Local insights saved -> {OUT}")
        return data

    raw = response.choices[0].message.content
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"[Insights] JSON parse failed: {e}\nRaw: {raw[:200]}")
        return None

    # Ensure generated_at is today
    data["generated_at"] = date.today().isoformat()

    OUT.parent.mkdir(exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"[Insights] Saved -> {OUT}")
    return data
