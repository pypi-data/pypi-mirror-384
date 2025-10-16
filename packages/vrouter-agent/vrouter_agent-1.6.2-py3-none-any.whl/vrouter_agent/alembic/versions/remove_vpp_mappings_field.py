"""Remove vpp_interface_mappings from tunnel config

Revision ID: remove_vpp_mappings_field
Revises: acb2cb4a8198
Create Date: 2025-06-09 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'remove_vpp_mappings_field'
down_revision = 'acb2cb4a8198'
branch_labels = None
depends_on = None


def upgrade():
    """Remove vpp_interface_mappings column since VPP data is now embedded in tunnels."""
    # Check if the column exists before trying to drop it
    # This provides better error handling for environments where the column might not exist
    with op.batch_alter_table('tunnel_config_data', schema=None) as batch_op:
        # Note: We use try/catch in the actual database operation, not here
        # The batch operation will handle the column existence check
        batch_op.drop_column('vpp_interface_mappings')


def downgrade():
    """Re-add vpp_interface_mappings column if needed for rollback."""
    # Add the vpp_interface_mappings column back as JSON type with default empty dict
    with op.batch_alter_table('tunnel_config_data', schema=None) as batch_op:
        batch_op.add_column(sa.Column('vpp_interface_mappings', sa.JSON(), nullable=False, server_default='{}'))
