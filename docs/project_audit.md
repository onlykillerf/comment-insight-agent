# Product Focus Audit

## Diagnosis

The first release had a wide cross-platform, multi-domain positioning. It exposed game, esports, sports, news, and draft taxonomies while its real collection support remained uneven. Strategy cards and A/B ideas added output volume without improving the core reliability of match-opinion analysis.

## Refocused Product

The repository now focuses on one workflow:

1. choose basketball or football
2. choose a Hupu board
3. define one match
4. select relevant public Hupu threads
5. optionally provide public news context
6. analyze sample quality, sentiment, topics, and representative opinions
7. compare fan opinions with the supplied factual background
8. inspect a bounded set of main-post, data, news, and official images while ignoring reply media

## Removed Surface Area

- game, IAA game, esports, general-news, and NBA-draft product modes
- strategy cards and A/B testing output
- multi-platform UI and platform comparison claims
- XHS-specific collection scripts and MediaCrawler product routing
- dedicated strategy-card page and API

## Remaining Risks

- Hupu can change public page structure or deny automated requests.
- One or two threads may overrepresent a fan group or a high-light controversy.
- Rule-based sentiment and sports labels require ongoing manual evaluation.
- Public news pages vary widely in extraction quality.
- Source images are still model-interpreted evidence; source authority, information value, and confidence must remain visible.
- Existing local SQLite files retain legacy columns/tables for compatibility, but new workflows do not read or write strategy cards.

## Next Priorities

1. Build a fixture library covering more Hupu thread layouts.
2. Add match-level sampling diagnostics across multiple threads.
3. Add manual label correction and evaluation export.
4. Improve news-source provenance and citation display.
