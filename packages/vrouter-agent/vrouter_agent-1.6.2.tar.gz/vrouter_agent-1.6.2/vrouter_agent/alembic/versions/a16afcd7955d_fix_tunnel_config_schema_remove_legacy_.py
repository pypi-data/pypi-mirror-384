"""Fix tunnel config schema - remove legacy status columns only

Revision ID: a16afcd7955d
Revises: 
Create Date: 2025-06-06 17:44:21.163143

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a16afcd7955d'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Remove legacy status columns and fix schema mismatch.
    
    Current state:
    - tunnel_config_data MAY have: status (legacy), state, config_data_state  
    - tunnel_config_history MAY have: old_status, new_status (legacy), old_config_data_state, new_config_data_state
    
    Target state:
    - tunnel_config_data has: state (NOT NULL), config_data_state (NOT NULL)
    - tunnel_config_history has: old_state, new_state (NOT NULL), old_config_data_state, new_config_data_state (NOT NULL)
    """
    
    # Get connection to check column existence
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tunnel_config_columns = [col['name'] for col in inspector.get_columns('tunnel_config_data')]
    history_columns = [col['name'] for col in inspector.get_columns('tunnel_config_history')]
    
    # Add missing columns to tunnel_config_data if they don't exist
    with op.batch_alter_table('tunnel_config_data', schema=None) as batch_op:
        if 'state' not in tunnel_config_columns:
            batch_op.add_column(sa.Column('state', sa.VARCHAR(), nullable=True, server_default='planned'))
        if 'config_data_state' not in tunnel_config_columns:
            batch_op.add_column(sa.Column('config_data_state', sa.VARCHAR(), nullable=True, server_default='pending'))
    
    # Refresh column list
    tunnel_config_columns = [col['name'] for col in inspector.get_columns('tunnel_config_data')]
    
    # Step 1: Migrate data from status to state in tunnel_config_data (only if status column exists)
    if 'status' in tunnel_config_columns:
        op.execute("""
            UPDATE tunnel_config_data 
            SET state = CASE 
                WHEN status = 'completed' THEN 'active'
                WHEN status = 'failed' THEN 'error' 
                WHEN status = 'processing' THEN 'pending'
                WHEN status = 'pending' THEN 'planned'
                ELSE 'planned'
            END
            WHERE state IS NULL OR state = 'planned'
        """)
    else:
        # If no status column, just set defaults for null states
        op.execute("UPDATE tunnel_config_data SET state = 'planned' WHERE state IS NULL")
    
    # Ensure config_data_state has defaults (only if column exists)
    if 'config_data_state' in tunnel_config_columns:
        op.execute("UPDATE tunnel_config_data SET config_data_state = 'pending' WHERE config_data_state IS NULL")
    
    # Step 2: Migrate data from old_status/new_status to old_state/new_state in tunnel_config_history
    # Add the new state columns first if they don't exist
    if 'old_state' not in history_columns:
        with op.batch_alter_table('tunnel_config_history', schema=None) as batch_op:
            batch_op.add_column(sa.Column('old_state', sa.VARCHAR(), nullable=True))
    
    if 'new_state' not in history_columns:
        with op.batch_alter_table('tunnel_config_history', schema=None) as batch_op:
            batch_op.add_column(sa.Column('new_state', sa.VARCHAR(), nullable=True))
    
    # Refresh column list after adding new columns
    history_columns = [col['name'] for col in inspector.get_columns('tunnel_config_history')]
    
    # Add missing columns to tunnel_config_history if needed
    with op.batch_alter_table('tunnel_config_history', schema=None) as batch_op:
        if 'old_config_data_state' not in history_columns:
            batch_op.add_column(sa.Column('old_config_data_state', sa.VARCHAR(), nullable=True))
        if 'new_config_data_state' not in history_columns:
            batch_op.add_column(sa.Column('new_config_data_state', sa.VARCHAR(), nullable=True, server_default='pending'))
    
    # Refresh column list again
    history_columns = [col['name'] for col in inspector.get_columns('tunnel_config_history')]
    
    # Copy data from status columns to state columns (only if old_status/new_status exist)
    if 'old_status' in history_columns or 'new_status' in history_columns:
        op.execute("""
            UPDATE tunnel_config_history 
            SET old_state = CASE 
                WHEN old_status = 'completed' THEN 'active'
                WHEN old_status = 'failed' THEN 'error'
                WHEN old_status = 'processing' THEN 'pending' 
                WHEN old_status = 'pending' THEN 'planned'
                ELSE old_status
            END,
            new_state = CASE
                WHEN new_status = 'completed' THEN 'active'
                WHEN new_status = 'failed' THEN 'error'
                WHEN new_status = 'processing' THEN 'pending'
                WHEN new_status = 'pending' THEN 'planned' 
                ELSE new_status
            END
        """)
    
    # Set default values for null columns (only if they exist)
    if 'new_state' in history_columns:
        op.execute("UPDATE tunnel_config_history SET new_state = 'planned' WHERE new_state IS NULL")
    if 'new_config_data_state' in history_columns:
        op.execute("UPDATE tunnel_config_history SET new_config_data_state = 'pending' WHERE new_config_data_state IS NULL")
    
    # Refresh tunnel_config_columns for final step
    tunnel_config_columns = [col['name'] for col in inspector.get_columns('tunnel_config_data')]
    
    # Step 3: Make state and config_data_state NOT NULL in tunnel_config_data
    with op.batch_alter_table('tunnel_config_data', schema=None) as batch_op:
        if 'state' in tunnel_config_columns:
            batch_op.alter_column('state', nullable=False, existing_server_default=sa.text("'planned'"))
        if 'config_data_state' in tunnel_config_columns:
            batch_op.alter_column('config_data_state', nullable=False, existing_server_default=sa.text("'pending'"))
        # Remove legacy status column only if it exists
        if 'status' in tunnel_config_columns:
            batch_op.drop_column('status')
    
    # Step 4: Make new_state and new_config_data_state NOT NULL in tunnel_config_history
    # Refresh column list
    history_columns = [col['name'] for col in inspector.get_columns('tunnel_config_history')]
    
    with op.batch_alter_table('tunnel_config_history', schema=None) as batch_op:
        batch_op.alter_column('new_state', nullable=False)
        batch_op.alter_column('new_config_data_state', nullable=False, existing_server_default=sa.text("'pending'"))
        # Remove legacy status columns only if they exist
        if 'old_status' in history_columns:
            batch_op.drop_column('old_status')
        if 'new_status' in history_columns:
            batch_op.drop_column('new_status')


def downgrade() -> None:
    """
    Restore legacy status columns (for rollback purposes).
    """
    
    # Step 1: Add back the legacy status column to tunnel_config_data
    with op.batch_alter_table('tunnel_config_data', schema=None) as batch_op:
        batch_op.add_column(sa.Column('status', sa.VARCHAR(), nullable=False, server_default='pending'))
        batch_op.alter_column('state', nullable=True)
        batch_op.alter_column('config_data_state', nullable=True)
    
    # Copy state back to status
    op.execute("""
        UPDATE tunnel_config_data 
        SET status = CASE 
            WHEN state = 'active' THEN 'completed'
            WHEN state = 'error' THEN 'failed'
            WHEN state = 'pending' THEN 'processing'
            WHEN state = 'planned' THEN 'pending'
            ELSE 'pending'
        END
    """)
    
    # Step 2: Add back legacy status columns to tunnel_config_history
    with op.batch_alter_table('tunnel_config_history', schema=None) as batch_op:
        batch_op.add_column(sa.Column('old_status', sa.VARCHAR(), nullable=True))
        batch_op.add_column(sa.Column('new_status', sa.VARCHAR(), nullable=False, server_default='pending'))
        batch_op.alter_column('new_state', nullable=True)
        batch_op.alter_column('new_config_data_state', nullable=True)
    
    # Copy state back to status  
    op.execute("""
        UPDATE tunnel_config_history 
        SET old_status = CASE 
            WHEN old_state = 'active' THEN 'completed'
            WHEN old_state = 'error' THEN 'failed'
            WHEN old_state = 'pending' THEN 'processing'
            WHEN old_state = 'planned' THEN 'pending'
            ELSE old_state
        END,
        new_status = CASE
            WHEN new_state = 'active' THEN 'completed'
            WHEN new_state = 'error' THEN 'failed'
            WHEN new_state = 'pending' THEN 'processing'
            WHEN new_state = 'planned' THEN 'pending'
            ELSE new_state
        END
    """)
    
    # Step 3: Remove the new state columns
    with op.batch_alter_table('tunnel_config_history', schema=None) as batch_op:
        batch_op.drop_column('old_state')
        batch_op.drop_column('new_state')
