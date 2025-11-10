"""Add project_type and start_date to projects table

Revision ID: 002
Revises: 001
Create Date: 2025-11-10 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add project_type column with default value
    op.add_column('projects', 
        sa.Column('project_type', sa.String(length=100), nullable=True, server_default='compliance_assessment')
    )
    
    # Add start_date column (nullable)
    op.add_column('projects', 
        sa.Column('start_date', sa.Date(), nullable=True)
    )


def downgrade() -> None:
    # Remove columns if rolling back
    op.drop_column('projects', 'start_date')
    op.drop_column('projects', 'project_type')
