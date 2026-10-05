"""Migrate sharepoint columns to storage columns on referrals table

Revision ID: 788e2d79ce15
Revises: 788e2d79ce14
Create Date: 2026-10-01 10:15:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '788e2d79ce15'
down_revision: Union[str, Sequence[str], None] = '788e2d79ce14'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('referrals')]

    cols_to_map = [
        ('sharepoint_drive_id', 'storage_drive_id', sa.String(255)),
        ('sharepoint_item_id', 'storage_item_id', sa.String(255)),
        ('sharepoint_file_id', 'storage_file_id', sa.String(255)),
        ('sharepoint_file_url', 'storage_file_url', sa.String(1000)),
    ]

    for old_col, new_col, col_type in cols_to_map:
        if new_col not in columns:
            if old_col in columns:
                with op.batch_alter_table('referrals', schema=None) as batch_op:
                    batch_op.alter_column(old_col, new_column_name=new_col)
            else:
                with op.batch_alter_table('referrals', schema=None) as batch_op:
                    batch_op.add_column(sa.Column(new_col, col_type, nullable=True))


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('referrals')]

    cols_to_map = [
        ('storage_drive_id', 'sharepoint_drive_id'),
        ('storage_item_id', 'sharepoint_item_id'),
        ('storage_file_id', 'sharepoint_file_id'),
        ('storage_file_url', 'sharepoint_file_url'),
    ]

    for new_col, old_col in cols_to_map:
        if new_col in columns and old_col not in columns:
            with op.batch_alter_table('referrals', schema=None) as batch_op:
                batch_op.alter_column(new_col, new_column_name=old_col)
