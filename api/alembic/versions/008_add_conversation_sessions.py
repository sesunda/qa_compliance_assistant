"""add conversation sessions

Revision ID: 008
Revises: 007
Create Date: 2025-01-04 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create conversation_sessions table
    op.create_table(
        'conversation_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(), nullable=False, unique=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('messages', postgresql.JSONB(), nullable=False, default=[]),
        sa.Column('context', postgresql.JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_activity', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('active', sa.Boolean(), nullable=False, default=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )
    
    # Create indices for performance
    op.create_index('ix_conversation_sessions_session_id', 'conversation_sessions', ['session_id'])
    op.create_index('ix_conversation_sessions_user_id', 'conversation_sessions', ['user_id'])
    op.create_index('ix_conversation_sessions_active', 'conversation_sessions', ['active'])
    op.create_index('ix_conversation_sessions_last_activity', 'conversation_sessions', ['last_activity'])


def downgrade() -> None:
    op.drop_index('ix_conversation_sessions_last_activity')
    op.drop_index('ix_conversation_sessions_active')
    op.drop_index('ix_conversation_sessions_user_id')
    op.drop_index('ix_conversation_sessions_session_id')
    op.drop_table('conversation_sessions')
