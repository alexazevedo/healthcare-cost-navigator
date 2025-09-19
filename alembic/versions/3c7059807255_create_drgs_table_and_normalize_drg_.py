"""create drgs table and normalize drg_prices

Revision ID: 3c7059807255
Revises: 2d9e45cb7d4f
Create Date: 2025-09-19 14:18:42.310951

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = '3c7059807255'
down_revision = '2d9e45cb7d4f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Step 1: Create the drgs table
    op.create_table('drgs',
        sa.Column('drg_id', sa.String(length=10), nullable=False),
        sa.Column('ms_drg_definition', sa.String(length=255), nullable=False),
        sa.PrimaryKeyConstraint('drg_id')
    )
    op.create_index('idx_drgs_definition', 'drgs', ['ms_drg_definition'])
    
    # Step 2: Populate drgs table with unique DRG definitions from drg_prices
    # We'll create a synthetic drg_id from the ms_drg_definition
    op.execute("""
        INSERT INTO drgs (drg_id, ms_drg_definition)
        SELECT 
            DISTINCT
            CASE 
                WHEN ms_drg_definition ~ '^[0-9]+' THEN 
                    SUBSTRING(ms_drg_definition FROM '^[0-9]+')
                ELSE 
                    'DRG_' || ROW_NUMBER() OVER (ORDER BY ms_drg_definition)::text
            END as drg_id,
            ms_drg_definition
        FROM drg_prices
        GROUP BY ms_drg_definition
        ORDER BY ms_drg_definition
    """)
    
    # Step 3: Add drg_id column to drg_prices table
    op.add_column('drg_prices', sa.Column('drg_id', sa.String(length=10), nullable=True))
    
    # Step 4: Populate drg_id in drg_prices by matching with drgs table
    op.execute("""
        UPDATE drg_prices 
        SET drg_id = drgs.drg_id 
        FROM drgs 
        WHERE drg_prices.ms_drg_definition = drgs.ms_drg_definition
    """)
    
    # Step 5: Make drg_id NOT NULL and add foreign key
    op.alter_column('drg_prices', 'drg_id', nullable=False)
    op.create_foreign_key('drg_prices_drg_id_fkey', 'drg_prices', 'drgs', ['drg_id'], ['drg_id'])
    
    # Step 6: Create indexes for drg_id
    op.create_index('idx_drg_id', 'drg_prices', ['drg_id'])
    
    # Step 7: Drop the old ms_drg_definition column and its indexes
    op.drop_index('idx_drg_definition', table_name='drg_prices')
    op.drop_index('idx_drg_provider_definition', table_name='drg_prices')
    op.drop_column('drg_prices', 'ms_drg_definition')


def downgrade() -> None:
    # Reverse the normalization
    # Step 1: Add back ms_drg_definition column
    op.add_column('drg_prices', sa.Column('ms_drg_definition', sa.String(length=255), nullable=True))
    
    # Step 2: Populate ms_drg_definition from drgs table
    op.execute("""
        UPDATE drg_prices 
        SET ms_drg_definition = drgs.ms_drg_definition 
        FROM drgs 
        WHERE drg_prices.drg_id = drgs.drg_id
    """)
    
    # Step 3: Make ms_drg_definition NOT NULL
    op.alter_column('drg_prices', 'ms_drg_definition', nullable=False)
    
    # Step 4: Recreate old indexes
    op.create_index('idx_drg_definition', 'drg_prices', ['ms_drg_definition'])
    op.create_index('idx_drg_provider_definition', 'drg_prices', ['provider_id', 'ms_drg_definition'])
    
    # Step 5: Drop foreign key and drg_id column
    op.drop_constraint('drg_prices_drg_id_fkey', 'drg_prices', type_='foreignkey')
    op.drop_index('idx_drg_id', table_name='drg_prices')
    op.drop_column('drg_prices', 'drg_id')
    
    # Step 6: Drop drgs table
    op.drop_index('idx_drgs_definition', table_name='drgs')
    op.drop_table('drgs')
