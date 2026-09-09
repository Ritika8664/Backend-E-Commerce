"""rename Stripe session reference to provider-agnostic payment reference

Revision ID: 0002
Revises: 0001
"""

from collections.abc import Sequence

from alembic import op


revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.alter_column(
        "orders",
        "stripe_session_id",
        new_column_name="payment_reference_id",
    )


def downgrade() -> None:
    op.alter_column(
        "orders",
        "payment_reference_id",
        new_column_name="stripe_session_id",
    )
