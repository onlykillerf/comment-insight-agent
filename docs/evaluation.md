# Evaluation

## Collection Quality

- selected threads belong to the intended match and board
- parser conversion accuracy for content, lights, replies, and time
- no duplicate floors across highlighted and paginated replies
- no usernames or private profile fields in persisted output

## Data Quality

- clean ratio
- duplicate ratio
- noise ratio
- sample size and confidence level
- cross-thread coverage for the same match

## Sentiment and Sports Labels

- manual spot check of at least 30 comments per sport
- positive/neutral/negative distribution sanity check
- basketball and football label precision
- referee-questioning and humor stance confusion checks

## Clustering

- cluster coherence
- representative-comment quality
- noise ratio
- whether one large controversy hides smaller tactical themes

## News Context Grounding

- article title/body extraction accuracy
- news facts clearly separated from sampled opinions
- context alignment supported by provided text
- fact/opinion gaps stated when evidence is incomplete
- no claims based on failed news fetches
- explicit winner/loser contradictions are removed by the outcome guardrail

## Comment Image Quality

- public image URL remains traceable to its source comment
- repeated image URLs do not trigger repeated multimodal calls
- low/unrelated images do not enter clusters or word clouds
- OCR and visual summaries are manually spot-checked against the image
- per-image errors do not fail the complete task

## Engineering

- offline demo runs without API keys
- Hupu parser tests use fixtures, not live network
- backend tests and frontend production build pass
- API and frontend types stay aligned
- configured image cap is respected in real runs
