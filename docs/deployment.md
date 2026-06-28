# Deployment

## Local Product Demo

Use the Fast Local Demo commands in the root README. SQLite, Mock comments, and MockLLM are the supported default. Uploaded files are written below `UPLOAD_DIR` and should live on persistent storage.

## Environment

- `DATABASE_URL`: SQLite by default; use a managed SQL database for hosted deployments.
- `UPLOAD_DIR`: persistent, private application storage for user uploads.
- `MAX_UPLOAD_MB`: request-level upload limit.
- `TASK_WORKER_COUNT`: in-process worker count for a single API replica.
- `CORS_ORIGINS`: JSON array of allowed frontend origins.
- `NEXT_PUBLIC_API_BASE_URL`: browser-visible API origin.

## Production Boundary

The v0.1 executor is an in-process queue. Run one API replica if tasks must execute locally. For horizontal scaling, replace it with Celery, RQ, Dramatiq, or another durable queue while keeping the existing status contract.

Put FastAPI behind HTTPS, restrict CORS to the deployed frontend, limit upload size at the reverse proxy, and periodically remove unbound uploads. Never put provider keys in frontend environment variables.

## Verification

```bash
python -m pytest backend/app/tests
cd frontend
npx tsc --noEmit
npm run build
npm run test:e2e
```

The E2E suite starts the API and Next.js application, runs a browser Demo, checks live status, opens the report tabs, and exercises the upload Wizard.
