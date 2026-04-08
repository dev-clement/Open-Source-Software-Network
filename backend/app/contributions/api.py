"""
Contribution API routes: apply, list contributions.

All routes delegate to ContributionService for business logic.
"""

from fastapi import APIRouter

from app.contributions.schemas import Contribution, ContributionCreate


router = APIRouter(prefix="/contributions", tags=["contributions"])


@router.post("/projects/{project_id}/apply", response_model=Contribution)
async def apply_to_project(project_id: int, contribution_data: ContributionCreate):
    """Apply to contribute to a project."""
    raise NotImplementedError


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
