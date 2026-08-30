from __future__ import annotations

import os

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

IDENTITY_DB_URL = os.getenv("IDENTITY_DB_URL", "sqlite+aiosqlite:///./identity.db")

identity_engine = create_async_engine(IDENTITY_DB_URL, echo=False)
identity_session = async_sessionmaker(identity_engine, expire_on_commit=False)


class IdentityBase(DeclarativeBase):
    pass
