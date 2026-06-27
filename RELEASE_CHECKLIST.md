# Release Checklist: v0.1 Public Release

Date: 2026-06-26  
Release target: GitHub v0.1 public release  
Previous status: `Conditional pass` from `CLEAN_CLONE_VALIDATION.md`  
Current verdict: **Ready for v0.1 public release**

## Release Polish Fixes

### README Quick Start

- Replaced the placeholder clone URL with `https://github.com/onlykillerf/comment-insight-agent.git`.
- Added the public repository URL at the top of README.
- Reworked Quick Start into:
  - `Fast Local Demo, No Docker Required`
  - `Optional Full Stack Mode`
- Made SQLite + `MockLLM` the recommended default path.
- Added separate Windows PowerShell and macOS/Linux commands.
- Added Python venv setup:
  - `python -m venv .venv`
  - `.\.venv\Scripts\Activate.ps1`
  - `source .venv/bin/activate`
  - `python -m pip install -U pip`
  - `python -m pip install -e ".[dev]"`
- Clarified Docker Desktop must be running before `docker compose up -d`.
- Added prerequisites:
  - Python 3.11+
  - Node.js 20 LTS, recommended `>=20.19.0`
  - npm 10+
  - Git
  - Docker Desktop only for Full Stack Mode

### Frontend Release Polish

- Added `/dashboard` route that redirects to `/`.
- Added `frontend/src/app/icon.svg`.
- Added `frontend/public/favicon.ico`.
- Updated metadata icons in `frontend/src/app/layout.tsx`.
- Verified:
  - `/` returns 200
  - `/dashboard` returns 200 and redirects to `/`
  - `/favicon.ico` returns 200
  - `/icon.svg` returns 200
  - no HTTP 404 noise on homepage/dashboard browser check

### npm Audit

- Ran `npm audit`.
- Ran non-force `npm audit fix`.
- Did **not** use `npm audit fix --force`.
- Upgraded frontend dependencies within a verified path:
  - `next` to `15.5.19`
  - `eslint-config-next` to `15.5.19`
  - `postcss` to `8.5.10`
  - `eslint` to `8.57.1`
  - `antd` to `5.29.3`
  - `@ant-design/icons` to latest resolved version
- Added npm `overrides` for `postcss: 8.5.10` so nested PostCSS audit findings are resolved.
- Added frontend engine requirement:
  - Node `>=20.19.0`
  - npm `>=10.0.0`

Result:

```text
npm audit
found 0 vulnerabilities
```

### Backend Warning Fix

- Replaced `datetime.utcnow()` in `backend/app/connectors/mock_connector.py`.
- New code uses timezone-aware `datetime.now(timezone.utc)`.
- Pytest no longer emits the previous `datetime.utcnow()` deprecation warning.

## Verification Environment

| Item | Version |
| --- | --- |
| Python | `Python 3.12.10` |
| Node.js used for release verification | `v20.20.2` |
| Node path | `D:\it_base\node-v20.20.2-win-x64` |
| npm | `10.8.2` |
| LLM mode | `MockLLM` |
| Database | SQLite |

Note: the machine's older default Node was `v18.16.1`, which is too old for the security-patched Next.js 15 release line. Release validation was run with Node 20 from `D:\it_base`.

## Verification Commands

### Backend Tests

Command:

```bash
cd backend
python -m pytest
```

Result:

```text
collected 9 items
9 passed in 48.09s
```

### Frontend Audit, Build, Typecheck

Command:

```powershell
$env:Path='D:\it_base\node-v20.20.2-win-x64;' + $env:Path
cd frontend
npm audit
npm run build
npx tsc --noEmit
```

Result:

```text
node v20.20.2
npm audit -> found 0 vulnerabilities
next build -> Compiled successfully
static/dynamic routes generated: /, /dashboard, /icon.svg, /strategy-cards, /tasks/[id], /tasks/[id]/report, /tasks/new
npx tsc --noEmit -> passed
```

### Demo Scenarios

Commands:

```bash
python backend/scripts/run_demo_task.py --scenario nba_draft
python backend/scripts/run_demo_task.py --scenario iaa_game
python backend/scripts/run_demo_task.py --scenario news_event
```

Results:

| Scenario | Task | Raw | Clean | Dedup | Sample confidence | Clusters | Strategy cards |
| --- | ---: | ---: | ---: | ---: | --- | ---: | ---: |
| `nba_draft` | #8 | 320 | 320 | 222 | medium | 6 | 5 |
| `iaa_game` | #9 | 320 | 320 | 240 | medium | 6 | 5 |
| `news_event` | #10 | 320 | 320 | 219 | medium | 6 | 3 |

### Frontend Browser Check

Browser automation checked:

- `http://127.0.0.1:3000/`
- `http://127.0.0.1:3000/dashboard`
- `http://127.0.0.1:3000/favicon.ico`
- `http://127.0.0.1:3000/icon.svg`

Result summary:

```text
home: status 200, no HTTP errors
dashboard: status 200, final URL http://127.0.0.1:3000/, no HTTP errors
favicon.ico: status 200
icon.svg: status 200
```

Detailed log:

```text
release_logs/frontend_console_check_final.json
```

## Remaining Release Notes

- Public repository target confirmed as `onlykillerf/comment-insight-agent`.
- Local Git repository and authenticated HTTPS remote were configured on 2026-06-27.
- Docker remains optional for v0.1. The fast demo path does not require Docker.
- The project now expects Node.js 20 LTS for frontend development and CI parity.

## v0.1 Verdict

**Ready for v0.1 public release.**

The previous `Conditional pass` blockers have been addressed:

- clone URL no longer uses `your-org`
- Quick Start defaults to a Docker-free demo path
- backend install uses venv instructions
- `/dashboard` no longer returns 404
- npm audit reports 0 vulnerabilities
- Python datetime warning is gone
- favicon/static 404 is gone
- tests, build, typecheck, demo scenarios, and browser checks pass
