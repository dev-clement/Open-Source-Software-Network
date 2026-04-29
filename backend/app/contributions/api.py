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
from app.auth.api import get_current_user

from app.auth.schemas import User
from app.contributions.exception import UserNotFound


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
async def list_my_contributions(
    user: User = Depends(get_current_user),
    service: ContributionService = Depends(get_contribution_service)
):
    """
    List all contributions made by the currently authenticated user.

    This endpoint retrieves the authenticated user's profile from the request context
    and delegates to the contribution service to fetch all contributions associated
    with that user. The endpoint is protected and requires a valid authentication token.
    If the user has made contributions, a list of those contributions is returned.
    If an error occurs (such as the user not being found or a backend issue),
    an HTTP 400 error is returned.

    Usage:
        - Clients must provide a valid bearer token in the Authorization header.
        - The endpoint returns all contributions for the authenticated user.
        - Useful for users to view their own contribution history across projects.

    Args:
        user: The currently authenticated user (injected by dependency).
        service: The contribution service dependency.

    Returns:
        List[Contribution]: A list of the user's contributions.
        Raises HTTPException on error.
    """
    try:
        return await service.list_by_user(user.id)
    except UserNotFound as unf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(unf)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/projects/{project_id}", response_model=list[Contribution])
async def list_project_contributors(project_id: int, service: ContributionService = Depends(get_contribution_service)):
    """List all contributors to a project."""
    try:
        return await service.list_by_project(project_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.patch("/{contribution_id}", response_model=Contribution)
async def update_contribution_status(contribution_id: int, new_status: str, service: ContributionService = Depends(get_contribution_service)):
    """Update a contribution's status."""
    raise NotImplementedError
