"""add notify trigger for agent tasks

Revision ID: 0000053
Revises: 0000052
Create Date: 2025-11-16

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0000053'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    """Add PostgreSQL NOTIFY trigger for immediate task notifications"""
    op.execute("""
        -- Create function to notify on new task insert
        CREATE OR REPLACE FUNCTION notify_new_task()
        RETURNS TRIGGER AS $$
        BEGIN
            -- Send notification with task ID as payload
            PERFORM pg_notify('new_task', NEW.id::text);
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
        
        -- Create trigger that fires after insert on agent_tasks
        DROP TRIGGER IF EXISTS agent_task_insert_trigger ON agent_tasks;
        CREATE TRIGGER agent_task_insert_trigger
        AFTER INSERT ON agent_tasks
        FOR EACH ROW
        EXECUTE FUNCTION notify_new_task();
    """)


def downgrade():
    """Remove NOTIFY trigger and function"""
    op.execute("""
        DROP TRIGGER IF EXISTS agent_task_insert_trigger ON agent_tasks;
        DROP FUNCTION IF EXISTS notify_new_task();
    """)
