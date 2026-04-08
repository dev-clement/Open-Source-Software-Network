from typing import Annotated, Optional
from datetime import datetime

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, EmailStr, Field, StringConstraints


MAX_BIGINT = 9_223_372_036_854_775_807

UserString = Annotated[str, StringConstraints(min_length=1, max_length=255)]
BigIntId = Annotated[int, Field(strict=True, ge=1, le=MAX_BIGINT)]


class UserBase(BaseModel):
    username: UserString
    email: EmailStr
    github_page: Optional[AnyHttpUrl] = None
    bio: Optional[str] = None


class UserCreate(UserBase):
    password: UserString


class UserUpdate(BaseModel):
    username: Optional[UserString] = None
    email: Optional[EmailStr] = None
    password: Optional[UserString] = None
    github_page: Optional[AnyHttpUrl] = None
    bio: Optional[str] = None


class User(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: BigIntId
    created_at: datetime
    updated_at: datetime
