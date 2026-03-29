from __future__ import annotations
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from time import time as now
from app.db import engine, Base
from app.models import models as _models  # ensure models are imported
from app.api.routes import router
from app.metrics import REQUESTS_TOTAL, REQUEST_LATENCY

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup (for demo simplicity; use Alembic in prod)
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(title="Ingestion Service", version="1.0.0", lifespan=lifespan)

@app.middleware("http")
async def prometheus_middleware(request: Request, call_next):
    start = now()
    response: Response = await call_next(request)
    duration = now() - start
    endpoint = request.url.path
    REQUESTS_TOTAL.labels(endpoint=endpoint, method=request.method, status=str(response.status_code)).inc()
    REQUEST_LATENCY.labels(endpoint=endpoint, method=request.method).observe(duration)
    return response

app.include_router(router)

@app.get("/metrics")
async def metrics():
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    data = generate_latest()  # type: ignore[arg-type]
    return Response(content=data, media_type=CONTENT_TYPE_LATEST)
