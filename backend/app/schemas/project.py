from typing import Annotated, Optional
from datetime import datetime

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, StringConstraints


MAX_BIGINT = 9_223_372_036_854_775_807

ProjectString = Annotated[str, StringConstraints(min_length=1, max_length=255)]
StrictBool = Annotated[bool, Field(strict=True)]
BigIntId = Annotated[int, Field(strict=True, ge=1, le=MAX_BIGINT)]


class ProjectBase(BaseModel):
    title: ProjectString
    description: Optional[str] = None
    repository_url: AnyHttpUrl
    help_wanted: StrictBool = False


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    title: Optional[ProjectString] = None
    description: Optional[str] = None
    repository_url: Optional[AnyHttpUrl] = None
    help_wanted: Optional[StrictBool] = None


class Project(ProjectBase):
    model_config = ConfigDict(from_attributes=True)

    id: BigIntId
    created_at: datetime
    updated_at: datetime