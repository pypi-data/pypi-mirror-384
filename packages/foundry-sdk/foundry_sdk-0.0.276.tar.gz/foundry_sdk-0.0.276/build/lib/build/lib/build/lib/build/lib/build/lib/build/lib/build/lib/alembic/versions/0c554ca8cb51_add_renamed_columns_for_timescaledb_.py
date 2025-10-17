"""add renamed columns for TimescaleDB compatibility

Revision ID: 0c554ca8cb51
Revises: f4510e2584dc
Create Date: 2025-09-19 16:21:21.917048

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0c554ca8cb51'
down_revision: Union[str, Sequence[str], None] = '1541fb9cfe23'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()

    # Add new columns as nullable first (TimescaleDB hypertable constraint)
    # Note: We keep the old time dimension columns as they cannot be dropped
    op.add_column('change_log_committed', sa.Column('expected_delivery_date', sa.Date(), nullable=True))
    op.add_column('deliveries_by_day', sa.Column('expected_delivery_date', sa.Date(), nullable=True))
    op.add_column('order_intake_daily', sa.Column('order_date', sa.Date(), nullable=True))
    op.add_column('order_intake_daily', sa.Column('expected_delivery_date', sa.Date(), nullable=True))

    # Copy data from old columns to new columns
    bind.execute(sa.text("UPDATE change_log_committed SET expected_delivery_date = delivery_day"))
    bind.execute(sa.text("UPDATE deliveries_by_day SET expected_delivery_date = delivery_day"))
    bind.execute(sa.text("UPDATE order_intake_daily SET order_date = order_day, expected_delivery_date = delivery_day"))

    # Make new columns NOT NULL after data migration
    bind.execute(sa.text("ALTER TABLE change_log_committed ALTER COLUMN expected_delivery_date SET NOT NULL"))
    bind.execute(sa.text("ALTER TABLE deliveries_by_day ALTER COLUMN expected_delivery_date SET NOT NULL"))
    bind.execute(sa.text("ALTER TABLE order_intake_daily ALTER COLUMN order_date SET NOT NULL"))
    bind.execute(sa.text("ALTER TABLE order_intake_daily ALTER COLUMN expected_delivery_date SET NOT NULL"))


def downgrade() -> None:
    """Downgrade schema."""
    # Drop the added columns
    op.drop_column('order_intake_daily', 'expected_delivery_date')
    op.drop_column('order_intake_daily', 'order_date')
    op.drop_column('deliveries_by_day', 'expected_delivery_date')
    op.drop_column('change_log_committed', 'expected_delivery_date')
