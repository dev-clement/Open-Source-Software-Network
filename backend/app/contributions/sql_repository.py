"""SQL backend repository implementation"""

from sqlmodel import select

from sqlalchemy.ext.asyncio import AsyncSession
from app.contributions.repository import ContributionRepository
from app.contributions.schemas import Contribution, ContributionBase
from app.projects.exception import CreateProjectError

class SqlContributionRepository(ContributionRepository):
    """Concrete ``ContributionRepository`` packed with an asynchronous SQLAlchemy session

    This implementation maps contribution schemas to the SQLModel user table and keeps
    all database interaction details hidden from the service layer.
    """

    def __init__(self, session: AsyncSession):
        """Store the async database session used for repository operations.

        :param session: Active asynchronous SQLAlchemy session used to execute
            user persistence queries and transactions."""
        self.session = session
    
    async def get_by_id(self, contribution_id):
        """
        Retrieve a contribution by its unique ID.

        :param contribution_id: The unique identifier of the contribution.
        :return: A Contribution model instance if found, otherwise None.
        """
        statement = select(Contribution).where(Contribution.id == contribution_id)
        result = await self.session.execute(statement)
        contribution = result.scalar_one_or_none()
        if contribution is None:
            return None
        return Contribution.model_validate(contribution)
    
    async def get_by_project(self, project_id):
        """
        Retrieve all contributions associated with a given project ID.

        :param project_id: The unique identifier of the project.
        :return: A list of Contribution model instances for the project.
        """
        statement = select(Contribution).where(Contribution.fk_project_id == project_id)
        result = await self.session.execute(statement)
        contributions = result.scalars().all()
        return [Contribution.model_validate(Contribution.model_dump(contribution)) for contribution in contributions]
    
    async def get_by_user(self, user_email):
        """
        Retrieve all contributions made by a user, identified by their email.

        :param user_email: The email address of the user.
        :return: A list of Contribution model instances for the user.
        """
        statement = select(Contribution).where(Contribution.fk_user_email == user_email)
        result = await self.session.execute(statement)
        contributions = result.scalars().all()
        return [Contribution.model_validate(Contribution.model_dump(contribution)) for contribution in contributions]
    
    async def get_by_user_and_project(self, user_id, project_id):
        """
        Retrieve a contribution by user ID and project ID.

        :param user_id: The unique identifier of the user.
        :param project_id: The unique identifier of the project.
        :return: A Contribution model instance if found, otherwise None.
        """
        statement = select(Contribution).where(Contribution.fk_user_id == user_id, Contribution.fk_project_id == project_id)
        result = await self.session.execute(statement)
        contribution = result.scalar_one_or_none()
        if contribution is None:
            return None
        return Contribution.model_validate(Contribution.model_dump(contribution))
    
    async def list_by_user(self, user_id):
        """
        List all contributions for a specific user by user ID.

        :param user_id: The unique identifier of the user.
        :return: A list of Contribution model instances for the user.
        """
        statement = select(Contribution).where(Contribution.fk_user_id == user_id)
        result = await self.session.execute(statement)
        contributions = result.scalars().all()
        return [Contribution.model_validate(Contribution.model_dump(contribution)) for contribution in contributions]

    async def list_by_project(self, project_id):
        """
        List all contributions for a specific project by project ID.

        :param project_id: The unique identifier of the project.
        :return: A list of Contribution model instances for the project.
        """
        statement = select(Contribution).where(Contribution.fk_project_id == project_id)
        result = await self.session.execute(statement)
        contributions = result.scalars().all()
        return [Contribution.model_validate(Contribution.model_dump(contribution)) for contribution in contributions]

    async def create(self, contribution_data: ContributionBase) -> Contribution:
        """
        Create a new contribution in the database.

        :param contribution_data: The data required to create a contribution.
        :return: The created Contribution model instance.
        :raises CreateProjectError: If the contribution cannot be created.
        """
        contribution_model = Contribution(**contribution_data.model_dump())
        self.session.add(contribution_model)
        try:
            await self.session.commit()
            await self.session.refresh(contribution_model)
        except Exception:
            await self.session.rollback()
            raise CreateProjectError(f'''Cannot create the contribution {contribution_model}''')
        return Contribution.model_validate(Contribution.model_dump(contribution_model))

    async def update_status(self, contribution_id, status):
        """
        Update the status of a contribution by its ID.

        :param contribution_id: The unique identifier of the contribution.
        :param status: The new status to set for the contribution.
        :return: The updated Contribution model instance if found, otherwise None.
        :raises CreateProjectError: If the update fails.
        """
        statement = select(Contribution).Where(Contribution.id == contribution_id)
        result = await self.session.execute(statement)
        contribution = result.scalar_one_or_none()
        if contribution is None:
            return None
        contribution.status = status
        self.session.add(contribution)
        try:
            await self.session.commit()
            await self.session.refresh(contribution)
        except Exception:
            await self.session.rollback()
            raise CreateProjectError(f'''Cannot update the status of the contribution {contribution}''')
        return Contribution.model_validate(Contribution.model_dump(contribution))
    
    async def delete_contribution_from_project(self, contribution_id):
        """
        Delete a contribution from a project by its ID.

        :param contribution_id: The unique identifier of the contribution to delete.
        :return: True if the contribution was deleted, False if not found.
        :raises CreateProjectError: If the deletion fails.
        """
        statement = select(Contribution).Where(Contribution.id == contribution_id)
        result = await self.session.execute(statement)
        contribution = result.scalar_one_or_none()
        if contribution is None:
            return False
        try:
            await self.session.delete(contribution)
            await self.session.commit()
        except Exception:
            await self.session.rollback()
            raise CreateProjectError(f'''Cannot delete the contribution {contribution}''')
        return True
