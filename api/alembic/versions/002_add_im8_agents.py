"""Add IM8, agents, tools, assessments and findings

Revision ID: 002
Revises: 001
Create Date: 2025-10-31 02:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create agencies table
    op.create_table(
        'agencies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('code', sa.String(length=100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('contact_email', sa.String(length=255), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agencies_id'), 'agencies', ['id'], unique=False)

    # Insert a default agency so existing tables that get a non-nullable agency_id can reference it.
    # This avoids foreign key errors when adding agency_id columns with a server_default.
    op.execute("INSERT INTO agencies (id, name, active, created_at) VALUES (1, 'Default Agency', true, now())")

    # Add agency_id to projects, controls, evidence
    op.add_column('projects', sa.Column('agency_id', sa.Integer(), nullable=False, server_default='1'))
    op.create_foreign_key(None, 'projects', 'agencies', ['agency_id'], ['id'])

    op.add_column('controls', sa.Column('agency_id', sa.Integer(), nullable=False, server_default='1'))
    op.create_foreign_key(None, 'controls', 'agencies', ['agency_id'], ['id'])

    op.add_column('evidence', sa.Column('agency_id', sa.Integer(), nullable=False, server_default='1'))
    op.create_foreign_key(None, 'evidence', 'agencies', ['agency_id'], ['id'])

    # Create assessments table
    op.create_table(
        'assessments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agency_id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('assessment_type', sa.String(length=50), nullable=True),
        sa.Column('performed_by', sa.String(length=255), nullable=True),
        sa.Column('scope', sa.Text(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['agency_id'], ['agencies.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_assessments_id'), 'assessments', ['id'], unique=False)

    # Create findings table
    op.create_table(
        'findings',
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
        sa.ForeignKeyConstraint(['assessment_id'], ['assessments.id'], ),
        sa.ForeignKeyConstraint(['control_id'], ['controls.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_findings_id'), 'findings', ['id'], unique=False)

    # Create IM8 knowledge areas
    op.create_table(
        'im8_knowledge_areas',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=100), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('framework_mappings', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_im8_knowledge_areas_id'), 'im8_knowledge_areas', ['id'], unique=False)

    # Create agents, tools, agent_tasks
    op.create_table(
        'agents',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('knowledge_area_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=True),
        sa.Column('endpoint', sa.String(length=500), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(['knowledge_area_id'], ['im8_knowledge_areas.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agents_id'), 'agents', ['id'], unique=False)

    op.create_table(
        'tools',
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

    op.create_table(
        'agent_tasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('agent_id', sa.Integer(), nullable=False),
        sa.Column('agency_id', sa.Integer(), nullable=False),
        sa.Column('task_type', sa.String(length=100), nullable=True),
        sa.Column('payload', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('result', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('finished_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.id'], ),
        sa.ForeignKeyConstraint(['agency_id'], ['agencies.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_agent_tasks_id'), 'agent_tasks', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_agent_tasks_id'), table_name='agent_tasks')
    op.drop_table('agent_tasks')
    op.drop_index(op.f('ix_tools_id'), table_name='tools')
    op.drop_table('tools')
    op.drop_index(op.f('ix_agents_id'), table_name='agents')
    op.drop_table('agents')
    op.drop_index(op.f('ix_im8_knowledge_areas_id'), table_name='im8_knowledge_areas')
    op.drop_table('im8_knowledge_areas')
    op.drop_index(op.f('ix_findings_id'), table_name='findings')
    op.drop_table('findings')
    op.drop_index(op.f('ix_assessments_id'), table_name='assessments')
    op.drop_table('assessments')
    # remove agency_id columns
    op.drop_constraint(None, 'evidence', type_='foreignkey')
    op.drop_column('evidence', 'agency_id')
    op.drop_constraint(None, 'controls', type_='foreignkey')
    op.drop_column('controls', 'agency_id')
    op.drop_constraint(None, 'projects', type_='foreignkey')
    op.drop_column('projects', 'agency_id')
    op.drop_index(op.f('ix_agencies_id'), table_name='agencies')
    op.drop_table('agencies')
