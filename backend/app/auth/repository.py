"""
AuthRepository defines the data access interface for user authentication.

Implementations will use SQLModel for database operations.
"""

from abc import ABC, abstractmethod
from typing import Optional

from app.auth.schemas import User, UserCreate


class UserRepository(ABC):
    """Abstract interface for user data access."""
    
    @abstractmethod
    async def create(self, user_data: UserCreate) -> User:
        """Create a new user in the database."""
        raise NotImplementedError
    
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """Retrieve user by email."""
        raise NotImplementedError
    
    @abstractmethod
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Retrieve user by ID."""
        raise NotImplementedError
    
    @abstractmethod
    async def update(self, user_id: int, **kwargs) -> Optional[User]:
        """Update user fields."""
        raise NotImplementedError
