"""Bootstrap complete schema from tables_ts.py for fresh database

Revision ID: fresh_db_bootstrap
Revises:
Create Date: 2025-09-21 19:54:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'fresh_db_bootstrap'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Bootstrap complete schema for fresh database."""

    # First, create TimescaleDB extension
    bind = op.get_bind()
    bind.execute(sa.text("CREATE EXTENSION IF NOT EXISTS timescaledb;"))

    # ### Standard table creation commands ###
    op.create_table('companies',
    sa.Column('company_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.Column('frequency', sa.Integer(), nullable=False),
    sa.Column('dataset_type', sa.Text(), nullable=False),
    sa.Column('min_date', sa.Date(), nullable=False),
    sa.Column('max_date', sa.Date(), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('company_id'),
    sa.UniqueConstraint('name')
    )

    op.create_table('regions',
    sa.Column('region_id', sa.Integer(), nullable=False),
    sa.Column('abbreviation', sa.Text(), nullable=False),
    sa.Column('type', sa.Text(), nullable=False),
    sa.Column('country', sa.Integer(), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.Column('parent_region_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['parent_region_id'], ['regions.region_id'], name='link_to_parent_regions', onupdate='RESTRICT', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('region_id'),
    sa.UniqueConstraint('abbreviation', 'type', 'country')
    )
    op.create_index('unique_region_index', 'regions', ['parent_region_id', 'name', 'abbreviation', 'type'], unique=True)
    op.create_index('unique_top_level_regions', 'regions', ['name', 'abbreviation', 'type'], unique=True)

    op.create_table('categories',
    sa.Column('company_id', sa.Integer(), nullable=False),
    sa.Column('category_id', sa.Integer(), sa.Identity(always=True), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.ForeignKeyConstraint(['company_id'], ['companies.company_id'], name='fk_categories_companies', onupdate='RESTRICT', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('company_id', 'category_id', name='pk_categories'),
    sa.UniqueConstraint('company_id', 'name', name='uq_categories_company_name')
    )
    op.create_index('ix_categories_company_id', 'categories', ['company_id'], unique=False)

    op.create_table('category_level_descriptions',
    sa.Column('company_id', sa.Integer(), nullable=False),
    sa.Column('level_id', sa.Integer(), sa.Identity(always=True), nullable=False),
    sa.Column('level', sa.Integer(), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.ForeignKeyConstraint(['company_id'], ['companies.company_id'], name='fk_catleveldesc_companies', onupdate='RESTRICT', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('company_id', 'level_id', name='pk_category_level_descriptions'),
    sa.UniqueConstraint('company_id', 'level', 'name', name='uq_catleveldesc_company_level_name')
    )
    op.create_index('ix_catleveldesc_company_id', 'category_level_descriptions', ['company_id'], unique=False)

    op.create_table('feature_descriptions',
    sa.Column('company_id', sa.Integer(), nullable=False),
    sa.Column('feature_id', sa.Integer(), sa.Identity(always=True), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('var_type', sa.Text(), nullable=False),
    sa.Column('feature_type', sa.Text(), nullable=False),
    sa.ForeignKeyConstraint(['company_id'], ['companies.company_id'], name='fk_feature_descriptions_companies', onupdate='RESTRICT', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('company_id', 'feature_id', name='pk_feature_descriptions'),
    sa.UniqueConstraint('company_id', 'name', name='uq_feature_descriptions_company_name')
    )
    op.create_index('ix_feature_descriptions_company_id', 'feature_descriptions', ['company_id'], unique=False)

    op.create_table('products',
    sa.Column('company_id', sa.Integer(), nullable=False),
    sa.Column('product_id', sa.Integer(), sa.Identity(always=True), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.ForeignKeyConstraint(['company_id'], ['companies.company_id'], name='fk_products_companies', onupdate='RESTRICT', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('company_id', 'product_id', name='pk_products'),
    sa.UniqueConstraint('company_id', 'name', name='uq_products_company_name')
    )
    op.create_index('ix_products_company_id', 'products', ['company_id'], unique=False)

    op.create_table('stores',
    sa.Column('company_id', sa.Integer(), nullable=False),
    sa.Column('store_id', sa.Integer(), sa.Identity(always=True), nullable=False),
    sa.Column('region_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.Text(), nullable=False),
    sa.ForeignKeyConstraint(['company_id'], ['companies.company_id'], name='link_to_companies', onupdate='RESTRICT', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['region_id'], ['regions.region_id'], name='link_to_regions', onupdate='RESTRICT', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('company_id', 'store_id', name='pk_stores'),
    sa.UniqueConstraint('company_id', 'name')
    )
    op.create_index('ix_stores_company_id', 'stores', ['company_id'], unique=False)
    op.create_index('ix_stores_region_id', 'stores', ['region_id'], unique=False)

    op.create_table('category_relations',
    sa.Column('company_id', sa.Integer(), nullable=False),
    sa.Column('sub_category_id', sa.Integer(), nullable=False),
    sa.Column('parent_category_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['company_id', 'parent_category_id'], ['categories.company_id', 'categories.category_id'], name='fk_category_relations_parent', onupdate='RESTRICT', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['company_id', 'sub_category_id'], ['categories.company_id', 'categories.category_id'], name='fk_category_relations_sub', onupdate='RESTRICT', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['company_id'], ['companies.company_id'], name='fk_category_relations_companies', onupdate='RESTRICT', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('company_id', 'sub_category_id', 'parent_category_id', name='pk_category_relations'),
    sa.UniqueConstraint('company_id', 'sub_category_id', 'parent_category_id')
    )
    op.create_index('ix_category_relations_company_id', 'category_relations', ['company_id'], unique=False)

    op.create_table('feature_levels',
    sa.Column('company_id', sa.Integer(), nullable=False),
    sa.Column('feature_id', sa.Integer(), nullable=False),
    sa.Column('level', sa.Text(), nullable=False),
    sa.Column('sort_order', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['company_id', 'feature_id'], ['feature_descriptions.company_id', 'feature_descriptions.feature_id'], name='fk_feature_levels_feature_descriptions', onupdate='RESTRICT', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('company_id', 'feature_id', 'level', name='pk_feature_levels'),
    sa.UniqueConstraint('company_id', 'feature_id', 'sort_order', name='uq_feature_levels_company_feature_order')
    )
    op.create_index('ix_feature_levels_company_feature', 'feature_levels', ['company_id', 'feature_id'], unique=False)
    op.create_index('ix_feature_levels_company_id', 'feature_levels', ['company_id'], unique=False)

    op.create_table('product_categories',
    sa.Column('company_id', sa.Integer(), nullable=False),
    sa.Column('product_id', sa.Integer(), nullable=False),
    sa.Column('category_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['company_id', 'category_id'], ['categories.company_id', 'categories.category_id'], name='fk_product_categories_categories', onupdate='RESTRICT', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['company_id', 'product_id'], ['products.company_id', 'products.product_id'], name='fk_product_categories_products', onupdate='RESTRICT', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('company_id', 'product_id', 'category_id', name='pk_product_categories'),
    sa.UniqueConstraint('company_id', 'product_id', 'category_id')
    )
    op.create_index('ix_product_categories_company_id', 'product_categories', ['company_id'], unique=False)
    op.create_index('ix_product_categories_product_id', 'product_categories', ['company_id', 'product_id'], unique=False)

    op.create_table('product_features',
    sa.Column('company_id', sa.Integer(), nullable=False),
    sa.Column('product_id', sa.Integer(), nullable=False),
    sa.Column('feature_id', sa.Integer(), nullable=False),
    sa.Column('value', postgresql.DOUBLE_PRECISION(), nullable=True),
    sa.ForeignKeyConstraint(['company_id', 'feature_id'], ['feature_descriptions.company_id', 'feature_descriptions.feature_id'], name='fk_product_features_feat', onupdate='RESTRICT', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['company_id', 'product_id'], ['products.company_id', 'products.product_id'], name='fk_product_features_products', onupdate='RESTRICT', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('company_id', 'product_id', 'feature_id', name='pk_product_features')
    )
    op.create_index('ix_product_features_company_feature', 'product_features', ['company_id', 'feature_id'], unique=False)
    op.create_index('ix_product_features_company_product', 'product_features', ['company_id', 'product_id'], unique=False)

    op.create_table('product_features_text',
    sa.Column('company_id', sa.Integer(), nullable=False),
    sa.Column('product_id', sa.Integer(), nullable=False),
    sa.Column('feature_id', sa.Integer(), nullable=False),
    sa.Column('value', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['company_id', 'feature_id'], ['feature_descriptions.company_id', 'feature_descriptions.feature_id'], name='fk_product_features_text_feat', onupdate='RESTRICT', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['company_id', 'product_id'], ['products.company_id', 'products.product_id'], name='fk_product_features_text_products', onupdate='RESTRICT', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('company_id', 'product_id', 'feature_id', name='pk_product_features_text')
    )
    op.create_index('ix_product_features_text_company_feature', 'product_features_text', ['company_id', 'feature_id'], unique=False)
    op.create_index('ix_product_features_text_company_product', 'product_features_text', ['company_id', 'product_id'], unique=False)

    op.create_table('sku_table',
    sa.Column('company_id', sa.Integer(), nullable=False),
    sa.Column('sku_id', sa.Integer(), sa.Identity(always=True), nullable=False),
    sa.Column('product_id', sa.Integer(), nullable=False),
    sa.Column('store_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['company_id', 'product_id'], ['products.company_id', 'products.product_id'], name='fk_sku_table_products', onupdate='RESTRICT', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['company_id', 'store_id'], ['stores.company_id', 'stores.store_id'], name='fk_sku_table_stores', onupdate='RESTRICT', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('company_id', 'sku_id', name='pk_sku_table'),
    sa.UniqueConstraint('company_id', 'product_id', 'store_id')
    )
    op.create_index('ix_sku_table_company_id', 'sku_table', ['company_id'], unique=False)
    op.create_index('ix_sku_table_sku_id', 'sku_table', ['company_id', 'sku_id'], unique=False)

    op.create_table('store_features',
    sa.Column('company_id', sa.Integer(), nullable=False),
    sa.Column('store_id', sa.Integer(), nullable=False),
    sa.Column('feature_id', sa.Integer(), nullable=False),
    sa.Column('value', postgresql.DOUBLE_PRECISION(), nullable=True),
    sa.ForeignKeyConstraint(['company_id', 'feature_id'], ['feature_descriptions.company_id', 'feature_descriptions.feature_id'], name='fk_store_features_feat', onupdate='RESTRICT', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['company_id', 'store_id'], ['stores.company_id', 'stores.store_id'], name='fk_store_features_stores', onupdate='RESTRICT', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('company_id', 'store_id', 'feature_id', name='pk_store_features')
    )
    op.create_index('ix_store_features_company_feature', 'store_features', ['company_id', 'feature_id'], unique=False)
    op.create_index('ix_store_features_company_store', 'store_features', ['company_id', 'store_id'], unique=False)

    op.create_table('store_features_text',
    sa.Column('company_id', sa.Integer(), nullable=False),
    sa.Column('store_id', sa.Integer(), nullable=False),
    sa.Column('feature_id', sa.Integer(), nullable=False),
    sa.Column('value', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['company_id', 'feature_id'], ['feature_descriptions.company_id', 'feature_descriptions.feature_id'], name='fk_store_features_text_feat', onupdate='RESTRICT', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['company_id', 'store_id'], ['stores.company_id', 'stores.store_id'], name='fk_store_features_text_stores', onupdate='RESTRICT', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('company_id', 'store_id', 'feature_id', name='pk_store_features_text')
    )
    op.create_index('ix_store_features_text_company_feature', 'store_features_text', ['company_id', 'feature_id'], unique=False)
    op.create_index('ix_store_features_text_company_store', 'store_features_text', ['company_id', 'store_id'], unique=False)

    # Create time-series tables (these will become hypertables)
    op.create_table('time_product_features',
    sa.Column('company_id', sa.Integer(), nullable=False),
    sa.Column('product_id', sa.Integer(), nullable=False),
    sa.Column('feature_id', sa.Integer(), nullable=False),
    sa.Column('ts', sa.Date(), nullable=False),
    sa.Column('value', postgresql.DOUBLE_PRECISION(), nullable=True),
    sa.ForeignKeyConstraint(['company_id', 'feature_id'], ['feature_descriptions.company_id', 'feature_descriptions.feature_id'], name='fk_tpf_features', onupdate='RESTRICT', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['company_id', 'product_id'], ['products.company_id', 'products.product_id'], name='fk_tpf_products', onupdate='RESTRICT', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('company_id', 'product_id', 'feature_id', 'ts', name='pk_time_product_features')
    )

    op.create_table('time_product_features_text',
    sa.Column('company_id', sa.Integer(), nullable=False),
    sa.Column('product_id', sa.Integer(), nullable=False),
    sa.Column('feature_id', sa.Integer(), nullable=False),
    sa.Column('ts', sa.Date(), nullable=False),
    sa.Column('value', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['company_id', 'feature_id'], ['feature_descriptions.company_id', 'feature_descriptions.feature_id'], name='fk_tpf_text_features', onupdate='RESTRICT', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['company_id', 'product_id'], ['products.company_id', 'products.product_id'], name='fk_tpf_text_products', onupdate='RESTRICT', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('company_id', 'product_id', 'feature_id', 'ts', name='pk_time_product_features_text')
    )

    op.create_table('time_region_features',
    sa.Column('company_id', sa.Integer(), nullable=False),
    sa.Column('region_id', sa.Integer(), nullable=False),
    sa.Column('feature_id', sa.Integer(), nullable=False),
    sa.Column('ts', sa.Date(), nullable=False),
    sa.Column('value', postgresql.DOUBLE_PRECISION(), nullable=True),
    sa.ForeignKeyConstraint(['company_id', 'feature_id'], ['feature_descriptions.company_id', 'feature_descriptions.feature_id'], name='fk_trf_features', onupdate='RESTRICT', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['region_id'], ['regions.region_id'], name='fk_trf_regions', onupdate='RESTRICT', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('company_id', 'region_id', 'feature_id', 'ts', name='pk_time_region_features')
    )

    op.create_table('time_region_features_text',
    sa.Column('company_id', sa.Integer(), nullable=False),
    sa.Column('region_id', sa.Integer(), nullable=False),
    sa.Column('feature_id', sa.Integer(), nullable=False),
    sa.Column('ts', sa.Date(), nullable=False),
    sa.Column('value', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['company_id', 'feature_id'], ['feature_descriptions.company_id', 'feature_descriptions.feature_id'], name='fk_trf_text_features', onupdate='RESTRICT', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['region_id'], ['regions.region_id'], name='fk_trf_text_regions', onupdate='RESTRICT', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('company_id', 'region_id', 'feature_id', 'ts', name='pk_time_region_features_text')
    )

    op.create_table('time_store_features',
    sa.Column('company_id', sa.Integer(), nullable=False),
    sa.Column('store_id', sa.Integer(), nullable=False),
    sa.Column('feature_id', sa.Integer(), nullable=False),
    sa.Column('ts', sa.Date(), nullable=False),
    sa.Column('value', postgresql.DOUBLE_PRECISION(), nullable=True),
    sa.ForeignKeyConstraint(['company_id', 'feature_id'], ['feature_descriptions.company_id', 'feature_descriptions.feature_id'], name='fk_tsf_features', onupdate='RESTRICT', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['company_id', 'store_id'], ['stores.company_id', 'stores.store_id'], name='fk_tsf_stores', onupdate='RESTRICT', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('company_id', 'store_id', 'feature_id', 'ts', name='pk_time_store_features')
    )

    op.create_table('time_store_features_text',
    sa.Column('company_id', sa.Integer(), nullable=False),
    sa.Column('store_id', sa.Integer(), nullable=False),
    sa.Column('feature_id', sa.Integer(), nullable=False),
    sa.Column('ts', sa.Date(), nullable=False),
    sa.Column('value', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['company_id', 'feature_id'], ['feature_descriptions.company_id', 'feature_descriptions.feature_id'], name='fk_tsf_text_features', onupdate='RESTRICT', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['company_id', 'store_id'], ['stores.company_id', 'stores.store_id'], name='fk_tsf_text_stores', onupdate='RESTRICT', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('company_id', 'store_id', 'feature_id', 'ts', name='pk_time_store_features_text')
    )

    op.create_table('time_sku_features',
    sa.Column('company_id', sa.Integer(), nullable=False),
    sa.Column('sku_id', sa.Integer(), nullable=False),
    sa.Column('feature_id', sa.Integer(), nullable=False),
    sa.Column('ts', sa.Date(), nullable=False),
    sa.Column('value', postgresql.DOUBLE_PRECISION(), nullable=True),
    sa.ForeignKeyConstraint(['company_id', 'feature_id'], ['feature_descriptions.company_id', 'feature_descriptions.feature_id'], name='fk_tskuf_features', onupdate='RESTRICT', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['company_id', 'sku_id'], ['sku_table.company_id', 'sku_table.sku_id'], name='fk_tskuf_sku', onupdate='RESTRICT', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('company_id', 'sku_id', 'feature_id', 'ts', name='pk_time_sku_features')
    )

    op.create_table('time_sku_features_text',
    sa.Column('company_id', sa.Integer(), nullable=False),
    sa.Column('sku_id', sa.Integer(), nullable=False),
    sa.Column('feature_id', sa.Integer(), nullable=False),
    sa.Column('ts', sa.Date(), nullable=False),
    sa.Column('value', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['company_id', 'feature_id'], ['feature_descriptions.company_id', 'feature_descriptions.feature_id'], name='fk_tskuf_text_features', onupdate='RESTRICT', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['company_id', 'sku_id'], ['sku_table.company_id', 'sku_table.sku_id'], name='fk_tskuf_text_sku', onupdate='RESTRICT', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('company_id', 'sku_id', 'feature_id', 'ts', name='pk_time_sku_features_text')
    )

    op.create_table('order_intake',
    sa.Column('company_id', sa.Integer(), nullable=False),
    sa.Column('sku_id', sa.Integer(), nullable=False),
    sa.Column('order_date', sa.Date(), nullable=False),
    sa.Column('expected_delivery_date', sa.Date(), nullable=False),
    sa.Column('quantity', postgresql.DOUBLE_PRECISION(), nullable=False),
    sa.ForeignKeyConstraint(['company_id', 'sku_id'], ['sku_table.company_id', 'sku_table.sku_id'], name='fk_oid_sku', onupdate='RESTRICT', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('company_id', 'sku_id', 'order_date', 'expected_delivery_date', name='pk_order_intake')
    )

    op.create_table('expected_deliveries',
    sa.Column('company_id', sa.Integer(), nullable=False),
    sa.Column('sku_id', sa.Integer(), nullable=False),
    sa.Column('expected_delivery_date', sa.Date(), nullable=False),
    sa.Column('quantity', postgresql.DOUBLE_PRECISION(), nullable=False),
    sa.ForeignKeyConstraint(['company_id', 'sku_id'], ['sku_table.company_id', 'sku_table.sku_id'], name='fk_dbd_sku', onupdate='RESTRICT', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('company_id', 'sku_id', 'expected_delivery_date', name='pk_expected_deliveries')
    )

    op.create_table('change_log_committed',
    sa.Column('company_id', sa.Integer(), nullable=False),
    sa.Column('sku_id', sa.Integer(), nullable=False),
    sa.Column('expected_delivery_date', sa.Date(), nullable=False),
    sa.Column('valid_from', sa.Date(), nullable=False),
    sa.Column('quantity', postgresql.DOUBLE_PRECISION(), nullable=False),
    sa.ForeignKeyConstraint(['company_id', 'sku_id'], ['sku_table.company_id', 'sku_table.sku_id'], name='fk_clc_sku', onupdate='RESTRICT', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('company_id', 'sku_id', 'expected_delivery_date', 'valid_from', name='pk_change_log_committed')
    )

    op.create_table('flags',
    sa.Column('company_id', sa.Integer(), nullable=False),
    sa.Column('sku_id', sa.Integer(), nullable=False),
    sa.Column('feature_id', sa.Integer(), nullable=False),
    sa.Column('ts', sa.Date(), nullable=False),
    sa.Column('value', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['company_id', 'feature_id'], ['feature_descriptions.company_id', 'feature_descriptions.feature_id'], name='fk_flags_features', onupdate='RESTRICT', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['company_id', 'sku_id'], ['sku_table.company_id', 'sku_table.sku_id'], name='fk_flags_sku', onupdate='RESTRICT', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('company_id', 'sku_id', 'feature_id', 'ts', name='pk_flags')
    )

    op.create_table('sku_features',
    sa.Column('company_id', sa.Integer(), nullable=False),
    sa.Column('sku_id', sa.Integer(), nullable=False),
    sa.Column('feature_id', sa.Integer(), nullable=False),
    sa.Column('value', postgresql.DOUBLE_PRECISION(), nullable=True),
    sa.ForeignKeyConstraint(['company_id', 'feature_id'], ['feature_descriptions.company_id', 'feature_descriptions.feature_id'], name='fk_sku_features_feat', onupdate='RESTRICT', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['company_id', 'sku_id'], ['sku_table.company_id', 'sku_table.sku_id'], name='fk_sku_features_sku', onupdate='RESTRICT', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('company_id', 'sku_id', 'feature_id', name='pk_sku_features')
    )
    op.create_index('ix_sku_features_company_feature', 'sku_features', ['company_id', 'feature_id'], unique=False)
    op.create_index('ix_sku_features_company_sku', 'sku_features', ['company_id', 'sku_id'], unique=False)

    op.create_table('sku_features_text',
    sa.Column('company_id', sa.Integer(), nullable=False),
    sa.Column('sku_id', sa.Integer(), nullable=False),
    sa.Column('feature_id', sa.Integer(), nullable=False),
    sa.Column('value', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['company_id', 'feature_id'], ['feature_descriptions.company_id', 'feature_descriptions.feature_id'], name='fk_sku_features_text_feat', onupdate='RESTRICT', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['company_id', 'sku_id'], ['sku_table.company_id', 'sku_table.sku_id'], name='fk_sku_features_text_sku', onupdate='RESTRICT', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('company_id', 'sku_id', 'feature_id', name='pk_sku_features_text')
    )
    op.create_index('ix_sku_features_text_company_feature', 'sku_features_text', ['company_id', 'feature_id'], unique=False)
    op.create_index('ix_sku_features_text_company_sku', 'sku_features_text', ['company_id', 'sku_id'], unique=False)

    # ### NOW CREATE TIMESCALEDB HYPERTABLES AND CONFIGURATION ###

    # Convert time-series tables to hypertables with compression
    timescale_tables = [
        # (table_name, time_column, space_column, number_partitions, orderby, segmentby)
        ('time_product_features', 'ts', 'product_id', 32, 'ts DESC', 'company_id,product_id,feature_id'),
        ('time_product_features_text', 'ts', 'product_id', 32, 'ts DESC', 'company_id,product_id,feature_id'),
        ('time_region_features', 'ts', 'region_id', 16, 'ts DESC', 'company_id,region_id,feature_id'),
        ('time_region_features_text', 'ts', 'region_id', 16, 'ts DESC', 'company_id,region_id,feature_id'),
        ('time_store_features', 'ts', 'store_id', 32, 'ts DESC', 'company_id,store_id,feature_id'),
        ('time_store_features_text', 'ts', 'store_id', 32, 'ts DESC', 'company_id,store_id,feature_id'),
        ('time_sku_features', 'ts', 'sku_id', 32, 'ts DESC', 'company_id,sku_id,feature_id'),
        ('time_sku_features_text', 'ts', 'sku_id', 32, 'ts DESC', 'company_id,sku_id,feature_id'),
        ('order_intake', 'order_date', 'sku_id', 32, 'order_date DESC', 'company_id,sku_id'),
        ('expected_deliveries', 'expected_delivery_date', 'sku_id', 32, 'expected_delivery_date DESC', 'company_id,sku_id'),
        ('change_log_committed', 'valid_from', 'sku_id', 32, 'valid_from DESC', 'company_id,sku_id,expected_delivery_date'),
        ('flags', 'ts', 'sku_id', 32, 'ts DESC', 'company_id,sku_id,feature_id')
    ]

    # Create hypertables
    for table_name, time_col, space_col, partitions, _, _ in timescale_tables:
        bind.execute(sa.text(f"""
            SELECT create_hypertable(
                '{table_name}',
                '{time_col}',
                partitioning_column => '{space_col}',
                number_partitions => {partitions},
                create_default_indexes => FALSE,
                if_not_exists => TRUE
            );
        """))

        # Set chunk time interval
        bind.execute(sa.text(f"SELECT set_chunk_time_interval('{table_name}', INTERVAL '14 days');"))

    # Configure compression for all hypertables
    for table_name, _, _, _, orderby, segmentby in timescale_tables:
        bind.execute(sa.text(f"""
            ALTER TABLE "{table_name}"
            SET (timescaledb.compress = 'on',
                 timescaledb.compress_orderby = '{orderby}',
                 timescaledb.compress_segmentby = '{segmentby}');
        """))

        # Add compression policy (compress after 30 days)
        bind.execute(sa.text(f"SELECT add_compression_policy('{table_name}', INTERVAL '30 days');"))


def downgrade() -> None:
    """Downgrade schema - Drop all tables."""
    # Drop all tables in reverse dependency order
    op.drop_table('sku_features_text')
    op.drop_table('sku_features')
    op.drop_table('flags')
    op.drop_table('change_log_committed')
    op.drop_table('expected_deliveries')
    op.drop_table('order_intake')
    op.drop_table('time_sku_features_text')
    op.drop_table('time_sku_features')
    op.drop_table('time_store_features_text')
    op.drop_table('time_store_features')
    op.drop_table('time_region_features_text')
    op.drop_table('time_region_features')
    op.drop_table('time_product_features_text')
    op.drop_table('time_product_features')
    op.drop_table('store_features_text')
    op.drop_table('store_features')
    op.drop_table('sku_table')
    op.drop_table('product_features_text')
    op.drop_table('product_features')
    op.drop_table('product_categories')
    op.drop_table('feature_levels')
    op.drop_table('category_relations')
    op.drop_table('stores')
    op.drop_table('products')
    op.drop_table('feature_descriptions')
    op.drop_table('category_level_descriptions')
    op.drop_table('categories')
    op.drop_table('regions')
    op.drop_table('companies')