"""add_client_interfaces_column_to_tunnel_config

Revision ID: 21c9f27314b4
Revises: 630b2588379d
Create Date: 2025-06-16 23:02:56.094117

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '21c9f27314b4'
down_revision: Union[str, None] = '630b2588379d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add client_interfaces column to tunnel_config_data table."""
    # Check if the column already exists (it might have been added by manual migration)
    inspector = sa.inspect(op.get_bind())
    columns = [col['name'] for col in inspector.get_columns('tunnel_config_data')]
    
    if 'client_interfaces' not in columns:
        # Add client_interfaces column as JSON
        with op.batch_alter_table('tunnel_config_data', schema=None) as batch_op:
            batch_op.add_column(sa.Column('client_interfaces', sa.JSON(), nullable=True))
        
        # Migrate existing data: populate client_interfaces from config_data if available
        op.execute("""
            UPDATE tunnel_config_data 
            SET client_interfaces = json_extract(config_data, '$.client_interfaces')
            WHERE config_data IS NOT NULL 
            AND json_extract(config_data, '$.client_interfaces') IS NOT NULL
        """)
    # If column already exists, this migration is essentially a no-op


def downgrade() -> None:
    """Remove client_interfaces column from tunnel_config_data table."""
    with op.batch_alter_table('tunnel_config_data', schema=None) as batch_op:
        batch_op.drop_column('client_interfaces')
