"""Add production constraints and optimizations

Revision ID: b00265253864
Revises: eea056c9e987
Create Date: 2025-10-14 21:35:07.785884

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b00265253864'
# Was 'eea056c9e987' - identical to 523b0c494123's parent, which created two
# diverged heads and makes `alembic upgrade head` fail with "Multiple head
# revisions". Rebased onto 523b0c494123 to restore a single linear chain.
down_revision: Union[str, None] = '523b0c494123'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Use batch mode for SQLite compatibility
    with op.batch_alter_table('users') as batch_op:
        # Add check constraints for data validation
        batch_op.create_check_constraint(
            'ck_users_email_format',
            "email LIKE '%@%'"
        )
        batch_op.create_check_constraint(
            'ck_users_username_length',
            'length(username) >= 3'
        )
        # Add index for better query performance
        batch_op.create_index('ix_users_is_active', ['is_active'])

    with op.batch_alter_table('api_keys') as batch_op:
        batch_op.create_check_constraint(
            'ck_api_keys_prefix_length',
            'length(key_prefix) = 8'
        )
        # Add indexes for better query performance
        batch_op.create_index('ix_api_keys_created_at', ['created_at'])
        batch_op.create_index('ix_api_keys_last_used_at', ['last_used_at'])


def downgrade() -> None:
    # Use batch mode for SQLite compatibility
    with op.batch_alter_table('api_keys') as batch_op:
        # Remove indexes
        batch_op.drop_index('ix_api_keys_last_used_at')
        batch_op.drop_index('ix_api_keys_created_at')
        # Remove check constraints
        batch_op.drop_constraint('ck_api_keys_prefix_length', type_='check')

    with op.batch_alter_table('users') as batch_op:
        # Remove index
        batch_op.drop_index('ix_users_is_active')
        # Remove check constraints
        batch_op.drop_constraint('ck_users_username_length', type_='check')
        batch_op.drop_constraint('ck_users_email_format', type_='check')
