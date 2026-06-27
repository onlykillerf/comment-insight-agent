# API

Base URL: `http://localhost:8000`

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/api/tasks` | Create a match analysis task. |
| GET | `/api/tasks` | List tasks. |
| GET | `/api/tasks/{id}` | Read match configuration and status. |
| POST | `/api/tasks/{id}/run` | Run the workflow. |
| GET | `/api/tasks/{id}/status` | Read per-agent progress. |
| GET | `/api/tasks/{id}/quality` | Read sample quality metrics. |
| GET | `/api/tasks/{id}/comments` | Read annotated comments. |
| GET | `/api/tasks/{id}/sentiment` | Read sentiment distribution. |
| GET | `/api/tasks/{id}/clusters` | Read topic clusters. |
| GET | `/api/tasks/{id}/wordclouds` | Read weighted word-cloud data. |
| GET | `/api/tasks/{id}/insights` | Read contextual match insights. |
| GET | `/api/tasks/{id}/report/markdown` | Export the report. |
| GET | `/api/media/proxy?url=...` | Display allowlisted public Hupu CDN images with hotlink-safe headers. |

`POST /api/tasks` accepts match fields documented in the root README. `domain` must be `basketball` or `football`; the backend always normalizes `platforms` to `["hupu"]`.

Image controls:

- `enable_image_analysis`: enable structured analysis of selected source-context images.
- `max_image_comments`: total main-post/news/official image budget sent to the vision model, from 0 to 20. The legacy field name is retained for API compatibility.
- `GET /api/tasks/{id}/insights` returns `context_media` with source URL, authority level, selection reasons, OCR, data points, confidence, and inclusion status.
- Reply images are never returned as evidence or sent to the vision model.
