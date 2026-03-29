import enum
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, DateTime, Enum, JSON, ForeignKey, UniqueConstraint, Text, BigInteger
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db import Base

class JobStatus(str, enum.Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"

class Job(Base):
    __tablename__ = "jobs"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status = Column(Enum(JobStatus), nullable=False, default=JobStatus.pending)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    started_at = Column(DateTime)
    finished_at = Column(DateTime)
    total = Column(Integer, default=0)
    processed = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    last_error = Column(Text)

    raw_events = relationship("RawEvent", back_populates="job")

class RawEvent(Base):
    __tablename__ = "raw_events"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("jobs.id"), nullable=False)
    provider = Column(String(64), nullable=False)
    external_id = Column(String(128), nullable=True)
    payload = Column(JSON, nullable=False)
    received_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    job = relationship("Job", back_populates="raw_events")

class Entity(Base):
    __tablename__ = "entities"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider = Column(String(64), nullable=False)
    external_id = Column(String(128), nullable=False)
    idempotency_key = Column(String(128), nullable=False, unique=True)
    name = Column(String(256), nullable=False)
    currency = Column(String(8))
    amount = Column(Integer)
    event_time = Column(DateTime, default=datetime.utcnow, nullable=False)
    derived_score = Column(Integer)

    __table_args__ = (
        UniqueConstraint('idempotency_key', name='uq_entities_idem_key'),
    )
