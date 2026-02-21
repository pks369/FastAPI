from __future__ import annotations
import os
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "ingestion",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

# Sensible defaults
celery_app.conf.update(
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_time_limit=600,
)
