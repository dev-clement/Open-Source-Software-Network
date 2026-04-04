import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import DatabaseEngine


def test_database_engine_get_session_yields_async_session():
    db_engine = DatabaseEngine(database_url="sqlite+aiosqlite:///:memory:")

    async def run_test():
        generator = db_engine.get_session()
        session = await generator.__anext__()
        assert isinstance(session, AsyncSession)
        await generator.aclose()

    asyncio.run(run_test())


def test_database_engine_init_db_creates_tables():
    db_engine = DatabaseEngine(database_url="sqlite+aiosqlite:///:memory:")

    async def run_test():
        await db_engine.init_db()

        async with db_engine.engine.begin() as conn:
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            )
            table_names = {row[0] for row in result}

        assert "user" in table_names
        assert "projects" in table_names
        assert "contributions" in table_names

    asyncio.run(run_test())
