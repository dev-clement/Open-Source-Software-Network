from app.projects.exception import CreateProjectError, ForbiddenError
import asyncio
from sqlalchemy import Column, Integer
from datetime import datetime
import pytest
from unittest.mock import AsyncMock, MagicMock, call
from sqlalchemy.dialects import sqlite as _sqlite_dialect
from app.projects.sql_repository import SqlRepository
from app.projects.schemas import ProjectCreate, ProjectUpdate
from app.db.models import Project as ProjectModel

# Patch: ensure ProjectModel.owner_id is available as a class attribute for tests
if not hasattr(ProjectModel, 'owner_id'):
    ProjectModel.owner_id = Column(Integer)


def _compiled_sql(statement) -> str:
    """Compile a SQLAlchemy statement to SQL text with literal bound values."""
    return str(
        statement.compile(
            dialect=_sqlite_dialect.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )


DT = datetime(2026, 1, 1, 0, 0, 0)


def make_session() -> AsyncMock:
    """Create a fresh mock database session."""
    session = AsyncMock()
    # add() is synchronous in SQLAlchemy's AsyncSession
    session.add = MagicMock()
    return session


def make_repository(session: AsyncMock | None = None) -> SqlRepository:
    """Create a SqlRepository with an optional mock session."""
    return SqlRepository(session=session or make_session())


def configure_refresh_with_db_defaults(session: AsyncMock) -> None:
    """Simulate database-generated fields populated during refresh."""

    async def refresh_side_effect(model: ProjectModel) -> None:
        model.id = 1
        model.created_at = DT
        model.updated_at = DT

    session.refresh.side_effect = refresh_side_effect


# ---------------------------------------------------------------------------
# create
# ---------------------------------------------------------------------------

def test_create_project_success():
    """Test successful creation of a project."""
    session = make_session()
    configure_refresh_with_db_defaults(session)
    repo = make_repository(session)
    project_data = ProjectCreate(
        title="Test Project",
        description="A project for testing.",
        repository_url="https://github.com/test/test-project",
        help_wanted=True,
        owner_id=42,
    )

    async def run():
        await repo.create(project_data)

    asyncio.run(run())

    session.add.assert_called_once()
    session.commit.assert_called_once()
    session.refresh.assert_called_once()


def test_create_project_commit_fails():
    """Test that a rollback is triggered when commit raises."""
    session = make_session()
    session.commit.side_effect = Exception("Commit failed")
    repo = make_repository(session)
    project_data = ProjectCreate(
        title="Test Project",
        description="A project for testing.",
        repository_url="https://github.com/test/test-project",
        owner_id=42,
    )

    async def run():
        with pytest.raises(CreateProjectError, match="Cannot create the project") as exc_info:
            await repo.create(project_data)
        assert exc_info.value.__cause__ is not None
        assert str(exc_info.value.__cause__) == "Commit failed"

    asyncio.run(run())

    session.add.assert_called_once()
    session.commit.assert_called_once()
    session.rollback.assert_called_once()
    session.refresh.assert_not_called()


def test_create_project_with_minimal_data():
    """Test creating a project with only the required fields."""
    session = make_session()
    configure_refresh_with_db_defaults(session)
    repo = make_repository(session)
    project_data = ProjectCreate(
        title="Minimal Project",
        repository_url="https://github.com/test/minimal",
        owner_id=42,
    )

    async def run():
        await repo.create(project_data)

    asyncio.run(run())

    session.add.assert_called_once()
    session.commit.assert_called_once()
    session.refresh.assert_called_once()
    added_model = session.add.call_args[0][0]
    assert added_model.title == "Minimal Project"
    assert added_model.description is None
    assert added_model.help_wanted is False
    assert added_model.owner_id == 42


def test_create_project_passes_all_fields_to_model():
    """Test that all fields from ProjectCreate are forwarded to the db model."""
    session = make_session()
    configure_refresh_with_db_defaults(session)
    repo = make_repository(session)
    project_data = ProjectCreate(
        title="Full Project",
        description="Full description.",
        repository_url="https://github.com/test/full",
        help_wanted=True,
        owner_id=42,
    )

    async def run():
        await repo.create(project_data)

    asyncio.run(run())

    added_model = session.add.call_args[0][0]
    assert added_model.title == "Full Project"
    assert added_model.description == "Full description."
    assert added_model.help_wanted is True


def test_create_calls_add_before_commit():
    """Test that add is called before commit during creation."""
    session = make_session()
    configure_refresh_with_db_defaults(session)
    repo = make_repository(session)
    project_data = ProjectCreate(
        title="Order Test",
        repository_url="https://github.com/test/order",
        owner_id=42,
    )

    async def run():
        await repo.create(project_data)

    asyncio.run(run())

    method_names = [c[0] for c in session.mock_calls]
    assert "add" in method_names
    assert "commit" in method_names
    assert method_names.index("add") < method_names.index("commit")


# ---------------------------------------------------------------------------
# get_by_id
# ---------------------------------------------------------------------------

def test_get_by_id_found():
    """Test retrieving a project by ID when it exists."""
    session = make_session()
    repo = make_repository(session)
    project_id = 1
    mock_db_row = ProjectModel(
        id=project_id,
        title="Test Project",
        repository_url="https://github.com/test/project",
        created_at=DT,
        updated_at=DT,
        owner_id=42,
    )
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_db_row
    session.execute.return_value = mock_result

    async def run():
        return await repo.get_by_id(project_id)

    project = asyncio.run(run())

    assert project is not None
    assert project.id == project_id
    session.execute.assert_called_once()


def test_get_by_id_not_found():
    """Test retrieving a project by ID when it does not exist."""
    session = make_session()
    repo = make_repository(session)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    session.execute.return_value = mock_result

    async def run():
        return await repo.get_by_id(999)

    project = asyncio.run(run())

    assert project is None
    session.execute.assert_called_once()


def test_get_by_id_returns_project_schema():
    """Test that get_by_id returns a Project schema, not a raw model."""
    from app.projects.schemas import Project
    session = make_session()
    repo = make_repository(session)
    from datetime import datetime
    mock_db_row = ProjectModel(
        id=1,
        title="Schema Test",
        repository_url="https://github.com/test/schema",
        help_wanted=False,
        owner_id=42,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_db_row
    session.execute.return_value = mock_result

    async def run():
        return await repo.get_by_id(1)

    project = asyncio.run(run())

    assert isinstance(project, Project)


def test_get_by_id_executes_query():
    """Test that get_by_id always calls session.execute."""
    session = make_session()
    repo = make_repository(session)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    session.execute.return_value = mock_result

    async def run():
        await repo.get_by_id(42)

    asyncio.run(run())

    session.execute.assert_called_once()


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------

def test_list_projects():
    """Test listing all projects returns all rows."""
    session = make_session()
    repo = make_repository(session)
    mock_rows = [
        ProjectModel(id=1, title="Project 1", repository_url="https://github.com/test/p1", owner_id=42, created_at=DT, updated_at=DT),
        ProjectModel(id=2, title="Project 2", repository_url="https://github.com/test/p2", owner_id=42, created_at=DT, updated_at=DT),
    ]
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = mock_rows
    session.execute.return_value = mock_result

    async def run():
        return await repo.list()

    projects = asyncio.run(run())

    assert len(projects) == 2
    assert projects[0].title == "Project 1"
    assert projects[1].title == "Project 2"
    session.execute.assert_called_once()


def test_list_projects_empty():
    """Test listing projects when there are none returns an empty list."""
    session = make_session()
    repo = make_repository(session)
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    session.execute.return_value = mock_result

    async def run():
        return await repo.list()

    projects = asyncio.run(run())

    assert projects == []
    session.execute.assert_called_once()


def test_list_default_pagination():
    """Test that list uses default skip=0 and limit=100."""
    session = make_session()
    repo = make_repository(session)
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    session.execute.return_value = mock_result

    async def run():
        await repo.list()

    asyncio.run(run())

    session.execute.assert_called_once()
    statement = session.execute.call_args[0][0]
    sql = _compiled_sql(statement)
    assert "LIMIT 100" in sql
    assert "OFFSET 0" in sql


def test_list_with_skip():
    """Test that list forwards skip to the query."""
    session = make_session()
    repo = make_repository(session)
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    session.execute.return_value = mock_result

    async def run():
        await repo.list(skip=10)

    asyncio.run(run())

    session.execute.assert_called_once()
    statement = session.execute.call_args[0][0]
    sql = _compiled_sql(statement)
    assert "LIMIT 100" in sql
    assert "OFFSET 10" in sql


def test_list_with_limit():
    """Test that list forwards limit to the query."""
    session = make_session()
    repo = make_repository(session)
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    session.execute.return_value = mock_result

    async def run():
        await repo.list(limit=5)

    asyncio.run(run())

    session.execute.assert_called_once()
    statement = session.execute.call_args[0][0]
    sql = _compiled_sql(statement)
    assert "LIMIT 5" in sql
    assert "OFFSET 0" in sql


def test_list_with_skip_and_limit_returns_paginated_result():
    """Test that list returns only the paginated rows provided by the query result."""
    session = make_session()
    repo = make_repository(session)
    mock_rows = [
        ProjectModel(id=2, title="Project 2", repository_url="https://github.com/test/p2", owner_id=42, created_at=DT, updated_at=DT),
        ProjectModel(id=3, title="Project 3", repository_url="https://github.com/test/p3", owner_id=42, created_at=DT, updated_at=DT),
    ]
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = mock_rows
    session.execute.return_value = mock_result

    async def run():
        return await repo.list(skip=1, limit=2)

    projects = asyncio.run(run())

    assert [project.id for project in projects] == [2, 3]
    statement = session.execute.call_args[0][0]
    sql = _compiled_sql(statement)
    assert "LIMIT 2" in sql
    assert "OFFSET 1" in sql


def test_list_returns_project_schemas():
    """Test that list returns Project schema instances."""
    from app.projects.schemas import Project
    from datetime import datetime
    session = make_session()
    repo = make_repository(session)
    mock_rows = [
        ProjectModel(
            id=1,
            title="Schema Project",
            repository_url="https://github.com/test/s1",
            help_wanted=False,
            owner_id=42,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
    ]
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = mock_rows
    session.execute.return_value = mock_result

    async def run():
        return await repo.list()

    projects = asyncio.run(run())

    assert all(isinstance(p, Project) for p in projects)


# ---------------------------------------------------------------------------
# get_by_repository_url
# ---------------------------------------------------------------------------

def test_get_by_repository_url_found():
    """Test retrieving a project by URL when it exists."""
    session = make_session()
    repo = make_repository(session)
    url = "https://github.com/test/project"
    mock_db_row = ProjectModel(id=1, title="URL Project", repository_url=url, owner_id=42, created_at=DT, updated_at=DT)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_db_row
    session.execute.return_value = mock_result

    async def run():
        return await repo.get_by_repository_url(url)

    project = asyncio.run(run())

    assert project is not None
    session.execute.assert_called_once()


def test_get_by_repository_url_not_found():
    """Test retrieving a project by URL when it does not exist."""
    session = make_session()
    repo = make_repository(session)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    session.execute.return_value = mock_result

    async def run():
        return await repo.get_by_repository_url("https://github.com/test/missing")

    project = asyncio.run(run())

    assert project is None
    session.execute.assert_called_once()


def test_get_by_repository_url_executes_query():
    """Test that get_by_repository_url always calls session.execute."""
    session = make_session()
    repo = make_repository(session)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    session.execute.return_value = mock_result

    async def run():
        await repo.get_by_repository_url("https://github.com/any/url")

    asyncio.run(run())

    session.execute.assert_called_once()


def test_get_by_repository_url_returns_project_schema():
    """Test that get_by_repository_url returns a Project schema instance."""
    from app.projects.schemas import Project
    from datetime import datetime
    session = make_session()
    repo = make_repository(session)
    url = "https://github.com/test/schema-url"
    mock_db_row = ProjectModel(
        id=5,
        title="URL Schema Test",
        repository_url=url,
        help_wanted=False,
        owner_id=42,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_db_row
    session.execute.return_value = mock_result

    async def run():
        return await repo.get_by_repository_url(url)

    project = asyncio.run(run())

    assert isinstance(project, Project)


# ---------------------------------------------------------------------------
# list_help_wanted
# ---------------------------------------------------------------------------

def test_list_help_wanted_projects():
    """Test listing projects with help_wanted=True."""
    session = make_session()
    repo = make_repository(session)
    mock_rows = [
        ProjectModel(id=1, title="Help 1", repository_url="https://github.com/test/h1", help_wanted=True, created_at=DT, updated_at=DT, owner_id=42),
        ProjectModel(id=2, title="Help 2", repository_url="https://github.com/test/h2", help_wanted=True, created_at=DT, updated_at=DT, owner_id=42),
    ]
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = mock_rows
    session.execute.return_value = mock_result

    async def run():
        return await repo.list_help_wanted()

    projects = asyncio.run(run())

    assert len(projects) == 2
    assert all(p.help_wanted for p in projects)
    session.execute.assert_called_once()


def test_list_help_wanted_empty():
    """Test listing help_wanted projects when there are none."""
    session = make_session()
    repo = make_repository(session)
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    session.execute.return_value = mock_result

    async def run():
        return await repo.list_help_wanted()

    projects = asyncio.run(run())

    assert projects == []
    session.execute.assert_called_once()


def test_list_help_wanted_with_skip():
    """Test list_help_wanted forwards skip to the query."""
    session = make_session()
    repo = make_repository(session)
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    session.execute.return_value = mock_result

    async def run():
        await repo.list_help_wanted(skip=3)

    asyncio.run(run())

    session.execute.assert_called_once()
    statement = session.execute.call_args[0][0]
    sql = _compiled_sql(statement)
    assert "LIMIT 100" in sql
    assert "OFFSET 3" in sql


def test_list_help_wanted_with_limit():
    """Test list_help_wanted forwards limit to the query."""
    session = make_session()
    repo = make_repository(session)
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    session.execute.return_value = mock_result

    async def run():
        await repo.list_help_wanted(limit=5)

    asyncio.run(run())

    session.execute.assert_called_once()
    statement = session.execute.call_args[0][0]
    sql = _compiled_sql(statement)
    assert "LIMIT 5" in sql
    assert "OFFSET 0" in sql


def test_list_help_wanted_with_skip_and_limit_returns_paginated_result():
    """Test that list_help_wanted returns only the paginated help-wanted rows."""
    session = make_session()
    repo = make_repository(session)
    mock_rows = [
        ProjectModel(id=3, title="Help 3", repository_url="https://github.com/test/h3", help_wanted=True, created_at=DT, updated_at=DT, owner_id=42),
        ProjectModel(id=4, title="Help 4", repository_url="https://github.com/test/h4", help_wanted=True, created_at=DT, updated_at=DT, owner_id=42),
    ]
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = mock_rows
    session.execute.return_value = mock_result

    async def run():
        return await repo.list_help_wanted(skip=2, limit=2)

    projects = asyncio.run(run())

    assert [project.id for project in projects] == [3, 4]
    statement = session.execute.call_args[0][0]
    sql = _compiled_sql(statement)
    assert "LIMIT 2" in sql
    assert "OFFSET 2" in sql

    session.execute.assert_called_once()


def test_list_help_wanted_default_pagination():
    """Test list_help_wanted uses default skip=0 and limit=100."""
    session = make_session()
    repo = make_repository(session)
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    session.execute.return_value = mock_result

    async def run():
        await repo.list_help_wanted()

    asyncio.run(run())

    session.execute.assert_called_once()


def test_list_help_wanted_returns_project_schemas():
    """Test that list_help_wanted returns Project schema instances."""
    from app.projects.schemas import Project
    from datetime import datetime
    session = make_session()
    repo = make_repository(session)
    mock_rows = [
        ProjectModel(
            id=1,
            title="HW Schema",
            repository_url="https://github.com/test/hw",
            help_wanted=True,
            created_at=DT,
            updated_at=DT,
            owner_id=42,
        ),
    ]
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = mock_rows
    session.execute.return_value = mock_result

    async def run():
        return await repo.list_help_wanted()

    projects = asyncio.run(run())

    assert all(isinstance(p, Project) for p in projects)


def test_list_help_wanted_single_project():
    """Test list_help_wanted returns exactly one project when only one matches."""
    session = make_session()
    repo = make_repository(session)
    mock_rows = [
        ProjectModel(id=1, title="Solo Help", repository_url="https://github.com/test/solo", owner_id=42, help_wanted=True, created_at=DT, updated_at=DT),
    ]
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = mock_rows
    session.execute.return_value = mock_result

    async def run():
        return await repo.list_help_wanted()

    projects = asyncio.run(run())

    assert len(projects) == 1
    assert projects[0].help_wanted is True


# ---------------------------------------------------------------------------
# edit
# ---------------------------------------------------------------------------

def test_edit_project_updates_requested_fields():
    """edit should update only the fields provided in ProjectUpdate."""
    session = make_session()
    repo = make_repository(session)
    model = ProjectModel(
        id=1,
        title="Old Title",
        description="Old description",
        repository_url="https://github.com/test/old",
        help_wanted=False,
        created_at=DT,
        updated_at=DT,
        owner_id=42,
    )
    class DummyUser:
        id = 42  # Owner
    user = DummyUser()
    # Ensure the model owner_id matches the user id
    model.owner_id = user.id
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = model
    session.execute.return_value = mock_result

    async def refresh_side_effect(project_model: ProjectModel) -> None:
        project_model.updated_at = datetime(2026, 1, 2, 0, 0, 0)

    session.refresh.side_effect = refresh_side_effect
    payload = ProjectUpdate(title="New Title", help_wanted=True)


    # Use DummyUser for test
    async def run():
        return await repo.edit(project_id=1, project_data=payload, user=user)

    project = asyncio.run(run())

    assert project != "forbidden"
    assert project is not None
    assert getattr(project, "title", None) == "New Title"
    assert getattr(project, "help_wanted", None) is True
    assert getattr(project, "description", None) == "Old description"
    assert str(getattr(project, "repository_url", "")) == "https://github.com/test/old"
    session.add.assert_called_once_with(model)
    session.commit.assert_called_once()
    session.refresh.assert_called_once_with(model)


def test_edit_project_returns_none_when_missing():
    """edit should return None when no project exists for the given id."""
    session = make_session()
    repo = make_repository(session)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    session.execute.return_value = mock_result


    class DummyUser:
        id = 42
    user = DummyUser()
    async def run():
        return await repo.edit(project_id=999, project_data=ProjectUpdate(title="Ignored"), user=user)

    project = asyncio.run(run())

    assert project is None
    session.execute.assert_called_once()
    session.add.assert_not_called()
    session.commit.assert_not_called()
    session.refresh.assert_not_called()
    session.rollback.assert_not_called()


def test_edit_project_no_changes_does_not_commit():
    """edit should not commit when update payload is empty."""
    session = make_session()
    repo = make_repository(session)
    model = ProjectModel(
        id=1,
        title="Stable Title",
        repository_url="https://github.com/test/stable",
        help_wanted=False,
        created_at=DT,
        updated_at=DT,
        owner_id=42,
    )
    class DummyUser:
        id = 42  # Owner
    user = DummyUser()
    # Ensure the model owner_id matches the user id
    model.owner_id = user.id
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = model
    session.execute.return_value = mock_result


    # Use DummyUser for test
    async def run():
        return await repo.edit(project_id=1, project_data=ProjectUpdate(), user=user)

    project = asyncio.run(run())

    assert project != "forbidden"
    assert project is not None
    assert getattr(project, "title", None) == "Stable Title"
    session.add.assert_not_called()
    session.commit.assert_not_called()
    session.refresh.assert_not_called()


def test_edit_project_rollback_when_commit_fails():
    """edit should rollback and raise CreateProjectError when commit fails."""
    session = make_session()
    repo = make_repository(session)
    model = ProjectModel(
        id=1,
        title="Rollback Title",
        repository_url="https://github.com/test/rollback",
        help_wanted=False,
        created_at=DT,
        updated_at=DT,
        owner_id=42,
    )
    class DummyUser:
        id = 42  # Owner
    user = DummyUser()
    # Ensure the model owner_id matches the user id
    model.owner_id = user.id
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = model
    session.execute.return_value = mock_result
    session.commit.side_effect = Exception("commit failed")


    # Use DummyUser for test
    async def run():
        with pytest.raises(CreateProjectError, match="Cannot edit project with id 1") as exc_info:
            await repo.edit(project_id=1, project_data=ProjectUpdate(title="New Title"), user=user)
        assert "commit failed" in str(exc_info.value)

    asyncio.run(run())

    session.add.assert_called_once_with(model)
    session.commit.assert_called_once()
    session.rollback.assert_called_once()

# ---------------------------------------------------------------------------
# Forbidden (non-owner) test
# ---------------------------------------------------------------------------
def test_edit_project_returns_forbidden_for_non_owner():
    session = make_session()
    repo = make_repository(session)
    model = ProjectModel(
        id=1,
        title="Should Not Edit",
        repository_url="https://github.com/test/forbidden",
        help_wanted=False,
        created_at=DT,
        updated_at=DT,
        owner_id=42
    )
    class NotOwner:
        id = 999
    user = NotOwner()
    # Ensure the model owner_id does NOT match the user id
    model.owner_id = 42
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = model
    session.execute.return_value = mock_result

    import pytest
    async def run():
        with pytest.raises(ForbiddenError):
            await repo.edit(project_id=1, project_data=ProjectUpdate(title="Should Fail"), user=user)
    asyncio.run(run())
