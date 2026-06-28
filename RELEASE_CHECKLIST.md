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
- [x] Informative main-post/news/official images analyzed with SiliconFlow `Qwen/Qwen3.5-4B`; reply images ignored.
- [x] Explicit outcome contradictions filtered before insight persistence.
- [x] Strategy cards removed.
- [x] A/B testing removed.

## Demo

- [x] `nba_game` with 320 synthetic comments.
- [x] `world_cup_game` with 320 synthetic comments.
- [x] Both scenarios run without a real API key.

## Verification

- [x] Backend: 24 tests passed.
- [x] Frontend: TypeScript passed.
- [x] Frontend: production build passed.
- [x] npm audit: 0 vulnerabilities.
- [x] OpenAPI contains no strategy endpoint.
- [x] Browser validation: Dashboard, New Task, Task Status, and real Analysis Report returned 200 with no console/request errors.
- [x] Source-image display uses the allowlisted Hupu proxy with source links and confidence metadata.
- [x] Real public Hupu task: 39 comments / 36 deduplicated comments sampled across five selected threads; all persisted sources are `bbs.hupu.com`.
- [x] Real source-image run: reply image count is zero; four main-post candidates were reviewed independently.
- [x] Visual grounding audit: one player portrait and three in-progress scoreboard screenshots were excluded; zero images were forced into the summary.
- [x] Real task output includes Markdown image-screening traceability and a low-sample warning.

## Compliance

- [x] User-selected public pages only.
- [x] No login, CAPTCHA, private API, or anti-bot bypass.
- [x] Author identifiers are hashed.
- [x] Private/local news URLs are rejected.
- [x] Local `.env`, database, browser profiles, and runtime logs remain ignored.

## Verdict

**Ready for focused sports release.**
