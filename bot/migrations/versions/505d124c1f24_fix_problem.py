"""fix problem

Revision ID: 505d124c1f24
Revises: eb613c5d975f
Create Date: 2025-03-12 19:33:02.318449

"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "505d124c1f24"
down_revision: Union[str, None] = "eb613c5d975f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###
