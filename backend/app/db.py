import time
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.config import get_settings

settings = get_settings()

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _wait_for_db(max_attempts: int = 30, sleep_seconds: float = 1.0) -> None:
    """
    Prevents FastAPI startup crash when Postgres is still booting.
    """
    last_err = None
    for _ in range(max_attempts):
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return
        except Exception as e:
            last_err = e
            time.sleep(sleep_seconds)

    raise RuntimeError(f"Database not ready after retries. Last error: {last_err}")


def init_db():
    _wait_for_db()
    from app.models import Base  # local import to avoid circulars
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()