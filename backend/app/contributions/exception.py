class ProjectAndUserNotLinked(Exception):
    """Raised when a user is not linked to a project as a contributor when trying to update status."""
    def __init__(self, user_id: int, project_id: int):
        super().__init__(f"User with id {user_id} is not linked to project with id {project_id}.")
        self.user_id = user_id
        self.project_id = project_id

class ProjectListForUserNotFound(Exception):
    """Raised when no projects are found for the specified user_id in the database."""
    def __init__(self, user_id: int):
        super().__init__(f"No projects found for user with id {user_id}.")
        self.user_id = user_id

class UserNotFound(Exception):
    """Raised when a user with the specified user_id does not exist in the database.

    This exception should be raised by the service layer when an operation requires
    a valid user, but the user_id provided does not correspond to any user in the database.
    """
    def __init__(self, user_id: int):
        super().__init__(f"User with id {user_id} does not exist.")
        self.user_id = user_id

class ProjectNotFound(Exception):
    """Raised when a project with the specified project_id does not exist in the database.

    This exception should be raised by the service layer when an operation requires
    a valid project, but the project_id provided does not correspond to any project in the database.
    """
    def __init__(self, project_id: int):
        super().__init__(f"Project with id {project_id} does not exist.")
        self.project_id = project_id

class ProjectAndUserAlreadyLinked(Exception):
    """Raised when a user is already linked to a project as a contributor.

    This exception is intended to be raised by the service layer when an attempt
    is made to create a contribution that already exists, indicating that the
    user has already applied to contribute to the specified project. It should
    be caught by the API layer and translated into an appropriate HTTP response,
    such as 400 Bad Request or 409 Conflict, depending on the desired semantics.
    """
    def __init__(self, user_id: int, project_id: int):
        """Initialize the exception with the user and project identifiers.

        Storing the ids as attributes allows callers to inspect the values
        programmatically without parsing the message string.

        Args:
            user_id: The identifier of the user who is already linked to the project.
            project_id: The identifier of the project that the user is already linked to.
        """
        super().__init__(f"User with id {user_id} is already linked to project with id {project_id}")
        self.user_id = user_id
        self.project_id = project_id