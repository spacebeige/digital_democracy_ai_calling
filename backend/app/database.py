import os
from pathlib import Path

from sqlalchemy import create_engine
from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker, declarative_base

BASE_DIR = Path(__file__).resolve().parents[1]
WORKSPACE_DIR = BASE_DIR.parent

load_dotenv(BASE_DIR / ".env", override=True)
load_dotenv(WORKSPACE_DIR / ".env", override=False)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./governance.db")

engine_kwargs = {"pool_pre_ping": True}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, **engine_kwargs)
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()