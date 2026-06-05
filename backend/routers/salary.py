from fastapi import APIRouter, Query
from backend import data_store

router = APIRouter()


@router.get("/salary")
def salary(role: str = Query(None), city: str = Query(None)):
    df = data_store.get_latest()
    if df.empty:
        return []

    # Only rows with salary data
    df = df[df["salary_min"].notna() & df["salary_max"].notna()]

    if df.empty:
        return []

    if role:
        df = df[df["title"].str.contains(role, case=False, na=False)]
    if city:
        df = df[df["city"].str.contains(city, case=False, na=False)]

    results = []
    for (title, city_name), group in df.groupby(["title", "city"]):
        results.append({
            "role": title,
            "city": city_name,
            "salary_min": int(group["salary_min"].min()),
            "salary_max": int(group["salary_max"].max()),
            "salary_median": int(group[["salary_min", "salary_max"]].mean(axis=1).median()),
            "sample_size": len(group),
        })

    return sorted(results, key=lambda x: x["sample_size"], reverse=True)
