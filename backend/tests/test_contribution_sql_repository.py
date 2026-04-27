import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel, Field
from datetime import datetime
from app.contributions.sql_repository import SqlContributionRepository
from app.domain.enums import ContributionStatus
from sqlalchemy import text
import asyncio
from unittest.mock import patch

# Use an in-memory SQLite database for testing
DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Define the test model globally with a unique table name
class SQLiteTestContribution(SQLModel, table=True):
    __tablename__ = "contributions_test"
    id: int = Field(default=None, primary_key=True)
    fk_user_id: int
    fk_project_id: int
    status: ContributionStatus = Field(default=ContributionStatus.INTERESTED)
    applied_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

@pytest_asyncio.fixture(scope="module")
def event_loop():
    loop = asyncio.get_event_loop()
    yield loop

@pytest_asyncio.fixture(scope="module")
async def async_session():
    engine = create_async_engine(DATABASE_URL, echo=False, future=True)
    # Create the test table once per session
    async with engine.begin() as conn:
        await conn.run_sync(SQLiteTestContribution.metadata.create_all)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    async with async_session() as session:
        yield session

@pytest_asyncio.fixture()
async def repository(async_session):
    await async_session.execute(text("DELETE FROM contributions_test"))
    await async_session.commit()
    with patch("app.contributions.sql_repository.Contribution", SQLiteTestContribution):
        user_id = 1
        project_id = 1
        contribution = SQLiteTestContribution(
            fk_user_id=user_id,
            fk_project_id=project_id,
            status=ContributionStatus.INTERESTED,
            applied_at=datetime(2026, 4, 27, 0, 0, 0),
            updated_at=datetime(2026, 4, 27, 0, 0, 0)
        )
        async_session.add(contribution)
        await async_session.commit()
        await async_session.refresh(contribution)
        yield SqlContributionRepository(async_session)

@pytest.mark.asyncio
async def test_get_by_id_invalid(repository):
    result = await repository.get_by_id(999)
    assert result is None

@pytest.mark.asyncio
async def test_get_by_id_valid(repository):
    result = await repository.get_by_id(1)
    assert result is not None
    assert result.id == 1

@pytest.mark.asyncio
async def test_get_by_project_valid(repository):
    results = await repository.get_by_project(1)
    assert len(results) == 1
    assert results[0].fk_project_id == 1

@pytest.mark.asyncio
async def test_list_by_user_valid(repository):
    results = await repository.list_by_user(1)
    assert len(results) == 1
    assert results[0].fk_user_id == 1

@pytest.mark.asyncio
async def test_list_by_user_invalid(repository):
    results = await repository.list_by_user(999)
    assert results == []

@pytest.mark.asyncio
async def test_list_by_project_valid(repository):
    results = await repository.list_by_project(1)
    assert len(results) == 1
    assert results[0].fk_project_id == 1

@pytest.mark.asyncio
async def test_get_by_user_and_project_invalid_user(repository):
    result = await repository.get_by_user_and_project(999, 1)
    assert result is None

@pytest.mark.asyncio
async def test_get_by_user_and_project_invalid_project(repository):
    result = await repository.get_by_user_and_project(1, 999)
    assert result is None

@pytest.mark.asyncio
async def test_get_by_user_and_project_invalid_both(repository):
    result = await repository.get_by_user_and_project(999, 999)
    assert result is None

@pytest.mark.asyncio
async def test_get_by_user_and_project_valid(repository):
    result = await repository.get_by_user_and_project(1, 1)
    assert result is not None
    assert result.fk_user_id == 1
    assert result.fk_project_id == 1

@pytest.mark.asyncio
async def test_get_by_user_and_project_valid_user_no_contribution(repository):
    result = await repository.get_by_user_and_project(1, 2)
    assert result is None
