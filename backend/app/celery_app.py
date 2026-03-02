from celery import Celery
from celery.schedules import crontab

from app.config import get_settings

settings = get_settings()

celery = Celery("jobflow", broker=settings.redis_url, backend=settings.redis_url)

# every 4 hours at minute 0
celery.conf.beat_schedule = {
    "ingest-cycle-every-4-hours": {
        "task": "app.tasks.scrape_cycle",
        "schedule": crontab(minute=0, hour="*/4"),
    }
}