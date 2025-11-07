"""Add maker-checker workflow fields to evidence

Revision ID: 005
Revises: 004
Create Date: 2025-11-03

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add verification workflow fields
    op.add_column('evidence', sa.Column('verification_status', sa.String(50), nullable=False, server_default='pending'))
    op.add_column('evidence', sa.Column('submitted_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True))
    op.add_column('evidence', sa.Column('reviewed_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True))
    op.add_column('evidence', sa.Column('reviewed_at', sa.DateTime(), nullable=True))
    op.add_column('evidence', sa.Column('review_comments', sa.Text(), nullable=True))
    
    # Create indexes for better query performance
    op.create_index('ix_evidence_verification_status', 'evidence', ['verification_status'])
    op.create_index('ix_evidence_submitted_by', 'evidence', ['submitted_by'])
    op.create_index('ix_evidence_reviewed_by', 'evidence', ['reviewed_by'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_evidence_reviewed_by', 'evidence')
    op.drop_index('ix_evidence_submitted_by', 'evidence')
    op.drop_index('ix_evidence_verification_status', 'evidence')
    
    # Drop columns
    op.drop_column('evidence', 'review_comments')
    op.drop_column('evidence', 'reviewed_at')
    op.drop_column('evidence', 'reviewed_by')
    op.drop_column('evidence', 'submitted_by')
    op.drop_column('evidence', 'verification_status')
