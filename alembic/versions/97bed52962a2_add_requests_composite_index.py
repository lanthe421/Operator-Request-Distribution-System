"""add_requests_composite_index

Revision ID: 97bed52962a2
Revises: 5da64e8b230c
Create Date: 2025-11-25 01:44:53.539164

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '97bed52962a2'
down_revision = '5da64e8b230c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add composite index on requests for efficient distribution queries
    # This index supports queries filtering by operator_id, source_id, and status
    # Complements existing individual indexes for more complex query patterns
    op.create_index(
        'ix_requests_operator_source_status',
        'requests',
        ['operator_id', 'source_id', 'status'],
        unique=False
    )


def downgrade() -> None:
    # Remove the composite index
    op.drop_index('ix_requests_operator_source_status', table_name='requests')
