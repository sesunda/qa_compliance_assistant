"""Convert all timestamp columns to timestamp with time zone (SGT)

Revision ID: 002
Revises: 0000053
Create Date: 2025-11-17 22:58:00.000000

This migration converts all timestamp columns from 'timestamp without time zone' 
to 'timestamp with time zone' to properly support Singapore timezone (SGT/UTC+8).

The existing data in the database is interpreted as UTC and will be preserved as-is.
New records will be saved with timezone information from the application (SGT).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '0000053'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Convert all timestamp columns to timestamp with time zone"""
    
    # agencies table
    op.execute("ALTER TABLE agencies ALTER COLUMN created_at TYPE timestamp with time zone USING created_at AT TIME ZONE 'UTC'")
    
    # user_roles table
    op.execute("ALTER TABLE user_roles ALTER COLUMN created_at TYPE timestamp with time zone USING created_at AT TIME ZONE 'UTC'")
    
    # users table
    op.execute("ALTER TABLE users ALTER COLUMN last_login TYPE timestamp with time zone USING last_login AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE users ALTER COLUMN created_at TYPE timestamp with time zone USING created_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE users ALTER COLUMN updated_at TYPE timestamp with time zone USING updated_at AT TIME ZONE 'UTC'")
    
    # projects table
    op.execute("ALTER TABLE projects ALTER COLUMN created_at TYPE timestamp with time zone USING created_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE projects ALTER COLUMN updated_at TYPE timestamp with time zone USING updated_at AT TIME ZONE 'UTC'")
    
    # assessments table
    op.execute("ALTER TABLE assessments ALTER COLUMN created_at TYPE timestamp with time zone USING created_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE assessments ALTER COLUMN completed_at TYPE timestamp with time zone USING completed_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE assessments ALTER COLUMN target_completion_date TYPE timestamp with time zone USING target_completion_date AT TIME ZONE 'UTC'")
    
    # controls table
    op.execute("ALTER TABLE controls ALTER COLUMN created_at TYPE timestamp with time zone USING created_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE controls ALTER COLUMN updated_at TYPE timestamp with time zone USING updated_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE controls ALTER COLUMN reviewed_at TYPE timestamp with time zone USING reviewed_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE controls ALTER COLUMN last_tested_at TYPE timestamp with time zone USING last_tested_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE controls ALTER COLUMN next_test_due TYPE timestamp with time zone USING next_test_due AT TIME ZONE 'UTC'")
    
    # evidence table
    op.execute("ALTER TABLE evidence ALTER COLUMN uploaded_at TYPE timestamp with time zone USING uploaded_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE evidence ALTER COLUMN reviewed_at TYPE timestamp with time zone USING reviewed_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE evidence ALTER COLUMN created_at TYPE timestamp with time zone USING created_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE evidence ALTER COLUMN updated_at TYPE timestamp with time zone USING updated_at AT TIME ZONE 'UTC'")
    
    # findings table
    op.execute("ALTER TABLE findings ALTER COLUMN created_at TYPE timestamp with time zone USING created_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE findings ALTER COLUMN resolved_at TYPE timestamp with time zone USING resolved_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE findings ALTER COLUMN validated_at TYPE timestamp with time zone USING validated_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE findings ALTER COLUMN due_date TYPE timestamp with time zone USING due_date AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE findings ALTER COLUMN updated_at TYPE timestamp with time zone USING updated_at AT TIME ZONE 'UTC'")
    
    # reports table
    op.execute("ALTER TABLE reports ALTER COLUMN generated_at TYPE timestamp with time zone USING generated_at AT TIME ZONE 'UTC'")
    
    # control_catalog table
    op.execute("ALTER TABLE control_catalog ALTER COLUMN approved_at TYPE timestamp with time zone USING approved_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE control_catalog ALTER COLUMN created_at TYPE timestamp with time zone USING created_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE control_catalog ALTER COLUMN updated_at TYPE timestamp with time zone USING updated_at AT TIME ZONE 'UTC'")
    
    # agent_tasks table
    op.execute("ALTER TABLE agent_tasks ALTER COLUMN created_at TYPE timestamp with time zone USING created_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE agent_tasks ALTER COLUMN updated_at TYPE timestamp with time zone USING updated_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE agent_tasks ALTER COLUMN started_at TYPE timestamp with time zone USING started_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE agent_tasks ALTER COLUMN completed_at TYPE timestamp with time zone USING completed_at AT TIME ZONE 'UTC'")
    
    # conversation_sessions table
    op.execute("ALTER TABLE conversation_sessions ALTER COLUMN created_at TYPE timestamp with time zone USING created_at AT TIME ZONE 'UTC'")
    op.execute("ALTER TABLE conversation_sessions ALTER COLUMN last_activity TYPE timestamp with time zone USING last_activity AT TIME ZONE 'UTC'")
    
    # assessment_controls table
    op.execute("ALTER TABLE assessment_controls ALTER COLUMN created_at TYPE timestamp with time zone USING created_at AT TIME ZONE 'UTC'")
    
    # finding_comments table
    op.execute("ALTER TABLE finding_comments ALTER COLUMN created_at TYPE timestamp with time zone USING created_at AT TIME ZONE 'UTC'")


def downgrade() -> None:
    """Convert all timestamp columns back to timestamp without time zone"""
    
    # agencies table
    op.execute("ALTER TABLE agencies ALTER COLUMN created_at TYPE timestamp without time zone")
    
    # user_roles table
    op.execute("ALTER TABLE user_roles ALTER COLUMN created_at TYPE timestamp without time zone")
    
    # users table
    op.execute("ALTER TABLE users ALTER COLUMN last_login TYPE timestamp without time zone")
    op.execute("ALTER TABLE users ALTER COLUMN created_at TYPE timestamp without time zone")
    op.execute("ALTER TABLE users ALTER COLUMN updated_at TYPE timestamp without time zone")
    
    # projects table
    op.execute("ALTER TABLE projects ALTER COLUMN created_at TYPE timestamp without time zone")
    op.execute("ALTER TABLE projects ALTER COLUMN updated_at TYPE timestamp without time zone")
    
    # assessments table
    op.execute("ALTER TABLE assessments ALTER COLUMN created_at TYPE timestamp without time zone")
    op.execute("ALTER TABLE assessments ALTER COLUMN completed_at TYPE timestamp without time zone")
    op.execute("ALTER TABLE assessments ALTER COLUMN target_completion_date TYPE timestamp without time zone")
    
    # controls table
    op.execute("ALTER TABLE controls ALTER COLUMN created_at TYPE timestamp without time zone")
    op.execute("ALTER TABLE controls ALTER COLUMN updated_at TYPE timestamp without time zone")
    op.execute("ALTER TABLE controls ALTER COLUMN reviewed_at TYPE timestamp without time zone")
    op.execute("ALTER TABLE controls ALTER COLUMN last_tested_at TYPE timestamp without time zone")
    op.execute("ALTER TABLE controls ALTER COLUMN next_test_due TYPE timestamp without time zone")
    
    # evidence table
    op.execute("ALTER TABLE evidence ALTER COLUMN uploaded_at TYPE timestamp without time zone")
    op.execute("ALTER TABLE evidence ALTER COLUMN reviewed_at TYPE timestamp without time zone")
    op.execute("ALTER TABLE evidence ALTER COLUMN created_at TYPE timestamp without time zone")
    op.execute("ALTER TABLE evidence ALTER COLUMN updated_at TYPE timestamp without time zone")
    
    # findings table
    op.execute("ALTER TABLE findings ALTER COLUMN created_at TYPE timestamp without time zone")
    op.execute("ALTER TABLE findings ALTER COLUMN resolved_at TYPE timestamp without time zone")
    op.execute("ALTER TABLE findings ALTER COLUMN validated_at TYPE timestamp without time zone")
    op.execute("ALTER TABLE findings ALTER COLUMN due_date TYPE timestamp without time zone")
    op.execute("ALTER TABLE findings ALTER COLUMN updated_at TYPE timestamp without time zone")
    
    # reports table
    op.execute("ALTER TABLE reports ALTER COLUMN generated_at TYPE timestamp without time zone")
    
    # control_catalog table
    op.execute("ALTER TABLE control_catalog ALTER COLUMN approved_at TYPE timestamp without time zone")
    op.execute("ALTER TABLE control_catalog ALTER COLUMN created_at TYPE timestamp without time zone")
    op.execute("ALTER TABLE control_catalog ALTER COLUMN updated_at TYPE timestamp without time zone")
    
    # agent_tasks table
    op.execute("ALTER TABLE agent_tasks ALTER COLUMN created_at TYPE timestamp without time zone")
    op.execute("ALTER TABLE agent_tasks ALTER COLUMN updated_at TYPE timestamp without time zone")
    op.execute("ALTER TABLE agent_tasks ALTER COLUMN started_at TYPE timestamp without time zone")
    op.execute("ALTER TABLE agent_tasks ALTER COLUMN completed_at TYPE timestamp without time zone")
    
    # conversation_sessions table
    op.execute("ALTER TABLE conversation_sessions ALTER COLUMN created_at TYPE timestamp without time zone")
    op.execute("ALTER TABLE conversation_sessions ALTER COLUMN last_activity TYPE timestamp without time zone")
    
    # assessment_controls table
    op.execute("ALTER TABLE assessment_controls ALTER COLUMN created_at TYPE timestamp without time zone")
    
    # finding_comments table
    op.execute("ALTER TABLE finding_comments ALTER COLUMN created_at TYPE timestamp without time zone")
