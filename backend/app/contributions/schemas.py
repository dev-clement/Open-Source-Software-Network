from typing import Annotated, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.domain.enums import ContributionStatus


MAX_BIGINT = 9_223_372_036_854_775_807

BigIntId = Annotated[int, Field(strict=True, ge=1, le=MAX_BIGINT)]

class ContributionBase(BaseModel):
    fk_user_id: BigIntId
    fk_project_id: BigIntId
    status: ContributionStatus = ContributionStatus.INTERESTED


class ContributionCreate(ContributionBase):
    pass


class ContributionUpdate(BaseModel):
    status: Optional[ContributionStatus] = None


class Contribution(ContributionBase):
    model_config = ConfigDict(from_attributes=True)

    id: BigIntId
    applied_at: datetime
    updated_at: datetime
