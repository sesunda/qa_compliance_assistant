"""Update agent_tasks table schema

Revision ID: 009_update_agent_tasks
Revises: 008_add_conversation_sessions
Create Date: 2025-11-07 10:10:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '009_update_agent_tasks'
down_revision = '008_add_conversation_sessions'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns
    op.add_column('agent_tasks', sa.Column('title', sa.String(length=255), nullable=True))
    op.add_column('agent_tasks', sa.Column('description', sa.Text(), nullable=True))
    op.add_column('agent_tasks', sa.Column('created_by', sa.Integer(), nullable=True))
    op.add_column('agent_tasks', sa.Column('error_message', sa.Text(), nullable=True))
    op.add_column('agent_tasks', sa.Column('progress', sa.Integer(), server_default='0', nullable=True))
    op.add_column('agent_tasks', sa.Column('updated_at', sa.DateTime(), nullable=True))
    op.add_column('agent_tasks', sa.Column('started_at', sa.DateTime(), nullable=True))
    op.add_column('agent_tasks', sa.Column('completed_at', sa.DateTime(), nullable=True))
    
    # Create foreign key for created_by
    op.create_foreign_key(
        'fk_agent_tasks_created_by_users',
        'agent_tasks', 'users',
        ['created_by'], ['id'],
        ondelete='CASCADE'
    )
    
    # Create indexes
    op.create_index(op.f('ix_agent_tasks_task_type'), 'agent_tasks', ['task_type'], unique=False)
    op.create_index(op.f('ix_agent_tasks_status'), 'agent_tasks', ['status'], unique=False)
    op.create_index(op.f('ix_agent_tasks_created_by'), 'agent_tasks', ['created_by'], unique=False)
    
    # Drop old columns that are no longer used
    op.drop_constraint('agent_tasks_agent_id_fkey', 'agent_tasks', type_='foreignkey')
    op.drop_constraint('agent_tasks_agency_id_fkey', 'agent_tasks', type_='foreignkey')
    op.drop_column('agent_tasks', 'agent_id')
    op.drop_column('agent_tasks', 'agency_id')
    op.drop_column('agent_tasks', 'finished_at')
    
    # Make task_type and title non-nullable (after adding them)
    # First set default values for existing rows
    op.execute("UPDATE agent_tasks SET title = 'Legacy Task' WHERE title IS NULL")
    op.execute("UPDATE agent_tasks SET task_type = 'unknown' WHERE task_type IS NULL")
    
    # Now make them non-nullable
    op.alter_column('agent_tasks', 'title', nullable=False)
    op.alter_column('agent_tasks', 'task_type', nullable=False)


def downgrade() -> None:
    # Restore old schema
    op.add_column('agent_tasks', sa.Column('agent_id', sa.Integer(), nullable=True))
    op.add_column('agent_tasks', sa.Column('agency_id', sa.Integer(), nullable=True))
    op.add_column('agent_tasks', sa.Column('finished_at', sa.DateTime(), nullable=True))
    
    op.create_foreign_key('agent_tasks_agent_id_fkey', 'agent_tasks', 'agents', ['agent_id'], ['id'])
    op.create_foreign_key('agent_tasks_agency_id_fkey', 'agent_tasks', 'agencies', ['agency_id'], ['id'])
    
    # Drop new columns
    op.drop_index(op.f('ix_agent_tasks_created_by'), table_name='agent_tasks')
    op.drop_index(op.f('ix_agent_tasks_status'), table_name='agent_tasks')
    op.drop_index(op.f('ix_agent_tasks_task_type'), table_name='agent_tasks')
    
    op.drop_constraint('fk_agent_tasks_created_by_users', 'agent_tasks', type_='foreignkey')
    
    op.drop_column('agent_tasks', 'completed_at')
    op.drop_column('agent_tasks', 'started_at')
    op.drop_column('agent_tasks', 'updated_at')
    op.drop_column('agent_tasks', 'progress')
    op.drop_column('agent_tasks', 'error_message')
    op.drop_column('agent_tasks', 'created_by')
    op.drop_column('agent_tasks', 'description')
    op.drop_column('agent_tasks', 'title')
