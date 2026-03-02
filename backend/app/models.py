import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Float, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, mapped_column
from sqlalchemy.dialects.postgresql import JSONB


class Base(DeclarativeBase):
    pass


class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        UniqueConstraint("provider", "external_id", name="uq_jobs_provider_external_id"),
    )

    id = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))

    # Provider = where we fetched from (e.g. jsearch, demo)
    provider = mapped_column(String, default="demo", nullable=False)

    # external_id = stable job id from provider if available (e.g. job_id)
    external_id = mapped_column(String, nullable=True)

    # publisher/source site (LinkedIn, Indeed, etc.)
    source = mapped_column(String, default="unknown", nullable=False)

    title = mapped_column(String, nullable=False)
    company = mapped_column(String, nullable=False)
    location = mapped_column(String, nullable=False)

    url = mapped_column(String, nullable=True)          # listing/apply link
    description_snippet = mapped_column(Text, nullable=True)

    posted_at = mapped_column(DateTime, nullable=True)

    discovered_at = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    last_seen_at = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    status = mapped_column(String, default="pending_approval", nullable=False)
    score = mapped_column(Float, nullable=True)

    raw = mapped_column(JSONB, nullable=True)