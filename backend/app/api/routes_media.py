from __future__ import annotations

from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, HTTPException, Response

router = APIRouter(prefix="/api/media", tags=["media"])

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
    ),
    "Referer": "https://bbs.hupu.com/",
    "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
}
_MAX_IMAGE_BYTES = 10 * 1024 * 1024


@router.get("/proxy")
def proxy_hupu_image(url: str) -> Response:
    """Proxy a public Hupu image so browser hotlink protection does not hide evidence."""

    _validate_hupu_image_url(url)
    try:
        with httpx.Client(headers=_HEADERS, follow_redirects=False, timeout=20) as client:
            upstream = client.get(url)
            upstream.raise_for_status()
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail=f"Hupu image fetch failed: {exc}") from exc

    media_type = upstream.headers.get("content-type", "").split(";", 1)[0].lower()
    if not media_type.startswith("image/"):
        raise HTTPException(status_code=415, detail="Upstream URL did not return an image")
    if len(upstream.content) > _MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image exceeds the 10 MB proxy limit")
    return Response(
        content=upstream.content,
        media_type=media_type,
        headers={"Cache-Control": "public, max-age=86400"},
    )


def _validate_hupu_image_url(url: str) -> None:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not host.endswith(".hoopchina.com.cn"):
        raise HTTPException(status_code=400, detail="Only public Hupu image URLs are allowed")
