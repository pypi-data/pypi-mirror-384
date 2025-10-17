"""update schema from fresh_master_test_20250930

Revision ID: c19fab5a6d53
Revises: fresh_master_test_20250930
Create Date: 2025-10-03 17:31:09.719297

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c19fab5a6d53'
down_revision: Union[str, Sequence[str], None] = 'fresh_master_test_20250930'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Split dataset_mapping into train and test_val tables."""

    # Get bind for SQL execution
    bind = op.get_bind()

    # Drop old dataset_mapping table
    op.drop_table('dataset_mapping')

    # Create SKUType enum (use raw SQL with IF NOT EXISTS)
    bind.execute(sa.text("""
        DO $$ BEGIN
            CREATE TYPE skutype AS ENUM ('known_sku', 'unknown_sku', 'unknown_store', 'unknown_product', 'unknown_company');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """))

    # Create dataset_mapping_train table
    op.create_table(
        'dataset_mapping_train',
        sa.Column('dataset_id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('sku_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.company_id'], name='fk_dataset_mapping_train_companies', onupdate='RESTRICT', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['company_id', 'sku_id'], ['sku_table.company_id', 'sku_table.sku_id'], name='fk_dataset_mapping_train_sku_table', onupdate='RESTRICT', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.dataset_id'], name='fk_dataset_mapping_train_datasets', onupdate='RESTRICT', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('dataset_id', 'sku_id', 'company_id', name='pk_dataset_mapping_train')
    )

    # Create dataset_mapping_test_val table
    op.create_table(
        'dataset_mapping_test_val',
        sa.Column('dataset_id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('sku_id', sa.Integer(), nullable=False),
        sa.Column('sku_type', postgresql.ENUM('known_sku', 'unknown_sku', 'unknown_store', 'unknown_product', 'unknown_company', name='skutype', create_type=False), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.company_id'], name='fk_dataset_mapping_test_val_companies', onupdate='RESTRICT', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['company_id', 'sku_id'], ['sku_table.company_id', 'sku_table.sku_id'], name='fk_dataset_mapping_test_val_sku_table', onupdate='RESTRICT', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.dataset_id'], name='fk_dataset_mapping_test_val_datasets', onupdate='RESTRICT', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('dataset_id', 'sku_id', 'company_id', name='pk_dataset_mapping_test_val')
    )


def downgrade() -> None:
    """Downgrade schema: Merge train and test_val tables back into dataset_mapping."""

    # Drop new tables
    op.drop_table('dataset_mapping_test_val')
    op.drop_table('dataset_mapping_train')

    # Drop SKUType enum
    skutype = postgresql.ENUM('known_sku', 'unknown_sku', 'unknown_store', 'unknown_product', 'unknown_company', name='skutype')
    skutype.drop(op.get_bind())

    # Recreate original dataset_mapping table
    op.create_table(
        'dataset_mapping',
        sa.Column('dataset_id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('sku_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.company_id'], name='fk_dataset_mapping_companies', onupdate='RESTRICT', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['company_id', 'sku_id'], ['sku_table.company_id', 'sku_table.sku_id'], name='fk_dataset_mapping_sku_table', onupdate='RESTRICT', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['dataset_id'], ['datasets.dataset_id'], name='fk_dataset_mapping_datasets', onupdate='RESTRICT', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('dataset_id', 'sku_id', 'company_id', name='pk_dataset_mapping')
    )
