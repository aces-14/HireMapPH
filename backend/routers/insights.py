from fastapi import APIRouter
from backend import data_store

router = APIRouter()


@router.get("/insights")
def insights():
    data = data_store.get_insights()
    if not data:
        return {"status": "pending", "message": "Insights not yet generated. Run the pipeline first."}
    return data
