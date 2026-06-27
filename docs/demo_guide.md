# Demo Guide

The project includes three reproducible demo scenarios.

## Generate Data

```bash
python backend/scripts/seed_demo_data.py
```

Files:

- `data/demo/nba_draft_comments.csv`
- `data/demo/iaa_game_comments.csv`
- `data/demo/news_event_comments.csv`

Each file has at least 300 synthetic comments with positive, neutral, and negative examples.

## Run Demos

```bash
python backend/scripts/run_demo_task.py --scenario nba_draft
python backend/scripts/run_demo_task.py --scenario iaa_game
python backend/scripts/run_demo_task.py --scenario news_event
```

The script prints:

- task id
- summary
- report URL
- Markdown export URL

## Expected Outputs

Every demo should generate:

- DataQualityReport
- sentiment distribution
- positive and negative taxonomy labels
- topic clusters and noise cluster
- representative comments
- LLM or MockLLM insight summary
- evidence-grounded strategy cards
- TF-IDF word clouds
- Markdown report

## Scenario Details

### NBA Draft

Focus:

- prospect hype
- draft-order debate
- player templates
- team fit
- fan disagreement

### IAA Game

Focus:

- forced ads
- ad frequency
- lag/heat
- payment pressure
- retention risk
- reward feedback

### News Event

Focus:

- information transparency
- stance controversy
- trust risk
- emotional polarization
- clarification needs

## Common Issues

### The report says sample confidence is low

This is expected for small samples. Increase `--max-comments` or use the 300+ demo CSVs.

### The LLM summary is mock

By default, demo tasks use MockLLM to avoid consuming API credits. Add `--real-llm` to use your configured provider.

### Strategy cards are fewer than expected

Cards require at least two real evidence comments. The system intentionally does not generate unsupported cards.
