# Agent Design

| Agent | Input | Output | Responsibility |
| --- | --- | --- | --- |
| `TaskUnderstandingAgent` | task model | normalized match config | Restrict sport to basketball/football and platform to Hupu. |
| `PlatformRouterAgent` | config | connector plans | Choose Mock, Hupu public page, uploaded CSV/JSON, or MediaCrawler export. |
| `CommentCrawlerAgent` | connector plans | RawComment dictionaries | Collect or import bounded comments. |
| `MediaUnderstandingAgent` | main-post metadata + news context + task limit | source-level visual evidence | Select data/official images, ignore reply media, and analyze each image with `Qwen/Qwen3.5-4B`. |
| `NewsContextAgent` | manual brief + public URLs | bounded context items | Extract optional factual background without failing the comment run. |
| `DataCleaningAgent` | raw comments | cleaned comments | Normalize text and filter low-quality rows. |
| `DeduplicationAgent` | cleaned comments | duplicate annotations | Reduce repeated comments and copies. |
| `DataQualityService` | raw + clean comments | quality report | Bound interpretation with sample metrics. |
| `SentimentAgent` | clean comments | sentiment labels/scores | Estimate positive, neutral, and negative distribution. |
| attribution agents | sentiment + sport taxonomy | sport labels and stance | Explain praise and criticism using match-specific labels. |
| `ClusteringAgent` | annotated comments | topic clusters | Use HDBSCAN, KMeans, or rules with an explicit noise cluster. |
| `RepresentativeSamplerAgent` | comments + clusters | traceable examples | Select high-signal comments per topic. |
| `InsightGenerationAgent` | structured analysis + visual evidence + news context | insight report | Summarize viewpoints, compare context, and filter explicit outcome contradictions. |
| `VisualizationAgent` | structured outputs | chart payload | Build sentiment, label, cluster, and word-cloud data. |

## State Flow

```text
understand → route → crawl → context → media → clean → dedup → quality
→ sentiment → attribute → cluster → sample → insight → visualize
```

Each step records status, duration, input summary, output summary, and error details. If LangGraph is unavailable, the same nodes run sequentially.

`POST /run` queues work and returns immediately. The frontend polls persistent task state while queued or running. Cancellation is cooperative between Agents; any uncaught exception updates the task to `failed` with a bounded error message.

## Failure Behavior

- Hupu parser failure: task fails with a clear public-page parsing error; use CSV/JSON fallback.
- Individual news failure: stored as a context error; comment analysis continues.
- Individual source-image failure: recorded on that source item; the remaining analysis continues. One transient transport retry is allowed.
- Low/unrelated image: stored for audit but excluded from the final contextual insight.
- Reply image: never collected or sent to the vision provider.
- LLM failure: returns a provider error insight while deterministic analysis remains available.
- Small samples: confidence is lowered and the report shows a warning.
- Process restart: stale queued/running tasks are marked failed and can be retried.
