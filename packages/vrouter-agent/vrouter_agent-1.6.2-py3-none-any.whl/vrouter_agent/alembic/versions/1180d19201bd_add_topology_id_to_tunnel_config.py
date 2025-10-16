"""add_topology_id_to_tunnel_config

Revision ID: 1180d19201bd
Revises: acb2cb4a8198
Create Date: 2025-06-08 05:48:59.287378

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1180d19201bd'
down_revision: Union[str, None] = 'acb2cb4a8198'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add topology_id column to tunnel_config_data table (only if it doesn't exist)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('tunnel_config_data')]
    
    if 'topology_id' not in columns:
        op.add_column('tunnel_config_data', sa.Column('topology_id', sa.Integer(), nullable=True))


def downgrade() -> None:
    # Remove topology_id column from tunnel_config_data table (only if it exists)
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('tunnel_config_data')]
    
    if 'topology_id' in columns:
        op.drop_column('tunnel_config_data', 'topology_id')
