# Evaluation

This project should be evaluated as a decision-support system, not only as a sentiment classifier.

## Data Quality

Metrics:

- `clean_ratio = clean_count / raw_count`
- `duplicate_ratio`
- `noise_ratio`
- language distribution
- sample confidence level

Checks:

- Are low-quality comments filtered?
- Are duplicates marked?
- Is the sample large enough for the report claims?
- Is the warning visible when `dedup_count < 100`?

## Sentiment Quality

Methods:

- Manual spot check 30 comments per scenario.
- Label distribution sanity check.
- Compare strong sentiment comments with representative comments.
- Track confusion between jokes, sarcasm, and true negative feedback.

## Clustering Quality

Metrics:

- cluster coherence
- representative comment quality
- noise ratio
- dominant-cluster ratio

Checks:

- Do top keywords describe the cluster?
- Are noise comments truly low signal?
- Does one huge cluster hide smaller themes?

## Strategy Card Quality

Metrics:

- evidence coverage
- affected ratio correctness
- confidence calibration
- actionability
- hallucination check

Checks:

- Does every card have real evidence comments?
- Is `affected_ratio` computed from real counts?
- Is confidence downgraded for small samples?
- Are suggested actions domain-specific?
- Did the LLM invent evidence? It should not.

## Engineering Quality

Checks:

- One-command demo works.
- Backend tests pass.
- Frontend build passes.
- API schemas match frontend types.
- README commands are accurate.
- Demo datasets are reproducible.
- CI runs on pull requests.

## Frontend Usability

Checks:

- Can a new user understand the project in one minute?
- Can they run a demo in five minutes?
- Can they see evidence, confidence, and next actions in ten minutes?
- Are warnings visible without digging?
