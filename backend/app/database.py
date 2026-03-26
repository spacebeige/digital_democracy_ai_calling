import os
from pathlib import Path

from sqlalchemy import text
from sqlalchemy import create_engine
from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker, declarative_base

BASE_DIR = Path(__file__).resolve().parents[1]
WORKSPACE_DIR = BASE_DIR.parent

load_dotenv(BASE_DIR / ".env", override=True)
load_dotenv(WORKSPACE_DIR / ".env", override=False)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./governance.db")

def _is_postgres_url(url: str) -> bool:
    return url.startswith("postgresql")


def is_neon_database_url(url: str | None = None) -> bool:
    value = (url or DATABASE_URL).lower()
    return _is_postgres_url(value) and "neon.tech" in value


engine_kwargs = {"pool_pre_ping": True, "pool_recycle": 300}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
elif _is_postgres_url(DATABASE_URL):
    # Keep connections fresh for managed Postgres providers like Neon.
    engine_kwargs["pool_size"] = int(os.getenv("DB_POOL_SIZE", "10"))
    engine_kwargs["max_overflow"] = int(os.getenv("DB_MAX_OVERFLOW", "20"))
    engine_kwargs["pool_timeout"] = int(os.getenv("DB_POOL_TIMEOUT", "30"))

engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)

Base = declarative_base()


def verify_database_connection() -> bool:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))
    return True