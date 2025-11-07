"""expand alembic_version column

Revision ID: 009_5
Revises: 009_update_agent_tasks
Create Date: 2025-11-07 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '009_5'
down_revision = '009_update_agent_tasks'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Expand the version_num column to accommodate longer revision IDs
    op.alter_column('alembic_version', 'version_num',
                    existing_type=sa.VARCHAR(32),
                    type_=sa.VARCHAR(100),
                    existing_nullable=False)


def downgrade() -> None:
    # Revert back to 32 characters
    op.alter_column('alembic_version', 'version_num',
                    existing_type=sa.VARCHAR(100),
                    type_=sa.VARCHAR(32),
                    existing_nullable=False)
