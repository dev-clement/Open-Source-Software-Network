"""This module provides a SQL-based implementation of the project repository."""

from __future__ import annotations
import datetime

from app.projects.repository import ProjectRepository
from app.projects.schemas import Project, ProjectCreate, ProjectUpdate
from app.db.models import Project as ProjectModel
from app.projects.exception import CreateProjectError, ForbiddenError
from app.auth.schemas import User
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

class SqlRepository(ProjectRepository):
    """SQL-based repository for projects."""
    def __init__(self, session: AsyncSession):
        """
        Initializes the SQL repository with a database session.

        Args:
            session: The database session.
        """
        self.session = session
    
    async def create(self, project_data: ProjectCreate) -> Project:
        """
        Creates a new project in the database.

        Args:
            project_data: The data for the new project.

        Returns:
            The created project with database-generated fields populated.

        Raises:
            CreateProjectError: If the project could not be created.
        """
        project_model = ProjectModel(**project_data.model_dump())
        self.session.add(project_model)
        try:
            await self.session.commit()
            await self.session.refresh(project_model)
            return Project.model_validate(project_model)
        except Exception as exc:
            await self.session.rollback()
            raise CreateProjectError(f'''Cannot create the project {project_model}''') from exc

    async def get_by_id(self, project_id: int) -> Project | None:
        """
        Retrieves a project by its ID.

        Args:
            project_id: The ID of the project to retrieve.

        Returns:
            The project, or None if not found.
        """
        statement = select(ProjectModel).where(ProjectModel.id == project_id)
        result = await self.session.execute(statement)
        result_model = result.scalar_one_or_none()
        if result_model is None:
            return None
        return Project.model_validate(result_model)

    async def edit(self, project_id: int, project_data: ProjectUpdate, user: User) -> Project | str | None:
        """Partially updates an existing project, only if owned by the user. Returns 'forbidden' if not owner."""
        # Check if project exists
        statement = select(ProjectModel).where(ProjectModel.id == project_id)
        result = await self.session.execute(statement)
        project_model = result.scalar_one_or_none()

        if project_model is None:
            return None
        if project_model.owner_id != user.id:
            from fastapi import status
            raise ForbiddenError(f"User with id {user.id} is not the owner of project with id {project_id}.")

        project_model.updated_at = datetime.datetime.now()
        updates = project_data.model_dump(exclude_unset=True)
        if not updates:
            return Project.model_validate(project_model)

        for field_name, field_value in updates.items():
            setattr(project_model, field_name, field_value)

        self.session.add(project_model)
        try:
            await self.session.commit()
            await self.session.refresh(project_model)
            return Project.model_validate(project_model)
        except Exception as exc:
            await self.session.rollback()
            raise CreateProjectError(
                f"Cannot edit project with id {project_id}: {exc}"
            ) from exc
    
    async def list(self, skip: int = 0, limit: int = 100) -> list[Project]:
        """
        Lists all projects.

        Args:
            skip: The number of projects to skip.
            limit: The maximum number of projects to return.

        Returns:
            A list of projects.
        """
        statement = select(ProjectModel).offset(skip).limit(limit)
        result = await self.session.execute(statement)
        project_models = result.scalars().all()
        return [Project.model_validate(model) for model in project_models]
    
    async def get_by_repository_url(self, url: str) -> Project | None:
        """
        Retrieves a project by its repository URL.

        Args:
            url: The repository URL of the project to retrieve.

        Returns:
            The project, or None if not found.
        """
        statement = select(ProjectModel).where(ProjectModel.repository_url == url)
        result = await self.session.execute(statement)
        result_model = result.scalar_one_or_none()
        if result_model is None:
            return None
        return Project.model_validate(result_model)
    
    async def list_help_wanted(self, skip: int = 0, limit: int = 100) -> list[Project]:
        """
        Lists all projects that have the 'help_wanted' flag set to True.

        Args:
            skip: The number of projects to skip.
            limit: The maximum number of projects to return.

        Returns:
            A list of projects that need help.
        """
        statement = select(ProjectModel).where(ProjectModel.help_wanted == True).offset(skip).limit(limit)
        result = await self.session.execute(statement)
        project_models = result.scalars().all()
        return [Project.model_validate(model) for model in project_models]
