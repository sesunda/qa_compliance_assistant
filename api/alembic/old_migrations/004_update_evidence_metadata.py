"""Enhance evidence metadata for file storage

Revision ID: 004
Revises: 003
Create Date: 2025-11-01 07:20:00

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "004"
down_revision: Union[str, None] = "5f706ede940a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("evidence", sa.Column("original_filename", sa.String(length=255), nullable=True))
    op.add_column("evidence", sa.Column("mime_type", sa.String(length=100), nullable=True))
    op.add_column("evidence", sa.Column("file_size", sa.Integer(), nullable=True))
    op.add_column("evidence", sa.Column("checksum", sa.String(length=64), nullable=True))
    op.add_column(
        "evidence",
        sa.Column("storage_backend", sa.String(length=50), nullable=False, server_default="local")
    )
    op.add_column("evidence", sa.Column("uploaded_by", sa.Integer(), nullable=True))
    op.add_column("evidence", sa.Column("uploaded_at", sa.DateTime(), nullable=True))
    op.create_foreign_key(
        "fk_evidence_uploaded_by_users",
        "evidence",
        "users",
        ["uploaded_by"],
        ["id"],
        ondelete="SET NULL"
    )


def downgrade() -> None:
    op.drop_constraint("fk_evidence_uploaded_by_users", "evidence", type_="foreignkey")
    op.drop_column("evidence", "uploaded_at")
    op.drop_column("evidence", "uploaded_by")
    op.drop_column("evidence", "storage_backend")
    op.drop_column("evidence", "checksum")
    op.drop_column("evidence", "file_size")
    op.drop_column("evidence", "mime_type")
    op.drop_column("evidence", "original_filename")
