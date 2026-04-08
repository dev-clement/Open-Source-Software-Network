"""
ProjectRepository defines the data access interface for projects.

Implementations will use SQLModel for database operations.
"""

from abc import ABC, abstractmethod
from typing import Optional, List

from app.projects.schemas import Project, ProjectCreate


class ProjectRepository(ABC):
    """Abstract interface for project data access."""
    
    @abstractmethod
    async def create(self, project_data: ProjectCreate) -> Project:
        """Create a new project in the database."""
        raise NotImplementedError
    
    @abstractmethod
    async def get_by_id(self, project_id: int) -> Optional[Project]:
        """Retrieve project by ID."""
        raise NotImplementedError
    
    @abstractmethod
    async def list(self, skip: int = 0, limit: int = 100) -> List[Project]:
        """List projects with pagination."""
        raise NotImplementedError
    
    @abstractmethod
    async def get_by_repository_url(self, url: str) -> Optional[Project]:
        """Retrieve project by repository URL (must be unique)."""
        raise NotImplementedError
    
    @abstractmethod
    async def list_help_wanted(self) -> List[Project]:
        """List projects where help_wanted=True."""
        raise NotImplementedError
