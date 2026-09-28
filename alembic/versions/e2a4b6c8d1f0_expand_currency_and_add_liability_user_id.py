"""expand currency length and add user_id to liabilities

Revision ID: e2a4b6c8d1f0
Revises: d1f3a9b2e7c8
Create Date: 2026-09-28

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "e2a4b6c8d1f0"
down_revision: str | None = "d1f3a9b2e7c8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. Expand currency column from VARCHAR(3) to VARCHAR(10) in all tables
    tables = [
        "accounts",
        "assets",
        "cashflow_entries",
        "financial_goals",
        "historical_snapshots",
        "liabilities",
        "transactions",
    ]
    for table in tables:
        op.alter_column(
            table,
            "currency",
            existing_type=sa.String(length=3),
            type_=sa.String(length=10),
            existing_nullable=False,
            server_default="TOMAN",
        )

    # 2. Add user_id column to liabilities table
    op.add_column(
        "liabilities",
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=True,
        ),
    )
    op.create_index("ix_liabilities_user_id", "liabilities", ["user_id"], if_not_exists=True)


def downgrade() -> None:
    op.drop_index("ix_liabilities_user_id", table_name="liabilities")
    op.drop_column("liabilities", "user_id")

    tables = [
        "accounts",
        "assets",
        "cashflow_entries",
        "financial_goals",
        "historical_snapshots",
        "liabilities",
        "transactions",
    ]
    for table in tables:
        op.alter_column(
            table,
            "currency",
            existing_type=sa.String(length=10),
            type_=sa.String(length=3),
            existing_nullable=False,
            server_default="USD",
        )
