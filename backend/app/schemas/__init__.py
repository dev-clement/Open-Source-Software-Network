"""
Backward compatibility: schemas have been moved to domain-based packages.

Old import paths (app.schemas.*) are maintained for backward compatibility.
New code should import directly from the domain-specific packages:
- app.auth.schemas for user-related schemas
- app.projects.schemas for project-related schemas
- app.contributions.schemas for contribution-related schemas

This file re-exports from the new locations to avoid breaking existing imports.
"""

# User schemas (moved to auth domain)
from app.auth.schemas import (
    UserBase,
    UserCreate,
    UserUpdate,
    User,
)

# Project schemas (moved to projects domain)
from app.projects.schemas import (
    ProjectBase,
    ProjectCreate,
    ProjectUpdate,
    Project,
)

# Contribution schemas (moved to contributions domain)
from app.contributions.schemas import (
    ContributionBase,
    ContributionCreate,
    ContributionUpdate,
    Contribution,
)

__all__ = [
    # User
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "User",
    # Project
    "ProjectBase",
    "ProjectCreate",
    "ProjectUpdate",
    "Project",
    # Contribution
    "ContributionBase",
    "ContributionCreate",
    "ContributionUpdate",
    "Contribution",
]