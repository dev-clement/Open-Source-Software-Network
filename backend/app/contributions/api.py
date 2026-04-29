"""
Contribution API routes: apply, list contributions.

All routes delegate to ContributionService for business logic.
"""

from fastapi import HTTPException, APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.contributions.schemas import Contribution, ContributionCreate
from app.shared.db import get_db_session
from app.contributions.service import ContributionService
from app.contributions.sql_service import SqlContributionService
from app.contributions.sql_repository import SqlContributionRepository


router = APIRouter(prefix="/contributions", tags=["contributions"])

def get_contribution_service(session: AsyncSession = Depends(get_db_session)) -> ContributionService:
    """Build the contribution service used by route handlers."""
    return SqlContributionService(SqlContributionRepository(session))

@router.post("/projects/{project_id}/apply", response_model=Contribution)
async def apply_to_project(
    project_id: int,
    contribution_data: ContributionCreate,
    service: ContributionService = Depends(get_contribution_service)
):
    """
    Apply a user contribution to a project.

    This endpoint assigns the given project_id from the route to the contribution data,
    then delegates the application logic to the contribution service. If an error occurs
    during processing, an HTTP 400 error is returned.

    Args:
        project_id: The ID of the project to which the contribution is applied (from the route).
        contribution_data: The contribution details provided by the user (request body).
        service: The contribution service dependency.

    Returns:
        None. Raises HTTPException on error.
    """
    try:
        contribution_data.project_id = project_id
        await service.apply_to_project(contribution_data)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/me", response_model=list[Contribution])
async def list_my_contributions():
    """List current user's contributions."""
    raise NotImplementedError


@router.get("/projects/{project_id}", response_model=list[Contribution])
async def list_project_contributors(project_id: int):
    """List all contributors to a project."""
    raise NotImplementedError


@router.patch("/{contribution_id}", response_model=Contribution)
async def update_contribution_status(contribution_id: int, new_status: str):
    """Update a contribution's status."""
    raise NotImplementedError
