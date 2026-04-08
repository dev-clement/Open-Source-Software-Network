"""initial_schema

Revision ID: 0001
Revises: 
Create Date: 2026-04-08 05:41:33.116460

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0001'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial database schema."""
    op.create_table(
        'user',
        sa.Column(
            'id',
            sa.BigInteger(),
            sa.Identity(always=True),
            nullable=False,
        ),
        sa.Column('username', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password', sa.String(255), nullable=False),
        sa.Column('github_page', sa.String(255), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=False),
            server_default=sa.text('CURRENT_TIMESTAMP'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=False),
            server_default=sa.text('CURRENT_TIMESTAMP'),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )

    op.create_table(
        'projects',
        sa.Column(
            'id',
            sa.BigInteger(),
            sa.Identity(always=True),
            nullable=False,
        ),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('repository_url', sa.String(255), nullable=False),
        sa.Column('help_wanted', sa.Boolean(), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=False),
            server_default=sa.text('CURRENT_TIMESTAMP'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=False),
            server_default=sa.text('CURRENT_TIMESTAMP'),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('repository_url'),
    )

    op.create_table(
        'contributions',
        sa.Column(
            'id',
            sa.BigInteger(),
            sa.Identity(always=True),
            nullable=False,
        ),
        sa.Column('fk_user_id', sa.BigInteger(), nullable=False),
        sa.Column('fk_project_id', sa.BigInteger(), nullable=False),
        sa.Column(
            'status',
            sa.String(20),
            server_default='interested',
            nullable=False,
        ),
        sa.Column(
            'applied_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('CURRENT_TIMESTAMP'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('CURRENT_TIMESTAMP'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ['fk_user_id'], ['user.id'], ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['fk_project_id'], ['projects.id'], ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    """Drop all tables created in the initial schema."""
    op.drop_table('contributions')
    op.drop_table('projects')
    op.drop_table('user')
