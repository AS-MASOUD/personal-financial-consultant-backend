"""cascade delete for asset_positions on asset delete

Revision ID: f3b5c7d9e1a2
Revises: e2a4b6c8d1f0
Create Date: 2026-09-29

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f3b5c7d9e1a2"
down_revision: str | None = "e2a4b6c8d1f0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.drop_constraint("asset_positions_asset_id_fkey", "asset_positions", type_="foreignkey")
    op.create_foreign_key(
        "asset_positions_asset_id_fkey",
        "asset_positions",
        "assets",
        ["asset_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint("asset_positions_asset_id_fkey", "asset_positions", type_="foreignkey")
    op.create_foreign_key(
        "asset_positions_asset_id_fkey",
        "asset_positions",
        "assets",
        ["asset_id"],
        ["id"],
        ondelete="RESTRICT",
    )
