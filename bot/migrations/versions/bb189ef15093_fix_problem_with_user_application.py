"""Fix problem with user application

Revision ID: bb189ef15093
Revises: 96e5835c5bba
Create Date: 2025-03-10 14:56:24.512576

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "bb189ef15093"
down_revision: Union[str, None] = "96e5835c5bba"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("applications", sa.Column("contact_name", sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("applications", "contact_name")
    # ### end Alembic commands ###
