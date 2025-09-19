"""change drg_id to INTEGER type

Revision ID: f5d6ffb206ef
Revises: 3c7059807255
Create Date: 2025-09-19 14:32:58.981291

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f5d6ffb206ef'
down_revision = '3c7059807255'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Step 1: Drop foreign key constraint in drg_prices
    op.drop_constraint('drg_prices_drg_id_fkey', 'drg_prices', type_='foreignkey')
    
    # Step 2: Convert drg_id to INTEGER in drgs table
    op.execute("ALTER TABLE drgs ALTER COLUMN drg_id TYPE INTEGER USING drg_id::INTEGER")
    
    # Step 3: Convert drg_id to INTEGER in drg_prices table
    op.execute("ALTER TABLE drg_prices ALTER COLUMN drg_id TYPE INTEGER USING drg_id::INTEGER")
    
    # Step 4: Recreate foreign key constraint
    op.create_foreign_key('drg_prices_drg_id_fkey', 'drg_prices', 'drgs', ['drg_id'], ['drg_id'])


def downgrade() -> None:
    # Step 1: Drop foreign key constraint in drg_prices
    op.drop_constraint('drg_prices_drg_id_fkey', 'drg_prices', type_='foreignkey')
    
    # Step 2: Convert drg_id back to VARCHAR in drgs table
    op.execute("ALTER TABLE drgs ALTER COLUMN drg_id TYPE VARCHAR(10) USING drg_id::VARCHAR")
    
    # Step 3: Convert drg_id back to VARCHAR in drg_prices table
    op.execute("ALTER TABLE drg_prices ALTER COLUMN drg_id TYPE VARCHAR(10) USING drg_id::VARCHAR")
    
    # Step 4: Recreate foreign key constraint
    op.create_foreign_key('drg_prices_drg_id_fkey', 'drg_prices', 'drgs', ['drg_id'], ['drg_id'])
