import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.db.session import DatabaseEngine


def _sqlite_file_url(tmp_path) -> str:
    return f"sqlite+aiosqlite:///{(tmp_path / 'test.db').as_posix()}"


def test_database_engine_get_session_yields_async_session():
    db_engine = DatabaseEngine(database_url="sqlite+aiosqlite:///:memory:")

    async def run_test():
        generator = db_engine.get_session()
        session = await generator.__anext__()
        assert isinstance(session, AsyncSession)
        await generator.aclose()

    asyncio.run(run_test())


def test_database_engine_init_stores_database_url():
    url = "sqlite+aiosqlite:///:memory:"
    db_engine = DatabaseEngine(database_url=url)

    assert db_engine.database_url == url


def test_database_engine_exposes_async_engine_instance():
    db_engine = DatabaseEngine(database_url="sqlite+aiosqlite:///:memory:")

    assert isinstance(db_engine.engine, AsyncEngine)


def test_database_engine_uses_echo_true():
    db_engine = DatabaseEngine(database_url="sqlite+aiosqlite:///:memory:")

    assert db_engine.engine.echo is True


def test_database_engine_sessionmaker_uses_async_session_class():
    db_engine = DatabaseEngine(database_url="sqlite+aiosqlite:///:memory:")

    async def run_test():
        session = db_engine.async_session()
        assert isinstance(session, AsyncSession)
        await session.close()

    asyncio.run(run_test())


def test_database_engine_sessionmaker_disables_expire_on_commit():
    db_engine = DatabaseEngine(database_url="sqlite+aiosqlite:///:memory:")

    assert db_engine.async_session.kw["expire_on_commit"] is False


def test_database_engine_get_session_yields_new_session_each_time():
    db_engine = DatabaseEngine(database_url="sqlite+aiosqlite:///:memory:")

    async def run_test():
        generator_one = db_engine.get_session()
        session_one = await generator_one.__anext__()

        generator_two = db_engine.get_session()
        session_two = await generator_two.__anext__()

        assert session_one is not session_two

        await generator_one.aclose()
        await generator_two.aclose()

    asyncio.run(run_test())


def test_database_engine_get_session_can_be_consumed_with_async_for():
    db_engine = DatabaseEngine(database_url="sqlite+aiosqlite:///:memory:")

    async def run_test():
        captured_session = None
        async for session in db_engine.get_session():
            captured_session = session
            break

        assert isinstance(captured_session, AsyncSession)

    asyncio.run(run_test())


def test_database_engine_init_db_creates_tables(tmp_path):
    db_engine = DatabaseEngine(database_url=_sqlite_file_url(tmp_path))

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


def test_database_engine_init_db_creates_user_table(tmp_path):
    db_engine = DatabaseEngine(database_url=_sqlite_file_url(tmp_path))

    async def run_test():
        await db_engine.init_db()
        async with db_engine.engine.begin() as conn:
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='user'")
            )
            assert result.first() is not None

    asyncio.run(run_test())


def test_database_engine_init_db_creates_projects_table(tmp_path):
    db_engine = DatabaseEngine(database_url=_sqlite_file_url(tmp_path))

    async def run_test():
        await db_engine.init_db()
        async with db_engine.engine.begin() as conn:
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='projects'")
            )
            assert result.first() is not None

    asyncio.run(run_test())


def test_database_engine_init_db_creates_contributions_table(tmp_path):
    db_engine = DatabaseEngine(database_url=_sqlite_file_url(tmp_path))

    async def run_test():
        await db_engine.init_db()
        async with db_engine.engine.begin() as conn:
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name='contributions'")
            )
            assert result.first() is not None

    asyncio.run(run_test())


def test_database_engine_init_db_is_idempotent(tmp_path):
    db_engine = DatabaseEngine(database_url=_sqlite_file_url(tmp_path))

    async def run_test():
        await db_engine.init_db()
        await db_engine.init_db()

        async with db_engine.engine.begin() as conn:
            result = await conn.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            )
            table_names = {row[0] for row in result}

        assert {"user", "projects", "contributions"}.issubset(table_names)

    asyncio.run(run_test())


def test_database_engine_init_db_allows_user_insert(tmp_path):
    db_engine = DatabaseEngine(database_url=_sqlite_file_url(tmp_path))

    async def run_test():
        await db_engine.init_db()
        async with db_engine.engine.begin() as conn:
            await conn.execute(
                text(
                    "INSERT INTO user (id, username, email, password) "
                    "VALUES (1, 'alice', 'alice@example.com', 'secret')"
                )
            )
            result = await conn.execute(text("SELECT COUNT(*) FROM user"))
            assert result.scalar_one() == 1

    asyncio.run(run_test())


def test_database_engine_init_db_allows_project_insert(tmp_path):
    db_engine = DatabaseEngine(database_url=_sqlite_file_url(tmp_path))

    async def run_test():
        await db_engine.init_db()
        async with db_engine.engine.begin() as conn:
            await conn.execute(
                text(
                    "INSERT INTO projects (id, title, repository_url, help_wanted) "
                    "VALUES (1, 'oss', 'https://github.com/example/oss', 1)"
                )
            )
            result = await conn.execute(text("SELECT COUNT(*) FROM projects"))
            assert result.scalar_one() == 1

    asyncio.run(run_test())


def test_database_engine_contributions_table_has_fk_user_column(tmp_path):
    db_engine = DatabaseEngine(database_url=_sqlite_file_url(tmp_path))

    async def run_test():
        await db_engine.init_db()
        async with db_engine.engine.begin() as conn:
            result = await conn.execute(text("PRAGMA table_info('contributions')"))
            columns = {row[1] for row in result}

        assert "fk_user_id" in columns

    asyncio.run(run_test())


def test_database_engine_contributions_table_has_fk_project_column(tmp_path):
    db_engine = DatabaseEngine(database_url=_sqlite_file_url(tmp_path))

    async def run_test():
        await db_engine.init_db()
        async with db_engine.engine.begin() as conn:
            result = await conn.execute(text("PRAGMA table_info('contributions')"))
            columns = {row[1] for row in result}

        assert "fk_project_id" in columns

    asyncio.run(run_test())


def test_database_engine_projects_table_help_wanted_is_not_nullable(tmp_path):
    db_engine = DatabaseEngine(database_url=_sqlite_file_url(tmp_path))

    async def run_test():
        await db_engine.init_db()
        async with db_engine.engine.begin() as conn:
            result = await conn.execute(text("PRAGMA table_info('projects')"))
            rows = list(result)

        help_wanted_row = next(row for row in rows if row[1] == "help_wanted")
        assert help_wanted_row[3] == 1

    asyncio.run(run_test())


def test_database_engine_user_table_has_unique_email_index(tmp_path):
    db_engine = DatabaseEngine(database_url=_sqlite_file_url(tmp_path))

    async def run_test():
        await db_engine.init_db()
        async with db_engine.engine.begin() as conn:
            index_list = await conn.execute(text("PRAGMA index_list('user')"))
            unique_indexes = [row for row in index_list if row[2] == 1]

        assert len(unique_indexes) >= 1

    asyncio.run(run_test())


def test_database_engine_connection_can_execute_select_one():
    db_engine = DatabaseEngine(database_url="sqlite+aiosqlite:///:memory:")

    async def run_test():
        async with db_engine.engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            assert result.scalar_one() == 1

    asyncio.run(run_test())


def test_database_engine_session_can_execute_select_one():
    db_engine = DatabaseEngine(database_url="sqlite+aiosqlite:///:memory:")

    async def run_test():
        generator = db_engine.get_session()
        session = await generator.__anext__()
        result = await session.execute(text("SELECT 1"))

        assert result.scalar_one() == 1

        await generator.aclose()

    asyncio.run(run_test())


def test_database_engine_uses_sqlite_dialect_name_for_sqlite_url():
    db_engine = DatabaseEngine(database_url="sqlite+aiosqlite:///:memory:")

    assert db_engine.engine.dialect.name == "sqlite"


def test_database_engine_uses_async_engine_driver_for_sqlite_url():
    db_engine = DatabaseEngine(database_url="sqlite+aiosqlite:///:memory:")

    assert db_engine.engine.driver == "aiosqlite"
