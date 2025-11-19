"""Upgrade assessments table with comprehensive structure

Revision ID: 003
Revises: 002
Create Date: 2025-11-19 18:00:00.000000

This migration:
1. Renames existing assessments table to assessments_old (backup)
2. Creates new comprehensive assessments table
3. Migrates data from old to new structure
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    # Step 1: Rename old table to backup
    op.rename_table('assessments', 'assessments_old')
    
    # Step 2: Create new comprehensive assessments table
    op.create_table(
        'assessments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('agency_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('assessment_type', sa.String(length=100), nullable=False),
        sa.Column('framework', sa.String(length=100), nullable=False),
        
        # Scope
        sa.Column('scope_description', sa.Text(), nullable=True),
        sa.Column('included_controls', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('excluded_areas', sa.Text(), nullable=True),
        
        # Schedule
        sa.Column('planned_start_date', sa.Date(), nullable=True),
        sa.Column('planned_end_date', sa.Date(), nullable=True),
        sa.Column('actual_start_date', sa.Date(), nullable=True),
        sa.Column('actual_end_date', sa.Date(), nullable=True),
        
        # Team
        sa.Column('lead_assessor_user_id', sa.Integer(), nullable=False),
        sa.Column('team_members', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        
        # Status
        sa.Column('status', sa.String(length=50), nullable=False, server_default='not_started'),
        sa.Column('completion_percentage', sa.Float(), nullable=True, server_default='0'),
        
        # Results
        sa.Column('overall_compliance_score', sa.Float(), nullable=True),
        sa.Column('findings_count_critical', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('findings_count_high', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('findings_count_medium', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('findings_count_low', sa.Integer(), nullable=True, server_default='0'),
        
        # Deliverables
        sa.Column('final_report_file_path', sa.String(length=500), nullable=True),
        sa.Column('executive_summary', sa.Text(), nullable=True),
        
        # Approval
        sa.Column('approved_by_user_id', sa.Integer(), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        
        # Audit fields
        sa.Column('created_by_user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        
        # Primary key
        sa.PrimaryKeyConstraint('id'),
        
        # Foreign keys
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['agency_id'], ['agencies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['lead_assessor_user_id'], ['users.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['approved_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ondelete='RESTRICT'),
    )
    
    # Create indexes for performance
    op.create_index('ix_assessments_project_id', 'assessments', ['project_id'])
    op.create_index('ix_assessments_agency_id', 'assessments', ['agency_id'])
    op.create_index('ix_assessments_status', 'assessments', ['status'])
    op.create_index('ix_assessments_assessment_type', 'assessments', ['assessment_type'])
    op.create_index('ix_assessments_planned_end_date', 'assessments', ['planned_end_date'])
    
    # Step 3: Migrate data from old to new table
    connection = op.get_bind()
    connection.execute(sa.text("""
        INSERT INTO assessments (
            id, project_id, agency_id, name, assessment_type, framework,
            scope_description, planned_start_date, planned_end_date,
            lead_assessor_user_id, status, completion_percentage,
            overall_compliance_score, findings_count_critical, findings_count_high,
            findings_count_medium, findings_count_low,
            created_by_user_id, created_at, updated_at
        )
        SELECT 
            id,
            project_id,
            agency_id,
            title as name,
            assessment_type,
            COALESCE(framework, 'IM8') as framework,
            scope as scope_description,
            assessment_period_start as planned_start_date,
            assessment_period_end as planned_end_date,
            COALESCE(assigned_to, 1) as lead_assessor_user_id,  -- Default to user 1 if null
            status,
            progress_percentage as completion_percentage,
            NULL as overall_compliance_score,
            0 as findings_count_critical,
            0 as findings_count_high,
            0 as findings_count_medium,
            0 as findings_count_low,
            COALESCE(assigned_to, 1) as created_by_user_id,
            COALESCE(created_at, NOW()) as created_at,
            COALESCE(created_at, NOW()) as updated_at
        FROM assessments_old
    """))


def downgrade():
    # Drop new table and restore old one
    op.drop_index('ix_assessments_planned_end_date', table_name='assessments')
    op.drop_index('ix_assessments_assessment_type', table_name='assessments')
    op.drop_index('ix_assessments_status', table_name='assessments')
    op.drop_index('ix_assessments_agency_id', table_name='assessments')
    op.drop_index('ix_assessments_project_id', table_name='assessments')
    op.drop_table('assessments')
    
    # Restore old table
    op.rename_table('assessments_old', 'assessments')
