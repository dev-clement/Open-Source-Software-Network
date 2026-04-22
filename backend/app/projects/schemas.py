from typing import Annotated, Optional
from datetime import datetime

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, StringConstraints
from app.auth.schemas import User

MAX_BIGINT = 9_223_372_036_854_775_807

ProjectString = Annotated[str, StringConstraints(min_length=1, max_length=255)]
StrictBool = Annotated[bool, Field(strict=True)]
BigIntId = Annotated[int, Field(strict=True, ge=1, le=MAX_BIGINT)]


class ProjectBase(BaseModel):
    """
    Base schema for Project objects.

    Attributes:
        title (str): Title of the project (1-255 chars).
        description (Optional[str]): Optional description of the project.
        repository_url (AnyHttpUrl): URL to the project's repository.
        help_wanted (bool): Whether the project is seeking contributors.
        owner_id (int): ID of the user who owns the project.
    """
    title: ProjectString
    description: Optional[str] = None
    repository_url: AnyHttpUrl
    help_wanted: StrictBool = False
    owner_id: int



class ProjectCreate(ProjectBase):
    """
    Schema for creating a new Project.
    Inherits all fields from ProjectBase.
    """
    pass


class ProjectUpdate(BaseModel):
    """
    Schema for updating an existing Project.

    All fields are optional and correspond to updatable project attributes.
    """
    title: Optional[ProjectString] = None
    description: Optional[str] = None
    repository_url: Optional[AnyHttpUrl] = None
    help_wanted: Optional[StrictBool] = None


class Project(ProjectBase):
    """
    Schema representing a Project with database fields.

    Attributes:
        id (int): Unique identifier for the project.
        created_at (datetime): Timestamp when the project was created.
        updated_at (datetime): Timestamp when the project was last updated.
        owner_id (int): ID of the user who owns the project.
    """
    model_config = ConfigDict(from_attributes=True)

    id: BigIntId
    created_at: datetime
    updated_at: datetime
    owner_id: int
