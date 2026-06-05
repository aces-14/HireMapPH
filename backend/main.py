"""
HireMap PH — FastAPI backend.
Run: uvicorn backend.main:app --reload --port 8000
Docs: http://localhost:8000/docs
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers import health, map_data, jobs, trending, salary, insights, skill_gap

app = FastAPI(
    title="HireMap PH API",
    description="Philippine job market intelligence — map data, trends, salary, insights.",
    version="1.0.0",
)

# Allow all origins during development; Streamlit and the React landing page
# both run on different ports/domains and need CORS access.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(map_data.router)
app.include_router(jobs.router)
app.include_router(trending.router)
app.include_router(salary.router)
app.include_router(insights.router)
app.include_router(skill_gap.router)
