"""Consolidated initial schema - all tables

Revision ID: 001
Revises: 
Create Date: 2025-11-07 08:53:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create agencies table first (referenced by many tables)
    op.create_table('agencies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('code', sa.String(length=100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('contact_email', sa.String(length=255), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_agencies_id'), 'agencies', ['id'], unique=False)
    
    # Create user_roles table
    op.create_table('user_roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('permissions', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_user_roles_id'), 'user_roles', ['id'], unique=False)
    
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('agency_id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('is_verified', sa.Boolean(), nullable=True, default=False),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['agency_id'], ['agencies.id'], ),
        sa.ForeignKeyConstraint(['role_id'], ['user_roles.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    
    # Create projects table
    op.create_table('projects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agency_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('project_type', sa.String(length=100), nullable=True, server_default='compliance_assessment'),
        sa.Column('status', sa.String(length=50), nullable=True, default='active'),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['agency_id'], ['agencies.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_projects_id'), 'projects', ['id'], unique=False)
    
    # Create assessments table
    op.create_table('assessments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agency_id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('assessment_type', sa.String(length=50), nullable=True),
        sa.Column('performed_by', sa.String(length=255), nullable=True),
        sa.Column('scope', sa.Text(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True, default='open'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('assigned_to', sa.Integer(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('progress_percentage', sa.Integer(), nullable=False, default=0),
        sa.Column('target_completion_date', sa.DateTime(), nullable=True),
        sa.Column('framework', sa.String(length=100), nullable=True),
        sa.Column('assessment_period_start', sa.Date(), nullable=True),
        sa.Column('assessment_period_end', sa.Date(), nullable=True),
        sa.Column('findings_count', sa.Integer(), nullable=False, default=0),
        sa.Column('controls_tested_count', sa.Integer(), nullable=False, default=0),
        sa.ForeignKeyConstraint(['agency_id'], ['agencies.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['assigned_to'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_assessments_id'), 'assessments', ['id'], unique=False)
    op.create_index(op.f('ix_assessments_status'), 'assessments', ['status'], unique=False)
    op.create_index(op.f('ix_assessments_assigned_to'), 'assessments', ['assigned_to'], unique=False)
    op.create_index(op.f('ix_assessments_framework'), 'assessments', ['framework'], unique=False)
    
    # Create controls table
    op.create_table('controls',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('agency_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('control_type', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True, default='pending'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('reviewed_by', sa.Integer(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('review_status', sa.String(length=50), nullable=False, default='pending'),
        sa.Column('assessment_score', sa.Integer(), nullable=True),
        sa.Column('test_procedure', sa.Text(), nullable=True),
        sa.Column('test_results', sa.Text(), nullable=True),
        sa.Column('testing_frequency', sa.String(length=50), nullable=True),
        sa.Column('last_tested_at', sa.DateTime(), nullable=True),
        sa.Column('next_test_due', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['agency_id'], ['agencies.id'], ),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_controls_id'), 'controls', ['id'], unique=False)
    op.create_index(op.f('ix_controls_review_status'), 'controls', ['review_status'], unique=False)
    op.create_index(op.f('ix_controls_next_test_due'), 'controls', ['next_test_due'], unique=False)
    
    # Create evidence table
    op.create_table('evidence',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('control_id', sa.Integer(), nullable=False),
        sa.Column('agency_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('file_path', sa.String(length=500), nullable=True),
        sa.Column('evidence_type', sa.String(length=100), nullable=True),
        sa.Column('verified', sa.Boolean(), nullable=True, default=False),
        sa.Column('original_filename', sa.String(length=255), nullable=True),
        sa.Column('mime_type', sa.String(length=100), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('checksum', sa.String(length=64), nullable=True),
        sa.Column('storage_backend', sa.String(length=50), nullable=True, default='local'),
        sa.Column('uploaded_by', sa.Integer(), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(), nullable=True),
        sa.Column('verification_status', sa.String(length=50), nullable=False, default='pending'),
        sa.Column('submitted_by', sa.Integer(), nullable=True),
        sa.Column('reviewed_by', sa.Integer(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('review_comments', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['control_id'], ['controls.id'], ),
        sa.ForeignKeyConstraint(['agency_id'], ['agencies.id'], ),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['submitted_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_evidence_id'), 'evidence', ['id'], unique=False)
    
    # Create findings table
    op.create_table('findings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('assessment_id', sa.Integer(), nullable=False),
        sa.Column('control_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('severity', sa.String(length=50), nullable=True),
        sa.Column('cve', sa.String(length=100), nullable=True),
        sa.Column('cvss', sa.String(length=20), nullable=True),
        sa.Column('remediation', sa.Text(), nullable=True),
        sa.Column('evidence', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('resolution_status', sa.String(length=50), nullable=False, default='open'),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_by', sa.Integer(), nullable=True),
        sa.Column('resolution_evidence_id', sa.Integer(), nullable=True),
        sa.Column('false_positive', sa.Boolean(), nullable=False, default=False),
        sa.Column('validated_by', sa.Integer(), nullable=True),
        sa.Column('validated_at', sa.DateTime(), nullable=True),
        sa.Column('assigned_to', sa.Integer(), nullable=True),
        sa.Column('due_date', sa.DateTime(), nullable=True),
        sa.Column('priority', sa.String(length=20), nullable=True),
        sa.Column('remediation_notes', sa.Text(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['assessment_id'], ['assessments.id'], ),
        sa.ForeignKeyConstraint(['control_id'], ['controls.id'], ),
        sa.ForeignKeyConstraint(['resolved_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['resolution_evidence_id'], ['evidence.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['validated_by'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['assigned_to'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_findings_id'), 'findings', ['id'], unique=False)
    op.create_index(op.f('ix_findings_resolution_status'), 'findings', ['resolution_status'], unique=False)
    op.create_index(op.f('ix_findings_assigned_to'), 'findings', ['assigned_to'], unique=False)
    op.create_index(op.f('ix_findings_due_date'), 'findings', ['due_date'], unique=False)
    op.create_index(op.f('ix_findings_priority'), 'findings', ['priority'], unique=False)
    
    # Create reports table
    op.create_table('reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('report_type', sa.String(length=100), nullable=True),
        sa.Column('generated_at', sa.DateTime(), nullable=True),
        sa.Column('file_path', sa.String(length=500), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reports_id'), 'reports', ['id'], unique=False)
    
    # Create IM8 domain areas table
    op.create_table('im8_domain_areas',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('framework_mappings', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    op.create_index(op.f('ix_im8_domain_areas_id'), 'im8_domain_areas', ['id'], unique=False)
    
    # Create agents table
    op.create_table('agents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('knowledge_area_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=True),
        sa.Column('endpoint', sa.String(length=500), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=True, default=True),
        sa.ForeignKeyConstraint(['knowledge_area_id'], ['im8_domain_areas.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agents_id'), 'agents', ['id'], unique=False)
    
    # Create tools table
    op.create_table('tools',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('tool_type', sa.String(length=100), nullable=True),
        sa.Column('endpoint', sa.String(length=500), nullable=True),
        sa.Column('config', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tools_id'), 'tools', ['id'], unique=False)
    
    # Create control catalog table
    op.create_table('control_catalog',
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
    
    # Create agent tasks table
    op.create_table('agent_tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_type', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=True, default='pending'),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=True),
        sa.Column('result', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('progress', sa.Integer(), nullable=True, default=0),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agent_tasks_id'), 'agent_tasks', ['id'], unique=False)
    op.create_index(op.f('ix_agent_tasks_task_type'), 'agent_tasks', ['task_type'], unique=False)
    op.create_index(op.f('ix_agent_tasks_status'), 'agent_tasks', ['status'], unique=False)
    op.create_index(op.f('ix_agent_tasks_created_by'), 'agent_tasks', ['created_by'], unique=False)
    
    # Create conversation sessions table
    op.create_table('conversation_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(length=255), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=True),
        sa.Column('messages', sa.JSON(), nullable=False),
        sa.Column('context', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('last_activity', sa.DateTime(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=True, default=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_id')
    )
    op.create_index(op.f('ix_conversation_sessions_id'), 'conversation_sessions', ['id'], unique=False)
    op.create_index(op.f('ix_conversation_sessions_session_id'), 'conversation_sessions', ['session_id'], unique=True)
    op.create_index(op.f('ix_conversation_sessions_user_id'), 'conversation_sessions', ['user_id'], unique=False)
    op.create_index(op.f('ix_conversation_sessions_last_activity'), 'conversation_sessions', ['last_activity'], unique=False)
    op.create_index(op.f('ix_conversation_sessions_active'), 'conversation_sessions', ['active'], unique=False)
    
    # Create assessment_controls junction table
    op.create_table('assessment_controls',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('assessment_id', sa.Integer(), nullable=False),
        sa.Column('control_id', sa.Integer(), nullable=False),
        sa.Column('selected_for_testing', sa.Boolean(), nullable=False, default=True),
        sa.Column('testing_status', sa.String(length=50), nullable=False, default='pending'),
        sa.Column('testing_priority', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['assessment_id'], ['assessments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['control_id'], ['controls.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_assessment_controls_id'), 'assessment_controls', ['id'], unique=False)
    op.create_index(op.f('ix_assessment_controls_assessment_id'), 'assessment_controls', ['assessment_id'], unique=False)
    op.create_index(op.f('ix_assessment_controls_control_id'), 'assessment_controls', ['control_id'], unique=False)
    op.create_index(op.f('ix_assessment_controls_testing_status'), 'assessment_controls', ['testing_status'], unique=False)
    
    # Create finding_comments table
    op.create_table('finding_comments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('finding_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('comment_text', sa.Text(), nullable=False),
        sa.Column('comment_type', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['finding_id'], ['findings.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_finding_comments_id'), 'finding_comments', ['id'], unique=False)
    op.create_index(op.f('ix_finding_comments_finding_id'), 'finding_comments', ['finding_id'], unique=False)
    op.create_index(op.f('ix_finding_comments_user_id'), 'finding_comments', ['user_id'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('finding_comments')
    op.drop_table('assessment_controls')
    op.drop_table('conversation_sessions')
    op.drop_table('agent_tasks')
    op.drop_table('control_catalog')
    op.drop_table('tools')
    op.drop_table('agents')
    op.drop_table('im8_domain_areas')
    op.drop_table('reports')
    op.drop_table('findings')
    op.drop_table('evidence')
    op.drop_table('controls')
    op.drop_table('assessments')
    op.drop_table('projects')
    op.drop_table('users')
    op.drop_table('user_roles')
    op.drop_table('agencies')
