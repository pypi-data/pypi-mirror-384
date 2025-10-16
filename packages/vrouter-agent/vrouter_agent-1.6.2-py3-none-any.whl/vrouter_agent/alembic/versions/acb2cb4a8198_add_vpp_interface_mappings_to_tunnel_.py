"""add_vpp_interface_mappings_to_tunnel_config

Revision ID: acb2cb4a8198
Revises: a16afcd7955d
Create Date: 2025-06-06 21:40:35.109041

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'acb2cb4a8198'
down_revision: Union[str, None] = 'a16afcd7955d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add vpp_interface_mappings column to tunnel_config_data table."""
    # Check if column already exists
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('tunnel_config_data')]
    
    if 'vpp_interface_mappings' not in columns:
        # Add the vpp_interface_mappings column as JSON type with default empty dict
        with op.batch_alter_table('tunnel_config_data', schema=None) as batch_op:
            batch_op.add_column(sa.Column('vpp_interface_mappings', sa.JSON(), nullable=False, server_default='{}'))


def downgrade() -> None:
    """Remove vpp_interface_mappings column from tunnel_config_data table."""
    # Check if column exists before dropping
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('tunnel_config_data')]
    
    if 'vpp_interface_mappings' in columns:
        # Remove the vpp_interface_mappings column
        with op.batch_alter_table('tunnel_config_data', schema=None) as batch_op:
            batch_op.drop_column('vpp_interface_mappings')
