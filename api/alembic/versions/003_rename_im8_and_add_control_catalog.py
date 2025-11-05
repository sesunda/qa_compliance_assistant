"""Rename IM8 table to IM8 domain areas and add control_catalog

Revision ID: 003
Revises: 002
Create Date: 2025-10-31 03:30:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename existing im8_knowledge_areas to im8_domain_areas
    op.rename_table('im8_knowledge_areas', 'im8_domain_areas')

    # Create control_catalog table
    op.create_table(
        'control_catalog',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('external_id', sa.String(length=100), nullable=True),
        sa.Column('title', sa.String(length=512), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('family', sa.String(length=255), nullable=True),
        sa.Column('raw_json', sa.JSON(), nullable=True),
        sa.Column('proposed_domain_id', sa.Integer(), nullable=True),
        sa.Column('proposed_confidence', sa.String(length=20), nullable=True),
        sa.Column('mapping_rationale', sa.Text(), nullable=True),
        sa.Column('approved_domain_id', sa.Integer(), nullable=True),
        sa.Column('approved_by', sa.String(length=255), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['proposed_domain_id'], ['im8_domain_areas.id'], ),
        sa.ForeignKeyConstraint(['approved_domain_id'], ['im8_domain_areas.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_control_catalog_id'), 'control_catalog', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_control_catalog_id'), table_name='control_catalog')
    op.drop_table('control_catalog')
    # rename back
    op.rename_table('im8_domain_areas', 'im8_knowledge_areas')
