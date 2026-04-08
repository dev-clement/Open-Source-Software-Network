"""
ProjectService handles project business logic.

Responsibilities:
- Project creation with validation
- Project listing and filtering
- Help-wanted status management
"""


class ProjectService:
    """High-level project operations."""
    
    def __init__(self):
        # Will be injected with ProjectRepository
        pass
    
    async def create(self, project_data):
        """Create a new project."""
        raise NotImplementedError
    
    async def list(self, skip: int = 0, limit: int = 100):
        """List all projects."""
        raise NotImplementedError
    
    async def get_by_id(self, project_id: int):
        """Get a single project by ID."""
        raise NotImplementedError
    
    async def list_help_wanted(self):
        """List projects with help_wanted=True."""
        raise NotImplementedError
