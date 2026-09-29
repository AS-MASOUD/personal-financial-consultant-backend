"""create_liability_types_table

Revision ID: 61d6bea83f3a
Revises: f3b5c7d9e1a2
Create Date: 2026-09-29 11:12:03.012738

"""
import uuid
from typing import Sequence, Union
from decimal import Decimal

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '61d6bea83f3a'
down_revision: Union[str, Sequence[str], None] = 'f3b5c7d9e1a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "liability_types",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("label", sa.String(length=100), nullable=False),
        sa.Column("short_label", sa.String(length=100), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("icon", sa.String(length=50), nullable=False, server_default="Building"),
        sa.Column("default_rate", sa.Numeric(precision=6, scale=3), nullable=False, server_default="0.000"),
        sa.Column("default_term_months", sa.Integer(), nullable=False, server_default="12"),
        sa.Column("is_friend", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("direction", sa.String(length=20), nullable=False, server_default="debt"),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_liability_types_code"),
    )
    op.create_index(op.f("ix_liability_types_code"), "liability_types", ["code"], unique=True)

    # Prepopulate standard liability types & labels
    liability_types_table = sa.table(
        "liability_types",
        sa.column("id", sa.UUID()),
        sa.column("code", sa.String()),
        sa.column("label", sa.String()),
        sa.column("short_label", sa.String()),
        sa.column("description", sa.Text()),
        sa.column("icon", sa.String()),
        sa.column("default_rate", sa.Numeric()),
        sa.column("default_term_months", sa.Integer()),
        sa.column("is_friend", sa.Boolean()),
        sa.column("direction", sa.String()),
        sa.column("display_order", sa.Integer()),
        sa.column("is_active", sa.Boolean()),
    )
    op.bulk_insert(
        liability_types_table,
        [
            {
                "id": uuid.uuid4(),
                "code": "bank_loan",
                "label": "وام بانکی",
                "short_label": "وام بانکی",
                "description": "تسهیلات بانکی با نرخ سود مصوب یا توافقی",
                "icon": "Building",
                "default_rate": Decimal("18.000"),
                "default_term_months": 24,
                "is_friend": False,
                "direction": "debt",
                "display_order": 1,
                "is_active": True,
            },
            {
                "id": uuid.uuid4(),
                "code": "friend_borrowed",
                "label": "قرض گرفتن از دوست / آشنا",
                "short_label": "قرض گرفته‌شده از دوست (بدهی)",
                "description": "بدهی من به دیگری (سود ۰٪ قرض‌الحسنه)",
                "icon": "ArrowDownLeft",
                "default_rate": Decimal("0.000"),
                "default_term_months": 3,
                "is_friend": True,
                "direction": "debt",
                "display_order": 2,
                "is_active": True,
            },
            {
                "id": uuid.uuid4(),
                "code": "friend_lent",
                "label": "قرض دادن به دوست / آشنا",
                "short_label": "قرض داده‌شده به دوست (طلب)",
                "description": "طلب من از دیگری / مطالبات مالی (سود ۰٪)",
                "icon": "ArrowUpRight",
                "default_rate": Decimal("0.000"),
                "default_term_months": 3,
                "is_friend": True,
                "direction": "claim",
                "display_order": 3,
                "is_active": True,
            },
            {
                "id": uuid.uuid4(),
                "code": "bnpl",
                "label": "خرید اقساطی پلتفرمی (BNPL)",
                "short_label": "خرید اقساطی پلتفرمی",
                "description": "اقساط اسنپ‌پی، دیجی‌پی، ازکی‌وام، تارا و ...",
                "icon": "CreditCard",
                "default_rate": Decimal("0.000"),
                "default_term_months": 4,
                "is_friend": False,
                "direction": "debt",
                "display_order": 4,
                "is_active": True,
            },
            {
                "id": uuid.uuid4(),
                "code": "personal_loan",
                "label": "وام شخصی / صندوق خانوادگی",
                "short_label": "وام شخصی / صندوق",
                "description": "صندوق‌های وام خانگی و قرض‌الحسنه کارمندی",
                "icon": "Users",
                "default_rate": Decimal("4.000"),
                "default_term_months": 12,
                "is_friend": False,
                "direction": "debt",
                "display_order": 5,
                "is_active": True,
            },
            {
                "id": uuid.uuid4(),
                "code": "mortgage",
                "label": "وام مسکن",
                "short_label": "وام مسکن",
                "description": "تسهیلات خرید یا ودیعه مسکن و جعاله",
                "icon": "Building",
                "default_rate": Decimal("23.000"),
                "default_term_months": 60,
                "is_friend": False,
                "direction": "debt",
                "display_order": 6,
                "is_active": True,
            },
            {
                "id": uuid.uuid4(),
                "code": "auto_loan",
                "label": "وام خودرو",
                "short_label": "وام خودرو",
                "description": "تسهیلات لیزینگ یا خرید خودرو",
                "icon": "CreditCard",
                "default_rate": Decimal("23.000"),
                "default_term_months": 36,
                "is_friend": False,
                "direction": "debt",
                "display_order": 7,
                "is_active": True,
            },
            {
                "id": uuid.uuid4(),
                "code": "student_loan",
                "label": "وام تحصیلی",
                "short_label": "وام تحصیلی",
                "description": "تسهیلات دانشجویی و صندوق رفاه دانشجویان",
                "icon": "GraduationCap",
                "default_rate": Decimal("4.000"),
                "default_term_months": 36,
                "is_friend": False,
                "direction": "debt",
                "display_order": 8,
                "is_active": True,
            },
            {
                "id": uuid.uuid4(),
                "code": "credit_card",
                "label": "کارت اعتباری",
                "short_label": "کارت اعتباری",
                "description": "اعتبار کارت بانکی با دوره تنفس یا بازپرداخت اقساطی",
                "icon": "CreditCard",
                "default_rate": Decimal("18.000"),
                "default_term_months": 12,
                "is_friend": False,
                "direction": "debt",
                "display_order": 9,
                "is_active": True,
            },
            {
                "id": uuid.uuid4(),
                "code": "other",
                "label": "سایر بدهی‌ها و تعهدات",
                "short_label": "سایر تعهدات",
                "description": "چک‌های صادره، بدهی بازار، تعهدات غیربانکی",
                "icon": "AlertCircle",
                "default_rate": Decimal("0.000"),
                "default_term_months": 6,
                "is_friend": False,
                "direction": "debt",
                "display_order": 10,
                "is_active": True,
            },
        ],
    )

    # Link existing liabilities to liability_types
    op.create_foreign_key(
        "fk_liabilities_liability_type",
        "liabilities",
        "liability_types",
        ["liability_type"],
        ["code"],
        onupdate="CASCADE",
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint("fk_liabilities_liability_type", "liabilities", type_="foreignkey")
    op.drop_index(op.f("ix_liability_types_code"), table_name="liability_types")
    op.drop_table("liability_types")
