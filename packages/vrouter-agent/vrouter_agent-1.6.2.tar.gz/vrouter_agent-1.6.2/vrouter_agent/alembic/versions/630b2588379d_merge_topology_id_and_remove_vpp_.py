"""merge topology_id and remove_vpp_mappings branches

Revision ID: 630b2588379d
Revises: 1180d19201bd, remove_vpp_mappings_field
Create Date: 2025-06-09 18:00:53.388709

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '630b2588379d'
down_revision: Union[str, None] = ('1180d19201bd', 'remove_vpp_mappings_field')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
