# python
"""Create auditlog

Revision ID: 09773d91d02d
Revises: f42722ced9a2
Create Date: 2025-09-09 13:00:41.312417

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '09773d91d02d'
down_revision: Union[str, Sequence[str], None] = 'f42722ced9a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Solo tabla audit_log
    op.create_table(
        'audit_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('table_name', sa.String(length=128), nullable=False),
        sa.Column('operation', sa.String(length=16), nullable=False),
        sa.Column('target_pk_id', sa.Integer(), nullable=True),
        sa.Column('target_pk', sa.JSON(), nullable=False),
        sa.Column('actor', sa.String(length=128), nullable=True),
        sa.Column('before', sa.JSON(), nullable=True),
        sa.Column('after', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        schema='iso'
    )
    op.create_index(op.f('ix_iso_audit_log_id'), 'audit_log', ['id'], unique=False, schema='iso')
    op.create_index(op.f('ix_iso_audit_log_target_pk_id'), 'audit_log', ['target_pk_id'], unique=False, schema='iso')


def downgrade() -> None:
    """Downgrade schema."""
    # Solo revertir audit_log
    op.drop_index(op.f('ix_iso_audit_log_target_pk_id'), table_name='audit_log', schema='iso')
    op.drop_index(op.f('ix_iso_audit_log_id'), table_name='audit_log', schema='iso')
    op.drop_table('audit_log', schema='iso')