from .service import ContributionService
from .schemas import ContributionCreate
from .exception import ProjectAndUserAlreadyLinked, UserNotFound, ProjectNotFound, ProjectListForUserNotFound, ProjectAndUserNotLinked

class SqlContributionService(ContributionService):
    """SQL-based implementation of ContributionService.

    This class implements the business logic defined in ContributionService
    using SQLAlchemy for database interactions. It relies on a repository
    layer to abstract away all database access, ensuring that the service
    focuses solely on application logic with all database interaction details
    hidden from the service layer."""
    def __init__(self, repository):
        """Initialize the SQL-based contribution service with a repository.

        :param repository: An instance of a repository class that provides
            methods for database access related to contributions."""
        self.repository = repository
    
    async def apply(self, user_id: int, project_id: int):
        """
        Create a new contribution linking a user to a project.

        This method checks if the user is already linked to the project. If not, it creates
        a new contribution record in the database with the given user and project IDs.

        Args:
            user_id (int): The ID of the user applying to contribute.
            project_id (int): The ID of the project to which the user is applying.

        Returns:
            Contribution: The created contribution object.

        Raises:
            ProjectAndUserAlreadyLinked: If the user is already linked to the project.
        """
        existing = await self.repository.get_by_user_and_project(user_id, project_id)
        if existing:
            raise ProjectAndUserAlreadyLinked(user_id, project_id)
        contribution_data = ContributionCreate(
            user_id=user_id,
            project_id=project_id
        )
        contribution = await self.repository.create(contribution_data)
        return contribution
    
    async def list_by_user(self, user_id: int):
        """
        List all contributions made by a specific user.

        Args:
            user_id (int): The ID of the user whose contributions are to be listed.

        Returns:
            List[Contribution]: A list of Contribution objects for the user.
        """
        existing_contributions = await self.repository.get_by_user(user_id)
        if not existing_contributions:
            raise UserNotFound(user_id)
        return await self.repository.list_by_user(user_id)
    
    async def list_by_project(self, project_id: int):
        """
        List all contributions for a specific project.

        Args:
            project_id (int): The ID of the project whose contributions are to be listed.

        Returns:
            List[Contribution]: A list of Contribution objects for the project.

        Raises:
            ProjectNotFound: If no contributions are found for the given project_id.
        """
        existing_contributions = await self.repository.get_by_project(project_id)
        if not existing_contributions:
            raise ProjectNotFound(project_id)
        return await self.repository.list_by_project(project_id)
    
    async def list_project_by_user(self, user_id: int):
        """
        List all projects for a specific user.

        Args:
            user_id (int): The ID of the user whose projects are to be listed.

        Returns:
            List[Project]: A list of Project objects for the user.

        Raises:
            ProjectListForUserNotFound: If no projects are found for the given user_id.
        """
        projects = await self.repository.list_project_by_user(user_id)
        if not projects:
            raise ProjectListForUserNotFound(user_id)
        return projects

    async def update_status(self, user_id: int, project_id: int, new_status: str):
        """
        Update the status of a contribution for a given user and project.

        Args:
            user_id (int): The ID of the user.
            project_id (int): The ID of the project.
            new_status (str): The new status to set.

        Raises:
            ProjectAndUserNotLinked: If the user is not linked to the project.
        """
        contribution = await self.repository.get_by_user_and_project(user_id, project_id)
        if not contribution:
            raise ProjectAndUserNotLinked(user_id, project_id)
        return await self.repository.update_status(user_id, project_id, new_status)