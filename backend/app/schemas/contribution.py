from typing import Annotated, Optional
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, StringConstraints


MAX_BIGINT = 9_223_372_036_854_775_807

BigIntId = Annotated[int, Field(strict=True, ge=1, le=MAX_BIGINT)]
ContributionStatus = Annotated[str, StringConstraints(min_length=1, max_length=20)]


class ContributionBase(BaseModel):
    fk_user_id: BigIntId
    fk_project_id: BigIntId
    status: ContributionStatus = "interested"


class ContributionCreate(ContributionBase):
    pass


class ContributionUpdate(BaseModel):
    status: Optional[ContributionStatus] = None


class Contribution(ContributionBase):
    model_config = ConfigDict(from_attributes=True)

    id: BigIntId
    applied_at: datetime
    updated_at: datetime