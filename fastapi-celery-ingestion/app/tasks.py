from __future__ import annotations
import concurrent.futures
from datetime import datetime
import uuid
from typing import Iterable
import requests
from sqlalchemy import insert, select, update
from sqlalchemy.exc import IntegrityError

from app.core.config import settings
from app.db import SessionLocal, engine
from app.models.models import Job, JobStatus, RawEvent, Entity
from app.rate_limiter import RateLimiter
from app.clients.jsonplaceholder_client import JSONPlaceholderClient
from app.clients.dummyjson_client import DummyJSONClient
from app.clients.reqres_client import ReqResClient
from app.processing import normalize
from app.utils import retry_with_backoff

from app.celery_app import celery_app

PROVIDERS = {
    "jsonplaceholder": JSONPlaceholderClient,
    "dummyjson": DummyJSONClient,
    "reqres": ReqResClient,
}


def _provider_limits() -> dict[str, int]:
    return {
        "jsonplaceholder": settings.PROVIDER_RPS_JSONPLACEHOLDER,
        "dummyjson": settings.PROVIDER_RPS_DUMMYJSON,
        "reqres": settings.PROVIDER_RPS_REQRES,
    }


def _iter_all_pages(clients: list):
    for client in clients:
        for page in client.iter_pages():
            yield client, page


@celery_app.task(bind=True, autoretry_for=(requests.RequestException,), retry_backoff=True, retry_kwargs={"max_retries": 3})
def ingest_job(self, job_id: str, providers: list[str] | None = None, since: str | None = None):
    # Create rate limiter instance shared within this process
    limiter = RateLimiter(settings.GLOBAL_RPS, _provider_limits())

    selected = providers or list(PROVIDERS.keys())
    clients = [PROVIDERS[p](limiter) for p in selected]

    db = SessionLocal()
    try:
        # Update job as running
        job_uuid = uuid.UUID(job_id)
        db.execute(
            update(Job)
            .where(Job.id == job_uuid)
            .values(status=JobStatus.running, started_at=datetime.utcnow())
        )
        db.commit()

        total_processed = 0
        failed = 0

        def process_item(provider: str, raw: dict):
            nonlocal total_processed, failed

            # Store raw event first
            external_id = str(raw.get("id") or raw.get("external_id") or "")
            db_local = SessionLocal()
            try:
                db_local.add(RawEvent(job_id=job_uuid, provider=provider, external_id=external_id, payload=raw))
                db_local.commit()
            except Exception:
                db_local.rollback()
            finally:
                db_local.close()

            # Normalize + validate + persist entity with idempotency
            try:
                entity_dict, ext_id = normalize(provider, raw)
            except Exception as e:  # bad record
                failed += 1
                db.execute(update(Job).where(Job.id == job_uuid).values(failed_count=failed, last_error=str(e)))
                db.commit()
                return

            def _insert_once():
                with SessionLocal() as s:
                    try:
                        stmt = insert(Entity).values(**entity_dict)
                        # Prefer ON CONFLICT DO NOTHING in Postgres
                        from sqlalchemy.dialects.postgresql import insert as pg_insert
                        stmt = pg_insert(Entity).values(**entity_dict).on_conflict_do_nothing(index_elements=[Entity.idempotency_key])
                        s.execute(stmt)
                        s.commit()
                    except IntegrityError:
                        s.rollback()

            # retry on transient DB errors
            retry_with_backoff(_insert_once, retries=2, base_delay=0.5)

            total_processed += 1
            db.execute(update(Job).where(Job.id == job_uuid).values(processed=total_processed))
            db.commit()

        # Use ThreadPoolExecutor for concurrent page & item handling
        with concurrent.futures.ThreadPoolExecutor(max_workers=settings.WORKER_MAX_THREADS) as pool:
            futures: list[concurrent.futures.Future] = []
            for client, page in _iter_all_pages(clients):
                provider = client.name
                for item in page:
                    futures.append(pool.submit(process_item, provider, item))

            for f in concurrent.futures.as_completed(futures):
                _ = f.result()  # raise exceptions if any

        db.execute(update(Job).where(Job.id == job_uuid).values(status=JobStatus.completed, finished_at=datetime.utcnow(), total=total_processed))
        db.commit()
    except Exception as e:
        db.execute(update(Job).where(Job.id == job_uuid).values(status=JobStatus.failed, finished_at=datetime.utcnow(), last_error=str(e)))
        db.commit()
        raise
    finally:
        db.close()
