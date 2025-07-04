"""Add additional_data column

Revision ID: e8bc2ccefca7
Revises: e55052041658
Create Date: 2025-07-04 18:05:58.005003

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e8bc2ccefca7'
down_revision: Union[str, Sequence[str], None] = 'e55052041658'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add additional_data column as JSON type
    op.add_column('jobs', sa.Column('additional_data', sa.JSON(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove additional_data column
    op.drop_column('jobs', 'additional_data')
