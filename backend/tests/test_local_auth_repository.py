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


def test_sql_user_repository_get_by_id_handles_malformed_id_input_backend_safely(db_engine):
    async def run_test():
        async with db_engine.async_session() as session:
            repository = SqlUserRepository(session)

            # Repository does not validate id type; backend behavior may vary.
            # SQLite may treat this as a lookup miss and return None, while
            # stricter backends/drivers may raise during type conversion/binding.
            try:
                fetched_user = await repository.get_by_id("not-an-id")
            except (SQLAlchemyError, ValueError, TypeError):
                return
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


def test_sql_user_repository_delete_by_email_deletes_existing_user(db_engine):
    async def run_test():
        async with db_engine.async_session() as session:
            repository = SqlUserRepository(session)
            payload = UserCreate(
                username="alice",
                email="alice@example.com",
                password="hashed-password",
            )

            await repository.create(payload)
            is_deleted = await repository.delete_by_email(payload.email)
            fetched_user = await repository.get_by_email(payload.email)

            assert is_deleted is True
            assert fetched_user is None

    asyncio.run(run_test())


def test_sql_user_repository_delete_by_id_deletes_existing_user(db_engine):
    async def run_test():
        async with db_engine.async_session() as session:
            repository = SqlUserRepository(session)
            payload = UserCreate(
                username="alice",
                email="alice@example.com",
                password="hashed-password",
            )

            created_user = await repository.create(payload)
            is_deleted = await repository.delete_by_id(created_user.id)
            fetched_user = await repository.get_by_id(created_user.id)

            assert is_deleted is True
            assert fetched_user is None

    asyncio.run(run_test())


def test_sql_user_repository_delete_by_id_returns_false_when_user_does_not_exist(db_engine):
    async def run_test():
        async with db_engine.async_session() as session:
            repository = SqlUserRepository(session)
            is_deleted = await repository.delete_by_id(999)

            assert is_deleted is False

    asyncio.run(run_test())


def test_sql_user_repository_delete_by_id_returns_false_for_malformed_id_input(db_engine):
    async def run_test():
        async with db_engine.async_session() as session:
            repository = SqlUserRepository(session)
            is_deleted = await repository.delete_by_id("not-an-id")

            assert is_deleted is False

    asyncio.run(run_test())


def test_sql_user_repository_delete_by_email_returns_false_when_user_does_not_exist(db_engine):
    async def run_test():
        async with db_engine.async_session() as session:
            repository = SqlUserRepository(session)
            is_deleted = await repository.delete_by_email("missing@example.com")

            assert is_deleted is False

    asyncio.run(run_test())


def test_sql_user_repository_delete_by_email_returns_false_for_malformed_email_input(db_engine):
    async def run_test():
        async with db_engine.async_session() as session:
            repository = SqlUserRepository(session)
            is_deleted = await repository.delete_by_email("not-an-email")

            assert is_deleted is False

    asyncio.run(run_test())


@pytest.mark.parametrize(
    "username,email,password",
    [
        ("user01", "user01@example.com", "hash-01"),
        ("user02", "user02@example.com", "hash-02"),
        ("user03", "user03@example.com", "hash-03"),
        ("user04", "user04@example.com", "hash-04"),
        ("user05", "user05@example.com", "hash-05"),
        ("user06", "user06@example.com", "hash-06"),
        ("user07", "user07@example.com", "hash-07"),
        ("user08", "user08@example.com", "hash-08"),
        ("user09", "user09@example.com", "hash-09"),
        ("user10", "user10@example.com", "hash-10"),
    ],
)
def test_sql_user_repository_create_persists_various_users(db_engine, username, email, password):
    async def run_test():
        async with db_engine.async_session() as session:
            repository = SqlUserRepository(session)
            payload = UserCreate(username=username, email=email, password=password)

            created_user = await repository.create(payload)
            fetched_user = await repository.get_by_id(created_user.id)

            assert created_user.id is not None
            assert created_user.username == username
            assert created_user.email == email
            assert fetched_user is not None
            assert fetched_user.username == username
            assert fetched_user.email == email

    asyncio.run(run_test())


@pytest.mark.parametrize(
    "username,email,password",
    [
        ("lookup01", "lookup01@example.com", "hash-a1"),
        ("lookup02", "lookup02@example.com", "hash-a2"),
        ("lookup03", "lookup03@example.com", "hash-a3"),
        ("lookup04", "lookup04@example.com", "hash-a4"),
        ("lookup05", "lookup05@example.com", "hash-a5"),
        ("lookup06", "lookup06@example.com", "hash-a6"),
    ],
)
def test_sql_user_repository_get_by_email_roundtrip_multiple_payloads(db_engine, username, email, password):
    async def run_test():
        async with db_engine.async_session() as session:
            repository = SqlUserRepository(session)
            payload = UserCreate(username=username, email=email, password=password)

            created_user = await repository.create(payload)
            fetched_user = await repository.get_by_email(email)

            assert fetched_user is not None
            assert fetched_user.id == created_user.id
            assert fetched_user.username == username
            assert fetched_user.email == email

    asyncio.run(run_test())


@pytest.mark.parametrize(
    "missing_email",
    [
        "ghost01@example.com",
        "ghost02@example.com",
        "ghost03@example.com",
        "ghost04@example.com",
    ],
)
def test_sql_user_repository_get_by_email_returns_none_for_multiple_missing_emails(db_engine, missing_email):
    async def run_test():
        async with db_engine.async_session() as session:
            repository = SqlUserRepository(session)
            fetched_user = await repository.get_by_email(missing_email)

            assert fetched_user is None

    asyncio.run(run_test())


@pytest.mark.parametrize(
    "username,email,password",
    [
        ("byid01", "byid01@example.com", "hash-b1"),
        ("byid02", "byid02@example.com", "hash-b2"),
        ("byid03", "byid03@example.com", "hash-b3"),
        ("byid04", "byid04@example.com", "hash-b4"),
        ("byid05", "byid05@example.com", "hash-b5"),
    ],
)
def test_sql_user_repository_get_by_id_roundtrip_multiple_payloads(db_engine, username, email, password):
    async def run_test():
        async with db_engine.async_session() as session:
            repository = SqlUserRepository(session)
            payload = UserCreate(username=username, email=email, password=password)

            created_user = await repository.create(payload)
            fetched_user = await repository.get_by_id(created_user.id)

            assert fetched_user is not None
            assert fetched_user.id == created_user.id
            assert fetched_user.username == username
            assert fetched_user.email == email

    asyncio.run(run_test())


@pytest.mark.parametrize(
    "field_name,field_value",
    [
        ("username", "updated-user-a"),
        ("username", "updated-user-b"),
        ("email", "updated-a@example.com"),
        ("bio", "Updated bio one"),
        ("bio", "Updated bio two"),
        ("github_page", "https://github.com/updated-user"),
    ],
)
def test_sql_user_repository_update_persists_each_supported_field(db_engine, field_name, field_value):
    async def run_test():
        async with db_engine.async_session() as session:
            repository = SqlUserRepository(session)
            payload = UserCreate(
                username="base-user",
                email="base-user@example.com",
                password="base-hash",
            )

            created_user = await repository.create(payload)
            updated_user = await repository.update(created_user.id, **{field_name: field_value})
            fetched_user = await repository.get_by_id(created_user.id)

            assert updated_user is not None
            assert fetched_user is not None

            if field_name == "username":
                assert updated_user.username == field_value
                assert fetched_user.username == field_value
            elif field_name == "email":
                assert updated_user.email == field_value
                assert fetched_user.email == field_value
            elif field_name == "bio":
                assert updated_user.bio == field_value
                assert fetched_user.bio == field_value
            elif field_name == "github_page":
                assert str(updated_user.github_page) == field_value
                assert str(fetched_user.github_page) == field_value

    asyncio.run(run_test())