"""
Minimal SQLAlchemy setup for an async SQLite database.

Provides:
    - Base: Declarative base class for ORM models
    - engine: Async engine bound to SQLite (aiosqlite driver)
    - AsyncSessionLocal: session factory
    - get_session(): async context manager yielding a session
    - init_db(): create tables for models inheriting from Base
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import event

from cua.settings import settings

logger = logging.getLogger(__name__)


def get_db_path() -> Path:
    path = Path(settings.CUA_ROOT_DIR) / "data" / "cua.sqlite3"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def get_database_url(db_path: Path | str | None = None) -> str:
    path = Path(db_path).expanduser() if db_path else get_db_path()
    absolute = path.resolve()
    return f"sqlite+aiosqlite:///{absolute.as_posix()}"


class Base(DeclarativeBase):
    """Base class for ORM models."""
    pass


engine = create_async_engine(
    get_database_url(),
    echo=False,
    pool_pre_ping=True,
)


@event.listens_for(engine.sync_engine, "connect")
def _set_sqlite_pragma(dbapi_connection, _connection_record):
    """Ensure SQLite enforces foreign keys on every new connection."""
    try:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    except Exception:
        logger.debug("Skipping PRAGMA foreign_keys; connection not SQLite-compatible")


AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@asynccontextmanager
async def get_session() -> AsyncSession:
    """Yield an async SQLAlchemy session with proper cleanup."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """Create tables for all models inheriting from Base."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("SQLite database initialized at %s", get_db_path())


