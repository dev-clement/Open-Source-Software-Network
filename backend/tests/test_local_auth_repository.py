from app.auth.repository import SqlUserRepository
from app.auth.schemas import UserCreate
from datetime import datetime


class FakeAsyncSession:
    def __init__(self):
        self.added = []
        self.committed = False
        self.refreshed = []

    def add(self, instance):
        self.added.append(instance)

    async def commit(self):
        self.committed = True

    async def refresh(self, instance):
        instance.id = 1
        instance.created_at = datetime(2026, 4, 9, 8, 0, 0)
        instance.updated_at = datetime(2026, 4, 9, 8, 0, 0)
        self.refreshed.append(instance)


def test_sql_user_repository_create_persists_user():
    async def run_test():
        session = FakeAsyncSession()
        repository = SqlUserRepository(session)

        user = await repository.create(
            UserCreate(
                username="alice",
                email="alice@example.com",
                password="hashed-password",
            )
        )

        assert len(session.added) == 1
        persisted_model = session.added[0]
        assert persisted_model.username == "alice"
        assert persisted_model.email == "alice@example.com"
        assert persisted_model.password == "hashed-password"
        assert session.committed is True
        assert len(session.refreshed) == 1

        assert user.id == 1
        assert user.username == "alice"
        assert user.email == "alice@example.com"

    import asyncio

    asyncio.run(run_test())