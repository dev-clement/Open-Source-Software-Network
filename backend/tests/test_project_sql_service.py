import asyncio
from datetime import datetime

import pytest
from unittest.mock import AsyncMock

from app.projects.sql_service import SQLProjectService
from app.projects.sql_repository import SqlRepository
from app.projects.schemas import Project, ProjectCreate
from app.projects.exception import CreateProjectError, ProjectNotFoundError


DT = datetime(2026, 1, 1, 0, 0, 0)


def make_project(**kwargs) -> Project:
    """Build a valid :class:`Project` instance with sensible defaults.

    Any keyword argument overrides the corresponding default field, which
    allows individual tests to customise only the fields they care about
    without repeating all required values every time.

    Args:
        **kwargs: Field overrides forwarded to the :class:`Project` constructor
            (e.g. ``id``, ``title``, ``repository_url``, ``help_wanted``).

    Returns:
        A :class:`Project` schema instance ready to be used as a stub return
        value from repository mocks.
    """
    defaults = dict(
        id=1,
        title="Test Project",
        description="A test project.",
        repository_url="https://github.com/test/project",
        help_wanted=False,
        created_at=DT,
        updated_at=DT,
    )
    defaults.update(kwargs)
    return Project(**defaults)


def make_repository() -> AsyncMock:
    """Create an :class:`AsyncMock` that mimics :class:`SqlRepository`.

    Using ``spec=SqlRepository`` ensures the mock only exposes methods that
    exist on the real repository, so any typo in a method name causes the
    test to fail immediately rather than silently succeeding.

    Returns:
        An :class:`AsyncMock` pre-configured with the :class:`SqlRepository`
        interface.
    """
    return AsyncMock(spec=SqlRepository)


def make_service(repository: AsyncMock | None = None) -> SQLProjectService:
    """Instantiate a :class:`SQLProjectService` wired to a mock repository.

    When *repository* is omitted a fresh mock is created via
    :func:`make_repository`, which is convenient for tests that only need to
    verify high-level behaviour and do not need to inspect repository calls.
    Pass an explicit *repository* when the test needs to configure return
    values or assert on specific calls afterward.

    Args:
        repository: Optional mock repository to inject. Defaults to a new
            :class:`AsyncMock` built by :func:`make_repository`.

    Returns:
        A :class:`SQLProjectService` instance ready to be exercised in tests.
    """
    return SQLProjectService(repository=repository or make_repository())


# ---------------------------------------------------------------------------
# create
# ---------------------------------------------------------------------------

def test_create_project_success():
    """create should persist the project when no project with the same URL exists."""
    repository = make_repository()
    service = make_service(repository)
    payload = ProjectCreate(
        title="New Project",
        description="Brand new project.",
        repository_url="https://github.com/test/new-project",
        help_wanted=False,
    )
    expected = make_project(title=payload.title, repository_url=str(payload.repository_url))
    repository.get_by_repository_url.return_value = None
    repository.create.return_value = expected

    async def run():
        result = await service.create(payload)
        assert result == expected

    asyncio.run(run())

    repository.get_by_repository_url.assert_called_once_with(payload.repository_url)
    repository.create.assert_called_once_with(payload)


def test_create_project_raises_when_url_already_exists():
    """create should raise CreateProjectError when a project with the same URL already exists."""
    repository = make_repository()
    service = make_service(repository)
    payload = ProjectCreate(
        title="Duplicate Project",
        repository_url="https://github.com/test/duplicate",
        help_wanted=False,
    )
    repository.get_by_repository_url.return_value = make_project(
        repository_url=str(payload.repository_url)
    )

    async def run():
        with pytest.raises(CreateProjectError):
            await service.create(payload)

    asyncio.run(run())

    repository.get_by_repository_url.assert_called_once_with(payload.repository_url)
    repository.create.assert_not_called()


def test_create_error_message_contains_repository_url():
    """create should include the conflicting URL in the CreateProjectError message."""
    repository = make_repository()
    service = make_service(repository)
    payload = ProjectCreate(
        title="Duplicate Project",
        repository_url="https://github.com/test/duplicate",
        help_wanted=False,
    )
    repository.get_by_repository_url.return_value = make_project(
        repository_url=str(payload.repository_url)
    )

    async def run():
        with pytest.raises(CreateProjectError) as exc_info:
            await service.create(payload)
        assert str(payload.repository_url) in str(exc_info.value)

    asyncio.run(run())


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------

def test_list_returns_all_projects():
    """list should return the full list of projects from the repository."""
    repository = make_repository()
    service = make_service(repository)
    projects = [
        make_project(id=1, title="Project A"),
        make_project(id=2, title="Project B", repository_url="https://github.com/test/b"),
    ]
    repository.list.return_value = projects

    async def run():
        result = await service.list()
        assert result == projects

    asyncio.run(run())

    repository.list.assert_called_once_with(skip=0, limit=100)


def test_list_forwards_custom_pagination():
    """list should forward custom skip and limit values to the repository."""
    repository = make_repository()
    service = make_service(repository)
    repository.list.return_value = []

    async def run():
        await service.list(skip=10, limit=25)

    asyncio.run(run())

    repository.list.assert_called_once_with(skip=10, limit=25)


def test_list_returns_empty_list_when_no_projects():
    """list should return an empty list when the database contains no projects."""
    repository = make_repository()
    service = make_service(repository)
    repository.list.return_value = []

    async def run():
        result = await service.list()
        assert result == []

    asyncio.run(run())


# ---------------------------------------------------------------------------
# get_by_id
# ---------------------------------------------------------------------------

def test_get_by_id_returns_project_when_found():
    """get_by_id should return the project when a matching id exists."""
    repository = make_repository()
    service = make_service(repository)
    project = make_project(id=42, title="Found Project")
    repository.get_by_id.return_value = project

    async def run():
        result = await service.get_by_id(42)
        assert result == project

    asyncio.run(run())

    repository.get_by_id.assert_called_once_with(42)


def test_get_by_id_raises_when_not_found():
    """get_by_id should raise ProjectNotFoundError when no project matches the id."""
    repository = make_repository()
    service = make_service(repository)
    repository.get_by_id.return_value = None

    async def run():
        with pytest.raises(ProjectNotFoundError) as exc_info:
            await service.get_by_id(99)
        assert exc_info.value.get_project_id() == 99

    asyncio.run(run())

    repository.get_by_id.assert_called_once_with(99)


def test_get_by_id_error_message_contains_project_id():
    """ProjectNotFoundError message should include the missing project id."""
    repository = make_repository()
    service = make_service(repository)
    repository.get_by_id.return_value = None

    async def run():
        with pytest.raises(ProjectNotFoundError) as exc_info:
            await service.get_by_id(99)
        assert "99" in str(exc_info.value)

    asyncio.run(run())


# ---------------------------------------------------------------------------
# list_help_wanted
# ---------------------------------------------------------------------------

def test_list_help_wanted_returns_only_flagged_projects():
    """list_help_wanted should return only projects that have help_wanted set to True."""
    repository = make_repository()
    service = make_service(repository)
    help_wanted_projects = [
        make_project(id=1, title="Open Project", help_wanted=True),
        make_project(id=2, title="Another Open Project", repository_url="https://github.com/test/open2", help_wanted=True),
    ]
    repository.list_help_wanted.return_value = help_wanted_projects

    async def run():
        result = await service.list_help_wanted()
        assert result == help_wanted_projects
        assert all(p.help_wanted for p in result)

    asyncio.run(run())

    repository.list_help_wanted.assert_called_once()


def test_list_help_wanted_returns_empty_list_when_no_flagged_projects():
    """list_help_wanted should return an empty list when no projects have help_wanted set."""
    repository = make_repository()
    service = make_service(repository)
    repository.list_help_wanted.return_value = []

    async def run():
        result = await service.list_help_wanted()
        assert result == []

    asyncio.run(run())

    repository.list_help_wanted.assert_called_once()
