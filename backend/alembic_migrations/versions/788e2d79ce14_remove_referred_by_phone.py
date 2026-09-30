"""Remove referred_by_phone from referrals

Revision ID: 788e2d79ce14
Revises: 788e2d79ce13
Create Date: 2026-09-29 14:55:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '788e2d79ce14'
down_revision: Union[str, Sequence[str], None] = '788e2d79ce13'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('referrals')]
    if 'referred_by_phone' in columns:
        with op.batch_alter_table('referrals', schema=None) as batch_op:
            batch_op.drop_column('referred_by_phone')


def downgrade() -> None:
    with op.batch_alter_table('referrals', schema=None) as batch_op:
        batch_op.add_column(sa.Column('referred_by_phone', sa.String(length=50), nullable=True))
