# Product Focus Audit

## Diagnosis

The first release had a wide cross-platform, multi-domain positioning. It exposed game, esports, sports, news, and draft taxonomies while its real collection support remained uneven. Early strategy output lacked reliable evidence binding; the current implementation only persists cards derived from classified comments and actual counts.

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
9. inspect evidence-backed action cards and optionally create an A/B draft

## Removed Surface Area

- game, IAA game, esports, general-news, and NBA-draft product modes
- multi-platform UI and platform comparison claims
- XHS-specific collection scripts and direct MediaCrawler crawling
- dedicated global strategy-card page; cards now live inside each report

## Remaining Risks

- Hupu can change public page structure or deny automated requests.
- One or two threads may overrepresent a fan group or a high-light controversy.
- Rule-based sentiment and sports labels require ongoing manual evaluation.
- Public news pages vary widely in extraction quality.
- Source images are still model-interpreted evidence; source authority, information value, and confidence must remain visible.
- The v0.1 in-process queue supports one API replica; horizontal deployment needs an external worker queue.

## Next Priorities

1. Build a fixture library covering more Hupu thread layouts.
2. Add match-level sampling diagnostics across multiple threads.
3. Add manual label correction and evaluation export.
4. Improve news-source provenance and citation display.
5. Calibrate strategy-card confidence against human review.
