"""
Project API routes: CRUD operations for projects.

All routes delegate to ProjectService for business logic.
"""

from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import settings
from app.db.session import DatabaseEngine
from app.projects.schemas import Project, ProjectCreate, ProjectUpdate
from app.projects.service import ProjectService
from app.projects.sql_repository import SqlRepository
from app.projects.sql_service import SQLProjectService
from app.projects.exception import CreateProjectError
from app.projects.exception import ProjectNotFoundError
from app.auth.api import get_current_user
from app.auth.schemas import User


router = APIRouter(prefix="/projects", tags=["projects"])

_db_engine = DatabaseEngine(database_url=settings.db_url)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session for project route dependencies."""
    async with _db_engine.async_session() as session:
        yield session


def get_project_service(session: AsyncSession = Depends(get_db_session)) -> ProjectService:
    """Build the project service used by route handlers."""
    return SQLProjectService(SqlRepository(session))


@router.post("/", response_model=Project, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    project_service: ProjectService = Depends(get_project_service),
):
    """
    Create a new project.

    This endpoint validates the incoming request body, delegates the creation
    logic to the project service, and returns the created project using an
    HTTP 201 Created response.

    Args:
        project_data: Validated payload containing the project fields to
            persist.
        project_service: Request-scoped service responsible for project
            creation business rules.

    Returns:
        The created project, including database-generated fields such as the
        identifier and timestamps.

    Raises:
        HTTPException: Returns a 409 Conflict response when project creation
            fails due to a business constraint such as a duplicate repository
            URL.
    """
    try:
        return await project_service.create(project_data=project_data)
    except CreateProjectError as cpe:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(cpe)
        )



@router.get("/", response_model=list[Project])
async def list_projects(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    project_service: ProjectService = Depends(get_project_service),
):
    """
    List projects with optional pagination.

    This endpoint delegates project retrieval to the project service and
    returns a paginated list of stored projects.

    Args:
        skip: Number of project records to skip before returning results.
        limit: Maximum number of project records to include in the response.
        project_service: Request-scoped service responsible for project
            listing operations.

    Returns:
        A list of projects matching the requested pagination parameters.
    """
    return await project_service.list(skip=skip, limit=limit)


@router.get("/help-wanted", response_model=list[Project])
async def list_help_wanted_projects(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    project_service: ProjectService = Depends(get_project_service),
):
    """
    List projects currently marked as seeking help.

    This endpoint delegates filtering to the project service and returns only
    projects where the ``help_wanted`` flag is set to ``True``.

    Args:
        skip: Number of help-wanted project records to skip.
        limit: Maximum number of help-wanted project records to include.
        project_service: Request-scoped service responsible for help-wanted
            listing operations.

    Returns:
        A list of projects flagged as help wanted.
    """
    return await project_service.list_help_wanted(skip=skip, limit=limit)


@router.get("/{project_id}", response_model=Project)
async def get_project(
    project_id: int,
    project_service: ProjectService = Depends(get_project_service),
):
    """
    Get a single project by its identifier.

    This endpoint delegates lookup to the project service and returns the
    matching project when found.

    Args:
        project_id: Identifier of the project to retrieve.
        project_service: Request-scoped service responsible for project
            retrieval operations.

    Returns:
        The project matching the provided id.

    Raises:
        HTTPException: Returns a 404 Not Found response when no project exists
            for the given id.
    """
    try:
        return await project_service.get_by_id(project_id=project_id)
    except ProjectNotFoundError as pnfe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(pnfe),
        )


@router.put("/edit/{project_id}", response_model=Project)
async def edit_project(
    project_id: int,
    project_data: ProjectUpdate,
    project_service: ProjectService = Depends(get_project_service),
    user: User = Depends(get_current_user)
):
    """Edit an existing project by id.

    This endpoint delegates partial update logic to the project service and
    returns the updated project when successful.

    Args:
        project_id: Identifier of the project to update.
        project_data: Partial payload containing fields to update.
        project_service: Request-scoped service responsible for update rules.

    Returns:
        The updated project.

    Raises:
        HTTPException: Returns a 404 Not Found response when no project exists
            for the given id.
        HTTPException: Returns a 409 Conflict response when update constraints
            fail, such as repository URL conflicts or invalid update rules.
    """
    try:
        return await project_service.edit(project_id=project_id, project_data=project_data, user=user)
    except ProjectNotFoundError as pnfe:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(pnfe),
        )
    except CreateProjectError as cpe:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(cpe),
        )
