from datetime import UTC, datetime

from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.now(UTC).isoformat()}
