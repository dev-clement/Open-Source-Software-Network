import asyncio
from datetime import datetime, timezone
from typing import Optional

import pytest
from sqlalchemy import event, text

from app.auth.auth_local_service import AuthLocalService
from app.auth.repository import SqlUserRepository, UserRepository
from app.auth.schemas import User, UserCreate
from app.db.models import User as UserModel
from app.db.session import DatabaseEngine


TEST_PBKDF2_ITERATIONS = 1_000


class FakeUserRepository(UserRepository):
    def __init__(self):
        self._next_id = 1
        self._users_by_id: dict[int, dict] = {}
        self._user_id_by_email: dict[str, int] = {}

    def _to_user_schema(self, record: dict) -> User:
        return User(
            id=record["id"],
            username=record["username"],
            email=record["email"],
            github_page=record.get("github_page"),
            bio=record.get("bio"),
            created_at=record["created_at"],
            updated_at=record["updated_at"],
        )

    async def create(self, user_data: UserCreate) -> User:
        now = datetime.now(timezone.utc)
        user_id = self._next_id
        self._next_id += 1
        record = {
            "id": user_id,
            "username": user_data.username,
            "email": user_data.email,
            "password": user_data.password,
            "github_page": user_data.github_page,
            "bio": user_data.bio,
            "created_at": now,
            "updated_at": now,
        }
        self._users_by_id[user_id] = record
        self._user_id_by_email[user_data.email] = user_id
        return self._to_user_schema(record)

    async def get_by_email(self, email: str) -> Optional[User]:
        user_id = self._user_id_by_email.get(email)
        if user_id is None:
            return None
        return self._to_user_schema(self._users_by_id[user_id])

    async def get_password_hash_by_email(self, email: str) -> Optional[str]:
        user_id = self._user_id_by_email.get(email)
        if user_id is None:
            return None
        return self._users_by_id[user_id]["password"]

    async def get_by_id(self, user_id: int) -> Optional[User]:
        record = self._users_by_id.get(user_id)
        if record is None:
            return None
        return self._to_user_schema(record)

    async def update(self, user_id: int, **kwargs) -> Optional[User]:
        record = self._users_by_id.get(user_id)
        if record is None:
            return None
        for key, value in kwargs.items():
            record[key] = value
        record["updated_at"] = datetime.now(timezone.utc)
        return self._to_user_schema(record)

    async def delete_by_id(self, user_id: int) -> bool:
        record = self._users_by_id.pop(user_id, None)
        if record is None:
            return False
        self._user_id_by_email.pop(record["email"], None)
        return True

    async def delete_by_email(self, email: str) -> bool:
        user_id = self._user_id_by_email.pop(email, None)
        if user_id is None:
            return False
        self._users_by_id.pop(user_id, None)
        return True


def _sqlite_url(tmp_path, db_name: str) -> str:
    db_path = tmp_path / db_name
    return f"sqlite+aiosqlite:///{db_path.as_posix()}"


def _assign_sqlite_user_id(mapper, connection, target):
    if connection.dialect.name != "sqlite":
        return
    if target.id is not None:
        return

    next_id_statement = text("SELECT COALESCE(MAX(id), 0) + 1 FROM user")
    target.id = connection.execute(next_id_statement).scalar_one()


@pytest.fixture
def sqlite_db_engine(tmp_path):
    async def setup_engine():
        engine = DatabaseEngine(database_url=_sqlite_url(tmp_path, "auth_local_service.db"))
        await engine.init_db()
        return engine

    event.listen(UserModel, "before_insert", _assign_sqlite_user_id)
    engine = asyncio.run(setup_engine())
    yield engine
    event.remove(UserModel, "before_insert", _assign_sqlite_user_id)
    asyncio.run(engine.engine.dispose())


def test_auth_local_service_register_hashes_password_and_returns_user():
    async def run_test():
        repository = FakeUserRepository()
        service = AuthLocalService(repository, pbkdf2_iterations=TEST_PBKDF2_ITERATIONS)

        payload = UserCreate(
            username="alice",
            email="alice@example.com",
            password="plain-password",
        )
        created_user = await service.register(payload)

        assert created_user.id is not None
        assert created_user.email == payload.email
        stored_hash = await repository.get_password_hash_by_email(payload.email)
        assert stored_hash is not None
        assert stored_hash != payload.password
        assert stored_hash.startswith("pbkdf2_sha256$")

    asyncio.run(run_test())


def test_auth_local_service_register_raises_when_email_already_exists():
    async def run_test():
        repository = FakeUserRepository()
        service = AuthLocalService(repository, pbkdf2_iterations=TEST_PBKDF2_ITERATIONS)

        payload = UserCreate(
            username="alice",
            email="alice@example.com",
            password="plain-password",
        )
        await service.register(payload)

        with pytest.raises(ValueError, match="Email already exists"):
            await service.register(payload)

    asyncio.run(run_test())


def test_auth_local_service_authenticate_returns_user_for_valid_credentials():
    async def run_test():
        repository = FakeUserRepository()
        service = AuthLocalService(repository, pbkdf2_iterations=TEST_PBKDF2_ITERATIONS)

        payload = UserCreate(
            username="alice",
            email="alice@example.com",
            password="plain-password",
        )
        registered_user = await service.register(payload)
        authenticated_user = await service.authenticate(payload.email, payload.password)

        assert authenticated_user is not None
        assert authenticated_user.id == registered_user.id
        assert authenticated_user.email == payload.email

    asyncio.run(run_test())


def test_auth_local_service_authenticate_returns_none_for_wrong_password():
    async def run_test():
        repository = FakeUserRepository()
        service = AuthLocalService(repository, pbkdf2_iterations=TEST_PBKDF2_ITERATIONS)

        payload = UserCreate(
            username="alice",
            email="alice@example.com",
            password="plain-password",
        )
        await service.register(payload)

        authenticated_user = await service.authenticate(payload.email, "wrong-password")
        assert authenticated_user is None

    asyncio.run(run_test())


def test_auth_local_service_authenticate_returns_none_for_unknown_email():
    async def run_test():
        repository = FakeUserRepository()
        service = AuthLocalService(repository, pbkdf2_iterations=TEST_PBKDF2_ITERATIONS)

        authenticated_user = await service.authenticate("missing@example.com", "any-password")
        assert authenticated_user is None

    asyncio.run(run_test())


def test_auth_local_service_authenticate_returns_none_for_malformed_stored_hash():
    async def run_test():
        repository = FakeUserRepository()
        service = AuthLocalService(repository, pbkdf2_iterations=TEST_PBKDF2_ITERATIONS)

        payload = UserCreate(
            username="alice",
            email="alice@example.com",
            password="plain-password",
        )
        created_user = await repository.create(payload)
        await repository.update(created_user.id, password="not-a-valid-hash")

        authenticated_user = await service.authenticate(payload.email, payload.password)
        assert authenticated_user is None

    asyncio.run(run_test())


def test_auth_local_service_get_user_by_id_delegates_to_repository():
    async def run_test():
        repository = FakeUserRepository()
        service = AuthLocalService(repository, pbkdf2_iterations=TEST_PBKDF2_ITERATIONS)

        created_user = await repository.create(
            UserCreate(
                username="alice",
                email="alice@example.com",
                password="stored-hash",
            )
        )

        fetched_user = await service.get_user_by_id(created_user.id)
        assert fetched_user is not None
        assert fetched_user.id == created_user.id

    asyncio.run(run_test())


def test_auth_local_service_hash_password_is_stored_hashed_in_sqlite(sqlite_db_engine):
    async def run_test():
        async with sqlite_db_engine.async_session() as session:
            repository = SqlUserRepository(session)
            service = AuthLocalService(repository, pbkdf2_iterations=TEST_PBKDF2_ITERATIONS)
            payload = UserCreate(
                username="sqlite-user",
                email="sqlite-user@example.com",
                password="plain-password",
            )

            await service.register(payload)
            stored_hash = await repository.get_password_hash_by_email(payload.email)

            assert stored_hash is not None
            assert stored_hash != payload.password
            assert stored_hash.startswith("pbkdf2_sha256$")
            assert service._verify_password(payload.password, stored_hash)

    asyncio.run(run_test())


def test_auth_local_service_verify_password_with_sqlite_hash(sqlite_db_engine):
    async def run_test():
        async with sqlite_db_engine.async_session() as session:
            repository = SqlUserRepository(session)
            service = AuthLocalService(repository, pbkdf2_iterations=TEST_PBKDF2_ITERATIONS)
            payload = UserCreate(
                username="verify-user",
                email="verify-user@example.com",
                password="plain-password",
            )

            await service.register(payload)
            stored_hash = await repository.get_password_hash_by_email(payload.email)

            assert stored_hash is not None
            assert service._verify_password("plain-password", stored_hash) is True
            assert service._verify_password("wrong-password", stored_hash) is False

    asyncio.run(run_test())


def test_auth_local_service_verify_password_returns_false_when_hash_parsing_fails():
    repository = FakeUserRepository()
    service = AuthLocalService(repository, pbkdf2_iterations=TEST_PBKDF2_ITERATIONS)

    # Invalid iterations and non-hex values force ValueError in _verify_password.
    malformed_hash = "pbkdf2_sha256$not-an-int$not-hex$also-not-hex"

    assert service._verify_password("plain-password", malformed_hash) is False


def test_auth_local_service_register_with_existing_user_none_in_sqlite(sqlite_db_engine):
    async def run_test():
        async with sqlite_db_engine.async_session() as session:
            repository = SqlUserRepository(session)
            service = AuthLocalService(repository, pbkdf2_iterations=TEST_PBKDF2_ITERATIONS)
            payload = UserCreate(
                username="new-user",
                email="new-user@example.com",
                password="plain-password",
            )

            existing_user = await repository.get_by_email(payload.email)
            assert existing_user is None

            created_user = await service.register(payload)
            assert created_user.email == payload.email

    asyncio.run(run_test())


def test_auth_local_service_register_raises_with_existing_user_from_sqlite(sqlite_db_engine):
    async def run_test():
        async with sqlite_db_engine.async_session() as session:
            repository = SqlUserRepository(session)
            service = AuthLocalService(repository, pbkdf2_iterations=TEST_PBKDF2_ITERATIONS)
            payload = UserCreate(
                username="duplicate-user",
                email="duplicate-user@example.com",
                password="plain-password",
            )

            await service.register(payload)
            existing_user = await repository.get_by_email(payload.email)
            assert existing_user is not None

            with pytest.raises(ValueError, match="Email already exists"):
                await service.register(payload)

    asyncio.run(run_test())


@pytest.mark.parametrize(
    "password",
    [
        "p1",
        "p2",
        "p3",
        "p4",
        "p5",
        "p6",
        "p7",
        "p8",
        "p9",
        "p10",
        "p11",
        "p12",
        "p13",
        "p14",
        "p15",
        "p16",
        "p17",
        "p18",
        "p19",
        "p20",
        "p21",
        "p22",
        "p23",
        "p24",
        "p25",
    ],
)
def test_auth_local_service_hash_and_verify_roundtrip_for_many_passwords(password):
    repository = FakeUserRepository()
    service = AuthLocalService(repository, pbkdf2_iterations=TEST_PBKDF2_ITERATIONS)

    stored_hash = service._hash_password(password)
    parts = stored_hash.split("$", 3)

    assert len(parts) == 4
    assert parts[0] == "pbkdf2_sha256"
    assert parts[1] == str(TEST_PBKDF2_ITERATIONS)
    assert parts[2]
    assert parts[3]
    assert stored_hash != password
    assert service._verify_password(password, stored_hash) is True


@pytest.mark.parametrize(
    "malformed_hash",
    [
        "",
        "pbkdf2_sha256",
        "pbkdf2_sha256$1000",
        "pbkdf2_sha256$1000$abcd",
        "unknown_algo$1000$abcd$ef01",
        "pbkdf2_sha256$not-int$abcd$ef01",
        "pbkdf2_sha256$1000$not-hex$ef01",
        "pbkdf2_sha256$1000$abcd$not-hex",
        "pbkdf2_sha256$1000$GG$ef01",
        "pbkdf2_sha256$1000$abcd$GG",
        "pbkdf2_sha256$-1$abcd$ef01",
        "pbkdf2_sha256$0$abcd$ef01",
        "pbkdf2_sha256$999999999999999999999999$abcd$ef01",
        "$1000$abcd$ef01",
        "pbkdf2_sha256$$abcd$ef01",
        "pbkdf2_sha256$1000$$ef01",
        "pbkdf2_sha256$1000$abcd$",
        "pbkdf2_sha256$1000$ab cd$ef01",
        "pbkdf2_sha256$1000$abcd$ef 01",
        "pbkdf2_sha256$1000$abcd$ef01$extra",
    ],
)
def test_auth_local_service_verify_password_rejects_many_malformed_hashes(malformed_hash):
    repository = FakeUserRepository()
    service = AuthLocalService(repository, pbkdf2_iterations=TEST_PBKDF2_ITERATIONS)

    assert service._verify_password("plain-password", malformed_hash) is False


@pytest.mark.parametrize(
    "email,password,wrong_password",
    [
        ("matrix01@example.com", "pass01", "wrong01"),
        ("matrix02@example.com", "pass02", "wrong02"),
        ("matrix03@example.com", "pass03", "wrong03"),
        ("matrix04@example.com", "pass04", "wrong04"),
        ("matrix05@example.com", "pass05", "wrong05"),
        ("matrix06@example.com", "pass06", "wrong06"),
        ("matrix07@example.com", "pass07", "wrong07"),
        ("matrix08@example.com", "pass08", "wrong08"),
        ("matrix09@example.com", "pass09", "wrong09"),
        ("matrix10@example.com", "pass10", "wrong10"),
    ],
)
def test_auth_local_service_authenticate_matrix_for_many_credentials(email, password, wrong_password):
    async def run_test():
        repository = FakeUserRepository()
        service = AuthLocalService(repository, pbkdf2_iterations=TEST_PBKDF2_ITERATIONS)

        payload = UserCreate(
            username=email.split("@")[0],
            email=email,
            password=password,
        )
        created_user = await service.register(payload)

        authenticated_user = await service.authenticate(email, password)
        assert authenticated_user is not None
        assert authenticated_user.id == created_user.id

        rejected_user = await service.authenticate(email, wrong_password)
        assert rejected_user is None

    asyncio.run(run_test())