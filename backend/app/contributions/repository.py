"""
ContributionRepository defines the data access interface for contributions.

Implementations will use SQLModel for database operations.
"""

from abc import ABC, abstractmethod
from typing import Optional, List

from app.contributions.schemas import Contribution, ContributionCreate


class ContributionRepository(ABC):
    """Abstract interface for contribution data access."""
    
    @abstractmethod
    async def create(self, contribution_data: ContributionCreate) -> Contribution:
        """Create a new contribution."""
        raise NotImplementedError
    
    @abstractmethod
    async def get_by_id(self, contribution_id: int) -> Optional[Contribution]:
        """Retrieve contribution by ID."""
        raise NotImplementedError
    
    @abstractmethod
    async def list_by_user(self, user_id: int) -> List[Contribution]:
        """List all contributions by a user."""
        raise NotImplementedError
    
    @abstractmethod
    async def list_by_project(self, project_id: int) -> List[Contribution]:
        """List all contributions to a project."""
        raise NotImplementedError
    
    @abstractmethod
    async def get_by_user_and_project(
        self, user_id: int, project_id: int
    ) -> Optional[Contribution]:
        """Check if user already contributed to project."""
        raise NotImplementedError
    
    @abstractmethod
    async def update_status(self, contribution_id: int, status: str) -> Optional[Contribution]:
        """Update contribution status."""
        raise NotImplementedError
