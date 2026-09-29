"""create goal_categories table

Revision ID: h2b3c4d5e6f7
Revises: g1a2b3c4d5e6
Create Date: 2026-09-29 13:40:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "h2b3c4d5e6f7"
down_revision: str | None = "g1a2b3c4d5e6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Create the goal_categories reference table
    op.create_table(
        "goal_categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("label", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("icon", sa.String(50), nullable=False, server_default="Target"),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index(op.f("ix_goal_categories_code"), "goal_categories", ["code"], unique=True)

    # Seed default goal categories so FK constraint is satisfied
    op.execute("""
        INSERT INTO goal_categories (id, code, label, description, icon, display_order, is_active, created_at, updated_at) VALUES
        (gen_random_uuid(), 'emergency_fund', 'صندوق اضطراری',             'صندوق ذخیره اضطراری برای حوادث و رویدادهای غیرمترقبه', 'ShieldAlert',    1, true, now(), now()),
        (gen_random_uuid(), 'retirement',     'بازنشستگی و استقلال مالی',    'صندوق بازنشستگی، استقلال مالی و پس‌انداز بلندمدت',      'Clock',          2, true, now(), now()),
        (gen_random_uuid(), 'real_estate',    'خرید مسکن و ملک',           'خرید خانه، آپارتمان، زمین یا ودیعه مسکن',                'Home',           3, true, now(), now()),
        (gen_random_uuid(), 'home_purchase',  'خرید مسکن',                 'خرید خانه و مسکن',                                     'Home',           4, true, now(), now()),
        (gen_random_uuid(), 'education',      'آموزش و تحصیل',             'دوره‌های آموزشی، تحصیل دانشگاهی و ارتقای مهارت',         'GraduationCap',  5, true, now(), now()),
        (gen_random_uuid(), 'investment',     'سرمایه‌گذاری هدفمند',       'سرمایه‌گذاری در بورس، طلا، صندوق‌ها یا رمزارزها',       'TrendingUp',     6, true, now(), now()),
        (gen_random_uuid(), 'debt_payoff',    'تسویه کامل بدهی',           'تسویه وام‌ها، اقساط و بدهی‌های شخصی',                   'CreditCard',     7, true, now(), now()),
        (gen_random_uuid(), 'vehicle',        'خرید خودرو',                'خرید یا تعویض خودرو و وسایل نقلیه',                    'Car',            8, true, now(), now()),
        (gen_random_uuid(), 'business',       'کسب‌وکار شخصی',             'راه‌اندازی، توسعه یا تجهیز کسب‌وکار و استارتاپ',         'Briefcase',      9, true, now(), now()),
        (gen_random_uuid(), 'personal',       'هدف شخصی',                  'اهداف و برنامه‌های شخصی و خانوادگی',                    'User',          10, true, now(), now()),
        (gen_random_uuid(), 'vacation',       'سفر و تفریح',               'هزینه‌های مسافرت، تفریح و اوقات فراغت',                  'Plane',         11, true, now(), now()),
        (gen_random_uuid(), 'other',          'سایر اهداف',                'سایر برنامه‌ها و اهداف مالی متفرقه',                    'Target',        12, true, now(), now())
    """)

    # Add FK from financial_goals.category -> goal_categories.code
    op.create_foreign_key(
        "fk_financial_goals_category_goal_categories",
        "financial_goals",
        "goal_categories",
        ["category"],
        ["code"],
        onupdate="CASCADE",
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    op.drop_constraint("fk_financial_goals_category_goal_categories", "financial_goals", type_="foreignkey")
    op.drop_index(op.f("ix_goal_categories_code"), table_name="goal_categories")
    op.drop_table("goal_categories")
