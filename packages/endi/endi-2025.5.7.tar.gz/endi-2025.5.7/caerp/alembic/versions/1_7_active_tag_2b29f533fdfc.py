"""1.7 : Add active tags to expense types and tva

Revision ID: 2b29f533fdfc
Revises: 4ce6b915de98
Create Date: 2013-09-03 16:05:22.824684

"""

# revision identifiers, used by Alembic.
revision = "2b29f533fdfc"
down_revision = "4ce6b915de98"

from alembic import op
import sqlalchemy as sa


def upgrade():
    try:
        col = sa.Column(
            "active",
            sa.Boolean(),
            default=True,
            server_default=sa.sql.expression.true(),
        )
        op.add_column("expense_type", col)
    except:
        print("The column already exists")
    col = sa.Column(
        "active", sa.Boolean(), default=True, server_default=sa.sql.expression.true()
    )
    op.add_column("tva", col)


def downgrade():
    op.drop_column("expense_type", "active")
    op.drop_column("tva", "active")
