"""
ContributionRepository defines the data access interface for contributions.

Implementations will use SQLModel for database operations.
"""

from abc import ABC, abstractmethod
from typing import Optional, List
from pydantic import EmailStr

from app.contributions.schemas import Contribution, ContributionCreate


class ContributionRepository(ABC):
    """
    Abstract base class defining the data access interface for contributions.

    This interface specifies the contract for repository implementations that manage
    contribution records, such as creating, retrieving, listing, and updating contributions.
    Implementations are expected to interact with the underlying data store (e.g., SQLModel).
    """

    @abstractmethod
    async def get_by_project(self, project_title: str) -> List[Contribution]:
        """
        Retrieve all contributions associated with a project by its title.

        Args:
            project_title (str): The title of the project (same type as Project.title).

        Returns:
            List[Contribution]: A list of contributions for the specified project.
        """
        ...

    @abstractmethod
    async def get_by_user(self, user_email: "EmailStr") -> List[Contribution]:
        """
        Retrieve all contributions made by a user identified by their email address.

        Args:
            user_email (EmailStr): The email address of the user (same type as UserBase.email).

        Returns:
            List[Contribution]: A list of contributions made by the specified user.
        """
        ...
    
    @abstractmethod
    async def create(self, contribution_data: ContributionCreate) -> Contribution:
        """
        Create a new contribution record in the data store.

        Args:
            contribution_data (ContributionCreate): The data required to create a contribution.

        Returns:
            Contribution: The created contribution object.
        """
        ...
    
    @abstractmethod
    async def get_by_id(self, contribution_id: int) -> Optional[Contribution]:
        """
        Retrieve a contribution by its unique identifier.

        Args:
            contribution_id (int): The ID of the contribution to retrieve.

        Returns:
            Optional[Contribution]: The contribution if found, otherwise None.
        """
        ...
    
    @abstractmethod
    async def list_by_user(self, user_id: int) -> List[Contribution]:
        """
        List all contributions made by a specific user.

        Args:
            user_id (int): The ID of the user whose contributions to list.

        Returns:
            List[Contribution]: A list of contributions made by the user.
        """
        ...
    
    @abstractmethod
    async def list_by_project(self, project_id: int) -> List[Contribution]:
        """
        List all contributions associated with a specific project.

        Args:
            project_id (int): The ID of the project whose contributions to list.

        Returns:
            List[Contribution]: A list of contributions for the project.
        """
        ...
    
    @abstractmethod
    async def get_by_user_and_project(
        self, user_id: int, project_id: int
    ) -> Optional[Contribution]:
        """
        Retrieve a contribution made by a specific user to a specific project.

        Args:
            user_id (int): The ID of the user.
            project_id (int): The ID of the project.

        Returns:
            Optional[Contribution]: The contribution if found, otherwise None.
        """
        ...
    
    @abstractmethod
    async def update_status(self, contribution_id: int, status: str) -> Optional[Contribution]:
        """
        Update the status of a contribution.

        Args:
            contribution_id (int): The ID of the contribution to update.
            status (str): The new status value to set.

        Returns:
            Optional[Contribution]: The updated contribution if found, otherwise None.
        """
        ...

    @abstractmethod
    async def delete_contribution_from_project(self, contribution_id: int) -> None:
        """
        Remove a contribution from a project using its unique identifier.

        This method deletes the contribution record associated with the given contribution ID.

        Args:
            contribution_id (int): The unique identifier of the contribution to remove.

        Returns:
            None
        """
        ...
