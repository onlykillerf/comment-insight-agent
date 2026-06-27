# Project Audit

This audit reviews the current repository as an open-source project, not as a course demo.

## 1. Completed Capabilities

- Backend FastAPI service exists in `backend/app/main.py` with task, report, and health routes.
- SQLAlchemy models in `backend/app/models/records.py` persist tasks, raw comments, clean comments, embeddings, sentiment, pain points, positive attribution, clusters, representatives, insight reports, strategy cards, and `DataQualityReport`.
- The workflow in `backend/app/workflows/comment_analysis_graph.py` runs the full chain from task understanding to visualization.
- Connectors support mock, CSV, JSON, MediaCrawler exports, and a local MediaCrawler adapter.
- Frontend pages exist for dashboard, task creation, task status, report, and strategy cards.
- Report page shows sentiment, clusters, positive/negative labels, TF-IDF word clouds, representative comments, data quality, and strategy cards.
- Strategy cards include evidence comments, affected ratio, confidence, confidence reason, and A/B test design.
- Demo scripts exist under `backend/scripts/` and now support three scenarios.

## 2. Parts That Still Feel Like a Demo

- The workflow runs synchronously in `run_and_store_task`, which is okay for demos but not production workloads.
- Some NLP components are rule-based. They are transparent and testable, but should be framed as a baseline.
- Vector storage is a local facade and not yet a production Qdrant integration.
- MediaCrawler integration is an adapter/import layer, not a managed collection service.
- The frontend has no authentication, workspace model, saved comparisons, or report sharing.

## 3. Main GitHub Star Blockers

- README first screen previously did not communicate the project in one minute.
- Demo data was not large or standardized enough for a convincing open-source showcase.
- Docs did not explain how to extend connectors, taxonomies, agents, or LLM providers.
- GitHub project hygiene was incomplete: license, contribution guide, issue templates, PR template, and CI were missing or incomplete.
- The old UI copy contained garbled text in several pages, which damaged trust immediately.

## 4. Backend Engineering Gaps

- No Alembic migration layer; `database.py` uses local additive SQLite upgrades for MVP convenience.
- Workflow execution is synchronous and should become async with Celery/RQ/Arq for long-running crawls.
- Agent state is a plain dictionary. It is flexible but needs stronger typed contracts.
- LLM prompts still need stronger automated evaluation and hallucination checks.
- Classification and clustering are transparent baselines but not benchmarked against labeled data.

## 5. Frontend Experience Gaps

- Dashboard needed a stronger product-oriented hero and demo scenario cards.
- Task status needed better input/output summaries for each agent.
- Report page needed an executive summary and a clearer data quality panel.
- Strategy card page needed to act as a showcase of evidence, confidence, expected impact, and A/B design.
- There is no empty-state path that creates and runs a demo task from the browser yet.

## 6. Agent Workflow Gaps

- `CommentAnalysisGraph` is LangGraph-compatible but still falls back to sequential execution.
- Failure handling is task-level, not per-agent retry with compensating actions.
- No formal evaluation step exists between LLM insight and strategy generation.
- Stance analysis is lightweight and rule-based.
- DataQuality is computed, but quality thresholds should eventually be configurable per domain.

## 7. Data Trustworthiness Gaps

- Small samples are now flagged, but report consumers still need guidance on interpreting low-confidence cards.
- Noise cluster ratio can be high for real social data; this is good to expose but should be accompanied by sampling guidance.
- Demo datasets are synthetic. They are useful for reproducibility but should be clearly labeled.
- There is no human spot-check UI for sentiment or taxonomy labels.

## 8. README And Documentation Gaps

- Previous README mixed implementation notes with garbled text and did not sell the project.
- Architecture, Agent design, connectors, taxonomy, strategy cards, demos, and evaluation needed separate docs.
- Extension instructions were not discoverable enough for fork-oriented developers.

## 9. Demo Data Gaps

- Existing sample files were small and scenario-specific.
- Demo data did not consistently include required normalized fields.
- There were not three complete demo scenarios with 300+ rows each.
- Synthetic generation needed enough variation to avoid obvious template repetition.

## 10. Three-Stage Optimization Roadmap

### Stage 1: Star-ready Local Demo

- Rewrite README and docs.
- Add three 300+ row demo datasets.
- Keep MockLLM as the default demo path.
- Make task status and report pages explain quality, evidence, and confidence.
- Add GitHub issue templates, PR template, license, and CI.

### Stage 2: Developer Extension Kit

- Add typed workflow state objects.
- Add connector SDK examples.
- Add taxonomy validation tests.
- Add LLM provider examples and prompt tests.
- Add better fixture-based integration tests.

### Stage 3: Trust And Evaluation

- Add manual review workflow for sentiment/taxonomy labels.
- Add clustering coherence evaluation.
- Add hallucination checks for insight and strategy cards.
- Add historical report comparison.
- Add async task queue and production database migrations.
