from fastapi import APIRouter
from backend import data_store

router = APIRouter()


@router.get("/health")
def health():
    df = data_store.get_latest()
    return {
        "status": "ok",
        "last_updated": data_store.last_updated(),
        "total_active_jobs": len(df),
        "sources": df["source"].value_counts().to_dict() if not df.empty else {},
    }
