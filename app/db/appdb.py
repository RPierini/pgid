from __future__ import annotations

import os

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

# APP_DB_URL can be provided directly, or assembled from individual POSTGRES_* variables.
# Example: ******host:5432/dbname
def _build_url() -> str:
    if "APP_DB_URL" in os.environ:
        return os.environ["APP_DB_URL"]
    host = os.environ.get("POSTGRES_HOST", "localhost")
    port = os.environ.get("POSTGRES_PORT", "5432")
    db   = os.environ.get("POSTGRES_DB",   "pgid")
    user = os.environ.get("POSTGRES_USER", "pgid")
    pwd  = os.environ.get("POSTGRES_PASSWORD", "pgid")
    return f"postgresql+asyncpg://{user}:{pwd}@{host}:{port}/{db}"


APP_DB_URL: str = _build_url()

app_engine = create_async_engine(APP_DB_URL, echo=False)
app_session = async_sessionmaker(app_engine, expire_on_commit=False)


class AppBase(DeclarativeBase):
    pass
