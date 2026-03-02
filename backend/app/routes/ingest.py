import asyncio
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db
from app.ingest import run_jsearch_ingest
from app.schemas import IngestRunResponse
from app.tasks import scrape_cycle

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.get("/ping")
def ping():
    return {"ok": True}


@router.post("/run", response_model=IngestRunResponse)
def run_ingest():
    """
    Kick off ingestion via Celery (async).
    """
    task = scrape_cycle.delay()
    return IngestRunResponse(ok=True, message="ingest scheduled", task_id=task.id)


@router.post("/run_sync", response_model=IngestRunResponse)
def run_ingest_sync(db: Session = Depends(get_db)):
    """
    Run ingestion inside the API process (sync) - useful for debugging.
    """
    settings = get_settings()
    # run async ingest in sync endpoint
    result = asyncio.run(run_jsearch_ingest(db, settings))
    if not result.get("ok"):
        return IngestRunResponse(ok=False, message=str(result.get("message", "failed")))
    return IngestRunResponse(ok=True, message=f"done: inserted={result.get('inserted')} updated={result.get('updated')}")