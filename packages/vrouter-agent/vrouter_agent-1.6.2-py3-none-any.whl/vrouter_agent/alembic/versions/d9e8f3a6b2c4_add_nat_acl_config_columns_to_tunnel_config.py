"""add_nat_acl_config_columns_to_tunnel_config

Revision ID: d9e8f3a6b2c4
Revises: c8f9d2e5a1b3
Create Date: 2025-10-09 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd9e8f3a6b2c4'
down_revision: Union[str, None] = 'c8f9d2e5a1b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add nat_config and acl_config JSON columns to tunnel_config_data table."""
    # Check if columns already exist
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('tunnel_config_data')]
    
    # Add nat_config column only if it doesn't exist
    if 'nat_config' not in columns:
        op.add_column('tunnel_config_data', sa.Column(
            'nat_config', 
            sa.JSON(), 
            nullable=True,
            comment='NAT44 configuration including address pools and static mappings'
        ))
    
    # Add acl_config column only if it doesn't exist
    if 'acl_config' not in columns:
        op.add_column('tunnel_config_data', sa.Column(
            'acl_config', 
            sa.JSON(), 
            nullable=True,
            comment='ACL (Access Control List) configuration with rules and policies'
        ))


def downgrade() -> None:
    """Remove nat_config and acl_config columns from tunnel_config_data table."""
    # Check if columns exist before dropping
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('tunnel_config_data')]
    
    if 'acl_config' in columns:
        op.drop_column('tunnel_config_data', 'acl_config')
    if 'nat_config' in columns:
        op.drop_column('tunnel_config_data', 'nat_config')
