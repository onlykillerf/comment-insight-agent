# Focused Sports Refactor Validation

Validation date: 2026-06-27
Repository: `onlykillerf/comment-insight-agent`
Scope: Hupu basketball/football match-opinion refactor

## Environment

- Windows / PowerShell
- Python 3.12.10
- Node.js 20.20.2
- Next.js 15.5.19
- SQLite local database
- MockLLM for reproducible demos

## Commands And Results

### Backend

```text
python -m pytest
10 passed in 28.24s
```

Coverage includes:

- Hupu `__NEXT_DATA__` page parsing
- Hupu URL validation
- news article extraction
- private/local news URL rejection
- basketball and football taxonomy classification
- data quality metrics and small-sample warning
- full workflow without strategy-card output

### Frontend

```text
npx tsc --noEmit
passed

npm run build
compiled successfully
```

Generated routes:

```text
/
/dashboard
/tasks/new
/tasks/[id]
/tasks/[id]/report
```

The previous `/strategy-cards` route is absent.

### Dependency Audit

```text
npm audit --audit-level=high
found 0 vulnerabilities
```

### Demo Scenarios

```text
python backend/scripts/run_demo_task.py --scenario nba_game
raw=320, deduped=145, confidence=medium, clusters=6, news_context=1

python backend/scripts/run_demo_task.py --scenario world_cup_game
raw=320, deduped=134, confidence=medium, clusters=6, news_context=1
```

Both demos generated sentiment, sports labels, clusters, three word clouds, representative comments, contextual insight, and Markdown reports.

### Real Hupu Connectivity

A bounded live check against one public Hupu post requested five comments:

```text
count=5
unique=5
source=hupu_public
```

No login cookies, private API, CAPTCHA handling, or permission bypass was used.

### Browser Validation

Playwright checked:

- Dashboard
- New Match Analysis
- Task Status
- Analysis Report

All returned HTTP 200 with no console errors, failed requests, or HTTP errors. Results are stored in ignored local logs; screenshots are committed under `docs/assets/`.

## Product Boundary Check

- Public UI exposes only basketball and football.
- Platform is normalized to Hupu.
- Tasks are organized by board and specific match.
- Optional news URLs/manual context are available.
- News facts and sampled fan opinions are separated.
- Strategy cards and A/B testing are removed from workflow, API, storage writes, frontend, demos, and docs.
- Existing SQLite files may retain legacy columns/tables for compatibility, but they are not read or written by the current workflow.

## Verdict

**Pass: ready for the focused sports release.**
