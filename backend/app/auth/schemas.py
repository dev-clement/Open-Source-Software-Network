"""Pydantic schemas used by the auth domain.

These models define the validated payloads exchanged between API, service,
and repository layers for local authentication and user profile management.
"""

from typing import Annotated, Optional
from datetime import datetime

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, EmailStr, Field, StringConstraints


MAX_BIGINT = 9_223_372_036_854_775_807

# Reusable constrained string alias for user-provided textual fields.
#
# We use Annotated + StringConstraints so validation rules are declared once
# and applied consistently by Pydantic wherever this alias is referenced.
UserString = Annotated[str, StringConstraints(min_length=1, max_length=255)]

# Shared strict identifier type for BIGINT-compatible database primary keys.
#
# This is used on response schemas (for example User.id) to keep IDs positive,
# bounded to PostgreSQL BIGINT limits, and rejected when non-integer input is
# provided.
BigIntId = Annotated[int, Field(strict=True, ge=1, le=MAX_BIGINT)]


class UserBase(BaseModel):
    """Common public user fields used across auth schemas.

    This base model is reused by both creation and response payloads to keep
    field definitions centralized and consistent.
    """

    username: UserString
    email: EmailStr
    github_page: Optional[AnyHttpUrl] = None
    bio: Optional[str] = None


class UserCreate(UserBase):
    """Input schema for creating a local-auth user account.

    Used when receiving signup data before persistence.
    """

    password: UserString


class UserUpdate(BaseModel):
    """Partial update schema for user profile and credential changes.

    All fields are optional to support PATCH-like update operations.
    """

    username: Optional[UserString] = None
    email: Optional[EmailStr] = None
    password: Optional[UserString] = None
    github_page: Optional[AnyHttpUrl] = None
    bio: Optional[str] = None


class User(UserBase):
    """Output schema representing a persisted user record.

    ``from_attributes=True`` enables model validation directly from ORM objects
    (for example SQLModel instances returned by the repository layer).
    """

    model_config = ConfigDict(from_attributes=True)

    id: BigIntId
    created_at: datetime
    updated_at: datetime


class LoginRequest(BaseModel):
    """Input schema for local-auth login.

    Carries credentials as a validated request body to avoid exposing
    sensitive values in query parameters or URL paths.
    """

    email: EmailStr
    password: UserString


class TokenResponse(BaseModel):
    """Output schema returned upon successful authentication.

    Follows the OAuth2 bearer token response convention so clients can
    treat the ``access_token`` uniformly regardless of the auth backend.
    """

    access_token: str
    token_type: str = "bearer"
