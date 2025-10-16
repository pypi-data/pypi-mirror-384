"""add_protocol_enablement_flags_to_tunnel_config

Revision ID: c8f9d2e5a1b3
Revises: b4d7e8f5c1a2
Create Date: 2025-07-09 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c8f9d2e5a1b3'
down_revision: Union[str, None] = 'b4d7e8f5c1a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add ospf_enabled and ebgp_enabled boolean columns to tunnel_config_data table."""
    # Check if columns already exist
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('tunnel_config_data')]
    
    # Add ospf_enabled column only if it doesn't exist
    if 'ospf_enabled' not in columns:
        op.add_column('tunnel_config_data', sa.Column(
            'ospf_enabled', 
            sa.Boolean(), 
            nullable=True,
            comment='Whether OSPF protocol is enabled for this configuration'
        ))
    
    # Add ebgp_enabled column only if it doesn't exist
    if 'ebgp_enabled' not in columns:
        op.add_column('tunnel_config_data', sa.Column(
            'ebgp_enabled', 
            sa.Boolean(), 
            nullable=True,
            comment='Whether eBGP protocol is enabled for this configuration'
        ))
    
    # Set default values for existing records (only if columns were just added or exist)
    if 'ospf_enabled' in columns or 'ospf_enabled' not in [col['name'] for col in inspector.get_columns('tunnel_config_data')]:
        op.execute("UPDATE tunnel_config_data SET ospf_enabled = false WHERE ospf_enabled IS NULL")
    if 'ebgp_enabled' in columns or 'ebgp_enabled' not in [col['name'] for col in inspector.get_columns('tunnel_config_data')]:
        op.execute("UPDATE tunnel_config_data SET ebgp_enabled = false WHERE ebgp_enabled IS NULL")


def downgrade() -> None:
    """Remove ospf_enabled and ebgp_enabled columns from tunnel_config_data table."""
    # Check if columns exist before dropping
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('tunnel_config_data')]
    
    if 'ebgp_enabled' in columns:
        op.drop_column('tunnel_config_data', 'ebgp_enabled')
    if 'ospf_enabled' in columns:
        op.drop_column('tunnel_config_data', 'ospf_enabled')
