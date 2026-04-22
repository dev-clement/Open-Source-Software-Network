import asyncio
from datetime import datetime

import pytest
from unittest.mock import AsyncMock

from app.projects.sql_service import SQLProjectService
from app.projects.sql_repository import SqlRepository
from app.projects.schemas import Project, ProjectCreate, ProjectUpdate
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
        owner_id=42,
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
        owner_id=42,
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
        owner_id=42,
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
        owner_id=42,
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


def test_create_calls_lookup_before_create():
    """create should check URL uniqueness before attempting repository.create."""
    repository = make_repository()
    service = make_service(repository)
    payload = ProjectCreate(
        title="Ordered Project",
        repository_url="https://github.com/test/ordered",
        help_wanted=False,
        owner_id=42,
    )
    repository.get_by_repository_url.return_value = None
    repository.create.return_value = make_project(repository_url=str(payload.repository_url))

    async def run():
        await service.create(payload)

    asyncio.run(run())

    call_names = [call[0] for call in repository.mock_calls]
    assert "get_by_repository_url" in call_names
    assert "create" in call_names
    assert call_names.index("get_by_repository_url") < call_names.index("create")


def test_create_propagates_lookup_exception():
    """create should bubble up repository errors during duplicate URL lookup."""
    repository = make_repository()
    service = make_service(repository)
    payload = ProjectCreate(
        title="Lookup Failure",
        repository_url="https://github.com/test/lookup-failure",
        help_wanted=False,
        owner_id=42,
    )
    repository.get_by_repository_url.side_effect = RuntimeError("lookup failed")

    async def run():
        with pytest.raises(RuntimeError, match="lookup failed"):
            await service.create(payload)

    asyncio.run(run())

    repository.create.assert_not_called()


def test_create_propagates_create_exception():
    """create should bubble up repository errors raised while persisting the project."""
    repository = make_repository()
    service = make_service(repository)
    payload = ProjectCreate(
        title="Persist Failure",
        repository_url="https://github.com/test/persist-failure",
        owner_id=42,
        help_wanted=False,
    )
    repository.get_by_repository_url.return_value = None
    repository.create.side_effect = RuntimeError("create failed")

    async def run():
        with pytest.raises(RuntimeError, match="create failed"):
            await service.create(payload)

    asyncio.run(run())


def test_create_passes_same_payload_instance_to_repository():
    """create should pass through the same ProjectCreate instance received by the service."""
    repository = make_repository()
    service = make_service(repository)
    payload = ProjectCreate(
        title="Identity Project",
        repository_url="https://github.com/test/identity",
        owner_id=42,
        help_wanted=False,
    )
    repository.get_by_repository_url.return_value = None
    repository.create.return_value = make_project(repository_url=str(payload.repository_url))

    async def run():
        await service.create(payload)

    asyncio.run(run())

    forwarded_payload = repository.create.call_args[0][0]
    assert forwarded_payload is payload


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


@pytest.mark.parametrize(
    "skip,limit",
    [
        (0, 100),
        (0, 1),
        (3, 5),
        (10, 0),
    ],
)
def test_list_forwards_pagination_matrix(skip, limit):
    """list should forward different pagination combinations to repository.list."""
    repository = make_repository()
    service = make_service(repository)
    repository.list.return_value = []

    async def run():
        await service.list(skip=skip, limit=limit)

    asyncio.run(run())

    repository.list.assert_called_once_with(skip=skip, limit=limit)


def test_list_propagates_repository_exception():
    """list should bubble up errors coming from repository.list."""
    repository = make_repository()
    service = make_service(repository)
    repository.list.side_effect = RuntimeError("list failed")

    async def run():
        with pytest.raises(RuntimeError, match="list failed"):
            await service.list()

    asyncio.run(run())


def test_list_returns_paginated_subset_from_repository():
    """list should return the subset produced by the repository for the requested pagination."""
    repository = make_repository()
    service = make_service(repository)
    paginated_projects = [
        make_project(id=2, title="Project B"),
        make_project(id=3, title="Project C", repository_url="https://github.com/test/c"),
    ]
    repository.list.return_value = paginated_projects

    async def run():
        result = await service.list(skip=1, limit=2)
        assert [project.id for project in result] == [2, 3]

    asyncio.run(run())

    repository.list.assert_called_once_with(skip=1, limit=2)


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


def test_get_by_id_returns_same_repository_instance():
    """get_by_id should return the same schema object returned by repository.get_by_id."""
    repository = make_repository()
    service = make_service(repository)
    project = make_project(id=51, title="Identity Return")
    repository.get_by_id.return_value = project

    async def run():
        result = await service.get_by_id(51)
        assert result is project

    asyncio.run(run())


def test_get_by_id_propagates_repository_exception():
    """get_by_id should bubble up repository errors unrelated to not-found cases."""
    repository = make_repository()
    service = make_service(repository)
    repository.get_by_id.side_effect = RuntimeError("db unavailable")

    async def run():
        with pytest.raises(RuntimeError, match="db unavailable"):
            await service.get_by_id(7)

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

    repository.list_help_wanted.assert_called_once_with(skip=0, limit=100)


def test_list_help_wanted_returns_empty_list_when_no_flagged_projects():
    """list_help_wanted should return an empty list when no projects have help_wanted set."""
    repository = make_repository()
    service = make_service(repository)
    repository.list_help_wanted.return_value = []

    async def run():
        result = await service.list_help_wanted()
        assert result == []

    asyncio.run(run())

    repository.list_help_wanted.assert_called_once_with(skip=0, limit=100)


def test_list_help_wanted_forwards_custom_pagination():
    """list_help_wanted should forward custom skip and limit to the repository."""
    repository = make_repository()
    service = make_service(repository)
    repository.list_help_wanted.return_value = []

    async def run():
        await service.list_help_wanted(skip=4, limit=6)

    asyncio.run(run())

    repository.list_help_wanted.assert_called_once_with(skip=4, limit=6)


@pytest.mark.parametrize(
    "skip,limit",
    [
        (0, 100),
        (0, 2),
        (2, 3),
        (6, 0),
    ],
)
def test_list_help_wanted_forwards_pagination_matrix(skip, limit):
    """list_help_wanted should forward different pagination combinations."""
    repository = make_repository()
    service = make_service(repository)
    repository.list_help_wanted.return_value = []

    async def run():
        await service.list_help_wanted(skip=skip, limit=limit)

    asyncio.run(run())

    repository.list_help_wanted.assert_called_once_with(skip=skip, limit=limit)


def test_list_help_wanted_propagates_repository_exception():
    """list_help_wanted should bubble up repository.list_help_wanted failures."""
    repository = make_repository()
    service = make_service(repository)
    repository.list_help_wanted.side_effect = RuntimeError("help_wanted failed")

    async def run():
        with pytest.raises(RuntimeError, match="help_wanted failed"):
            await service.list_help_wanted()

    asyncio.run(run())


def test_list_help_wanted_preserves_repository_order():
    """list_help_wanted should preserve project ordering from repository output."""
    repository = make_repository()
    service = make_service(repository)
    repository.list_help_wanted.return_value = [
        make_project(id=5, title="Open E", help_wanted=True),
        make_project(id=2, title="Open B", repository_url="https://github.com/test/open-b", help_wanted=True),
        make_project(id=9, title="Open I", repository_url="https://github.com/test/open-i", help_wanted=True),
    ]

    async def run():
        result = await service.list_help_wanted()
        assert [project.id for project in result] == [5, 2, 9]

    asyncio.run(run())


def test_list_help_wanted_returns_paginated_subset_from_repository():
    """list_help_wanted should return the paginated subset produced by the repository."""
    repository = make_repository()
    service = make_service(repository)
    paginated_help_wanted = [
        make_project(id=2, title="Open B", help_wanted=True),
        make_project(id=3, title="Open C", repository_url="https://github.com/test/open-c", help_wanted=True),
    ]
    repository.list_help_wanted.return_value = paginated_help_wanted

    async def run():
        result = await service.list_help_wanted(skip=1, limit=2)
        assert [project.id for project in result] == [2, 3]

    asyncio.run(run())

    repository.list_help_wanted.assert_called_once_with(skip=1, limit=2)


# ---------------------------------------------------------------------------
# edit
# ---------------------------------------------------------------------------

def test_edit_updates_project_when_found():
    """edit should return the updated project when the target exists."""
    repository = make_repository()
    service = make_service(repository)
    payload = ProjectUpdate(title="Updated Title")
    class DummyUser:
            id = 42
    user = DummyUser()  # Dummy user object for test
    repository.get_by_id.return_value = make_project(id=1)
    expected = make_project(id=1, title="Updated Title")
    repository.edit.return_value = expected

    async def run():
        result = await service.edit(project_id=1, project_data=payload, user=user)
        assert result == expected

    asyncio.run(run())

    repository.get_by_id.assert_called_once_with(1)
    repository.get_by_repository_url.assert_not_called()
    repository.edit.assert_called_once_with(project_id=1, project_data=payload, user=user)


def test_edit_raises_when_project_not_found():
    """edit should raise ProjectNotFoundError when the target project does not exist."""
    repository = make_repository()
    service = make_service(repository)
    payload = ProjectUpdate(title="No Target")
    user = object()
    repository.get_by_id.return_value = None

    async def run():
        with pytest.raises(ProjectNotFoundError) as exc_info:
            await service.edit(project_id=999, project_data=payload, user=user)
        assert exc_info.value.get_project_id() == 999

    asyncio.run(run())

    repository.get_by_id.assert_called_once_with(999)
    repository.get_by_repository_url.assert_not_called()
    repository.edit.assert_not_called()


def test_edit_checks_repository_url_conflict_for_another_project():
    """edit should reject repository_url updates that belong to another project."""
    repository = make_repository()
    service = make_service(repository)
    payload = ProjectUpdate(repository_url="https://github.com/test/conflict")
    user = object()
    repository.get_by_id.return_value = make_project(id=1)
    repository.get_by_repository_url.return_value = make_project(
        id=2,
        repository_url="https://github.com/test/conflict",
    )

    async def run():
        with pytest.raises(CreateProjectError):
            await service.edit(project_id=1, project_data=payload, user=user)

    asyncio.run(run())

    repository.get_by_id.assert_called_once_with(1)
    repository.get_by_repository_url.assert_called_once_with(payload.repository_url)
    repository.edit.assert_not_called()


def test_edit_raises_when_repository_url_does_not_exist():
    """edit should reject repository_url updates when the URL does not resolve to a project."""
    repository = make_repository()
    service = make_service(repository)
    payload = ProjectUpdate(repository_url="https://github.com/test/missing")
    user = object()
    repository.get_by_id.return_value = make_project(id=1)
    repository.get_by_repository_url.return_value = None

    async def run():
        with pytest.raises(CreateProjectError) as exc_info:
            await service.edit(project_id=1, project_data=payload, user=user)
        assert "does not exist" in str(exc_info.value)

    asyncio.run(run())

    repository.get_by_id.assert_called_once_with(1)
    repository.get_by_repository_url.assert_called_once_with(payload.repository_url)
    repository.edit.assert_not_called()


def test_edit_allows_same_repository_url_for_same_project():
    """edit should allow repository_url when it belongs to the same project."""
    repository = make_repository()
    service = make_service(repository)
    payload = ProjectUpdate(repository_url="https://github.com/test/project")
    user = object()
    repository.get_by_id.return_value = make_project(id=1, repository_url="https://github.com/test/project")
    repository.get_by_repository_url.return_value = make_project(
        id=1,
        repository_url="https://github.com/test/project",
    )
    repository.edit.return_value = make_project(id=1, repository_url="https://github.com/test/project")

    async def run():
        result = await service.edit(project_id=1, project_data=payload, user=user)
        assert result.id == 1

    asyncio.run(run())

    repository.get_by_id.assert_called_once_with(1)
    repository.get_by_repository_url.assert_called_once_with(payload.repository_url)
    repository.edit.assert_called_once_with(project_id=1, project_data=payload, user=user)


# ---------------------------------------------------------------------------
# delete_by_id and delete_by_repository_url
# ---------------------------------------------------------------------------

def make_user(user_id):
    class DummyUser:
        id = user_id
    return DummyUser()

def test_delete_by_id_not_found():
    """delete_by_id returns False if project does not exist."""
    repository = make_repository()
    service = make_service(repository)
    user = make_user(42)
    repository.delete_by_id.return_value = False

    async def run():
        result = await service.delete_by_id(999, user)
        assert result is False

    asyncio.run(run())
    repository.delete_by_id.assert_called_once_with(999, user)

def test_delete_by_id_forbidden():
    """delete_by_id raises ForbiddenError if user is not owner."""
    repository = make_repository()
    service = make_service(repository)
    user = make_user(42)
    repository.delete_by_id.side_effect = Exception("ForbiddenError")

    async def run():
        with pytest.raises(Exception) as exc_info:
            await service.delete_by_id(1, user)
        assert "ForbiddenError" in str(exc_info.value)

    asyncio.run(run())
    repository.delete_by_id.assert_called_once_with(1, user)

def test_delete_by_id_success():
    """delete_by_id deletes project if user is owner."""
    repository = make_repository()
    service = make_service(repository)
    user = make_user(42)
    repository.delete_by_id.return_value = True

    async def run():
        result = await service.delete_by_id(1, user)
        assert result is True

    asyncio.run(run())
    repository.delete_by_id.assert_called_once_with(1, user)

def test_delete_by_repository_url_not_found():
    """delete_by_repository_url returns False if project does not exist."""
    repository = make_repository()
    service = make_service(repository)
    user = make_user(42)
    repository.delete_by_repository_url.return_value = False

    async def run():
        result = await service.delete_by_repository_url("missing-url", user)
        assert result is False

    asyncio.run(run())
    repository.delete_by_repository_url.assert_called_once_with("missing-url", user)

def test_delete_by_repository_url_forbidden():
    """delete_by_repository_url raises ForbiddenError if user is not owner."""
    repository = make_repository()
    service = make_service(repository)
    user = make_user(42)
    repository.delete_by_repository_url.side_effect = Exception("ForbiddenError")

    async def run():
        with pytest.raises(Exception) as exc_info:
            await service.delete_by_repository_url("url", user)
        assert "ForbiddenError" in str(exc_info.value)

    asyncio.run(run())
    repository.delete_by_repository_url.assert_called_once_with("url", user)

def test_delete_by_repository_url_success():
    """delete_by_repository_url deletes project if user is owner."""
    repository = make_repository()
    service = make_service(repository)
    user = make_user(42)
    repository.delete_by_repository_url.return_value = True

    async def run():
        result = await service.delete_by_repository_url("url", user)
        assert result is True

    asyncio.run(run())
    repository.delete_by_repository_url.assert_called_once_with("url", user)
