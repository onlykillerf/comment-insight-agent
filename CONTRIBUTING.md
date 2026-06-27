# Contributing

Thanks for helping improve Cross-Platform Comment Insight Agent.

## Development Setup

```bash
cp .env.example .env
docker compose up -d
cd backend
python -m pip install -e .[dev]
python -m pytest
cd ../frontend
npm install
npm run build
```

## Contribute A Connector

1. Implement `PlatformConnector`.
2. Normalize output into RawComment fields.
3. Do not bypass login, CAPTCHA, paywalls, private APIs, or platform permissions.
4. Add tests with mock/sample outputs.
5. Update `docs/connectors.md`.

## Contribute A Taxonomy

1. Add a `DomainTaxonomy`.
2. Include positive, negative, and stance labels.
3. Add keyword hints.
4. Add a small classification test.
5. Update `docs/domain_taxonomy.md`.

## Contribute A Demo Dataset

1. Use synthetic, public, or permission-safe data.
2. Include the normalized CSV fields.
3. Include positive, neutral, and negative examples.
4. Avoid private user data.
5. Document the dataset in `data/demo/README.md`.

## Contribute An Agent

1. Keep the agent contract narrow.
2. Add it to `CommentAnalysisGraph`.
3. Add progress summaries if it appears on the status page.
4. Add persistence/API/frontend support only when needed.
5. Add tests.

## Pull Request Checklist

- Backend tests pass.
- Frontend build passes.
- README commands remain accurate.
- No `.env`, database files, or private exports are committed.
- Strategy cards remain evidence-grounded.
