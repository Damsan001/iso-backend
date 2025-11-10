"""Create urls from user

Revision ID: 7ab730966e00
Revises: 9632b62e56cb
Create Date: 2025-11-06 12:19:16.671134

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import os
SCHEMA = os.getenv("DB_SCHEMA", "iso")

# revision identifiers, used by Alembic.
revision: str = '7ab730966e00'
down_revision: Union[str, Sequence[str], None] = '9632b62e56cb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "usuario",
        sa.Column("url_foto", sa.Text(), nullable=True),
        schema=SCHEMA,
    )
    op.add_column(
        "usuario",
        sa.Column("url_firma", sa.Text(), nullable=True),
        schema=SCHEMA,
    )


def downgrade() -> None:
    op.drop_column("usuario", "url_firma", schema=SCHEMA)
    op.drop_column("usuario", "url_foto", schema=SCHEMA)
