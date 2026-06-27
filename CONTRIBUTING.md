# Contributing

Thanks for helping improve Hupu Sports Comment Insight Agent.

## Development Setup

```bash
cp .env.example .env
python -m venv .venv
source .venv/bin/activate  # Windows: .\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -e "./backend[dev]"
python -m pytest backend/app/tests

cd frontend
npm install
npm run build
```

## Contribute Hupu Parsing Support

1. Keep collection limited to user-selected public pages.
2. Normalize output into the existing RawComment fields.
3. Do not add login automation, private APIs, CAPTCHA bypasses, or anti-bot workarounds.
4. Do not persist usernames; hash stable public author identifiers.
5. Add parser fixtures instead of depending on live network access in tests.
6. Update `docs/connectors.md` when page parsing behavior changes.

## Improve Sports Taxonomy

The public product exposes only `basketball` and `football`.

1. Add labels or terms to the correct sport.
2. Keep labels about match discussion, not unrelated product or marketing use cases.
3. Add classification tests for every new label family.
4. Update `docs/domain_taxonomy.md`.

## Contribute Demo Data

1. Use synthetic, public, or permission-safe data.
2. Keep each dataset focused on one specific match.
3. Include positive, neutral, and negative comments with clusterable topics.
4. Do not include usernames or private user data.
5. Document the dataset in `data/demo/README.md`.

## Pull Request Checklist

- Backend tests pass.
- Frontend typecheck and production build pass.
- README commands remain accurate.
- No `.env`, database files, private exports, or author identities are committed.
- News facts and sampled fan opinions remain clearly separated.
- No strategy-card or A/B-testing functionality is reintroduced.
