"""Add user preferences column

Revision ID: eea056c9e987
Revises: 934bfc2a0292
Create Date: 2025-10-14 21:33:21.480978

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'eea056c9e987'
down_revision: Union[str, None] = '934bfc2a0292'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add user preferences column
    op.add_column('users', sa.Column('preferences', sa.JSON(), nullable=True))


def downgrade() -> None:
    # Remove user preferences column
    op.drop_column('users', 'preferences')
