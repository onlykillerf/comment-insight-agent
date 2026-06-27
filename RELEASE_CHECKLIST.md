# Focused Sports Release Checklist

Date: 2026-06-27
Target: focused Hupu sports release

## Product

- [x] Scope limited to basketball and football.
- [x] Match-first fields: board, teams, stage, date, and thread URLs.
- [x] Public Hupu thread connector implemented and live-checked.
- [x] Original thread context preserved with comments.
- [x] Optional public-news and manual context supported.
- [x] News facts separated from fan opinions.
- [x] Public comment images parsed and analyzed with SiliconFlow `Qwen/Qwen3.5-4B`.
- [x] Explicit outcome contradictions filtered before insight persistence.
- [x] Strategy cards removed.
- [x] A/B testing removed.

## Demo

- [x] `nba_game` with 320 synthetic comments.
- [x] `world_cup_game` with 320 synthetic comments.
- [x] Both scenarios run without a real API key.

## Verification

- [x] Backend: 20 tests passed.
- [x] Frontend: TypeScript passed.
- [x] Frontend: production build passed.
- [x] npm audit: 0 vulnerabilities.
- [x] OpenAPI contains no strategy endpoint.
- [x] Browser validation: Dashboard, New Task, Task Status, and real Analysis Report returned 200 with no console/request errors.
- [x] Image display: 7 report image elements loaded through the allowlisted proxy; 0 broken images.
- [x] Real public Hupu task: 60 comments collected from four user-selected thread URLs, all persisted sources are `bbs.hupu.com`.
- [x] Real image run: 17 image-bearing comments found; 6 unique images analyzed successfully; low/unrelated images excluded from NLP enrichment.
- [x] Real task output: 57 deduplicated comments, 6 clusters, Markdown report, and low-sample warning.

## Compliance

- [x] User-selected public pages only.
- [x] No login, CAPTCHA, private API, or anti-bot bypass.
- [x] Author identifiers are hashed.
- [x] Private/local news URLs are rejected.
- [x] Local `.env`, database, browser profiles, and runtime logs remain ignored.

## Verdict

**Ready for focused sports release.**
