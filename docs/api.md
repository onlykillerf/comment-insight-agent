# API

Base URL: `http://localhost:8000`

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/tasks` | Create a match analysis task. |
| GET | `/api/tasks` | List tasks. |
| GET | `/api/tasks/{id}` | Read match configuration and status. |
| POST | `/api/demos/{scenario}` | Create and queue a browser demo. |
| POST | `/api/tasks/{id}/run` | Queue the workflow and return `202`. |
| POST | `/api/tasks/{id}/cancel` | Request cooperative cancellation. |
| POST | `/api/tasks/{id}/retry` | Requeue a failed or cancelled task. |
| GET | `/api/tasks/{id}/status` | Read per-agent progress. |
| POST | `/api/uploads` | Upload and preview CSV/JSON/MediaCrawler data. |
| PATCH | `/api/uploads/{id}/mapping` | Validate canonical field mapping. |
| GET | `/api/tasks/{id}/quality` | Read sample quality metrics. |
| GET | `/api/tasks/{id}/comments` | Read annotated comments. |
| GET | `/api/tasks/{id}/sentiment` | Read sentiment distribution. |
| GET | `/api/tasks/{id}/clusters` | Read topic clusters. |
| GET | `/api/tasks/{id}/wordclouds` | Read weighted word-cloud data. |
| GET | `/api/tasks/{id}/insights` | Read contextual match insights. |
| GET | `/api/tasks/{id}/strategy-cards` | Read evidence-backed cards. |
| GET | `/api/strategy-cards/{id}/export` | Download one card as JSON. |
| POST | `/api/strategy-cards/{id}/ab-test-drafts` | Persist an A/B draft. |
| GET | `/api/tasks/{id}/report/markdown` | Export the report. |
| GET | `/api/media/proxy?url=...` | Display allowlisted public Hupu CDN images with hotlink-safe headers. |

`POST /api/tasks` accepts match fields documented in the root README. `domain` must be `basketball` or `football`; the backend always normalizes `platforms` to `["hupu"]`.

Task states are `created`, `queued`, `running`, `completed`, `failed`, and `cancelled`. Every uncaught workflow error is persisted in `error_message`; progress entries contain status, elapsed milliseconds, input/output summaries, and the current Agent error.

For uploads, send multipart fields `file` and `source_kind`. Bind the returned `upload_id` when creating a task. Browser clients never need the generated `stored_path`.

Image controls:

- `enable_image_analysis`: enable structured analysis of selected source-context images.
- `max_image_comments`: total main-post/news/official image budget sent to the vision model, from 0 to 20. The legacy field name is retained for API compatibility.
- `GET /api/tasks/{id}/insights` returns `context_media` with source URL, authority level, selection reasons, OCR, data points, confidence, and inclusion status.
- Reply images are never returned as evidence or sent to the vision model.
