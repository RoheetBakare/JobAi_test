import random
from datetime import datetime, timedelta

from sqlalchemy import select, func

from app.celery_app import celery
from app.db import SessionLocal
from app.models import Job

@celery.task(name="app.tasks.scrape_cycle")
def scrape_cycle():
    with SessionLocal() as db:
        count = db.execute(select(func.count(Job.id))).scalar_one()

        # Keep it small while testing
        if count >= 50:
            return {"ok": True, "message": "Already have 50+ jobs, skipping demo insert."}

        titles = ["Data Scientist", "ML Engineer", "Data Analyst", "Data Engineer"]
        companies = ["Acme AI", "Nimbus Labs", "BrightData", "Northwind", "VertexWorks"]
        locations = ["San Francisco, CA", "Remote - US", "San Jose, CA", "New York, NY"]

        for _ in range(10):
            days_ago = random.randint(1, 10)
            posted_at = datetime.utcnow() - timedelta(days=days_ago)

            job = Job(
                source="demo",
                title=random.choice(titles),
                company=random.choice(companies),
                location=random.choice(locations),
                url="https://example.com/job",
                description_snippet="Demo job inserted by Celery. Next: replace with real job provider.",
                posted_at=posted_at,
                status="pending_approval",
            )
            db.add(job)

        db.commit()

    return {"ok": True, "inserted": 10}