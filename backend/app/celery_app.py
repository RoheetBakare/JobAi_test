import os
from celery import Celery
from celery.schedules import crontab

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery = Celery("jobflow", broker=REDIS_URL, backend=REDIS_URL)

# Runs at minute 0 every 4th hour
celery.conf.beat_schedule = {
    "scrape-cycle-every-4-hours": {
        "task": "app.tasks.scrape_cycle",
        "schedule": crontab(minute=0, hour="*/4"),
    }
}