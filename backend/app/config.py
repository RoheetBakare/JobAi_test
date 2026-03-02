import os
from dataclasses import dataclass
from typing import List, Tuple


def _parse_queries(raw: str) -> List[Tuple[str, str]]:
    """
    Format:
      JOBFLOW_QUERIES="Data Scientist|San Francisco, CA;ML Engineer|Remote - US"
    """
    items: List[Tuple[str, str]] = []
    raw = (raw or "").strip()
    if not raw:
        return items

    for part in raw.split(";"):
        part = part.strip()
        if not part:
            continue
        if "|" not in part:
            # allow "Data Scientist in San Francisco, CA" as a single string
            items.append((part, ""))
            continue
        title, location = part.split("|", 1)
        items.append((title.strip(), location.strip()))
    return items


@dataclass(frozen=True)
class Settings:
    database_url: str
    redis_url: str

    # Ingestion / provider
    rapidapi_key: str
    rapidapi_host: str
    jsearch_base_url: str

    # Search config
    queries: List[Tuple[str, str]]
    num_pages: int
    posted_min_days: int
    posted_max_days: int

    # Demo fallback when no API key
    demo_insert_if_no_key: bool


def get_settings() -> Settings:
    database_url = os.getenv("DATABASE_URL", "postgresql://jobflow:jobflow@db:5432/jobflow")
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")

    rapidapi_key = os.getenv("RAPIDAPI_KEY", "").strip()
    rapidapi_host = os.getenv("RAPIDAPI_HOST", "jsearch.p.rapidapi.com").strip()
    jsearch_base_url = os.getenv("JSEARCH_BASE_URL", "https://jsearch.p.rapidapi.com").strip().rstrip("/")

    queries = _parse_queries(os.getenv("JOBFLOW_QUERIES", "Data Scientist|San Francisco, CA;ML Engineer|Remote - US"))
    num_pages = int(os.getenv("JOBFLOW_NUM_PAGES", "1"))
    posted_min_days = int(os.getenv("JOBFLOW_POSTED_MIN_DAYS", "0"))
    posted_max_days = int(os.getenv("JOBFLOW_POSTED_MAX_DAYS", "7"))

    demo_insert_if_no_key = os.getenv("JOBFLOW_DEMO_IF_NO_KEY", "true").lower() in ("1", "true", "yes", "y")

    return Settings(
        database_url=database_url,
        redis_url=redis_url,
        rapidapi_key=rapidapi_key,
        rapidapi_host=rapidapi_host,
        jsearch_base_url=jsearch_base_url,
        queries=queries,
        num_pages=num_pages,
        posted_min_days=posted_min_days,
        posted_max_days=posted_max_days,
        demo_insert_if_no_key=demo_insert_if_no_key,
    )