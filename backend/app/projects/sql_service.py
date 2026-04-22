from typing import List

from app.projects.sql_repository import SqlRepository
from app.auth.schemas import User
from .service import ProjectService
from .schemas import ProjectCreate, Project, ProjectUpdate
from .exception import ProjectNotFoundError, CreateProjectError

class SQLProjectService(ProjectService):
    """
    SQL-based implementation of the ProjectService interface.

    This class provides concrete implementations of the project operations defined in the ProjectService
    abstract base class, using SQL queries to interact with a relational database. It handles tasks such as
    creating new projects, listing existing projects with pagination, retrieving projects by their unique
    identifiers, and filtering projects based on their help-wanted status.
    """
    def __init__(self, repository: SqlRepository):
        """
        Initialize the SQLProjectService with a repository.

        Args:
            repository: An instance of SqlRepository to interact with the database.
        """
        self.repository = repository
    
    async def create(self, project_data: ProjectCreate) -> Project:
        """Create a new project in the database.

        Args:
            project_data: Validated payload containing the project fields to persist.

        Returns:
            The newly created project, including its generated id and timestamps.
        """
        existing_project = await self.repository.get_by_repository_url(project_data.repository_url)
        if existing_project is not None:
            raise CreateProjectError(f'''A project with the repository URL '{project_data.repository_url}' already exists.''')
        return await self.repository.create(project_data)

    async def list(self, skip: int = 0, limit: int = 100) -> List[Project]:
        """List all projects with optional pagination.

        Args:
            skip: Number of records to skip before returning results. Defaults to 0.
            limit: Maximum number of records to return. Defaults to 100.

        Returns:
            A list of projects.
        """
        return await self.repository.list(skip=skip, limit=limit)

    async def get_by_id(self, project_id: int) -> Project:
        """Retrieve a single project by its primary key.

        Args:
            project_id: The unique identifier of the project.

        Returns:
            The matching project.

        Raises:
            ProjectNotFoundError: If no project with the given id exists.
        """
        project = await self.repository.get_by_id(project_id)
        if project is None:
            raise ProjectNotFoundError(project_id)
        return project

    async def edit(self, project_id: int, project_data: ProjectUpdate, user: User) -> Project:
        """Partially update an existing project.

        Args:
            project_id: The unique identifier of the project to update.
            project_data: Payload with one or more fields to update.

        Returns:
            The updated project.

        Raises:
            ProjectNotFoundError: If no project with the given id exists.
            CreateProjectError: If the requested repository_url does not exist
                or conflicts with another project.
        """
        project = await self.repository.get_by_id(project_id)
        if project is None:
            raise ProjectNotFoundError(project_id)

        if project_data.repository_url is not None:
            existing_project = await self.repository.get_by_repository_url(project_data.repository_url)
            if existing_project is None:
                raise CreateProjectError(
                    f"""Cannot edit project with repository URL '{project_data.repository_url}' because it does not exist."""
                )
            if existing_project is not None and existing_project.id != project_id:
                raise CreateProjectError(
                    f"""A project with the repository URL '{project_data.repository_url}' already exists."""
                )

        updated_project = await self.repository.edit(project_id=project_id, project_data=project_data, user=user)
        if updated_project is None:
            raise ProjectNotFoundError(project_id)
        return updated_project

    async def list_help_wanted(self, skip: int = 0, limit: int = 100) -> List[Project]:
        """List help-wanted projects with optional pagination.

        Args:
            skip: Number of records to skip before returning results. Defaults to 0.
            limit: Maximum number of records to return. Defaults to 100.

        Returns:
            A list of projects where help_wanted is True.
        """
        return await self.repository.list_help_wanted(skip=skip, limit=limit)
    
    async def delete_by_id(self, project_id: int, user: User) -> bool:
        """Delete a project by its unique identifier.

        Args:
            project_id: The unique identifier of the project to delete
            user: The user attempting to delete the project.
        Returns:
            True if the project was deleted, False if no project with the given id exists.
        """
        return await self.repository.delete_by_id(project_id, user)
    
    async def delete_by_repository_url(self, repository_url: str, user: User) -> bool:
        """Delete a project by its unique repository URL.

        Args:
            repository_url: The unique repository URL of the project to delete
            user: The user attempting to delete the project.
        Returns:
            True if the project was deleted, False if no project with the given repository URL exists.
        """
        return await self.repository.delete_by_repository_url(repository_url, user)