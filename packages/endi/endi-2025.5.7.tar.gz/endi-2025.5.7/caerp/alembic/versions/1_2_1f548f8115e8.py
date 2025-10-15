"""1.2 : Update primary_groups to fit enDI

Revision ID: 1f548f8115e8
Revises: 3ffdda6a6fe6
Create Date: 2012-08-28 23:29:01.873171

"""

# revision identifiers, used by Alembic.
revision = "1f548f8115e8"
down_revision = "3ffdda6a6fe6"

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.execute(
        """
alter table coop_tva add column `default` int(11) default 0;
"""
    )
    op.execute(
        """
update egw_accounts set account_primary_group=3 where account_primary_group!= -10 and account_primary_group != -14;
"""
    )
    op.execute(
        """
update egw_accounts set account_primary_group=1 where account_primary_group=-10;
"""
    )
    op.execute(
        """
update egw_accounts set account_primary_group=2 where account_primary_group=-14;
"""
    )


def downgrade():
    pass
