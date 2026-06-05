"""Quick API validation script — run after starting uvicorn."""
import httpx
import sys

BASE = "http://localhost:8000"
failures = []


def check(label, condition, detail=""):
    if condition:
        print(f"  PASS  {label}")
    else:
        print(f"  FAIL  {label}  {detail}")
        failures.append(label)


# ── /health ──────────────────────────────────────────────────────────────────
print("=== /health ===")
h = httpx.get(f"{BASE}/health").json()
check("status is ok",           h["status"] == "ok")
check("last_updated not null",  h["last_updated"] is not None)
check("total_active_jobs > 0",  h["total_active_jobs"] > 0)
check("sources has jsearch",    "jsearch" in h["sources"])
check("sources has kalibrr",    "kalibrr" in h["sources"])

# ── /map-data ─────────────────────────────────────────────────────────────────
print("\n=== /map-data ===")
m = httpx.get(f"{BASE}/map-data").json()
check("returns a list",         isinstance(m, list))
check("at least 3 cities",      len(m) >= 3)

manila = next((c for c in m if c["city"] == "Manila"), None)
check("Manila is in results",   manila is not None)
if manila:
    check("Manila lat in PH range", 13 < manila["lat"] < 22,   f"lat={manila['lat']}")
    check("Manila lng in PH range", 117 < manila["lng"] < 127, f"lng={manila['lng']}")
    check("Manila job_count > 0",   manila["job_count"] > 0)
    check("Manila top_roles list",  isinstance(manila["top_roles"], list))
    check("Manila top_skills list", isinstance(manila["top_skills"], list))

check("all cities have lat",    all(c["lat"] is not None for c in m))
check("all cities have lng",    all(c["lng"] is not None for c in m))
check("sorted desc by count",   m == sorted(m, key=lambda x: x["job_count"], reverse=True))

print("\n=== /map-data filters ===")
mr = httpx.get(f"{BASE}/map-data?remote=true").json()
check("remote filter -> list",   isinstance(mr, list))
me = httpx.get(f"{BASE}/map-data?role=engineer").json()
check("role filter -> list",     isinstance(me, list))

# ── /jobs ─────────────────────────────────────────────────────────────────────
print("\n=== /jobs ===")
j = httpx.get(f"{BASE}/jobs").json()
check("has total",              "total" in j)
check("has results",            "results" in j)
check("total > 0",              j["total"] > 0)
check("results is list",        isinstance(j["results"], list))

if j["results"]:
    r = j["results"][0]
    for field in ["job_id", "title", "company", "city", "region", "remote", "source", "apply_url"]:
        check(f"job has {field}", field in r)
    check("remote is bool",     isinstance(r["remote"], bool))
    check("skills is list",     isinstance(r["skills"], list))
    check("apply_url not empty", bool(r["apply_url"]))

print("\n=== /jobs filters ===")
jm = httpx.get(f"{BASE}/jobs?city=Manila").json()
check("city=Manila has results", jm["total"] > 0)
offenders = [r["city"] for r in jm["results"] if r["city"] != "Manila"]
check("all results are Manila",  len(offenders) == 0, f"got non-Manila: {offenders}")

jd = httpx.get(f"{BASE}/jobs?role=data").json()
check("role=data has results",   jd["total"] > 0)
bad = [r["title"] for r in jd["results"] if "data" not in r["title"].lower()]
check("all titles contain data", len(bad) == 0, f"offenders: {bad}")

jr = httpx.get(f"{BASE}/jobs?remote=true").json()
check("remote=true has results", jr["total"] > 0)
check("all are remote",          all(r["remote"] for r in jr["results"]))

print("\n=== /jobs pagination ===")
p1 = httpx.get(f"{BASE}/jobs?page=1&page_size=10").json()
p2 = httpx.get(f"{BASE}/jobs?page=2&page_size=10").json()
check("page 1 has 10 results",   len(p1["results"]) == 10)
check("page 2 has results",      len(p2["results"]) > 0)
ids1 = {r["job_id"] for r in p1["results"]}
ids2 = {r["job_id"] for r in p2["results"]}
check("pages do not overlap",    len(ids1 & ids2) == 0)

# ── /trending ────────────────────────────────────────────────────────────────
print("\n=== /trending ===")
t = httpx.get(f"{BASE}/trending").json()
check("has this_week",           "this_week" in t)
check("has last_week",           "last_week" in t)
check("has all_time_top_skills", "all_time_top_skills" in t)
check("this_week new_jobs > 0",  t["this_week"]["new_jobs"] > 0)
check("top_skills has python",   "python" in t["all_time_top_skills"])
check("top_skills has sql",      "sql"    in t["all_time_top_skills"])

# ── /salary ──────────────────────────────────────────────────────────────────
print("\n=== /salary ===")
s = httpx.get(f"{BASE}/salary").json()
check("returns a list",          isinstance(s, list))

# ── /insights ────────────────────────────────────────────────────────────────
print("\n=== /insights ===")
i = httpx.get(f"{BASE}/insights").json()
check("returns a dict",          isinstance(i, dict))
check("has status or generated_at", "status" in i or "generated_at" in i)

# ── Summary ───────────────────────────────────────────────────────────────────
print()
if not failures:
    print("All checks passed.")
else:
    print(f"{len(failures)} FAILED: {failures}")
    sys.exit(1)
