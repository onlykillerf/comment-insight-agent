from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    """Return service health."""

    return {"status": "ok", "service": "comment-insight-agent"}

