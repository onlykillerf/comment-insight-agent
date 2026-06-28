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

## Source Image Quality

- reply images are absent from normalized comments and provider requests
- each image remains traceable to its original post, news page, or official URL
- repeated image URLs do not trigger repeated multimodal calls
- player portraits, reaction media, and in-progress scoreboard screenshots are excluded
- visual evidence never enters comment clusters or word clouds
- OCR and visual summaries are manually spot-checked against the image
- per-source-image errors do not fail the complete task

## Engineering

- offline demo runs without API keys
- Hupu parser tests use fixtures, not live network
- backend tests and frontend production build pass
- API and frontend types stay aligned
- configured source-image cap is respected in real runs
- browser demo reaches a completed report without a CLI script
- upload preview and mapping reject missing comment content
- workflow exceptions persist `failed` and `error_message`
- task status polling exposes non-zero Agent duration and summaries
- label, cluster, and keyword clicks filter traceable comments
- strategy-card evidence IDs exist in the task sample and ratios match real counts
