"""Add project_controls table

Revision ID: 006
Revises: 898cc8361b19
Create Date: 2025-01-08 10:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '006'
down_revision: Union[str, None] = '898cc8361b19'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create project_controls table
    op.create_table(
        'project_controls',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('control_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('implementation_notes', sa.Text(), nullable=True),
        sa.Column('last_assessed', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['control_id'], ['controls.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'control_id', name='uq_project_control')
    )
    op.create_index(op.f('ix_project_controls_id'), 'project_controls', ['id'], unique=False)
    op.create_index(op.f('ix_project_controls_project_id'), 'project_controls', ['project_id'], unique=False)
    op.create_index(op.f('ix_project_controls_control_id'), 'project_controls', ['control_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_project_controls_control_id'), table_name='project_controls')
    op.drop_index(op.f('ix_project_controls_project_id'), table_name='project_controls')
    op.drop_index(op.f('ix_project_controls_id'), table_name='project_controls')
    op.drop_table('project_controls')
