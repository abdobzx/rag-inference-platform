"""Add performance indexes

Revision ID: 523b0c494123
Revises: eea056c9e987
Create Date: 2025-10-14 21:34:05.884724

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '523b0c494123'
down_revision: Union[str, None] = 'eea056c9e987'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ix_users_email / ix_users_username / hashed_key's unique constraint already
    # exist from migration 934bfc2a0292 (create_users_and_api_keys_tables) - this
    # migration originally recreated them (fails: "index already exists") and also
    # referenced a nonexistent 'key' column on api_keys (only key_prefix/hashed_key
    # exist). Only ix_api_keys_user_id was genuinely new; that's all that's kept here.
    op.create_index('ix_api_keys_user_id', 'api_keys', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_api_keys_user_id', table_name='api_keys')
