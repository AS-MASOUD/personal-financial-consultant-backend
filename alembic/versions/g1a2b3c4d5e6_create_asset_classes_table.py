"""create asset_classes table

Revision ID: g1a2b3c4d5e6
Revises: f3b5c7d9e1a2
Create Date: 2026-09-29 13:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "g1a2b3c4d5e6"
down_revision: str | None = "61d6bea83f3a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create the asset_classes reference table
    op.create_table(
        "asset_classes",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("label", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("icon", sa.String(50), nullable=False, server_default="Layers"),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index(op.f("ix_asset_classes_code"), "asset_classes", ["code"], unique=True)

    # Seed default asset classes so FK constraint is satisfied
    op.execute("""
        INSERT INTO asset_classes (id, code, label, description, icon, display_order, is_active, created_at, updated_at) VALUES
        (gen_random_uuid(), 'equity',       'سهام و ETF',          'سهام شرکت‌ها و صندوق‌های قابل معامله در بورس',  'TrendingUp',  1, true, now(), now()),
        (gen_random_uuid(), 'crypto',       'ارز دیجیتال',        'رمزارزها و توکن‌های دیجیتال',                     'Gem',         2, true, now(), now()),
        (gen_random_uuid(), 'commodity',    'طلا و کالاها',       'طلا، نقره، نفت، مس و سایر کالاهای فیزیکی',       'Coins',       3, true, now(), now()),
        (gen_random_uuid(), 'fixed_income', 'درآمد ثابت و اوراق', 'اوراق قرضه، صکوک و ابزارهای درآمد ثابت',         'DollarSign',  4, true, now(), now()),
        (gen_random_uuid(), 'real_estate',  'املاک و مستغلات',    'سرمایه‌گذاری در املاک و مستغلات',                 'Building',    5, true, now(), now()),
        (gen_random_uuid(), 'cash',         'ارز و نقدینگی',      'ارزهای فیات، حساب‌های جاری و سپرده‌های نقدی',   'Banknote',    6, true, now(), now())
    """)

    # Add FK from assets.asset_class -> asset_classes.code
    op.create_foreign_key(
        "fk_assets_asset_class_asset_classes",
        "assets",
        "asset_classes",
        ["asset_class"],
        ["code"],
        onupdate="CASCADE",
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint("fk_assets_asset_class_asset_classes", "assets", type_="foreignkey")
    op.drop_index(op.f("ix_asset_classes_code"), table_name="asset_classes")
    op.drop_table("asset_classes")
