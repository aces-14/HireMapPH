from collections import Counter

from fastapi import APIRouter, Query
from backend import data_store

router = APIRouter()


@router.get("/skill-gap")
def skill_gap(role: str = Query(None), city: str = Query(None)):
    df = data_store.get_latest()
    if df.empty:
        return {"total_postings": 0, "role": role or "", "city": city or "", "top_skills": []}

    if role:
        df = df[df["title"].str.contains(role, case=False, na=False)]
    if city:
        df = df[df["city"].str.contains(city, case=False, na=False)]

    total = len(df)
    if total == 0:
        return {"total_postings": 0, "role": role or "", "city": city or "", "top_skills": []}

    all_skills = [s for skills in df["skills"] for s in (skills if isinstance(skills, list) else [])]
    skill_counts = Counter(all_skills).most_common(20)

    return {
        "total_postings": total,
        "role": role or "All roles",
        "city": city or "All cities",
        "top_skills": [
            {"skill": s, "count": c, "pct": round(c / total * 100)}
            for s, c in skill_counts
        ],
    }
