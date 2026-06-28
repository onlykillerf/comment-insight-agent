# Demo Guide

## Browser Demo

Start the API and frontend, open `http://localhost:3000`, then click **一键运行 Demo** on either sports scenario. The task enters `queued`, the status page refreshes automatically, and the report link becomes available after completion. This path uses Mock data and MockLLM by default.

## Seed Data

```bash
python backend/scripts/seed_demo_data.py --scenario all
```

This creates:

- `data/demo/nba_game_comments.csv`
- `data/demo/world_cup_game_comments.csv`

Each dataset contains 320 synthetic Hupu-style comments about one match.

## Run Basketball Demo

```bash
python backend/scripts/run_demo_task.py --scenario nba_game
```

## Run Football Demo

```bash
python backend/scripts/run_demo_task.py --scenario world_cup_game
```

Both CLI demos use MockLLM unless `--real-llm` is passed. Expected output includes data quality, sentiment, sports labels, clusters, word clouds, representative comments, contextual insight, evidence-backed strategy cards, and a Markdown report.

## Real Hupu Run

Use the web Wizard and choose `虎扑公开帖子`, or submit the API payload shown in the root README. A real run requires at least one public Hupu thread URL. Add a manual match brief when no stable public news page is available.

For CSV, JSON, JSONL, or MediaCrawler exports, choose the matching upload mode. Confirm the auto-detected comment-content field and inspect the preview before continuing.

With SiliconFlow configured, enable source-image analysis and keep the default limit of six. The workflow ignores reply images, scores main-post/news/official images for information value, analyzes them one by one, and only includes results that pass both relevance and information-value thresholds.

## Troubleshooting

- **Small sample warning**: add more relevant match threads, not unrelated board pages.
- **Hupu returns an error**: do not work around platform controls; use CSV/JSON import.
- **News extraction is empty**: paste a concise manual background summary.
- **LLM unavailable**: MockLLM keeps the rest of the workflow runnable.
- **Task fails**: the status page shows the failing Agent and `error_message`; fix the input and click retry.
- **One image fails**: the error is recorded on that source item; a single transient request is retried and the task continues.
- **No image appears in the report**: the selected posts may contain only player photos, reaction media, or in-progress scoreboard screenshots; these are intentionally excluded.
