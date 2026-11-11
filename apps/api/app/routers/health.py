from fastapi import APIRouter

from app.config import get_settings

router = APIRouter()


@router.get("/health")
def health():
    settings = get_settings()
    return {
        "ok": True,
        "phase": 3,
        "writes": "disabled_by_product_rules",
        "dev_ingest": settings.dev_ingest_enabled,
    }
