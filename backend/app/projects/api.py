"""
Project API routes: CRUD operations for projects.

All routes delegate to ProjectService for business logic.
"""

from fastapi import APIRouter

from app.projects.schemas import Project, ProjectCreate


router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("/", response_model=Project)
async def create_project(project_data: ProjectCreate):
    """Create a new project."""
    raise NotImplementedError


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
