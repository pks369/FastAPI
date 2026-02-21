from __future__ import annotations
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, text

from app.db import SessionLocal, engine
from app.schemas.schemas import IngestRequest, JobStatusResponse, EntityOut
from app.models.models import Job, JobStatus, Entity
from app.celery_app import celery_app
from app.tasks import ingest_job, PROVIDERS

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/jobs/ingest", response_model=JobStatusResponse)
def start_ingest(payload: IngestRequest, db: Session = Depends(get_db)):
    # Validate providers
    selected = payload.providers or list(PROVIDERS.keys())
    for p in selected:
        if p not in PROVIDERS:
            raise HTTPException(status_code=400, detail=f"unknown provider: {p}")

    # Create job
    job = Job(status=JobStatus.pending)
    db.add(job)
    db.commit()
    db.refresh(job)

    # Enqueue celery task
    ingest_job.delay(str(job.id), selected, payload.since.isoformat() if payload.since else None)

    return JobStatusResponse(
        id=str(job.id),
        status=job.status.value,
        created_at=job.created_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
        total=job.total,
        processed=job.processed,
        failed_count=job.failed_count,
        last_error=job.last_error,
    )


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
def job_status(job_id: str, db: Session = Depends(get_db)):
    from uuid import UUID as _UUID
    job = db.get(Job, _UUID(job_id))
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return JobStatusResponse(
        id=str(job.id),
        status=job.status.value,
        created_at=job.created_at,
        started_at=job.started_at,
        finished_at=job.finished_at,
        total=job.total,
        processed=job.processed,
        failed_count=job.failed_count,
        last_error=job.last_error,
    )


@router.get("/entities", response_model=list[EntityOut])
def list_entities(
    provider: str | None = Query(default=None),
    since: datetime | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    stmt = select(Entity)
    if provider:
        stmt = stmt.where(Entity.provider == provider)
    if since:
        stmt = stmt.where(Entity.event_time >= since)
    stmt = stmt.order_by(Entity.event_time.desc()).limit(limit).offset(offset)
    rows = db.execute(stmt).scalars().all()
    return [
        EntityOut(
            id=str(r.id),
            provider=r.provider,
            external_id=r.external_id,
            name=r.name,
            currency=r.currency,
            amount=r.amount,
            event_time=r.event_time,
            derived_score=r.derived_score,
        )
        for r in rows
    ]


@router.get("/health")
def health(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(e))
