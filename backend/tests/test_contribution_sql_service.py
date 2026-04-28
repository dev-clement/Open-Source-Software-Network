import pytest
from unittest.mock import AsyncMock, MagicMock
from app.contributions.sql_service import SqlContributionService
from app.contributions.exception import ProjectAndUserAlreadyLinked, UserNotFound, ProjectListForUserNotFound, ProjectAndUserNotLinked
from app.contributions.schemas import ContributionCreate, Contribution


@pytest.mark.asyncio
class TestSqlContributionService:
    async def test_update_status_success(self, service, mock_repository):
        # Simulate existing contribution
        mock_repository.get_by_user_and_project = AsyncMock(return_value={"user_id": 1, "project_id": 2})
        mock_repository.update_status = AsyncMock(return_value="updated")
        result = await service.update_status(1, 2, "contribute")
        assert result == "updated"

    async def test_update_status_not_linked(self, service, mock_repository):
        # Simulate missing contribution
        mock_repository.get_by_user_and_project = AsyncMock(return_value=None)
        with pytest.raises(ProjectAndUserNotLinked):
            await service.update_status(1, 2, "contribute")
    async def test_list_project_by_user_success(self, service, mock_repository):
        # Simulate projects found for user_id=1
        projects = ["ProjectA", "ProjectB"]
        mock_repository.list_project_by_user = AsyncMock(return_value=projects)
        result = await service.list_project_by_user(1)
        assert result == projects

    async def test_list_project_by_user_not_found(self, service, mock_repository):
        # Simulate no projects found for user_id=999
        mock_repository.list_project_by_user = AsyncMock(return_value=None)
        with pytest.raises(ProjectListForUserNotFound):
            await service.list_project_by_user(999)

    @pytest.fixture
    def mock_repository(self):
        repo = MagicMock()
        repo.create = AsyncMock()
        repo.get_by_user_and_project = AsyncMock(return_value=None)
        repo.get_by_user = AsyncMock()
        repo.list_by_user = AsyncMock()
        repo.get_by_project = AsyncMock()
        repo.list_by_project = AsyncMock()
        return repo

    @pytest.fixture
    def service(self, mock_repository):
        return SqlContributionService(mock_repository)

    async def test_list_by_user_success(self, service, mock_repository):
        # Simulate contributions found for user_id=1
        contributions = [Contribution(user_id=1, project_id=2, id=1, applied_at='2024-04-28T00:00:00', updated_at='2024-04-28T00:00:00')]
        mock_repository.get_by_user.return_value = contributions
        mock_repository.list_by_user.return_value = contributions
        result = await service.list_by_user(1)
        assert result == contributions

    async def test_list_by_user_user_not_found(self, service, mock_repository):
        # Simulate no contributions found for user_id=999
        mock_repository.get_by_user.return_value = []
        with pytest.raises(UserNotFound):
            await service.list_by_user(999)

    async def test_list_by_project_success(self, service, mock_repository):
        # Simulate contributions found for project_id=2
        contributions = [Contribution(user_id=1, project_id=2, id=1, applied_at='2024-04-28T00:00:00', updated_at='2024-04-28T00:00:00')]
        mock_repository.get_by_project.return_value = contributions
        mock_repository.list_by_project.return_value = contributions
        result = await service.list_by_project(2)
        assert result == contributions

    async def test_list_by_project_project_not_found(self, service, mock_repository):
        # Simulate no contributions found for project_id=999
        mock_repository.get_by_project.return_value = []
        try:
            from app.contributions.exception import ProjectNotFound
        except ImportError:
            class ProjectNotFound(Exception):
                pass
        service.ProjectNotFound = ProjectNotFound
        with pytest.raises(ProjectNotFound):
            await service.list_by_project(999)

    @pytest.mark.parametrize("user_id, project_id", [
        (None, None),
        (1, None),
        (None, 1),
    ])
    async def test_apply_invalid_ids(self, service, user_id, project_id):
        with pytest.raises((TypeError, ValueError)):
            await service.apply(user_id, project_id)


    async def test_apply_user_and_project_already_linked(self, service, mock_repository):
        # Simulate already existing contribution
        mock_repository.get_by_user_and_project.return_value = ContributionCreate(user_id=1, project_id=2)
        with pytest.raises(ProjectAndUserAlreadyLinked):
            await service.apply(1, 2)

    async def test_apply_success(self, service, mock_repository):
        mock_repository.get_by_user_and_project.return_value = None
        mock_repository.create.return_value = ContributionCreate(user_id=1, project_id=2)
        result = await service.apply(1, 2)
        assert result.user_id == 1
        assert result.project_id == 2
