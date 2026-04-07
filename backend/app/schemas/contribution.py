from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ContributionBase(BaseModel):
    fk_user_id: int
    fk_project_id: int
    status: str = "interested"


class ContributionCreate(ContributionBase):
    pass


class ContributionUpdate(BaseModel):
    status: Optional[str] = None


class Contribution(ContributionBase):
    id: int
    applied_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True