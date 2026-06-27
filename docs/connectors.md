# Connectors

## Supported Inputs

| Connector | Use |
| --- | --- |
| `HupuPublicConnector` | Read user-selected public Hupu thread pages and pagination. |
| `CSVConnector` | Import a normalized local CSV export. |
| `JsonConnector` | Import JSON or JSONL comments. |
| `MockConnector` | Run a deterministic basketball/football demo offline. |

## Hupu Public Connector

Input URLs must match `https://bbs.hupu.com/<thread-id>.html` or the mobile equivalent. The connector normalizes the first page to `-1.html`, follows public pagination, and parses the page's public `__NEXT_DATA__` payload.

Collected fields:

- hashed comment and author identifiers
- plain-text comment content
- light and reply counts
- publish time and canonical thread URL
- original-post image URLs stored only in thread metadata
- thread title and body excerpt
- board and match metadata

The connector does not search Hupu automatically. Selecting the relevant board, match, and threads remains an explicit user decision, which keeps the sample interpretable. Reply images are discarded. Main-post images are scored for official/data signals, URL-deduplicated, and analyzed one by one within the task image budget.

## Local Import Schema

CSV/JSON rows should contain:

```text
id, platform, topic, content, author_hash, like_count,
reply_count, publish_time, source_url, parent_id
```

## Compliance Boundary

- Public pages only.
- No login cookies, private APIs, CAPTCHA handling, or anti-bot bypasses.
- No usernames in persisted analysis; stable public IDs are hashed.
- Stop when the platform denies access or changes its page structure.
- Prefer user-provided exports when direct public-page access is unstable.
