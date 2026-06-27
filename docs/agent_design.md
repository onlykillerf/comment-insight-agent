# Agent Design

The workflow is implemented in `backend/app/workflows/comment_analysis_graph.py`.

## Workflow State

The workflow state is a dictionary with these major keys:

- `task`
- `config`
- `connector_plans`
- `raw_comments`
- `comments`
- `data_quality_report`
- `positive_attributions`
- `painpoints`
- `clusters`
- `representatives`
- `insight_report`
- `strategy_cards`
- `visualizations`
- `summary`
- `agent_progress`

`agent_progress` stores status, duration, error, input summary, and output summary for the task status page.

## Agents

| Agent | Input | Output | Responsibility |
| --- | --- | --- | --- |
| `TaskUnderstandingAgent` | `Task` model | `config` | Normalize user task settings. |
| `PlatformRouterAgent` | `config` | `connector_plans` | Select connector and build fetch requests. |
| `CommentCrawlerAgent` | `connector_plans` | `raw_comments` | Import or collect normalized public/sample comments. |
| `DataCleaningAgent` | `raw_comments` | `comments` | Normalize text, filter ads/noise, detect language. |
| `DeduplicationAgent` | `comments` | `comments` with duplicate flags and embeddings | Identify near-duplicate comments. |
| `DataQualityAgent` | `raw_comments`, `comments` | `data_quality_report` | Compute raw, clean, deduped, duplicate, noise, language, sample confidence. |
| `SentimentAgent` | `comments` | sentiment annotations | Rule-based sentiment baseline. |
| `PositiveAttributionAgent` | positive comments + taxonomy | positive attribution annotations | Explain positive drivers. |
| `PainPointAgent` | negative comments + taxonomy | pain point annotations | Explain negative drivers. |
| `ClusteringAgent` | annotated comments | clusters + `cluster_id` on comments | HDBSCAN/KMeans/rule fallback clustering with noise cluster. |
| `RepresentativeSamplerAgent` | comments + clusters | representative comments | Select high-signal comments per cluster. |
| `InsightGenerationAgent` | structured workflow state | insight report | Summarize structured analysis with MockLLM or provider. |
| `StrategyCardAgent` | quality + labels + evidence | strategy cards | Generate evidence-grounded actions and A/B ideas. |
| `VisualizationAgent` | workflow state | chart payloads | Build chart and word-cloud data. |

## Failure And Fallback

- LangGraph unavailable: workflow falls back to sequential execution.
- LLM provider missing or failing: MockLLM or provider-error summary is returned.
- HDBSCAN missing: KMeans fallback is used.
- Small sample: `DataQualityReport.sample_confidence_level=low` and strategy confidence is downgraded.
- Evidence missing: strategy cards are not generated.

## Adding A New Agent

1. Add a class under `backend/app/agents/`.
2. Implement `run(...)`.
3. Add it to `CommentAnalysisGraph.__init__`.
4. Insert a timed workflow node.
5. Store output in workflow state.
6. Add persistence/API/frontend support if the output should be visible.

Keep the agent contract narrow: one input responsibility, one output responsibility, and no hidden database writes inside the agent.
