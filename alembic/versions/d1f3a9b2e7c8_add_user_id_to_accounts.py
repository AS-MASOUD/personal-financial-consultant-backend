"""add user_id to accounts

Revision ID: d1f3a9b2e7c8
Revises: c724b2ccfaee
Create Date: 2026-09-26

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "d1f3a9b2e7c8"
down_revision: str | None = "ac0c4d6f07b6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "accounts",
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.create_index("ix_accounts_user_id", "accounts", ["user_id"], if_not_exists=True)


def downgrade() -> None:
    op.drop_index("ix_accounts_user_id", table_name="accounts")
    op.drop_column("accounts", "user_id")
