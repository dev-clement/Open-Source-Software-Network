"""
AuthRepository defines the data access interface for user authentication.

Implementations will use SQLModel for database operations.
"""

from abc import ABC, abstractmethod
from typing import Optional

from app.auth.schemas import User, UserCreate


class UserRepository(ABC):
    """Abstract interface for auth-related user persistence operations.

    This contract intentionally stays focused on storage concerns only.
    Callers are expected to handle business rules such as password hashing,
    duplicate-email checks, or provider-specific signup decisions before they
    invoke repository methods.
    """

    @abstractmethod
    async def create(self, user_data: UserCreate) -> User:
        """Persist a new user record and return the stored user snapshot.

        Implementations should translate the incoming schema into the database
        model, write it to persistent storage, and return the resulting user as
        an auth schema. The password contained in ``user_data`` is assumed to be
        already prepared by the caller, typically as a hashed value for local
        signup.

        :param user_data: Normalized user payload to persist, including the
            caller-prepared password value and optional profile fields.
        :return: The stored user represented as an auth schema, including any
            generated database fields such as identifiers or timestamps.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """Return the user associated with a unique email address, if any.

        This method is commonly used by the service layer to enforce signup
        uniqueness checks and to resolve users during local authentication.

        :param email: Unique email address used to locate the corresponding
            user record.
        :return: The matching user schema when a record exists, otherwise
            ``None``.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_password_hash_by_email(self, email: str) -> Optional[str]:
        """Return the persisted password hash for the given email.

        This method is intended for local-auth credential verification in the
        service layer. It returns ``None`` when no user exists for the email.

        :param email: Unique email address used to find the credential record.
        :return: Password hash string when found, otherwise ``None``.
        """
        raise NotImplementedError

    @abstractmethod
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Return a user by primary key, or ``None`` when no row exists.

        The method exposes an identifier-based lookup for authenticated flows
        that already know the user id, such as token resolution or profile
        retrieval.

        :param user_id: Database identifier of the user to retrieve.
        :return: The matching user schema when found, otherwise ``None``.
        """
        raise NotImplementedError

    @abstractmethod
    async def update(self, user_id: int, **kwargs) -> Optional[User]:
        """Apply partial field updates to an existing user record.

        Implementations should update only the supplied attributes, persist the
        change, and return the refreshed user snapshot. If the target user does
        not exist, ``None`` should be returned.

        :param user_id: Database identifier of the user to update.
        :param kwargs: Partial set of user attributes to mutate in storage.
        :return: The refreshed user schema after persistence, or ``None`` when
            the target user does not exist.
        """
        raise NotImplementedError

    @abstractmethod
    async def delete_by_id(self, user_id: int) -> bool:
        """Delete a user by primary key.

        :param user_id: Database identifier of the user to delete.
        :return: ``True`` when a user was deleted, otherwise ``False``.
        """
        raise NotImplementedError

    @abstractmethod
    async def delete_by_email(self, email: str) -> bool:
        """Delete a user by unique email address.

        :param email: Unique email address of the user to delete.
        :return: ``True`` when a user was deleted, otherwise ``False``.
        """
        raise NotImplementedError
