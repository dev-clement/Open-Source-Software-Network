"""
AuthRepository defines the data access interface for user authentication.

Implementations will use SQLModel for database operations.
"""

from abc import ABC, abstractmethod
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.auth.schemas import User, UserCreate
from app.db.models import User as UserModel


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


class SqlUserRepository(UserRepository):
    """Concrete ``UserRepository`` backed by an asynchronous SQLAlchemy session.

    This implementation maps auth schemas to the SQLModel user table and keeps
    all database interaction details hidden from the service layer.
    """

    def __init__(self, session: AsyncSession):
        """Store the async database session used for repository operations.

        :param session: Active asynchronous SQLAlchemy session used to execute
            user persistence queries and transactions.
        """
        self.session = session

    async def create(self, user_data: UserCreate) -> User:
        """Persist a new user record and return it as an auth schema.

        The repository expects the password field to already be prepared by the
        caller, which keeps hashing and signup policy in the service layer.
        After insertion, the method refreshes the ORM instance so generated
        fields like the primary key and timestamps are available in the
        returned schema.

        :param user_data: User creation payload containing the values to insert
            into the ``user`` table.
        :return: Newly persisted user schema enriched with generated fields
            loaded from the database after refresh.
        """
        user_model = UserModel(**user_data.model_dump())
        self.session.add(user_model)
        try:
            await self.session.commit()
            await self.session.refresh(user_model)
        except Exception as e:
            await self.session.rollback()
            raise e
        return User.model_validate(user_model)

    async def get_by_email(self, email: str) -> Optional[User]:
        """Retrieve a single user by unique email address.

        Returns ``None`` when the email is not present in storage, allowing the
        caller to distinguish between missing users and successful lookups
        without relying on exceptions for control flow.

        :param email: Unique email address to search for in persistent storage.
        :return: Matching user schema when found, otherwise ``None``.
        """
        statement = select(UserModel).where(UserModel.email == email)
        result = await self.session.execute(statement)
        user_model = result.scalar_one_or_none()
        if user_model is None:
            return None
        return User.model_validate(user_model)

    async def get_password_hash_by_email(self, email: str) -> Optional[str]:
        """Retrieve a user's password hash using their unique email.

        :param email: Unique email address to search for in persistent storage.
        :return: Stored password hash string when found, otherwise ``None``.
        """
        statement = select(UserModel.password).where(UserModel.email == email)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Retrieve a single user by primary key.

        This is the repository-level lookup used after authentication when the
        application already trusts the user identifier, for example after token
        decoding.

        :param user_id: Primary key of the user row to fetch.
        :return: Matching user schema when found, otherwise ``None``.
        """
        statement = select(UserModel).where(UserModel.id == user_id)
        result = await self.session.execute(statement)
        user_model = result.scalar_one_or_none()
        if user_model is None:
            return None
        return User.model_validate(user_model)

    async def update(self, user_id: int, **kwargs) -> Optional[User]:
        """Update an existing user and return the refreshed schema.

        The repository validates that each provided keyword matches a known ORM
        attribute before mutating the loaded user model. Unknown field names are
        rejected immediately with ``ValueError`` to keep silent data loss out of
        the persistence layer.

        :param user_id: Primary key of the user row to mutate.
        :param kwargs: Mapping of attribute names to replacement values for the
            target user row.
        :return: Refreshed user schema after a successful update, or ``None``
            when no user exists for the provided identifier.
        """
        statement = select(UserModel).where(UserModel.id == user_id)
        result = await self.session.execute(statement)
        user_model = result.scalar_one_or_none()
        if user_model is None:
            return None

        for field_name, field_value in kwargs.items():
            if field_name not in UserModel.__table__.columns:
                raise ValueError(f"Unknown user field: {field_name}")
            setattr(user_model, field_name, field_value)

        self.session.add(user_model)
        try:
            await self.session.commit()
            await self.session.refresh(user_model)
        except Exception as e:
            await self.session.rollback()
            raise e
        return User.model_validate(user_model)

    async def delete_by_id(self, user_id: int) -> bool:
        """Delete a user by primary key when it exists.

        The repository returns a boolean rather than raising when the user is
        missing so callers can handle delete idempotently.

        :param user_id: Primary key of the user row to delete.
        :return: ``True`` when a matching row was deleted, otherwise ``False``.
        """
        statement = select(UserModel).where(UserModel.id == user_id)
        result = await self.session.execute(statement)
        user_model = result.scalar_one_or_none()
        if user_model is None:
            return False

        try:
            await self.session.delete(user_model)
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
        return True

    async def delete_by_email(self, email: str) -> bool:
        """Delete a user by unique email address when it exists.

        :param email: Unique email address of the user row to delete.
        :return: ``True`` when a matching row was deleted, otherwise ``False``.
        """
        statement = select(UserModel).where(UserModel.email == email)
        result = await self.session.execute(statement)
        user_model = result.scalar_one_or_none()
        if user_model is None:
            return False

        try:
            await self.session.delete(user_model)
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise
        return True
