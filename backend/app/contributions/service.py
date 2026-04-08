"""
ContributionService handles contribution business logic.

Responsibilities:
- User application to contribute to projects
- Contribution status tracking and updates
- Listing user contributions and project contributors
"""


class ContributionService:
    """High-level contribution operations."""
    
    def __init__(self):
        # Will be injected with ContributionRepository
        pass
    
    async def apply(self, user_id: int, project_id: int):
        """User applies to contribute to a project."""
        raise NotImplementedError
    
    async def list_by_user(self, user_id: int):
        """List all contributions by a user."""
        raise NotImplementedError
    
    async def list_by_project(self, project_id: int):
        """List all contributors to a project."""
        raise NotImplementedError
    
    async def update_status(self, contribution_id: int, new_status: str):
        """Update contribution status."""
        raise NotImplementedError
