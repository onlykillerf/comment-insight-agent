# Demo Guide

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

Both demos use MockLLM unless `--real-llm` is passed. Expected output includes data quality, sentiment, sports labels, clusters, word clouds, representative comments, contextual insight, and a Markdown report.

## Real Hupu Run

Use the web task form and choose `Hupu public threads`, or submit the API payload shown in the root README. A real run requires at least one public Hupu thread URL. Add a manual match brief when no stable public news page is available.

With SiliconFlow configured, enable comment-image analysis and keep the default limit of six. The workflow deduplicates image URLs, records each model result, and only injects `high`/`medium` relevance summaries into text analysis.

## Troubleshooting

- **Small sample warning**: add more relevant match threads, not unrelated board pages.
- **Hupu returns an error**: do not work around platform controls; use CSV/JSON import.
- **News extraction is empty**: paste a concise manual background summary.
- **LLM unavailable**: MockLLM keeps the rest of the workflow runnable.
- **One image fails**: the error is recorded on that comment; a single transient request is retried and the task continues.
