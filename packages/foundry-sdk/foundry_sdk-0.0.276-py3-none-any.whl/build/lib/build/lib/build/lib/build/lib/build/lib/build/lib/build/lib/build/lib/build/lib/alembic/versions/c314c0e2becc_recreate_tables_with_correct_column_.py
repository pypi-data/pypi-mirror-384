"""recreate tables with correct column names

Revision ID: c314c0e2becc
Revises: 0c554ca8cb51
Create Date: 2025-09-19 16:29:29.636015

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c314c0e2becc'
down_revision: Union[str, Sequence[str], None] = '0c554ca8cb51'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()

    # Create order_intake table
    op.create_table(
        'order_intake',
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('sku_id', sa.Integer(), nullable=False),
        sa.Column('order_date', sa.Date(), nullable=False),
        sa.Column('expected_delivery_date', sa.Date(), nullable=False),
        sa.Column('qty_total', sa.DOUBLE_PRECISION(), nullable=False),
        sa.PrimaryKeyConstraint('company_id', 'sku_id', 'order_date', 'expected_delivery_date', name='pk_order_intake'),
        sa.ForeignKeyConstraint(['company_id', 'sku_id'], ['sku_table.company_id', 'sku_table.sku_id'], name='fk_oid_sku', onupdate='RESTRICT', ondelete='CASCADE')
    )

    # Create expected_deliveries table
    op.create_table(
        'expected_deliveries',
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('sku_id', sa.Integer(), nullable=False),
        sa.Column('expected_delivery_date', sa.Date(), nullable=False),
        sa.Column('total_qty', sa.DOUBLE_PRECISION(), nullable=False),
        sa.PrimaryKeyConstraint('company_id', 'sku_id', 'expected_delivery_date', name='pk_expected_deliveries'),
        sa.ForeignKeyConstraint(['company_id', 'sku_id'], ['sku_table.company_id', 'sku_table.sku_id'], name='fk_dbd_sku', onupdate='RESTRICT', ondelete='CASCADE')
    )

    # Create change_log_committed table
    op.create_table(
        'change_log_committed',
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('sku_id', sa.Integer(), nullable=False),
        sa.Column('expected_delivery_date', sa.Date(), nullable=False),
        sa.Column('valid_from', sa.Date(), nullable=False),
        sa.Column('committed_qty', sa.DOUBLE_PRECISION(), nullable=False),
        sa.PrimaryKeyConstraint('company_id', 'sku_id', 'expected_delivery_date', 'valid_from', name='pk_change_log_committed'),
        sa.ForeignKeyConstraint(['company_id', 'sku_id'], ['sku_table.company_id', 'sku_table.sku_id'], name='fk_clc_sku', onupdate='RESTRICT', ondelete='CASCADE')
    )

    # Configure TimescaleDB hypertables and compression
    # Create hypertable for order_intake
    bind.execute(sa.text("""
        SELECT create_hypertable(
            'order_intake',
            'order_date',
            partitioning_column => 'sku_id',
            number_partitions => 32,
            chunk_time_interval => INTERVAL '14 days'
        )
    """))

    # Create hypertable for expected_deliveries
    bind.execute(sa.text("""
        SELECT create_hypertable(
            'expected_deliveries',
            'expected_delivery_date',
            partitioning_column => 'sku_id',
            number_partitions => 32,
            chunk_time_interval => INTERVAL '14 days'
        )
    """))

    # Create hypertable for change_log_committed
    bind.execute(sa.text("""
        SELECT create_hypertable(
            'change_log_committed',
            'valid_from',
            partitioning_column => 'sku_id',
            number_partitions => 32,
            chunk_time_interval => INTERVAL '14 days'
        )
    """))

    # Add compression policies
    bind.execute(sa.text("""
        ALTER TABLE order_intake SET (
            timescaledb.compress,
            timescaledb.compress_orderby = 'order_date DESC',
            timescaledb.compress_segmentby = 'company_id,sku_id'
        )
    """))

    bind.execute(sa.text("""
        ALTER TABLE expected_deliveries SET (
            timescaledb.compress,
            timescaledb.compress_orderby = 'expected_delivery_date DESC',
            timescaledb.compress_segmentby = 'company_id,sku_id'
        )
    """))

    bind.execute(sa.text("""
        ALTER TABLE change_log_committed SET (
            timescaledb.compress,
            timescaledb.compress_orderby = 'valid_from DESC',
            timescaledb.compress_segmentby = 'company_id,sku_id,expected_delivery_date'
        )
    """))

    # Add compression policies (compress after 30 days)
    bind.execute(sa.text("""
        SELECT add_compression_policy('order_intake', INTERVAL '30 days')
    """))

    bind.execute(sa.text("""
        SELECT add_compression_policy('expected_deliveries', INTERVAL '30 days')
    """))

    bind.execute(sa.text("""
        SELECT add_compression_policy('change_log_committed', INTERVAL '30 days')
    """))


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the tables (TimescaleDB will automatically handle hypertable cleanup)
    op.drop_table('change_log_committed')
    op.drop_table('expected_deliveries')
    op.drop_table('order_intake')
