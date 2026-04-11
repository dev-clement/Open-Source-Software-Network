"""SQL-backed repository implementation for auth-related user persistence."""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.auth.repository import UserRepository
from app.auth.schemas import User, UserCreate
from app.db.models import User as UserModel


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
