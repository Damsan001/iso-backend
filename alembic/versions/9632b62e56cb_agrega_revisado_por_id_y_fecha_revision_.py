"""Agrega revisado_por_id y fecha_revision a DocumentoVersion

Revision ID: 9632b62e56cb
Revises: 09773d91d02d
Create Date: 2025-10-06 11:46:25.229183

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

import os
SCHEMA = os.getenv("DB_SCHEMA", "iso")

# revision identifiers, used by Alembic.
revision: str = '9632b62e56cb'
down_revision: Union[str, Sequence[str], None] = '09773d91d02d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.add_column('documento_version',
        sa.Column('revisado_por_id', sa.BigInteger(), nullable=True),
        schema=SCHEMA
    )
    op.add_column('documento_version',
        sa.Column('fecha_revision', sa.DateTime(timezone=True), nullable=True),
        schema=SCHEMA
    )
    op.create_foreign_key(
        'fk_documento_version_revisado_por_id_usuario',
        'documento_version', 'usuario',
        ['revisado_por_id'], ['usuario_id'],
        source_schema=SCHEMA, referent_schema=SCHEMA
    )

def downgrade():
    op.drop_constraint(
        'fk_documento_version_revisado_por_id_usuario',
        'documento_version',
        type_='foreignkey',
        schema=SCHEMA
    )
    op.drop_column('documento_version', 'fecha_revision', schema=SCHEMA)
    op.drop_column('documento_version', 'revisado_por_id', schema=SCHEMA)