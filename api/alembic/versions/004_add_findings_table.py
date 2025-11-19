"""Upgrade findings table with comprehensive structure

Revision ID: 004
Revises: 003
Create Date: 2025-11-19 18:01:00.000000

This migration:
1. Renames existing findings table to findings_old (backup)
2. Creates new comprehensive findings table
3. Migrates data from old to new structure
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    # Step 1: Rename old table to backup
    op.rename_table('findings', 'findings_old')
    
    # Step 2: Create new comprehensive findings table
    op.create_table(
        'findings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('assessment_id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('agency_id', sa.Integer(), nullable=False),
        sa.Column('control_id', sa.Integer(), nullable=True),
        
        # Core Info
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('severity', sa.String(length=50), nullable=False),
        sa.Column('cvss_score', sa.Float(), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        
        # Asset Info
        sa.Column('affected_asset', sa.String(length=255), nullable=True),
        sa.Column('affected_url', sa.String(length=500), nullable=True),
        sa.Column('affected_component', sa.String(length=255), nullable=True),
        
        # Status Tracking
        sa.Column('status', sa.String(length=50), nullable=False, server_default='open'),
        sa.Column('discovery_date', sa.Date(), nullable=False),
        
        # Remediation
        sa.Column('remediation_recommendation', sa.Text(), nullable=True),
        sa.Column('remediation_priority', sa.String(length=50), nullable=True),
        sa.Column('target_remediation_date', sa.Date(), nullable=True),
        sa.Column('assigned_to_user_id', sa.Integer(), nullable=True),
        sa.Column('actual_remediation_date', sa.Date(), nullable=True),
        
        # Evidence/Proof
        sa.Column('evidence_file_paths', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('reproduction_steps', sa.Text(), nullable=True),
        
        # Verification
        sa.Column('verified_by_user_id', sa.Integer(), nullable=True),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.Column('verification_notes', sa.Text(), nullable=True),
        
        # Audit fields
        sa.Column('created_by_user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        
        # Primary key
        sa.PrimaryKeyConstraint('id'),
        
        # Foreign keys
        sa.ForeignKeyConstraint(['assessment_id'], ['assessments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['agency_id'], ['agencies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['control_id'], ['controls.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['assigned_to_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['verified_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ondelete='RESTRICT'),
    )
    
    # Create indexes for performance
    op.create_index('ix_findings_assessment_id', 'findings', ['assessment_id'])
    op.create_index('ix_findings_project_id', 'findings', ['project_id'])
    op.create_index('ix_findings_agency_id', 'findings', ['agency_id'])
    op.create_index('ix_findings_control_id', 'findings', ['control_id'])
    op.create_index('ix_findings_severity', 'findings', ['severity'])
    op.create_index('ix_findings_status', 'findings', ['status'])
    op.create_index('ix_findings_assigned_to_user_id', 'findings', ['assigned_to_user_id'])
    op.create_index('ix_findings_target_remediation_date', 'findings', ['target_remediation_date'])
    
    # Step 3: Migrate data from old to new table
    connection = op.get_bind()
    connection.execute(sa.text("""
        INSERT INTO findings (
            id, assessment_id, project_id, agency_id, control_id,
            title, description, severity, cvss_score, category,
            affected_asset, status, discovery_date,
            remediation_recommendation, assigned_to_user_id,
            actual_remediation_date, verified_by_user_id, verified_at,
            created_by_user_id, created_at, updated_at
        )
        SELECT 
            f.id,
            f.assessment_id,
            COALESCE(a.project_id, 1) as project_id,  -- Get from assessment
            COALESCE(a.agency_id, 1) as agency_id,     -- Get from assessment
            f.control_id,
            f.title,
            f.description,
            f.severity,
            CASE 
                WHEN f.cvss ~ '^[0-9.]+$' THEN CAST(f.cvss AS FLOAT)
                ELSE NULL 
            END as cvss_score,
            NULL as category,
            NULL as affected_asset,
            f.resolution_status as status,
            COALESCE(f.created_at::DATE, CURRENT_DATE) as discovery_date,
            f.remediation as remediation_recommendation,
            f.assigned_to as assigned_to_user_id,
            f.resolved_at::DATE as actual_remediation_date,
            f.validated_by as verified_by_user_id,
            f.validated_at,
            COALESCE(f.resolved_by, 1) as created_by_user_id,
            COALESCE(f.created_at, NOW()) as created_at,
            COALESCE(f.updated_at, NOW()) as updated_at
        FROM findings_old f
        LEFT JOIN assessments a ON f.assessment_id = a.id
    """))


def downgrade():
    op.drop_index('ix_findings_target_remediation_date', table_name='findings')
    op.drop_index('ix_findings_assigned_to_user_id', table_name='findings')
    op.drop_index('ix_findings_status', table_name='findings')
    op.drop_index('ix_findings_severity', table_name='findings')
    op.drop_index('ix_findings_control_id', table_name='findings')
    op.drop_index('ix_findings_agency_id', table_name='findings')
    op.drop_index('ix_findings_project_id', table_name='findings')
    op.drop_index('ix_findings_assessment_id', table_name='findings')
    op.drop_table('findings')
    
    # Restore old table
    op.rename_table('findings_old', 'findings')
