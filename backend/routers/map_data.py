from collections import Counter

from fastapi import APIRouter, Query
from backend import data_store

router = APIRouter()


@router.get("/map-data")
def map_data(
    role: str = Query(None),
    remote: bool = Query(None),
    experience: str = Query(None),
):
    df = data_store.get_latest()
    if df.empty:
        return []

    if role:
        df = df[df["title"].str.contains(role, case=False, na=False)]
    if remote is not None:
        df = df[df["remote"] == remote]
    if experience:
        df = df[df["experience_level"] == experience]

    # Drop rows with no coordinates
    df = df[df["lat"].notna() & df["lng"].notna()]

    result = []
    for city, group in df.groupby("city"):
        top_roles = (
            group["title"]
            .value_counts()
            .head(5)
            .index.tolist()
        )
        top_companies = (
            group["company"]
            .value_counts()
            .head(5)
            .index.tolist()
        )
        all_skills = [s for skills in group["skills"] for s in skills]
        top_skills = [s for s, _ in Counter(all_skills).most_common(5)]

        result.append({
            "city": city,
            "region": group["region"].iloc[0],
            "lat": float(group["lat"].iloc[0]),
            "lng": float(group["lng"].iloc[0]),
            "job_count": len(group),
            "top_roles": top_roles,
            "top_companies": top_companies,
            "top_skills": top_skills,
        })

    return sorted(result, key=lambda x: x["job_count"], reverse=True)
