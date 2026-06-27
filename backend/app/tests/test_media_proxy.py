from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.api.routes_media import _validate_hupu_image_url


def test_media_proxy_accepts_hupu_cdn_url() -> None:
    _validate_hupu_image_url("https://i3.hoopchina.com.cn/newsPost/example.jpg")


@pytest.mark.parametrize(
    "url",
    [
        "http://i3.hoopchina.com.cn/example.jpg",
        "https://example.com/image.jpg",
        "https://hoopchina.com.cn.evil.example/image.jpg",
        "file:///etc/passwd",
    ],
)
def test_media_proxy_rejects_non_hupu_urls(url: str) -> None:
    with pytest.raises(HTTPException) as caught:
        _validate_hupu_image_url(url)
    assert caught.value.status_code == 400
