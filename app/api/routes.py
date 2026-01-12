"""API routes for the translation service."""
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def api_health():
    """API health check."""
    return {"status": "ok"}
