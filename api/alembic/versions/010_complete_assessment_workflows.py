"""Complete assessment workflows - findings, controls, assessments enhancements

Revision ID: 010_complete_assessment_workflows
Revises: 009_update_agent_tasks
Create Date: 2025-11-07 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '010_complete_assessment_workflows'
down_revision = '009_update_agent_tasks'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ============================================================================
    # FINDINGS TABLE ENHANCEMENTS
    # ============================================================================
    print("Enhancing findings table...")
    
    # Add resolution tracking columns
    op.add_column('findings', sa.Column('resolution_status', sa.String(50), server_default='open', nullable=False))
    op.add_column('findings', sa.Column('resolved_at', sa.DateTime(), nullable=True))
    op.add_column('findings', sa.Column('resolved_by', sa.Integer(), nullable=True))
    op.add_column('findings', sa.Column('resolution_evidence_id', sa.Integer(), nullable=True))
    
    # Add validation columns
    op.add_column('findings', sa.Column('false_positive', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('findings', sa.Column('validated_by', sa.Integer(), nullable=True))
    op.add_column('findings', sa.Column('validated_at', sa.DateTime(), nullable=True))
    
    # Add assignment and tracking columns
    op.add_column('findings', sa.Column('assigned_to', sa.Integer(), nullable=True))
    op.add_column('findings', sa.Column('due_date', sa.DateTime(), nullable=True))
    op.add_column('findings', sa.Column('priority', sa.String(20), nullable=True))
    op.add_column('findings', sa.Column('remediation_notes', sa.Text(), nullable=True))
    op.add_column('findings', sa.Column('updated_at', sa.DateTime(), nullable=True))
    
    # Create foreign keys for findings
    op.create_foreign_key('fk_findings_resolved_by', 'findings', 'users', ['resolved_by'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_findings_validated_by', 'findings', 'users', ['validated_by'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_findings_assigned_to', 'findings', 'users', ['assigned_to'], ['id'], ondelete='SET NULL')
    op.create_foreign_key('fk_findings_resolution_evidence', 'findings', 'evidence', ['resolution_evidence_id'], ['id'], ondelete='SET NULL')
    
    # Create indexes for findings
    op.create_index('ix_findings_resolution_status', 'findings', ['resolution_status'])
    op.create_index('ix_findings_assigned_to', 'findings', ['assigned_to'])
    op.create_index('ix_findings_due_date', 'findings', ['due_date'])
    op.create_index('ix_findings_priority', 'findings', ['priority'])
    
    # ============================================================================
    # CONTROLS TABLE ENHANCEMENTS
    # ============================================================================
    print("Enhancing controls table...")
    
    # Add review tracking columns
    op.add_column('controls', sa.Column('reviewed_by', sa.Integer(), nullable=True))
    op.add_column('controls', sa.Column('reviewed_at', sa.DateTime(), nullable=True))
    op.add_column('controls', sa.Column('review_status', sa.String(50), server_default='pending', nullable=False))
    op.add_column('controls', sa.Column('assessment_score', sa.Integer(), nullable=True))
    
    # Add testing columns
    op.add_column('controls', sa.Column('test_procedure', sa.Text(), nullable=True))
    op.add_column('controls', sa.Column('test_results', sa.Text(), nullable=True))
    op.add_column('controls', sa.Column('testing_frequency', sa.String(50), nullable=True))
    op.add_column('controls', sa.Column('last_tested_at', sa.DateTime(), nullable=True))
    op.add_column('controls', sa.Column('next_test_due', sa.DateTime(), nullable=True))
    
    # Create foreign keys for controls
    op.create_foreign_key('fk_controls_reviewed_by', 'controls', 'users', ['reviewed_by'], ['id'], ondelete='SET NULL')
    
    # Create indexes for controls
    op.create_index('ix_controls_review_status', 'controls', ['review_status'])
    op.create_index('ix_controls_next_test_due', 'controls', ['next_test_due'])
    
    # ============================================================================
    # ASSESSMENTS TABLE ENHANCEMENTS
    # ============================================================================
    print("Enhancing assessments table...")
    
    # Add assignment and tracking columns
    op.add_column('assessments', sa.Column('assigned_to', sa.Integer(), nullable=True))
    op.add_column('assessments', sa.Column('completed_at', sa.DateTime(), nullable=True))
    op.add_column('assessments', sa.Column('progress_percentage', sa.Integer(), server_default='0', nullable=False))
    op.add_column('assessments', sa.Column('target_completion_date', sa.DateTime(), nullable=True))
    
    # Add framework and period columns
    op.add_column('assessments', sa.Column('framework', sa.String(100), nullable=True))
    op.add_column('assessments', sa.Column('assessment_period_start', sa.Date(), nullable=True))
    op.add_column('assessments', sa.Column('assessment_period_end', sa.Date(), nullable=True))
    
    # Add metrics columns
    op.add_column('assessments', sa.Column('findings_count', sa.Integer(), server_default='0', nullable=False))
    op.add_column('assessments', sa.Column('controls_tested_count', sa.Integer(), server_default='0', nullable=False))
    
    # Create foreign keys for assessments
    op.create_foreign_key('fk_assessments_assigned_to', 'assessments', 'users', ['assigned_to'], ['id'], ondelete='SET NULL')
    
    # Create indexes for assessments
    op.create_index('ix_assessments_assigned_to', 'assessments', ['assigned_to'])
    op.create_index('ix_assessments_status', 'assessments', ['status'])
    op.create_index('ix_assessments_framework', 'assessments', ['framework'])
    
    # ============================================================================
    # NEW TABLE: ASSESSMENT_CONTROLS (Junction Table)
    # ============================================================================
    print("Creating assessment_controls junction table...")
    
    op.create_table(
        'assessment_controls',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('assessment_id', sa.Integer(), nullable=False),
        sa.Column('control_id', sa.Integer(), nullable=False),
        sa.Column('selected_for_testing', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('testing_status', sa.String(50), server_default='pending', nullable=False),
        sa.Column('testing_priority', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['assessment_id'], ['assessments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['control_id'], ['controls.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('ix_assessment_controls_assessment_id', 'assessment_controls', ['assessment_id'])
    op.create_index('ix_assessment_controls_control_id', 'assessment_controls', ['control_id'])
    op.create_index('ix_assessment_controls_testing_status', 'assessment_controls', ['testing_status'])
    
    # ============================================================================
    # NEW TABLE: FINDING_COMMENTS
    # ============================================================================
    print("Creating finding_comments table...")
    
    op.create_table(
        'finding_comments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('finding_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('comment_text', sa.Text(), nullable=False),
        sa.Column('comment_type', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['finding_id'], ['findings.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    op.create_index('ix_finding_comments_finding_id', 'finding_comments', ['finding_id'])
    op.create_index('ix_finding_comments_user_id', 'finding_comments', ['user_id'])
    
    print("Migration 010 completed successfully!")


def downgrade() -> None:
    # Drop new tables
    print("Dropping finding_comments table...")
    op.drop_index('ix_finding_comments_user_id', table_name='finding_comments')
    op.drop_index('ix_finding_comments_finding_id', table_name='finding_comments')
    op.drop_table('finding_comments')
    
    print("Dropping assessment_controls table...")
    op.drop_index('ix_assessment_controls_testing_status', table_name='assessment_controls')
    op.drop_index('ix_assessment_controls_control_id', table_name='assessment_controls')
    op.drop_index('ix_assessment_controls_assessment_id', table_name='assessment_controls')
    op.drop_table('assessment_controls')
    
    # Drop assessments enhancements
    print("Removing assessments enhancements...")
    op.drop_index('ix_assessments_framework', table_name='assessments')
    op.drop_index('ix_assessments_status', table_name='assessments')
    op.drop_index('ix_assessments_assigned_to', table_name='assessments')
    op.drop_constraint('fk_assessments_assigned_to', 'assessments', type_='foreignkey')
    op.drop_column('assessments', 'controls_tested_count')
    op.drop_column('assessments', 'findings_count')
    op.drop_column('assessments', 'assessment_period_end')
    op.drop_column('assessments', 'assessment_period_start')
    op.drop_column('assessments', 'framework')
    op.drop_column('assessments', 'target_completion_date')
    op.drop_column('assessments', 'progress_percentage')
    op.drop_column('assessments', 'completed_at')
    op.drop_column('assessments', 'assigned_to')
    
    # Drop controls enhancements
    print("Removing controls enhancements...")
    op.drop_index('ix_controls_next_test_due', table_name='controls')
    op.drop_index('ix_controls_review_status', table_name='controls')
    op.drop_constraint('fk_controls_reviewed_by', 'controls', type_='foreignkey')
    op.drop_column('controls', 'next_test_due')
    op.drop_column('controls', 'last_tested_at')
    op.drop_column('controls', 'testing_frequency')
    op.drop_column('controls', 'test_results')
    op.drop_column('controls', 'test_procedure')
    op.drop_column('controls', 'assessment_score')
    op.drop_column('controls', 'review_status')
    op.drop_column('controls', 'reviewed_at')
    op.drop_column('controls', 'reviewed_by')
    
    # Drop findings enhancements
    print("Removing findings enhancements...")
    op.drop_index('ix_findings_priority', table_name='findings')
    op.drop_index('ix_findings_due_date', table_name='findings')
    op.drop_index('ix_findings_assigned_to', table_name='findings')
    op.drop_index('ix_findings_resolution_status', table_name='findings')
    op.drop_constraint('fk_findings_resolution_evidence', 'findings', type_='foreignkey')
    op.drop_constraint('fk_findings_assigned_to', 'findings', type_='foreignkey')
    op.drop_constraint('fk_findings_validated_by', 'findings', type_='foreignkey')
    op.drop_constraint('fk_findings_resolved_by', 'findings', type_='foreignkey')
    op.drop_column('findings', 'updated_at')
    op.drop_column('findings', 'remediation_notes')
    op.drop_column('findings', 'priority')
    op.drop_column('findings', 'due_date')
    op.drop_column('findings', 'assigned_to')
    op.drop_column('findings', 'validated_at')
    op.drop_column('findings', 'validated_by')
    op.drop_column('findings', 'false_positive')
    op.drop_column('findings', 'resolution_evidence_id')
    op.drop_column('findings', 'resolved_by')
    op.drop_column('findings', 'resolved_at')
    op.drop_column('findings', 'resolution_status')
    
    print("Migration 010 downgrade completed!")
