from __future__ import annotations

import json
import re
import time
from datetime import datetime, timezone
from hashlib import sha1
from pathlib import Path
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from app.connectors.base import FetchRequest, NormalizedComment


class HupuPublicConnector:
    """Read comments from user-selected, publicly accessible Hupu threads."""

    name = "hupu_public"
    _thread_pattern = re.compile(r"/(?:bbs/)?(?P<thread_id>\d+)(?:[-_]\d+)?\.html")
    _headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
        ),
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Referer": "https://bbs.hupu.com/",
    }

    def fetch_comments(self, request: FetchRequest) -> list[NormalizedComment]:
        """Fetch public thread pages without login cookies or protected APIs."""

        if request.source_path:
            html = Path(request.source_path).read_text(encoding="utf-8")
            comments, _ = self.parse_page(html, request, request.source_path)
            return comments[: request.max_comments]

        urls = list(dict.fromkeys(request.source_urls))
        if not urls:
            raise ValueError("Hupu public collection requires at least one thread URL")

        collected: list[NormalizedComment] = []
        seen: set[str] = set()
        with httpx.Client(headers=self._headers, follow_redirects=True, timeout=20) as client:
            for source_url in urls:
                thread_id = self._thread_id(source_url)
                page = 1
                total_pages = 1
                while page <= total_pages and len(collected) < request.max_comments:
                    page_url = f"https://bbs.hupu.com/{thread_id}-{page}.html"
                    response = client.get(page_url)
                    response.raise_for_status()
                    page_comments, total_pages = self.parse_page(response.text, request, source_url)
                    for comment in page_comments:
                        if comment["id"] in seen:
                            continue
                        seen.add(comment["id"])
                        collected.append(comment)
                        if len(collected) >= request.max_comments:
                            break
                    page += 1
                    if page <= total_pages and len(collected) < request.max_comments:
                        time.sleep(0.35)
        if not collected:
            raise ValueError("No public comments were found in the selected Hupu threads")
        return collected

    def parse_page(
        self, html: str, request: FetchRequest, source_url: str
    ) -> tuple[list[NormalizedComment], int]:
        """Convert a public Hupu page into normalized comments."""

        soup = BeautifulSoup(html, "html.parser")
        script = soup.select_one("script#__NEXT_DATA__")
        if not script:
            raise ValueError("Hupu page does not contain public thread data")
        payload = json.loads(script.string or script.get_text())
        detail = payload.get("props", {}).get("pageProps", {}).get("detail", {})
        thread = detail.get("thread") or {}
        replies = detail.get("replies") or {}
        total_pages = max(1, int(replies.get("total") or 1))
        thread_id = str(thread.get("tid") or self._thread_id(source_url))
        thread_title = str(thread.get("title") or detail.get("keywords") or "虎扑比赛讨论")
        thread_html = str(thread.get("content") or "")
        thread_excerpt = self._plain_text(thread_html)[:1200]
        thread_image_urls = self._image_urls(thread_html)
        breadcrumb = detail.get("breadCrumb") or []
        board_name = request.board or self._board_name(breadcrumb)
        canonical_url = f"https://bbs.hupu.com/{thread_id}.html"

        posts = list(replies.get("list") or []) + list(detail.get("lights") or [])
        rows: list[NormalizedComment] = []
        for post in posts:
            if post.get("isDelete") or post.get("isSelfDelete") or post.get("isHidden"):
                continue
            post_html = str(post.get("content") or "")
            content = self._plain_text(post_html)
            image_urls = self._image_urls(post_html)
            if not content and not image_urls:
                continue
            if not content:
                content = "[图片评论]"
            post_id = str(post.get("pid") or sha1(content.encode("utf-8")).hexdigest()[:16])
            author_id = str(post.get("authorId") or (post.get("author") or {}).get("puid") or post_id)
            rows.append(
                {
                    "id": f"hupu-{thread_id}-{post_id}",
                    "platform": "hupu",
                    "topic": thread_title,
                    "content": content,
                    "author_hash": sha1(author_id.encode("utf-8")).hexdigest()[:16],
                    "like_count": int(post.get("allLightCount") or post.get("count") or 0),
                    "reply_count": int(post.get("replyNum") or 0),
                    "publish_time": self._publish_time(post.get("createdAt")),
                    "source_url": canonical_url,
                    "parent_id": None,
                    "image_urls": image_urls,
                    "image_analysis": {},
                    "metadata": {
                        "source": "hupu_public",
                        "thread_id": thread_id,
                        "thread_title": thread_title,
                        "thread_excerpt": thread_excerpt,
                        "thread_image_urls": thread_image_urls,
                        "board": board_name,
                        "sport": request.domain,
                        "match_name": request.match_name,
                        "home_team": request.home_team,
                        "away_team": request.away_team,
                        "match_stage": request.match_stage,
                        "match_date": request.match_date,
                        "compliance": "public_page_without_login",
                    },
                }
            )
        return rows, total_pages

    def _thread_id(self, url: str) -> str:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"} or parsed.hostname not in {"bbs.hupu.com", "m.hupu.com"}:
            raise ValueError(f"Unsupported Hupu thread URL: {url}")
        match = self._thread_pattern.search(parsed.path)
        if not match:
            raise ValueError(f"Cannot determine Hupu thread id from URL: {url}")
        return match.group("thread_id")

    @staticmethod
    def _plain_text(html: str) -> str:
        if "<" not in html and ">" not in html:
            return " ".join(html.split())
        return " ".join(BeautifulSoup(html, "html.parser").get_text(" ", strip=True).split())

    @staticmethod
    def _image_urls(html: str) -> list[str]:
        if "<" not in html:
            return []
        urls: list[str] = []
        for image in BeautifulSoup(html, "html.parser").find_all("img"):
            value = str(image.get("src") or image.get("data-src") or "").strip()
            if value.startswith("//"):
                value = f"https:{value}"
            if value.startswith(("https://", "http://")) and value not in urls:
                urls.append(value)
            if len(urls) >= 4:
                break
        return urls

    @staticmethod
    def _board_name(breadcrumb: list[dict]) -> str:
        names = [str(item.get("title") or "").strip() for item in breadcrumb]
        useful = [name for name in names if name and name != "社区"]
        return useful[-2] if len(useful) >= 2 else (useful[0] if useful else "")

    @staticmethod
    def _publish_time(value: object) -> str:
        try:
            timestamp = float(value or 0)
            if timestamp > 10_000_000_000:
                timestamp /= 1000
            return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()
        except (TypeError, ValueError, OSError):
            return ""
