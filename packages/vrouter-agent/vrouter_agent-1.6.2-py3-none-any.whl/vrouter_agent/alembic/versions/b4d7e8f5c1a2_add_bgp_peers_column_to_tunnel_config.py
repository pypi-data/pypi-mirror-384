"""add_bgp_peers_column_to_tunnel_config

Revision ID: b4d7e8f5c1a2
Revises: 21c9f27314b4
Create Date: 2025-07-09 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b4d7e8f5c1a2'
down_revision: Union[str, None] = '21c9f27314b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add bgp_peers column to tunnel_config_data table."""
    # Check if the column already exists (it might have been added by manual migration)
    inspector = sa.inspect(op.get_bind())
    columns = [col['name'] for col in inspector.get_columns('tunnel_config_data')]
    
    if 'bgp_peers' not in columns:
        # Add bgp_peers column as JSON
        with op.batch_alter_table('tunnel_config_data', schema=None) as batch_op:
            batch_op.add_column(sa.Column('bgp_peers', sa.JSON(), nullable=True))
        
        # Migrate existing data: populate bgp_peers from raw_config_data if available
        op.execute("""
            UPDATE tunnel_config_data 
            SET bgp_peers = json_extract(raw_config_data, '$.bgp_peers')
            WHERE raw_config_data IS NOT NULL 
            AND json_extract(raw_config_data, '$.bgp_peers') IS NOT NULL
        """)
        
        print("Added bgp_peers column to tunnel_config_data table")
    else:
        print("bgp_peers column already exists in tunnel_config_data table")


def downgrade() -> None:
    """Remove bgp_peers column from tunnel_config_data table."""
    with op.batch_alter_table('tunnel_config_data', schema=None) as batch_op:
        batch_op.drop_column('bgp_peers')
