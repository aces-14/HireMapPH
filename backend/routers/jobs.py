from fastapi import APIRouter, Query
from backend import data_store

router = APIRouter()


@router.get("/jobs")
def jobs(
    role: str = Query(None),
    city: str = Query(None),
    remote: bool = Query(None),
    experience: str = Query(None),
    source: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
):
    df = data_store.get_latest()
    if df.empty:
        return {"total": 0, "page": page, "results": []}

    if role:
        df = df[df["title"].str.contains(role, case=False, na=False)]
    if city:
        df = df[df["city"].str.contains(city, case=False, na=False)]
    if remote is not None:
        df = df[df["remote"] == remote]
    if experience:
        df = df[df["experience_level"] == experience]
    if source:
        df = df[df["source"] == source]

    total = len(df)
    start = (page - 1) * page_size
    end = start + page_size
    page_df = df.iloc[start:end]

    results = []
    for _, row in page_df.iterrows():
        results.append({
            "job_id": row["job_id"],
            "title": row["title"],
            "company": row["company"],
            "city": row["city"],
            "region": row["region"],
            "remote": bool(row["remote"]),
            "salary_min": int(row["salary_min"]) if row["salary_min"] is not None and str(row["salary_min"]) != "<NA>" else None,
            "salary_max": int(row["salary_max"]) if row["salary_max"] is not None and str(row["salary_max"]) != "<NA>" else None,
            "experience_level": row["experience_level"],
            "skills": row["skills"],
            "source": row["source"],
            "date_posted": str(row["date_posted"]) if row["date_posted"] is not None else None,
            "apply_url": row["apply_url"],
            "apply_urls": row["apply_urls"] if "apply_urls" in row.index and isinstance(row["apply_urls"], list) else [],
        })

    return {"total": total, "page": page, "page_size": page_size, "results": results}
