"""
Shared database session dependency for FastAPI routes.

Provides a reusable async session generator for all API modules.
"""

from typing import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import settings
from app.db.session import DatabaseEngine

_db_engine = DatabaseEngine(database_url=settings.db_url)

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session for route dependencies."""
    async with _db_engine.async_session() as session:
        yield session
