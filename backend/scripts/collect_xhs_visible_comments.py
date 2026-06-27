from __future__ import annotations

import argparse
import hashlib
import json
import re
import time
from pathlib import Path
from urllib.parse import quote

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEFAULT_QUERY_TEMPLATES = ["{keyword}", "{keyword} 热门", "{keyword} 讨论"]

TIME_RE = re.compile(
    r"^(?:\d+\s*(?:秒|分钟|小时|天|周|月|年)前|刚刚|今天(?:\s+\d{1,2}:\d{2})?|"
    r"昨天(?:\s+\d{1,2}:\d{2})?|前天(?:\s+\d{1,2}:\d{2})?|"
    r"\d{1,2}-\d{1,2}(?:\s+[^\s]+)?|\d{4}-\d{1,2}-\d{1,2}(?:\s+[^\s]+)?)(?:\s*[^\s]*)?$"
)
COMMENT_COUNT_RE = re.compile(r"^共\s*(\d+)\s*条评论$")
COUNT_RE = re.compile(r"^\d+$")
EXPAND_RE = re.compile(r"^展开\s*\d+\s*条回复$")
NOISE_CONTENT_RE = re.compile(
    r"(点点关注|点点赞|多多转发|喜欢的朋友点|置顶评论|关注点赞|互关|求关注|VX|加微|开户地址)"
)
CONTROL_WORDS = {
    "作者",
    "置顶评论",
    "猜你想搜",
    "赞",
    "回复",
    "发送",
    "取消",
    "关注",
    "已关注",
    "- THE END -",
    "说点什么...",
    "收起",
    "更多",
    "活动",
    "可以添加到收藏夹啦",
    "分享",
    "收藏",
    "点赞",
    "评论",
    "首页",
    "点点",
    "ai",
    "RED",
    "直播",
    "发布",
    "通知",
    "我",
    "关于我们",
    "筛选",
    "全部",
    "图文",
    "视频",
    "用户",
}
FOLLOW = "关注"
GUESS_SEARCH = "猜你想搜"
THE_END = "- THE END -"
COMMENT_INPUT = "说点什么"
AUTHOR_OR_PIN_RE = re.compile(r"(^|\s)(作者|置顶评论|回复|赞)(\s|$)")
EXPAND_INLINE_RE = re.compile(r"展开\s*\d+\s*条回复")
MENTION_RE = re.compile(r"@\S+")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect visible Xiaohongshu comments from a logged-in CDP browser.")
    parser.add_argument("--cdp-url", default="http://127.0.0.1:9222")
    parser.add_argument("--keyword", default="2026 NBA选秀")
    parser.add_argument("--queries", default="", help="Pipe-separated search queries. Defaults to keyword variants.")
    parser.add_argument("--out", default="data/xhs_2026_nba_draft_visible_comments.jsonl")
    parser.add_argument("--snapshot", default="data/xhs_2026_nba_draft_visible_snapshot.json")
    parser.add_argument("--max-links-per-query", type=int, default=8)
    parser.add_argument("--max-notes", type=int, default=16)
    parser.add_argument("--target-comments", type=int, default=70)
    parser.add_argument("--max-comments-per-note", type=int, default=12)
    parser.add_argument("--required-terms", default="", help="Pipe-separated terms; a note must contain at least one.")
    parser.add_argument("--exclude-terms", default="", help="Pipe-separated terms; a note is skipped if any term matches.")
    return parser.parse_args()


def note_id_from_url(url: str) -> str:
    match = re.search(r"/(?:explore|search_result)/([^/?#]+)", url)
    return match.group(1) if match else hashlib.sha1(url.encode("utf-8")).hexdigest()[:12]


def stable_hash(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:16]


def clean_lines(text: str) -> list[str]:
    lines = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("沪ICP备") or line.startswith("© 2014-") or "违法不良信息举报" in line:
            continue
        if line.startswith("地址：") or line.startswith("电话："):
            continue
        lines.append(line)
    return lines


def is_time_line(line: str) -> bool:
    return len(line) <= 32 and bool(TIME_RE.match(line))


def is_control(line: str) -> bool:
    return line in CONTROL_WORDS or bool(
        COUNT_RE.match(line) or EXPAND_RE.match(line) or line.startswith("鼠标悬停查看")
    )


def parse_note(lines: list[str]) -> tuple[str, str, int | None, list[str]]:
    marker_idx = None
    declared_count = None
    for i, line in enumerate(lines):
        match = COMMENT_COUNT_RE.match(line)
        if match:
            marker_idx = i
            declared_count = int(match.group(1))
            break
    if marker_idx is None:
        return "", "", None, []

    before = lines[:marker_idx]
    title = ""
    desc = ""
    if FOLLOW in before:
        focus_idx = len(before) - 1 - before[::-1].index(FOLLOW)
        after_focus = before[focus_idx + 1 :]
        if after_focus:
            title = after_focus[0]
        if len(after_focus) >= 2:
            parts = []
            for item in after_focus[1:]:
                if is_time_line(item) or item == GUESS_SEARCH:
                    break
                parts.append(item)
            desc = "\n".join(parts).strip()
    if not title:
        for item in reversed(before):
            if not is_control(item) and len(item) >= 2:
                title = item
                break

    tail = []
    for line in lines[marker_idx + 1 :]:
        if line == THE_END or line.startswith(COMMENT_INPUT):
            break
        tail.append(line)
    return title, desc, declared_count, tail


def extract_media_context(page) -> dict:
    return page.evaluate(
        """() => {
          const imgs = [...document.querySelectorAll('img')].filter((img) => {
            const rect = img.getBoundingClientRect();
            return rect.width >= 80 && rect.height >= 80;
          });
          const videos = [...document.querySelectorAll('video')].filter((video) => {
            const rect = video.getBoundingClientRect();
            return rect.width >= 80 && rect.height >= 80;
          });
          const imageHints = imgs.slice(0, 6).map((img) => ({
            alt: (img.alt || '').trim(),
            src_host: (() => {
              try { return new URL(img.currentSrc || img.src || '').host; } catch { return ''; }
            })()
          }));
          return {
            media_type: videos.length ? 'video' : (imgs.length ? 'image' : 'text'),
            image_count: imgs.length,
            video_count: videos.length,
            image_hints: imageHints
          };
        }"""
    )


def normalize_content(parts: list[str]) -> str:
    kept = [part for part in parts if not is_control(part)]
    content = "\n".join(kept).strip()
    content = MENTION_RE.sub(" ", content)
    content = AUTHOR_OR_PIN_RE.sub(" ", content)
    content = EXPAND_INLINE_RE.sub(" ", content)
    return re.sub(r"\s+", " ", content).strip()


def parse_comments(
    comment_lines: list[str],
    note_id: str,
    note_url: str,
    note_title: str,
    source_query: str,
    keyword: str,
    note_desc: str,
    media_context: dict,
    max_comments: int,
) -> list[dict]:
    comments = []
    i = 0
    while i < len(comment_lines):
        while i < len(comment_lines) and is_control(comment_lines[i]):
            i += 1
        if i >= len(comment_lines):
            break
        author = comment_lines[i]
        if is_time_line(author) or len(author) > 45:
            i += 1
            continue
        j = i + 1
        content_parts = []
        while j < len(comment_lines) and not is_time_line(comment_lines[j]):
            if not is_control(comment_lines[j]):
                content_parts.append(comment_lines[j])
            j += 1
        if j >= len(comment_lines):
            i += 1
            continue
        content = normalize_content(content_parts)
        create_time = comment_lines[j]
        if content and len(content) >= 2 and not NOISE_CONTENT_RE.search(content):
            digest = stable_hash(f"{note_id}:{author}:{content}:{create_time}")
            comments.append(
                {
                    "comment_id": f"xhs-visible-{digest}",
                    "note_id": note_id,
                    "content": content,
                    "user_id": f"visible-user-{stable_hash(author)}",
                    "like_count": 0,
                    "sub_comment_count": 0,
                    "create_time": create_time,
                    "parent_comment_id": "",
                    "source_keyword": keyword,
                    "source_query": source_query,
                    "title": note_title,
                    "note_title": note_title,
                    "note_desc": note_desc,
                    "note_media_type": media_context.get("media_type", "text"),
                    "note_image_count": media_context.get("image_count", 0),
                    "note_video_count": media_context.get("video_count", 0),
                    "note_media_hints": media_context.get("image_hints", []),
                    "note_url": note_url,
                    "platform": "xhs",
                }
            )
        i = j + 1
    return comments[:max_comments]


def collect_search_links(page, query: str, max_links: int) -> list[dict]:
    url = "https://www.xiaohongshu.com/search_result?keyword=" + quote(query)
    page.goto(url, wait_until="domcontentloaded", timeout=30_000)
    page.wait_for_timeout(3_500)
    for _ in range(2):
        page.mouse.wheel(0, 1000)
        page.wait_for_timeout(1_300)
    links = page.eval_on_selector_all(
        "a[href]",
        """els => {
          const seen = new Set(); const out = [];
          for (const a of els) {
            const href = a.href || '';
            if (!href.includes('/search_result/')) continue;
            const match = href.match(/search_result\\/([^?]+)/);
            const id = match ? match[1] : href;
            if (seen.has(id)) continue;
            seen.add(id);
            const text = (a.innerText || a.textContent || '').trim();
            out.push({id, href, text});
          }
          return out;
        }""",
    )
    return links[:max_links]


def balanced_note_links(note_by_id: dict[str, dict], queries: list[str], limit: int) -> list[dict]:
    buckets = {
        query: [item for item in note_by_id.values() if item.get("source_query") == query]
        for query in queries
    }
    selected = []
    seen = set()
    index = 0
    while len(selected) < limit:
        progressed = False
        for query in queries:
            bucket = buckets.get(query, [])
            if index >= len(bucket):
                continue
            item = bucket[index]
            if item["id"] not in seen:
                selected.append(item)
                seen.add(item["id"])
                progressed = True
                if len(selected) >= limit:
                    break
        if not progressed:
            break
        index += 1
    return selected


def split_terms(value: str) -> list[str]:
    return [item.strip().lower() for item in value.split("|") if item.strip()]


def is_relevant_note(title: str, desc: str, body: str, required_terms: list[str], exclude_terms: list[str]) -> bool:
    text = f"{title}\n{desc}\n{body[:1200]}".lower()
    if exclude_terms and any(term in text for term in exclude_terms):
        return False
    if required_terms and not any(term in text for term in required_terms):
        return False
    return True


def main() -> None:
    args = parse_args()
    queries = [item.strip() for item in args.queries.split("|") if item.strip()] or [
        template.format(keyword=args.keyword) for template in DEFAULT_QUERY_TEMPLATES
    ]
    required_terms = split_terms(args.required_terms)
    exclude_terms = split_terms(args.exclude_terms)
    out_path = PROJECT_ROOT / args.out
    snapshot_path = PROJECT_ROOT / args.snapshot

    with sync_playwright() as playwright:
        browser = playwright.chromium.connect_over_cdp(args.cdp_url)
        context = browser.contexts[0]
        search_page = context.new_page()
        note_by_id: dict[str, dict] = {}
        query_stats = []
        for query in queries:
            try:
                links = collect_search_links(search_page, query, args.max_links_per_query)
            except Exception as exc:
                print(f"search_error query={query} error={exc}")
                continue
            added = 0
            for link in links:
                item = dict(link)
                item["source_query"] = query
                if item["id"] not in note_by_id:
                    note_by_id[item["id"]] = item
                    added += 1
            query_stats.append({"query": query, "found": len(links), "added": added})
            print(f"search query={query} found={len(links)} added={added} total_notes={len(note_by_id)}")
            time.sleep(1.5)
        search_page.close()

        note_links = balanced_note_links(note_by_id, queries, args.max_notes)
        all_comments = []
        snapshots = []
        page = context.new_page()
        for idx, link in enumerate(note_links, start=1):
            try:
                page.goto(link["href"], wait_until="domcontentloaded", timeout=30_000)
                page.wait_for_timeout(3_500)
                for _ in range(3):
                    page.mouse.wheel(0, 900)
                    page.wait_for_timeout(1_200)
                body = page.locator("body").inner_text(timeout=10_000)
                media_context = extract_media_context(page)
            except PlaywrightTimeoutError as exc:
                print(f"note_timeout idx={idx} id={link['id']} {exc}")
                continue
            except Exception as exc:
                print(f"note_error idx={idx} id={link['id']} {exc}")
                continue
            lines = clean_lines(body)
            note_url = page.url
            note_id = note_id_from_url(note_url)
            title, desc, declared_count, comment_lines = parse_note(lines)
            if not is_relevant_note(title, desc, body, required_terms, exclude_terms):
                print(f"note_skip_irrelevant idx={idx} title={title[:48]}")
                continue
            comments = parse_comments(
                comment_lines,
                note_id,
                note_url,
                title,
                link.get("source_query") or "",
                args.keyword,
                desc,
                media_context,
                args.max_comments_per_note,
            )
            all_comments.extend(comments)
            snapshots.append(
                {
                    "idx": idx,
                    "id": note_id,
                    "source_query": link.get("source_query"),
                    "url": note_url,
                    "search_text": link.get("text", ""),
                    "title": title,
                    "desc": desc[:500],
                    "media": media_context,
                    "declared_comment_count": declared_count,
                    "parsed_comment_count": len(comments),
                    "first_comments": [comment["content"] for comment in comments[:4]],
                }
            )
            print(
                f"note {idx}/{len(note_links)} declared={declared_count} parsed={len(comments)} "
                f"total_comments={len(all_comments)} title={title[:48]}"
            )
            if len(all_comments) >= args.target_comments:
                break
            time.sleep(1.4)
        page.close()

    deduped = []
    seen = set()
    for row in all_comments:
        key = (row["note_id"], row["content"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as file:
        for row in deduped:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")
    snapshot_path.write_text(
        json.dumps(
            {
                "keyword": args.keyword,
                "queries": query_stats,
                "candidate_note_count": len(note_by_id),
                "visited_note_count": len(snapshots),
                "notes": snapshots,
                "total_comments": len(deduped),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"written={out_path}")
    print(f"snapshot={snapshot_path}")
    print(
        f"candidate_note_count={len(note_by_id)} "
        f"visited_note_count={len(snapshots)} total_comments={len(deduped)}"
    )


if __name__ == "__main__":
    main()
