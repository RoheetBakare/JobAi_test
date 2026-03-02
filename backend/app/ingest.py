from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Tuple, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.models import Job
from app.providers.jsearch import JSearchClient


def _iso_to_utc_naive(s: str) -> Optional[datetime]:
    try:
        s = s.strip()
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            # assume utc if missing tz
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    except Exception:
        return None


def _parse_relative_posted(s: str, now_utc: datetime) -> Optional[datetime]:
    """
    Handles strings like:
      "3 days ago", "5 hours ago", "Today", "Yesterday"
    """
    if not s:
        return None
    t = s.strip().lower()

    if "today" in t:
        return now_utc
    if "yesterday" in t:
        return now_utc - timedelta(days=1)

    parts = t.split()
    if len(parts) >= 2 and parts[0].isdigit():
        n = int(parts[0])
        unit = parts[1]
        if "day" in unit:
            return now_utc - timedelta(days=n)
        if "hour" in unit:
            return now_utc - timedelta(hours=n)
        if "minute" in unit:
            return now_utc - timedelta(minutes=n)
        if "week" in unit:
            return now_utc - timedelta(days=7 * n)

    return None


def parse_posted_at(item: Dict[str, Any], now_utc: datetime) -> Optional[datetime]:
    # Common JSearch fields (varies by plan/version)
    for key in ("job_posted_at_datetime_utc", "job_posted_at_datetime", "job_posted_at_datetime_utc_iso"):
        v = item.get(key)
        if isinstance(v, str):
            dt = _iso_to_utc_naive(v)
            if dt:
                return dt

    ts = item.get("job_posted_at_timestamp")
    if isinstance(ts, (int, float)):
        try:
            return datetime.fromtimestamp(float(ts), tz=timezone.utc).replace(tzinfo=None)
        except Exception:
            pass

    rel = item.get("job_posted_at") or item.get("job_posted_at_human")
    if isinstance(rel, str):
        dt = _parse_relative_posted(rel, now_utc)
        if dt:
            return dt

    return None


def in_age_window(posted_at: Optional[datetime], now_utc: datetime, min_days: int, max_days: int) -> bool:
    if posted_at is None:
        return False
    age_days = (now_utc - posted_at).total_seconds() / 86400.0
    return (age_days >= float(min_days)) and (age_days <= float(max_days))


def _safe_snippet(text: Optional[str], max_len: int = 500) -> Optional[str]:
    if not text:
        return None
    t = " ".join(text.split())
    return t[:max_len]


def _fallback_external_id(item: Dict[str, Any]) -> str:
    basis = (
        (item.get("job_title") or "")
        + "|"
        + (item.get("employer_name") or "")
        + "|"
        + (item.get("job_location") or item.get("job_city") or "")
        + "|"
        + (item.get("job_apply_link") or item.get("job_google_link") or item.get("job_link") or "")
    )
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()


def normalize_jsearch(item: Dict[str, Any], query_title: str, query_location: str, now_utc: datetime) -> Dict[str, Any]:
    title = item.get("job_title") or "Unknown Title"
    company = item.get("employer_name") or "Unknown Company"
    location = item.get("job_location") or item.get("job_city") or query_location or "Unknown Location"

    posted_at = parse_posted_at(item, now_utc)

    source = item.get("job_publisher") or item.get("job_publisher_name") or "unknown"
    url = item.get("job_apply_link") or item.get("job_google_link") or item.get("job_link")

    external_id = item.get("job_id")
    if not external_id:
        external_id = _fallback_external_id(item)

    desc = item.get("job_description")
    snippet = _safe_snippet(desc)

    return {
        "provider": "jsearch",
        "external_id": external_id,
        "source": str(source),
        "title": str(title),
        "company": str(company),
        "location": str(location),
        "url": str(url) if url else None,
        "description_snippet": snippet,
        "posted_at": posted_at,
        "raw": item,
    }


def upsert_job(db: Session, job_data: Dict[str, Any]) -> Tuple[bool, Job]:
    """
    Returns (created, job)
    """
    provider = job_data["provider"]
    external_id = job_data.get("external_id")

    existing: Optional[Job] = None
    if external_id:
        existing = db.execute(
            select(Job).where(Job.provider == provider, Job.external_id == external_id)
        ).scalar_one_or_none()

    now = datetime.utcnow()

    if existing:
        # update fields we care about
        existing.source = job_data.get("source", existing.source)
        existing.title = job_data.get("title", existing.title)
        existing.company = job_data.get("company", existing.company)
        existing.location = job_data.get("location", existing.location)
        existing.url = job_data.get("url", existing.url)
        existing.description_snippet = job_data.get("description_snippet", existing.description_snippet)
        existing.posted_at = job_data.get("posted_at", existing.posted_at)
        existing.raw = job_data.get("raw", existing.raw)
        existing.last_seen_at = now

        db.add(existing)
        return (False, existing)

    job = Job(
        provider=provider,
        external_id=external_id,
        source=job_data.get("source", "unknown"),
        title=job_data["title"],
        company=job_data["company"],
        location=job_data["location"],
        url=job_data.get("url"),
        description_snippet=job_data.get("description_snippet"),
        posted_at=job_data.get("posted_at"),
        status="pending_approval",
        raw=job_data.get("raw"),
        discovered_at=now,
        last_seen_at=now,
    )
    db.add(job)
    return (True, job)


async def run_jsearch_ingest(db: Session, settings: Settings) -> Dict[str, Any]:
    if not settings.rapidapi_key:
        return {"ok": False, "inserted": 0, "updated": 0, "message": "RAPIDAPI_KEY is missing"}

    client = JSearchClient(
        base_url=settings.jsearch_base_url,
        rapidapi_key=settings.rapidapi_key,
        rapidapi_host=settings.rapidapi_host,
    )

    now_utc = datetime.utcnow()

    inserted = 0
    updated = 0

    for title, location in settings.queries:
        if location:
            query = f"{title} in {location}"
        else:
            query = title

        results: List[Dict[str, Any]] = await client.search(query=query, page=1, num_pages=settings.num_pages)

        for item in results:
            job_data = normalize_jsearch(item, title, location, now_utc)

            # date filter: only keep jobs within min/max days
            if not in_age_window(job_data["posted_at"], now_utc, settings.posted_min_days, settings.posted_max_days):
                continue

            created, job = upsert_job(db, job_data)
            if created:
                inserted += 1
            else:
                updated += 1

    db.commit()
    return {"ok": True, "inserted": inserted, "updated": updated, "message": "ingest complete"}