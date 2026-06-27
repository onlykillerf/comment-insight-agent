# Clean Clone Validation

Validation date: 2026-06-26  
Validation mode: GitHub user clean-clone acceptance test  
Source project: `D:\IT_items\paper\实践学习\comment-insight-agent`  
Clean validation copy: `D:\IT_items\paper\clean-clone-validation-20260626-221722\comment-insight-agent`

## 1. Validation Environment

| Item | Result |
| --- | --- |
| OS / Shell | Windows / PowerShell |
| Python | `Python 3.12.10` |
| Node.js | `v18.16.1` |
| npm | `9.5.1` |
| Docker CLI | `Docker version 26.0.0` |
| Docker Compose | `v2.26.1-desktop.1` |
| Docker daemon | Failed, daemon was not running |
| Git CLI | Failed, `git` command was not available |
| Browser for screenshots | `C:\Program Files\Google\Chrome\Application\chrome.exe` |
| LLM mode | `LLM_PROVIDER=mock` from `.env.example` |
| Database | Fresh SQLite file created from clean copy |

Clean copy was created by copying the project into a new directory and excluding local state:

- Excluded files: `.env`, `comment_insight.db`, `*.db`, `*.sqlite`, `*.sqlite3`
- Excluded directories: `.git`, `node_modules`, `.next`, `__pycache__`, `.pytest_cache`, `.browser-profiles`, `dist`, `build`

Initial clean-state checks:

```text
Test-Path .env                  -> False
Test-Path comment_insight.db    -> False
Test-Path frontend\node_modules -> False
Test-Path frontend\.next        -> False
Test-Path backend\.pytest_cache -> False
```

## 2. README Command Validation

| README command | Result | Output summary |
| --- | --- | --- |
| `git clone https://github.com/your-org/comment-insight-agent.git` | Failed in this environment | `git : The term 'git' is not recognized...` |
| `cd comment-insight-agent` | Passed via clean copy | Clean root entered successfully |
| `cp .env.example .env` | Passed | `.env` created. Defaults include `DATABASE_URL=sqlite:///./comment_insight.db`, `LLM_PROVIDER=mock`, `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` |
| `docker compose up -d` | Failed in this environment | Docker daemon was not running: `open //./pipe/docker_engine: The system cannot find the file specified.` |
| `cd backend` | Passed | Backend directory entered |
| `python -m pip install -e .[dev]` | Passed | Editable backend package built and installed. Many dependencies were already satisfied from the global Python environment |
| `uvicorn app.main:app --reload` | Passed | Uvicorn started from clean copy. `/api/health` returned `{"status":"ok","service":"comment-insight-agent"}` |
| `cd frontend` | Passed | Frontend directory entered |
| `npm install` | Passed with warnings | `added 438 packages`; npm reported `5 vulnerabilities (1 moderate, 4 high)` and several deprecated packages |
| `npm run dev` | Passed | Next.js served `http://localhost:3000`; homepage returned HTTP 200 |
| `python backend/scripts/seed_demo_data.py` | Passed | Wrote 320 rows for each demo CSV |
| `python backend/scripts/run_demo_task.py --scenario nba_draft` | Passed | Task #1 completed |
| `python backend/scripts/run_demo_task.py --scenario iaa_game` | Passed | Task #2 completed |
| `python backend/scripts/run_demo_task.py --scenario news_event` | Passed | Task #3 completed |

Notes:

- The README file itself is valid UTF-8. PowerShell displayed some Unicode symbols incorrectly in terminal output, but Python read the file correctly.
- `git clone` currently uses a placeholder URL, so a real GitHub user would need the final repository URL.
- The README Quick Start depends on Docker Desktop being started. The app still ran with SQLite and MockLLM after the Docker failure.

## 3. Demo Scenario Results

### NBA Draft

Command:

```bash
python backend/scripts/run_demo_task.py --scenario nba_draft
```

Output summary:

```text
Demo scenario `nba_draft` completed
Task #1
Summary: {'raw_count': 320, 'cleaned_count': 320, 'deduped_count': 222, 'sample_confidence_level': 'medium', 'cluster_count': 6, 'strategy_card_count': 5}
Report: http://127.0.0.1:3000/tasks/1/report
Markdown: http://127.0.0.1:8000/api/tasks/1/report/markdown
```

Generated artifacts:

- Sentiment distribution: positive 63, neutral 103, strong_positive 14, negative 42
- Topic clusters: 6
- Word clouds: all 60 words, positive 51 words, negative 21 words
- Representative comments: 18 cluster representative comments, 18 comments with `representative_reason`
- LLM insights: summary, positive insights, negative insights, platform differences, risks, recommendations all present
- Strategy cards: 5
- Markdown report: 6747 chars

### IAA Game

Command:

```bash
python backend/scripts/run_demo_task.py --scenario iaa_game
```

Output summary:

```text
Demo scenario `iaa_game` completed
Task #2
Summary: {'raw_count': 320, 'cleaned_count': 320, 'deduped_count': 240, 'sample_confidence_level': 'medium', 'cluster_count': 6, 'strategy_card_count': 5}
Report: http://127.0.0.1:3000/tasks/2/report
Markdown: http://127.0.0.1:8000/api/tasks/2/report/markdown
```

Generated artifacts:

- Sentiment distribution: positive 24, negative 92, strong_negative 41, neutral 83
- Topic clusters: 6
- Word clouds: all 60 words, positive 14 words, negative 53 words
- Representative comments: 18 cluster representative comments, 18 comments with `representative_reason`
- LLM insights: summary, positive insights, negative insights, platform differences, risks, recommendations all present
- Strategy cards: 5
- Markdown report: 6609 chars

### News Event

Command:

```bash
python backend/scripts/run_demo_task.py --scenario news_event
```

Output summary:

```text
Demo scenario `news_event` completed
Task #3
Summary: {'raw_count': 320, 'cleaned_count': 320, 'deduped_count': 219, 'sample_confidence_level': 'medium', 'cluster_count': 6, 'strategy_card_count': 3}
Report: http://127.0.0.1:3000/tasks/3/report
Markdown: http://127.0.0.1:8000/api/tasks/3/report/markdown
```

Generated artifacts:

- Sentiment distribution: neutral 137, negative 82
- Topic clusters: 6
- Word clouds: all 14 words, positive 2 words, negative 7 words
- Representative comments: 18 cluster representative comments, 18 comments with `representative_reason`
- LLM insights: summary, positive insights, negative insights, platform differences, risks, recommendations all present
- Strategy cards: 3
- Markdown report: 4588 chars

## 4. Strategy Card Evidence Validation

Structured validation checked every strategy card in the three completed tasks.

Rules checked:

- Every `evidence_comments` item appears in the task's real comment corpus.
- `affected_ratio` equals `evidence_count / sample_size`, rounded to one decimal place.
- `confidence` is present and paired with `confidence_reason`.
- Cards have at least 2 evidence comments.
- `ab_test_design` includes `control_group`, `experiment_group`, and `metrics`.

Result: passed for all 13 strategy cards.

Selected examples:

| Task | Card | Evidence count | Sample size | Affected ratio | Expected ratio | Confidence | Evidence matched |
| --- | --- | ---: | ---: | --- | ---: | --- | ---: |
| NBA Draft | `样本联赛含金量争议` | 14 | 222 | 6.3% | 6.3% | medium | 3/3 |
| NBA Draft | `适配球队需求` | 16 | 222 | 7.2% | 7.2% | medium | 3/3 |
| IAA Game | `强制广告打断` | 59 | 240 | 24.6% | 24.6% | high | 3/3 |
| IAA Game | `广告可接受度` | 2 | 240 | 0.8% | 0.8% | low | 2/2 |
| News Event | `立场争议` | 68 | 219 | 31.1% | 31.1% | high | 3/3 |
| News Event | `信任问题` | 14 | 219 | 6.4% | 6.4% | medium | 3/3 |

The confidence behavior is directionally correct in the output: low evidence cards are downgraded, medium evidence cards remain medium, and high evidence plus higher affected ratios can become high.

Structured validation log:

```text
validation_logs/structured_validation.json
failures: []
```

## 5. Frontend Page Validation

Screenshots were captured from the clean clone services.

| Page | URL | Status | Screenshot | Notes |
| --- | --- | ---: | --- | --- |
| Home / Dashboard | `http://localhost:3000/` | 200 | `validation_screenshots/home_dashboard.png` | Loads hero, scenario cards, recent tasks |
| New Task | `http://localhost:3000/tasks/new` | 200 | `validation_screenshots/new_task.png` | Loads task form and demo defaults |
| Task Status | `http://localhost:3000/tasks/1` | 200 | `validation_screenshots/task_status.png` | Shows Agent chain, status, duration, input/output summaries |
| Analysis Report | `http://localhost:3000/tasks/1/report` | 200 | `validation_screenshots/analysis_report_retry.png` | Loads executive summary, data quality panel, charts, word clouds, representative comments, strategy cards |
| Strategy Cards | `http://localhost:3000/strategy-cards` | 200 | `validation_screenshots/strategy_cards.png` | Shows cards with evidence count, affected ratio, confidence, actions, A/B tests |
| Dashboard route check | `http://localhost:3000/dashboard` | 404 | `validation_screenshots/dashboard_route_check.png` | There is no separate `/dashboard` route; dashboard content is on `/` |

Frontend observations:

- The first screenshot attempt for `/tasks/1/report` caught the page at `Loading...` during initial Next.js compilation/client fetch. A retry with explicit wait for `Executive Summary` loaded successfully.
- The home page produced a console 404 for a missing resource, likely favicon or a missing static asset. No React page errors were captured.
- `/dashboard` is not a route. README/navigation label says Dashboard but points to `/`.

## 6. GitHub Engineering Files

| File | Result | Summary |
| --- | --- | --- |
| `LICENSE` | Passed | MIT License present |
| `CONTRIBUTING.md` | Passed | Contribution guide present |
| `.gitignore` | Passed | Ignores `.env`, `node_modules`, `.next`, DB files, caches, logs |
| `.github/ISSUE_TEMPLATE/bug_report.md` | Passed | Present |
| `.github/ISSUE_TEMPLATE/feature_request.md` | Passed | Present |
| `.github/ISSUE_TEMPLATE/connector_request.md` | Passed | Present |
| `.github/pull_request_template.md` | Passed | Present |
| `.github/workflows/ci.yml` | Passed | Runs backend pytest and frontend build |

CI-equivalent local checks from the clean copy:

```text
python -m pytest
9 passed, 3 warnings in 3.76s
Warning: datetime.datetime.utcnow() is deprecated in mock_connector.py
```

```text
npm run build
Compiled successfully
Linting and checking validity of types ...
Generated static pages (6/6)
Routes included /, /strategy-cards, /tasks/[id], /tasks/[id]/report, /tasks/new
```

## 7. Passed Items

- Clean copy did not reuse `.env`, SQLite DB, `node_modules`, `.next`, pytest cache, or browser profiles.
- MockLLM default works without API keys.
- SQLite fallback works even when Docker daemon is unavailable.
- Backend starts from README command and `/api/health` returns OK.
- Frontend starts from README command and serves the UI.
- All three demo scenarios run end to end.
- Each demo produces sentiment distribution, topic clusters, word clouds, representative comments, LLM insights, strategy cards, and Markdown report.
- Strategy cards are evidence-grounded and ratio-checked against real counts.
- Frontend pages load for home/dashboard, task creation, task status, analysis report, and strategy cards.
- GitHub engineering files are present.
- Backend tests and frontend production build pass in the clean copy.

## 8. Failed Items

| Item | Severity | Detail |
| --- | --- | --- |
| README `git clone` command | Medium | `git` is not installed in the validation environment, and the README URL is still `your-org/comment-insight-agent.git` placeholder. A real published repo URL is needed. |
| README `docker compose up -d` command | Medium | Docker CLI exists, but daemon was not running, so the command failed. The app can still run with SQLite, but the README should clarify Docker is optional or requires Docker Desktop to be started. |
| Separate `/dashboard` route | Low | User-facing requirement mentions Dashboard. Current app uses `/` as Dashboard. Direct `/dashboard` returns 404. |
| npm audit | Medium | `npm install` reports 5 vulnerabilities: 1 moderate, 4 high. |
| Dependency warnings | Low | Several deprecated npm packages; Python tests warn about `datetime.utcnow()` deprecation. |
| New-user isolation | Low | README installs backend dependencies into the active global Python environment. A venv recommendation would make clean-start instructions safer. |

## 9. Remaining Issues

1. Replace README placeholder clone URL with the final GitHub repository URL before publishing.
2. Clarify that Docker services are optional for local SQLite demo mode, or document that Docker Desktop must be running.
3. Decide whether to add a real `/dashboard` route or rename the navigation label to avoid mismatch.
4. Review npm audit results before public release.
5. Add a venv-based backend setup path to README.
6. Replace `datetime.utcnow()` in `mock_connector.py` with timezone-aware datetime.
7. Optionally add a favicon/static asset check to remove the homepage 404 console noise.

## 10. Open-source Ready Verdict

Verdict: **Conditional pass**.

The project meets the core GitHub open-source readiness bar for a first public release candidate:

- A new user can run the app without real API keys.
- The three demo scenarios work end to end.
- Reports and strategy cards are evidence-grounded.
- Tests and frontend build pass.
- Documentation, license, contribution guide, templates, and CI are present.

It is not yet a perfect clean-clone experience because the README still contains a placeholder clone URL, Docker startup depends on a daemon that may not be running, npm audit reports vulnerabilities, and `/dashboard` is a label rather than a route. These are polish/release-readiness issues, not blockers for the core product demo.

