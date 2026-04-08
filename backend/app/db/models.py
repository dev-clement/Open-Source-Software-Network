from datetime import datetime
from typing import List, Optional
from pydantic import AnyHttpUrl
from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.sql import func
from sqlalchemy.sql.schema import Identity
from sqlmodel import Field, Relationship, SQLModel
from app.domain.enums import ContributionStatus


class User(SQLModel, table=True):
    """
    Represents a user in the OSS Network platform.
    
    Users can create profiles with their GitHub information and bio,
    and participate in open source projects by making contributions.
    """
    __tablename__ = "user"

    id: Optional[int] = Field(
        default=None,
        sa_column=Column(BigInteger, Identity(always=True), primary_key=True),
    )
    username: str = Field(sa_column=Column(String(255), nullable=False))
    email: str = Field(sa_column=Column(String(255), nullable=False, unique=True))
    password: str = Field(sa_column=Column(String(255), nullable=False))
    github_page: Optional[AnyHttpUrl] = Field(default=None, sa_column=Column(String(255), nullable=True))
    bio: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    created_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=False),
            server_default=func.current_timestamp(),
            nullable=False,
        ),
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=False),
            server_default=func.current_timestamp(),
            onupdate=func.current_timestamp(),
            nullable=False,
        ),
    )

    contributions: List["Contribution"] = Relationship(back_populates="user")


class Project(SQLModel, table=True):
    """
    Represents an open source project in the OSS Network platform.
    
    Projects are GitHub repositories that users can contribute to.
    Project owners can mark them as "help wanted" to attract contributors.
    """
    __tablename__ = "projects"

    id: Optional[int] = Field(
        default=None,
        sa_column=Column(BigInteger, Identity(always=True), primary_key=True),
    )
    title: str = Field(sa_column=Column(String(255), nullable=False))
    description: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    repository_url: AnyHttpUrl = Field(sa_column=Column(String(255), nullable=False, unique=True))
    help_wanted: bool = Field(default=False, sa_column=Column(Boolean, nullable=False))
    created_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=False),
            server_default=func.current_timestamp(),
            nullable=False,
        ),
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=False),
            server_default=func.current_timestamp(),
            onupdate=func.current_timestamp(),
            nullable=False,
        ),
    )

    contributions: List["Contribution"] = Relationship(back_populates="project")


class Contribution(SQLModel, table=True):
    """
    Represents a user's contribution to a project in the OSS Network platform.
    
    This is a many-to-many relationship between users and projects,
    tracking the status of their contribution (interested, contributed, closed).
    """
    __tablename__ = "contributions"

    id: Optional[int] = Field(
        default=None,
        sa_column=Column(BigInteger, Identity(always=True), primary_key=True),
    )
    fk_user_id: int = Field(
        sa_column=Column(BigInteger, ForeignKey("user.id", ondelete="CASCADE"), nullable=False),
    )
    fk_project_id: int = Field(
        sa_column=Column(BigInteger, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
    )
    status: ContributionStatus = Field(
        default=ContributionStatus.INTERESTED,
        sa_column=Column(String(20), nullable=False, server_default=ContributionStatus.INTERESTED.value),
    )
    applied_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.current_timestamp(),
            nullable=False,
        ),
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        sa_column=Column(
            DateTime(timezone=True),
            server_default=func.current_timestamp(),
            onupdate=func.current_timestamp(),
            nullable=False,
        ),
    )

    user: Optional[User] = Relationship(back_populates="contributions")
    project: Optional[Project] = Relationship(back_populates="contributions")
