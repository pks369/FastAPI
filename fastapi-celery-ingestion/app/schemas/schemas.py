from datetime import datetime
from pydantic import BaseModel, Field

class IngestRequest(BaseModel):
    providers: list[str] | None = Field(default=None, description="subset of providers to run; default = all")
    since: datetime | None = None

class JobStatusResponse(BaseModel):
    id: str
    status: str
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    total: int
    processed: int
    failed_count: int
    last_error: str | None

class EntityOut(BaseModel):
    id: str
    provider: str
    external_id: str
    name: str
    currency: str | None
    amount: int | None
    event_time: datetime
    derived_score: int | None

class EntitiesQuery(BaseModel):
    provider: str | None = None
    since: datetime | None = None
    limit: int = 100
    offset: int = 0
