"""
AuthService handles user authentication business logic.

Responsibilities:
- User registration with password hashing
- User login with password verification
- JWT token generation and validation
- User profile retrieval and updates
"""

import hashlib
import hmac
import os
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


class AuthLocalService(AuthService):
    """Email/password authentication service for local accounts."""

    def __init__(
        self,
        user_repository: UserRepository,
        *,
        pbkdf2_iterations: int = 390000,
        salt_size: int = 16,
    ):
        """
        Initialize local authentication service dependencies and settings.

        :param user_repository: Repository used to query and persist users.
        :param pbkdf2_iterations: Number of PBKDF2 rounds used for hashing.
        :param salt_size: Number of random bytes generated for password salt.
        :return: None.
        """
        self.user_repository = user_repository
        self.pbkdf2_iterations = pbkdf2_iterations
        self.salt_size = salt_size

    def _hash_password(self, password: str) -> str:
        """
        Hash a plain-text password using PBKDF2-HMAC-SHA256.

        :param password: Plain-text password to hash.
        :return: Formatted password hash string including algorithm,
            iterations, salt, and digest.
        """
        salt = os.urandom(self.salt_size)
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            self.pbkdf2_iterations,
        )
        return (
            f"pbkdf2_sha256${self.pbkdf2_iterations}$"
            f"{salt.hex()}${digest.hex()}"
        )

    def _verify_password(self, password: str, stored_hash: str) -> bool:
        """
        Verify a plain-text password against a stored hash string.

        :param password: Plain-text password to validate.
        :param stored_hash: Persisted password hash to compare against.
        :return: True when the password matches the stored hash, False
            otherwise.
        """
        try:
            algorithm, iterations, salt_hex, digest_hex = stored_hash.split("$", 3)
            if algorithm != "pbkdf2_sha256":
                return False

            digest = hashlib.pbkdf2_hmac(
                "sha256",
                password.encode("utf-8"),
                bytes.fromhex(salt_hex),
                int(iterations),
            )
            return hmac.compare_digest(digest.hex(), digest_hex)
        except (ValueError, TypeError, OverflowError):
            return False

    async def register(self, user_data: UserCreate) -> User:
        """
        Register a local user with a securely hashed password.

        :param user_data: User creation payload with plain-text password.
        :return: The created user entity.
        """
        existing_user = await self.user_repository.get_by_email(user_data.email)
        if existing_user is not None:
            raise ValueError("Email already exists")

        hashed_password = self._hash_password(user_data.password)
        user_to_create = UserCreate(
            username=user_data.username,
            email=user_data.email,
            password=hashed_password,
            github_page=user_data.github_page,
            bio=user_data.bio,
        )
        return await self.user_repository.create(user_to_create)

    async def authenticate(self, email: str, password: str) -> Optional[User]:
        """
        Authenticate a user using email and plain-text password.

        :param email: Email address associated with the user account.
        :param password: Plain-text password to verify.
        :return: Authenticated user when credentials are valid; otherwise
            None.
        """
        stored_hash = await self.user_repository.get_password_hash_by_email(email)
        if stored_hash is None:
            return None

        if not self._verify_password(password, stored_hash):
            return None

        return await self.user_repository.get_by_email(email)

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Retrieve a user profile by user identifier.

        :param user_id: Unique identifier of the user.
        :return: User profile if found; otherwise None.
        """
        return await self.user_repository.get_by_id(user_id)
