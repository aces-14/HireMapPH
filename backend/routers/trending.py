from collections import Counter
from datetime import date, timedelta

from fastapi import APIRouter
from backend import data_store

router = APIRouter()


def _week_range(weeks_ago: int = 0):
    today = date.today()
    end = today - timedelta(weeks=weeks_ago)
    start = end - timedelta(weeks=1)
    return start.isoformat(), end.isoformat()


@router.get("/trending")
def trending():
    master = data_store.get_master()
    if master.empty:
        return {}

    # Ensure first_seen is a string column for comparison
    if "first_seen" not in master.columns:
        return {}

    master = master.copy()
    master["first_seen"] = master["first_seen"].astype(str)

    this_start, this_end = _week_range(0)
    last_start, last_end = _week_range(1)

    this_week = master[(master["first_seen"] >= this_start) & (master["first_seen"] <= this_end)]
    last_week = master[(master["first_seen"] >= last_start) & (master["first_seen"] <= last_end)]

    def top_roles(df, n=10):
        return df["title"].value_counts().head(n).to_dict()

    def top_skills(df, n=10):
        all_skills = [s for skills in df["skills"] for s in skills]
        return dict(Counter(all_skills).most_common(n))

    def role_changes(this_df, last_df, n=5):
        this_counts = Counter(this_df["title"])
        last_counts = Counter(last_df["title"])
        all_roles = set(this_counts) | set(last_counts)
        changes = []
        for role in all_roles:
            this_n = this_counts.get(role, 0)
            last_n = last_counts.get(role, 0)
            if last_n == 0 and this_n > 0:
                pct = 100
            elif last_n == 0:
                pct = 0
            else:
                pct = round(((this_n - last_n) / last_n) * 100)
            if this_n >= 2:
                changes.append({"role": role, "this_week": this_n, "last_week": last_n, "change_pct": pct})
        return sorted(changes, key=lambda x: x["change_pct"], reverse=True)[:n]

    return {
        "this_week": {
            "period": f"{this_start} to {this_end}",
            "new_jobs": len(this_week),
            "top_roles": top_roles(this_week),
            "top_skills": top_skills(this_week),
        },
        "last_week": {
            "period": f"{last_start} to {last_end}",
            "new_jobs": len(last_week),
            "top_roles": top_roles(last_week),
            "top_skills": top_skills(last_week),
        },
        "fastest_growing_roles": role_changes(this_week, last_week),
        "all_time_top_skills": top_skills(master, n=15),
    }
