import random
from datetime import datetime, timedelta
import asyncio

from sqlalchemy import select, func

from app.celery_app import celery
from app.config import get_settings
from app.db import SessionLocal
from app.models import Job
from app.ingest import run_jsearch_ingest


@celery.task(name="app.tasks.scrape_cycle")
def scrape_cycle():
    """
    If RAPIDAPI_KEY is set -> real JSearch ingestion
    Else (dev mode) -> insert demo jobs so UI always has data
    """
    settings = get_settings()

    with SessionLocal() as db:
        if settings.rapidapi_key:
            result = asyncio.run(run_jsearch_ingest(db, settings))
            return result

        if not settings.demo_insert_if_no_key:
            return {"ok": False, "message": "RAPIDAPI_KEY missing and demo fallback disabled"}

        # demo fallback
        count = db.execute(select(func.count(Job.id))).scalar_one()
        if count >= 50:
            return {"ok": True, "message": "Already have 50+ jobs, skipping demo insert."}

        titles = ["Data Scientist", "ML Engineer", "Data Analyst", "Data Engineer"]
        companies = ["Acme AI", "Nimbus Labs", "BrightData", "Northwind", "VertexWorks"]
        locations = ["San Francisco, CA", "Remote - US", "San Jose, CA", "New York, NY"]

        for _ in range(10):
            days_ago = random.randint(1, 10)
            posted_at = datetime.utcnow() - timedelta(days=days_ago)

            job = Job(
                provider="demo",
                external_id=None,
                source="demo",
                title=random.choice(titles),
                company=random.choice(companies),
                location=random.choice(locations),
                url="https://example.com/job",
                description_snippet="Demo job inserted. Set RAPIDAPI_KEY for real ingestion.",
                posted_at=posted_at,
                status="pending_approval",
                raw={"demo": True},
                discovered_at=datetime.utcnow(),
                last_seen_at=datetime.utcnow(),
            )
            db.add(job)

        db.commit()

    return {"ok": True, "inserted": 10, "provider": "demo"}