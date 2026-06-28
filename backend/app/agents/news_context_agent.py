from __future__ import annotations

import ipaddress
import socket
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup


class NewsContextAgent:
    """Collect bounded context from user-provided summaries and public news URLs."""

    _headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
        ),
        "Accept-Language": "zh-CN,zh;q=0.9",
    }

    def run(self, config: dict[str, Any]) -> list[dict[str, Any]]:
        """Return public news context without turning fetch errors into task failures."""

        items: list[dict[str, Any]] = []
        manual = str(config.get("news_context") or "").strip()
        if manual:
            items.append(
                {
                    "title": "用户提供的比赛背景",
                    "summary": manual[:3000],
                    "url": "",
                    "published_at": "",
                    "source": "manual",
                    "status": "provided",
                    "image_urls": [],
                }
            )

        urls = list(dict.fromkeys(config.get("news_urls") or []))[:6]
        if not urls:
            return items
        with httpx.Client(headers=self._headers, follow_redirects=False, timeout=15) as client:
            for url in urls:
                try:
                    response = self._fetch_public(client, url)
                    response.raise_for_status()
                    items.append(self.parse_article(response.text, str(response.url)))
                except Exception as exc:
                    items.append(
                        {
                            "title": "新闻上下文读取失败",
                            "summary": str(exc)[:300],
                            "url": url,
                            "published_at": "",
                            "source": "public_url",
                            "status": "error",
                            "image_urls": [],
                        }
                    )
        return items

    def _fetch_public(self, client: httpx.Client, url: str) -> httpx.Response:
        current = url
        for _ in range(4):
            self._validate_public_url(current)
            response = client.get(current)
            if response.status_code not in {301, 302, 303, 307, 308}:
                return response
            location = response.headers.get("location")
            if not location:
                return response
            current = str(response.url.join(location))
        raise ValueError("News URL redirected too many times")

    def parse_article(self, html: str, url: str) -> dict[str, Any]:
        """Extract a compact title and body summary from an article page."""

        soup = BeautifulSoup(html, "html.parser")
        title = self._meta(soup, "property", "og:title") or self._meta(soup, "name", "title")
        if not title and soup.title:
            title = soup.title.get_text(" ", strip=True)
        description = self._meta(soup, "property", "og:description") or self._meta(soup, "name", "description")
        published_at = (
            self._meta(soup, "property", "article:published_time")
            or self._meta(soup, "name", "publishdate")
            or self._meta(soup, "name", "pubdate")
        )
        paragraphs: list[str] = []
        for node in soup.select("article p, main p, [class*='article'] p, [class*='content'] p, p"):
            text = " ".join(node.get_text(" ", strip=True).split())
            if len(text) >= 24 and text not in paragraphs:
                paragraphs.append(text)
            if sum(len(item) for item in paragraphs) >= 1800:
                break
        summary_parts = [part for part in [description, *paragraphs] if part]
        return {
            "title": (title or "未命名新闻")[:300],
            "summary": "\n".join(summary_parts)[:2400],
            "url": url,
            "published_at": published_at[:80],
            "source": "public_url",
            "status": "fetched",
            "image_urls": self._article_images(soup, url),
        }

    @staticmethod
    def _article_images(soup: BeautifulSoup, page_url: str) -> list[str]:
        values: list[str] = []
        og_image = NewsContextAgent._meta(soup, "property", "og:image")
        if og_image:
            values.append(og_image)
        for image in soup.select("article img, main img, [class*='article'] img, [class*='content'] img"):
            value = str(image.get("data-src") or image.get("src") or "").strip()
            if value:
                values.append(value)

        urls: list[str] = []
        for value in values:
            url = urljoin(page_url, value)
            lowered = url.lower()
            if not url.startswith(("https://", "http://")):
                continue
            if any(token in lowered for token in ["avatar", "logo", "icon", ".gif"]):
                continue
            if url not in urls:
                urls.append(url)
            if len(urls) >= 6:
                break
        return urls

    @staticmethod
    def _meta(soup: BeautifulSoup, key: str, value: str) -> str:
        node = soup.find("meta", attrs={key: value})
        return str(node.get("content") or "").strip() if node else ""

    @staticmethod
    def _validate_public_url(url: str) -> None:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
        if parsed.scheme not in {"http", "https"} or not host:
            raise ValueError("News URL must use http or https")
        if host == "localhost" or host.endswith(".local"):
            raise ValueError("Private or local news URLs are not allowed")
        try:
            address = ipaddress.ip_address(host)
        except ValueError:
            try:
                addresses = {item[4][0] for item in socket.getaddrinfo(host, None)}
            except socket.gaierror as exc:
                raise ValueError(f"News host cannot be resolved: {host}") from exc
            if any(not ipaddress.ip_address(value).is_global for value in addresses):
                raise ValueError("Private or local news URLs are not allowed")
            return
        if not address.is_global:
            raise ValueError("Private or local news URLs are not allowed")
