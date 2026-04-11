"""
AuthService handles user authentication business logic.

Responsibilities:
- User registration with password hashing
- User login with password verification
- JWT token generation and validation
- User profile retrieval and updates
"""

from abc import ABC, abstractmethod
from typing import Optional

from app.auth.repository import UserRepository
from app.auth.schemas import UserCreate, User


class AuthService(ABC):
    """Define the contract for high-level authentication operations."""
    
    def __init__(self):
        """Initialize the authentication service base class."""
        # Will be injected with UserRepository in __init__
        pass
    
    @abstractmethod
    async def register(self, user_data: UserCreate) -> User:
        """
        Register a new user account.

        :param user_data: User creation payload containing username, email,
            and plain-text password.
        :return: The created user entity.
        """
        raise NotImplementedError
    
    @abstractmethod
    async def authenticate(self, email: str, password: str) -> Optional[User]:
        """
        Authenticate user by email and password.

        :param email: Email address used to identify the user account.
        :param password: Plain-text password provided by the user.
        :return: The authenticated user if credentials are valid; otherwise
            None.
        """
        raise NotImplementedError
    
    @abstractmethod
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Retrieve a user by its unique identifier.

        :param user_id: Unique identifier of the user.
        :return: The matching user if found; otherwise None.
        """
        raise NotImplementedError
