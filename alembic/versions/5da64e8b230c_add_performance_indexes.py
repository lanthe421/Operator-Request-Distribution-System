"""add_performance_indexes

Revision ID: 5da64e8b230c
Revises: 88355e9bf82b
Create Date: 2025-11-25 01:21:47.346150

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5da64e8b230c'
down_revision = '88355e9bf82b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add composite index on operators for efficient available operator queries
    # This index supports queries filtering by is_active and current_load
    op.create_index(
        'ix_operators_active_load',
        'operators',
        ['is_active', 'current_load'],
        unique=False
    )


def downgrade() -> None:
    # Remove the composite index (if it exists)
    try:
        op.drop_index('ix_operators_active_load', table_name='operators')
    except Exception:
        # Index might not exist, skip
        pass
