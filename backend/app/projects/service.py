"""
ProjectService handles project business logic.

Responsibilities:
- Project creation with validation
- Project listing and filtering
- Help-wanted status management
"""
from abc import ABC, abstractmethod
from typing import List
from app.projects.schemas import Project, ProjectCreate


class ProjectService(ABC):
    """High-level project operations."""

    @abstractmethod
    async def create(self, project_data: ProjectCreate) -> Project:
        """Create a new project.

        Args:
            project_data: Validated payload containing the project fields to persist.

        Returns:
            The newly created project, including its generated id and timestamps.
        """
        ...

    @abstractmethod
    async def list(self, skip: int = 0, limit: int = 100) -> List[Project]:
        """List all projects with optional pagination.

        Args:
            skip: Number of records to skip before returning results. Defaults to 0.
            limit: Maximum number of records to return. Defaults to 100.

        Returns:
            A list of projects.
        """
        ...

    @abstractmethod
    async def get_by_id(self, project_id: int) -> Project:
        """Retrieve a single project by its primary key.

        Args:
            project_id: The unique identifier of the project.

        Returns:
            The matching project.

        Raises:
            ProjectNotFoundError: If no project with the given id exists.
        """
        ...

    @abstractmethod
    async def list_help_wanted(self, skip: int = 0, limit: int = 100) -> List[Project]:
        """List help-wanted projects with optional pagination.

        Args:
            skip: Number of records to skip before returning results. Defaults to 0.
            limit: Maximum number of records to return. Defaults to 100.

        Returns:
            A list of projects where help_wanted is True.
        """
        ...
