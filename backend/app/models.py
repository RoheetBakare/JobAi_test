import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Float, Text
from sqlalchemy.orm import DeclarativeBase, mapped_column
from sqlalchemy.dialects.postgresql import JSONB

class Base(DeclarativeBase):
    pass

class Job(Base):
    __tablename__ = "jobs"

    id = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    source = mapped_column(String, default="demo")  # later: indeed/linkedin/glassdoor/api
    title = mapped_column(String, nullable=False)
    company = mapped_column(String, nullable=False)
    location = mapped_column(String, nullable=False)

    url = mapped_column(String, nullable=True)
    description_snippet = mapped_column(Text, nullable=True)

    posted_at = mapped_column(DateTime, nullable=True)
    discovered_at = mapped_column(DateTime, default=datetime.utcnow)

    status = mapped_column(String, default="pending_approval")  # pending_approval/approved/skipped/applied/interviewing/...
    score = mapped_column(Float, nullable=True)

    raw = mapped_column(JSONB, nullable=True)