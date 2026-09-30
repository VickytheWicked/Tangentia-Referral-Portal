"""Add password to users and referrer contact fields to referrals

Revision ID: 788e2d79ce13
Revises: 788e2d79ce12
Create Date: 2026-09-27 22:55:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '788e2d79ce13'
down_revision: Union[str, Sequence[str], None] = '788e2d79ce12'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users table updates
    op.add_column('users', sa.Column('password', sa.String(length=255), nullable=True))
    op.alter_column('users', 'entra_user_id', existing_type=sa.String(length=100), nullable=True)

    # Referrals table updates
    op.add_column('referrals', sa.Column('referred_by_name', sa.String(length=255), nullable=True))
    op.add_column('referrals', sa.Column('referred_by_email', sa.String(length=255), nullable=True))
    op.add_column('referrals', sa.Column('referred_by_phone', sa.String(length=50), nullable=True))


def downgrade() -> None:
    op.drop_column('referrals', 'referred_by_phone')
    op.drop_column('referrals', 'referred_by_email')
    op.drop_column('referrals', 'referred_by_name')
    op.alter_column('users', 'entra_user_id', existing_type=sa.String(length=100), nullable=False)
    op.drop_column('users', 'password')
