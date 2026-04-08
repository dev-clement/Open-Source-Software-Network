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

from app.auth.schemas import UserCreate, User


class AuthService:
    """High-level authentication operations."""
    
    def __init__(self):
        # Will be injected with UserRepository in __init__
        pass
    
    async def register(self, user_data: UserCreate) -> User:
        """
        Register a new user.
        
        Args:
            user_data: UserCreate schema with username, email, password
            
        Returns:
            User: The created user object
            
        Raises:
            ValueError: If email already exists
        """
        raise NotImplementedError
    
    async def authenticate(self, email: str, password: str) -> Optional[User]:
        """
        Authenticate user by email and password.
        
        Args:
            email: User email
            password: Plain-text password
            
        Returns:
            User object if credentials are valid, None otherwise
        """
        raise NotImplementedError
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        raise NotImplementedError
