"""Create initial database schema with providers, drg_prices, and ratings tables

Revision ID: 856091cd0b7c
Revises: 
Create Date: 2025-09-17 14:09:36.432482

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '856091cd0b7c'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create providers table
    op.create_table('providers',
        sa.Column('provider_id', sa.VARCHAR(length=6), nullable=False),
        sa.Column('provider_name', sa.String(length=255), nullable=False),
        sa.Column('provider_city', sa.String(length=100), nullable=False),
        sa.Column('provider_state', sa.String(length=2), nullable=False),
        sa.Column('provider_zip_code', sa.String(length=10), nullable=False),
        sa.PrimaryKeyConstraint('provider_id')
    )
    
    # Create indexes for providers table
    op.create_index('idx_provider_zip_code', 'providers', ['provider_zip_code'])
    op.create_index('idx_provider_state', 'providers', ['provider_state'])
    op.create_index('idx_provider_city', 'providers', ['provider_city'])
    
    # Create drg_prices table
    op.create_table('drg_prices',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('provider_id', sa.VARCHAR(length=6), nullable=False),
        sa.Column('ms_drg_definition', sa.String(length=10), nullable=False),
        sa.Column('total_discharges', sa.Integer(), nullable=False),
        sa.Column('average_covered_charges', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('average_total_payments', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('average_medicare_payments', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.ForeignKeyConstraint(['provider_id'], ['providers.provider_id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for drg_prices table
    op.create_index('idx_drg_provider_id', 'drg_prices', ['provider_id'])
    op.create_index('idx_drg_definition', 'drg_prices', ['ms_drg_definition'])
    op.create_index('idx_drg_provider_definition', 'drg_prices', ['provider_id', 'ms_drg_definition'])
    
    # Create ratings table
    op.create_table('ratings',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('provider_id', sa.VARCHAR(length=6), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['provider_id'], ['providers.provider_id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('rating >= 1 AND rating <= 10', name='check_rating_range')
    )
    
    # Create indexes for ratings table
    op.create_index('idx_rating_provider_id', 'ratings', ['provider_id'])
    op.create_index('idx_rating_value', 'ratings', ['rating'])


def downgrade() -> None:
    # Drop tables in reverse order due to foreign key constraints
    op.drop_table('ratings')
    op.drop_table('drg_prices')
    op.drop_table('providers')
