"""DB fix problem delete

Revision ID: 4c5e9e20f551
Revises: 19f07324da4c
Create Date: 2025-03-11 20:38:34.600968

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4c5e9e20f551'
down_revision: Union[str, None] = '19f07324da4c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('applications_user_id_fkey', 'applications', type_='foreignkey')
    op.create_foreign_key(None, 'applications', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.drop_constraint('bankdebts_application_id_fkey', 'bankdebts', type_='foreignkey')
    op.create_foreign_key(None, 'bankdebts', 'applications', ['application_id'], ['id'], ondelete='CASCADE')
    op.drop_constraint('photos_application_id_fkey', 'photos', type_='foreignkey')
    op.create_foreign_key(None, 'photos', 'applications', ['application_id'], ['id'], ondelete='CASCADE')
    op.drop_constraint('videos_application_id_fkey', 'videos', type_='foreignkey')
    op.create_foreign_key(None, 'videos', 'applications', ['application_id'], ['id'], ondelete='CASCADE')
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'videos', type_='foreignkey')
    op.create_foreign_key('videos_application_id_fkey', 'videos', 'applications', ['application_id'], ['id'])
    op.drop_constraint(None, 'photos', type_='foreignkey')
    op.create_foreign_key('photos_application_id_fkey', 'photos', 'applications', ['application_id'], ['id'])
    op.drop_constraint(None, 'bankdebts', type_='foreignkey')
    op.create_foreign_key('bankdebts_application_id_fkey', 'bankdebts', 'applications', ['application_id'], ['id'])
    op.drop_constraint(None, 'applications', type_='foreignkey')
    op.create_foreign_key('applications_user_id_fkey', 'applications', 'users', ['user_id'], ['id'])
    # ### end Alembic commands ###
