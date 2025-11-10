from __future__ import annotations

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker

load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://admin:admin@localhost:5432/postgres",
)

SCHEMA = os.getenv("DB_SCHEMA", "iso")

# IMPORTANT: ensure we look first into schema 'iso' and then 'public'
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    future=True,
    connect_args={"options": f"-csearch_path={SCHEMA},public"},
)

# All tables live in schema iso
metadata = MetaData(schema=SCHEMA)


# Session factory
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
