"""Merge authentication and evidence metadata branches

Revision ID: 898cc8361b19
Revises: 5f706ede940a, 004
Create Date: 2025-11-01 09:17:24.756709

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '898cc8361b19'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
