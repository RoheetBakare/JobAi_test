from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from pydantic.config import ConfigDict


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    provider: str
    external_id: Optional[str] = None
    source: str

    title: str
    company: str
    location: str

    url: Optional[str] = None
    description_snippet: Optional[str] = None

    posted_at: Optional[datetime] = None
    discovered_at: datetime
    last_seen_at: datetime

    status: str
    score: Optional[float] = None


class JobStatusUpdate(BaseModel):
    status: str


class IngestRunResponse(BaseModel):
    ok: bool
    message: str
    task_id: Optional[str] = None