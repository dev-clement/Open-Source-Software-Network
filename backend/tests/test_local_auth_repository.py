import asyncio

import pytest
from sqlalchemy import event, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.auth.repository import SqlUserRepository
from app.auth.schemas import UserCreate
from app.db.models import User as UserModel
from app.db.session import DatabaseEngine

def _sqlite_url(tmp_path, db_name: str) -> str:
    db_path = tmp_path / db_name
    return f"sqlite+aiosqlite:///{db_path.as_posix()}"


def _assign_sqlite_user_id(mapper, connection, target):
    if connection.dialect.name != "sqlite":
        return
    if target.id is not None:
        return

    # In SQLite tests, emulate auto-increment for BIGINT ids defined for PostgreSQL.
    next_id_statement = text("SELECT COALESCE(MAX(id), 0) + 1 FROM user")
    target.id = connection.execute(next_id_statement).scalar_one()


@pytest.fixture
def db_engine(tmp_path):
    async def setup_engine():
        engine = DatabaseEngine(database_url=_sqlite_url(tmp_path, "auth_repository.db"))
        await engine.init_db()
        return engine

    # SQLAlchemy ORM event hook: run before inserting User rows.
    event.listen(UserModel, "before_insert", _assign_sqlite_user_id)
    engine = asyncio.run(setup_engine())
    # pytest fixtures use yield to provide the value, then run teardown below.
    yield engine
    event.remove(UserModel, "before_insert", _assign_sqlite_user_id)
    asyncio.run(engine.engine.dispose())


def test_sql_user_repository_create_persists_user(db_engine):
    async def run_test():
        async with db_engine.async_session() as session:
            repository = SqlUserRepository(session)
            payload = UserCreate(
                username="alice",
                email="alice@example.com",
                password="hashed-password",
            )

            user = await repository.create(payload)

            assert user.id is not None
            assert user.username == payload.username
            assert user.email == payload.email
            assert "password" not in user.model_dump()

    asyncio.run(run_test())


def test_sql_user_repository_create_raises_on_duplicate_email(db_engine):
    async def run_test():
        async with db_engine.async_session() as session:
            repository = SqlUserRepository(session)
            first_payload = UserCreate(
                username="alice",
                email="alice@example.com",
                password="hashed-password-1",
            )
            duplicate_email_payload = UserCreate(
                username="alice-2",
                email="alice@example.com",
                password="hashed-password-2",
            )

            await repository.create(first_payload)

            with pytest.raises(IntegrityError):
                await repository.create(duplicate_email_payload)

    asyncio.run(run_test())


def test_sql_user_repository_get_by_email_returns_user_when_exists(db_engine):
    async def run_test():
        async with db_engine.async_session() as session:
            repository = SqlUserRepository(session)
            payload = UserCreate(
                username="alice",
                email="alice@example.com",
                password="hashed-password",
            )

            created_user = await repository.create(payload)
            fetched_user = await repository.get_by_email(payload.email)

            assert fetched_user is not None
            assert fetched_user.id == created_user.id
            assert fetched_user.username == created_user.username
            assert fetched_user.email == created_user.email
            assert "password" not in fetched_user.model_dump()

    asyncio.run(run_test())


def test_sql_user_repository_create_propagates_database_error(db_engine):
    async def run_test():
        async with db_engine.async_session() as session:
            repository = SqlUserRepository(session)
            payload = UserCreate(
                username="alice",
                email="alice@example.com",
                password="hashed-password",
            )

            async def failing_commit():
                raise SQLAlchemyError("Database write failed")

            session.commit = failing_commit

            with pytest.raises(SQLAlchemyError, match="Database write failed"):
                await repository.create(payload)

    asyncio.run(run_test())


def test_sql_user_repository_get_by_email_returns_none_when_email_does_not_exist(db_engine):
    async def run_test():
        async with db_engine.async_session() as session:
            repository = SqlUserRepository(session)
            fetched_user = await repository.get_by_email("missing@example.com")

            assert fetched_user is None

    asyncio.run(run_test())


def test_sql_user_repository_get_by_email_returns_none_for_malformed_email_input(db_engine):
    async def run_test():
        async with db_engine.async_session() as session:
            repository = SqlUserRepository(session)
            fetched_user = await repository.get_by_email("not-an-email")

            # Repository does not validate email format; it performs a DB lookup as-is.
            assert fetched_user is None

    asyncio.run(run_test())


def test_sql_user_repository_get_by_id_returns_user_when_exists(db_engine):
    async def run_test():
        async with db_engine.async_session() as session:
            repository = SqlUserRepository(session)
            payload = UserCreate(
                username="alice",
                email="alice@example.com",
                password="hashed-password",
            )

            created_user = await repository.create(payload)
            fetched_user = await repository.get_by_id(created_user.id)

            assert fetched_user is not None
            assert fetched_user.id == created_user.id
            assert fetched_user.username == created_user.username
            assert fetched_user.email == created_user.email
            assert "password" not in fetched_user.model_dump()

    asyncio.run(run_test())


def test_sql_user_repository_get_by_id_returns_none_when_id_does_not_exist(db_engine):
    async def run_test():
        async with db_engine.async_session() as session:
            repository = SqlUserRepository(session)
            fetched_user = await repository.get_by_id(999)

            assert fetched_user is None

    asyncio.run(run_test())


def test_sql_user_repository_get_by_id_returns_none_for_malformed_id_input(db_engine):
    async def run_test():
        async with db_engine.async_session() as session:
            repository = SqlUserRepository(session)
            fetched_user = await repository.get_by_id("not-an-id")

            # Repository does not validate id type; it performs a DB lookup as-is.
            assert fetched_user is None

    asyncio.run(run_test())


def test_sql_user_repository_get_by_id_propagates_database_error(db_engine):
    async def run_test():
        async with db_engine.async_session() as session:
            repository = SqlUserRepository(session)

            async def failing_execute(statement):
                raise SQLAlchemyError("Database read failed")

            session.execute = failing_execute

            with pytest.raises(SQLAlchemyError, match="Database read failed"):
                await repository.get_by_id(1)

    asyncio.run(run_test())


def test_sql_user_repository_update_returns_none_when_user_id_is_none(db_engine):
    async def run_test():
        async with db_engine.async_session() as session:
            repository = SqlUserRepository(session)
            updated_user = await repository.update(None, username="updated-alice")

            assert updated_user is None

    asyncio.run(run_test())


def test_sql_user_repository_update_returns_none_for_malformed_user_id(db_engine):
    async def run_test():
        async with db_engine.async_session() as session:
            repository = SqlUserRepository(session)
            updated_user = await repository.update("not-an-id", username="updated-alice")

            assert updated_user is None

    asyncio.run(run_test())


def test_sql_user_repository_update_raises_value_error_for_unknown_field(db_engine):
    async def run_test():
        async with db_engine.async_session() as session:
            repository = SqlUserRepository(session)
            payload = UserCreate(
                username="alice",
                email="alice@example.com",
                password="hashed-password",
            )

            created_user = await repository.create(payload)

            with pytest.raises(ValueError, match="Unknown user field: unknown_field"):
                await repository.update(created_user.id, unknown_field="unexpected")

    asyncio.run(run_test())


def test_sql_user_repository_update_persists_and_returns_updated_user(db_engine):
    async def run_test():
        async with db_engine.async_session() as session:
            repository = SqlUserRepository(session)
            payload = UserCreate(
                username="alice",
                email="alice@example.com",
                password="hashed-password",
            )

            created_user = await repository.create(payload)
            updated_user = await repository.update(created_user.id, username="updated-alice")
            fetched_user = await repository.get_by_id(created_user.id)

            assert updated_user is not None
            assert updated_user.id == created_user.id
            assert updated_user.username == "updated-alice"
            assert updated_user.email == created_user.email

            assert fetched_user is not None
            assert fetched_user.username == "updated-alice"
            assert fetched_user.email == created_user.email

    asyncio.run(run_test())