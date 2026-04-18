"""
Project API routes: CRUD operations for projects.

All routes delegate to ProjectService for business logic.
"""

from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import settings
from app.db.session import DatabaseEngine
from app.projects.schemas import Project, ProjectCreate
from app.projects.service import ProjectService
from app.projects.sql_repository import SqlRepository
from app.projects.sql_service import SQLProjectService
from app.projects.exception import CreateProjectError


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
async def list_projects(skip: int = 0, limit: int = 100):
    """List all projects."""
    raise NotImplementedError


@router.get("/{project_id}", response_model=Project)
async def get_project(project_id: int):
    """Get a single project by ID."""
    raise NotImplementedError


@router.get("/help-wanted", response_model=list[Project])
async def list_help_wanted_projects():
    """List projects seeking help."""
    raise NotImplementedError
