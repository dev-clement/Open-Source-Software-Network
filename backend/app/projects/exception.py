class ProjectNotFoundError(Exception):
    """Raised when a requested project does not exist in the database.

    This exception is intended to be caught by the API layer and translated
    into an HTTP 404 Not Found response, keeping HTTP concerns out of the
    service layer.
    """

    def __init__(self, project_id: int):
        """Initialize the exception with the missing project's identifier.

        Storing the id as an attribute allows callers to inspect the value
        programmatically without parsing the message string.

        Args:
            project_id: The identifier of the project that could not be found.
        """
        super().__init__(f"Project with id {project_id} not found")
        self.project_id = project_id

    def get_project_id(self) -> int:
        """Return the identifier of the project that could not be found.

        Returns:
            The project id that triggered this exception.
        """
        return self.project_id

class CreateProjectError(Exception):
    """Raised when a project cannot be created due to a conflict or validation error.

    This exception can be used to indicate issues such as duplicate repository URLs
    or other constraints that prevent a new project from being persisted. It should
    be caught by the API layer and translated into an appropriate HTTP response, such
    as 400 Bad Request or 409 Conflict, depending on the nature of the error.
    """

    def __init__(self, message: str):
        """Initialize the exception with a descriptive error message.

        Args:
            message: A human-readable description of the error that occurred during project creation.
        """
        super().__init__(message)