# Connectors

Connectors normalize data into the RawComment schema.

## Interface

Defined in `backend/app/connectors/base.py`:

```python
class PlatformConnector(Protocol):
    name: str

    def fetch_comments(self, request: FetchRequest) -> list[NormalizedComment]:
        ...
```

`FetchRequest` includes task id, platform, domain, keywords, semantic query, time range, max comments, and optional source path.

## Normalized RawComment Fields

- `id`
- `platform`
- `topic`
- `content`
- `author_hash`
- `like_count`
- `reply_count`
- `publish_time`
- `source_url`
- `parent_id`
- `metadata`

## Built-in Connectors

### MockConnector

Synthetic comments for local smoke tests.

### CSVConnector

Reads local CSV files with normalized or near-normalized fields.

### JsonConnector

Reads JSON arrays or objects with `comments`.

### MediaCrawlerExportConnector

Reads existing MediaCrawler CSV/JSON/JSONL/SQLite outputs and converts them into RawComment records.

### MediaCrawlerAdapter

Thin wrapper around a local MediaCrawler checkout. It does not copy MediaCrawler source code.

Set:

```bash
MEDIA_CRAWLER_PATH=/path/to/MediaCrawler
```

Supported platform aliases:

- `xhs`
- `dy`
- `ks`
- `bili`
- `wb`
- `tieba`
- `zhihu`

Hupu, Reddit, and YouTube remain mock/generic connectors for now.

## Add A Connector

1. Create `backend/app/connectors/my_connector.py`.
2. Implement `fetch_comments`.
3. Return RawComment-compatible dicts.
4. Register the connector in `PlatformRouterAgent`.
5. Add connector docs and tests.

## Compliance Boundary

Connectors must not bypass login, CAPTCHA, paywalls, private APIs, anti-bot controls, or platform permissions. Prefer user-provided exports, public data, and mock datasets for demos.
