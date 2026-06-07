from fastapi import APIRouter
from app.api.webhook import router as webhook_router

router = APIRouter()

# health check for the API itself
@router.get("/health")
async def health():
    return {"status": "ok"}

# GitHub webhook lives at /api/v1/webhook
router.include_router(webhook_router, prefix="/webhook", tags=["webhook"])