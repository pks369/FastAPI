# FastAPI + Celery Ingestion Service

A production-ready reference service that fetches from **3 external APIs concurrently**, applies validation & de-duplication, stores **raw + normalized** records in PostgreSQL, and exposes results via **FastAPI**. Long-running ingestion runs as a **Celery background job** (Redis broker) so API responses stay fast.

## Features
- **Concurrency**: 'ThreadPoolExecutor' with configurable workers
- **Robust HTTP**: pagination, timeouts, and retries
- **Thread-safe rate limiting**: global + per-provider, enforced **inside worker threads**
- **Validation**: Pydantic schemas, required fields, normalization
- **Idempotency**: unique '(provider, external_id)' hash prevents duplicates
- **Persistence**: 'jobs', 'raw_events', 'entities' tables in PostgreSQL
- **APIs**:
  - 'POST /jobs/ingest' → start ingestion job
  - 'GET /jobs/{job_id}' → job status/progress/errors
  - 'GET /entities?provider=&since=' → query results
  - 'GET /health' → DB check
  - *(optional)* 'GET /metrics' → Prometheus metrics
- **Background Jobs**: Celery + Redis with retries/backoff

## Quick Start (Docker)

# 1) Copy env template and edit if needed
cp .env .env

# 2) Build & start
docker compose up --build

# 3) Open API docs
open http://localhost:8000/docs


Services:
- API: http://localhost:8000
- Redis: redis://redis:6379/0
- Postgres: postgres://postgres:postgres@postgres:5432/app

## Local Dev (without Docker)
Requirements: Python 3.11+, Postgres, Redis running locally.
'''bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env .env  # adjust DATABASE_URL and REDIS_URL

# Create tables on first run
uvicorn app.main:app --reload

# Start Celery worker in another shell
celery -A app.celery_app.celery_app worker -l info --pool=threads
'''

> Note: We use a **threads** pool in Celery so the in-process rate limiters are shared across worker threads.

## Environment
See '.env' for all variables.

- 'DATABASE_URL' (default uses Postgres)
- 'REDIS_URL' (Celery broker/result backend)
- 'WORKER_MAX_THREADS' (concurrent HTTP requests inside a job)
- 'GLOBAL_RPS' (global requests/sec limit across providers)
- 'PROVIDER_RPS_JSONPLACEHOLDER' (per-provider RPS)
- 'PROVIDER_RPS_DUMMYJSON'
- 'PROVIDER_RPS_REQRES'
- 'HTTP_TIMEOUT_SECONDS'
- 'JOB_RETRY_MAX' / 'JOB_RETRY_BACKOFF_SECONDS'

## Providers Implemented (no auth required)
- **JSONPlaceholder**: 'https://jsonplaceholder.typicode.com/posts' (pagination via '_page' & '_limit')
- **DummyJSON**: 'https://dummyjson.com/products' (pagination via 'limit' & 'skip')
- **ReqRes Users**: 'https://reqres.in/api/users' (pagination via 'page')

## Data Model (simplified)
- **jobs**: job lifecycle & progress
- **raw_events**: provider raw JSON + metadata
- **entities**: normalized records with idempotency_key unique

## Workflow
1. 'POST /jobs/ingest' creates a job row and enqueues 'ingest_job' Celery task
2. Task concurrently fetches pages across providers using ThreadPoolExecutor
3. Each request enforces **global + per-provider rate limits** (thread-safe)
4. Raw JSON stored in raw_events'; normalized & validated entity stored in 'entities' with **upsert ignore**
5. Job progress is updated progressively; errors recorded

## Push to GitHub
Once generated, you can push this folder to your GitHub:
'''bash
git init
git add .
git commit -m "feat: fastapi + celery ingestion service"
git branch -M main
git remote add origin https://github.com/<username>/<repo>.git
git push -u origin main
'''

## License
MIT
