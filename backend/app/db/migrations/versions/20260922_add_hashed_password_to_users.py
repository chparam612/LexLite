"""add_hashed_password_to_users

Revision ID: a1b2c3d4e5f6
Revises: 08950f91bfe0
Create Date: 2026-09-22 01:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '08950f91bfe0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('hashed_password', sa.String(length=255), nullable=True))
        batch_op.alter_column('firebase_uid',
                              existing_type=sa.String(length=128),
                              nullable=True)


def downgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('firebase_uid',
                              existing_type=sa.String(length=128),
                              nullable=False)
        batch_op.drop_column('hashed_password')
