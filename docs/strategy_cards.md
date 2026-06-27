# Strategy Cards

Strategy cards are the main product output. They turn comment analysis into action.

Implementation: `backend/app/agents/strategy_card_agent.py`

## Fields

- `title`: concise action/risk/opportunity name.
- `type`: `problem_fix`, `opportunity_amplification`, `risk_explanation`, or future `ab_test`.
- `priority`: `high`, `medium`, or `low`.
- `problem_or_opportunity`: evidence-grounded explanation.
- `evidence_comments`: representative real comments.
- `evidence_count`: number of comments classified into the theme.
- `sample_size`: deduplicated sample size.
- `affected_ratio`: `evidence_count / sample_size`.
- `confidence`: `high`, `medium`, or `low`.
- `confidence_reason`: why the confidence was assigned.
- `suggested_actions`: concrete domain-specific actions.
- `expected_impact`: expected business/content/community impact.
- `ab_test_design`: control group, experiment group, and metrics.

## affected_ratio

`affected_ratio` is calculated from real classification counts:

```text
affected_ratio = evidence_count / sample_size
```

It is never manually invented.

## confidence

Confidence uses:

- `evidence_count`
- `sample_size`
- `affected_ratio`
- sentiment concentration
- small-sample downgrade

Rules:

- `sample_size < 100` always downgrades to low confidence.
- fewer than two evidence comments means no card is generated.
- high confidence requires strong evidence volume, ratio, and sentiment concentration.
- medium confidence means evidence is real but not yet strong enough.

## A/B Test Design

A/B design is domain-specific:

- NBA draft: content explainer vs generic draft news.
- IAA game: product flow/copy experiment vs current flow.
- News: clarification-first framing vs standard article flow.

## Hallucination Guardrail

StrategyCardAgent only receives structured analysis results. It does not ask the LLM to create evidence comments. Cards without evidence are not displayed.
