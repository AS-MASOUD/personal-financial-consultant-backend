import asyncio
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import delete

from src.app.core.security import hash_password
from src.app.database.models import (
    AccountModel,
    AssetModel,
    AssetPositionModel,
    CashflowCategoryModel,
    CashflowEntryModel,
    FinancialGoalModel,
    HistoricalSnapshotModel,
    LiabilityModel,
    LiabilityPaymentModel,
    NotificationModel,
    OTPRequestModel,
    SystemRole,
    TransactionModel,
    UserModel,
)
from src.app.database.session import AsyncSessionFactory


async def seed_data():
    async with AsyncSessionFactory() as db:
        print("Clearing existing seed data...")
        await db.execute(delete(HistoricalSnapshotModel))
        await db.execute(delete(CashflowEntryModel))
        await db.execute(delete(CashflowCategoryModel))
        await db.execute(delete(LiabilityPaymentModel))
        await db.execute(delete(LiabilityModel))
        await db.execute(delete(TransactionModel))
        await db.execute(delete(AssetPositionModel))
        await db.execute(delete(AssetModel))
        await db.execute(delete(AccountModel))
        await db.execute(delete(FinancialGoalModel))
        await db.execute(delete(NotificationModel))
        await db.execute(delete(OTPRequestModel))
        await db.execute(delete(UserModel))
        await db.commit()

        print("Seeding Users & Roles (Email & Phone OTP)...")
        default_password = hash_password("AdminPassword123!")
        users = [
            UserModel(
                email="sysmanager@personal-fc.local",
                phone_number="09121111111",
                hashed_password=default_password,
                full_name="مدیر ارشد سامانه (SysManager)",
                role=SystemRole.SYSMANAGER.value,
                is_active=True,
                is_verified=True,
            ),
            UserModel(
                email="admin@personal-fc.local",
                phone_number="09122222222",
                hashed_password=default_password,
                full_name="مدیر مالی ارشد (Financial Admin)",
                role=SystemRole.ADMIN.value,
                is_active=True,
                is_verified=True,
            ),
            UserModel(
                email="user@personal-fc.local",
                phone_number="09123333333",
                hashed_password=default_password,
                full_name="کاربر شخصی (Personal User)",
                role=SystemRole.USER.value,
                is_active=True,
                is_verified=True,
            ),
            UserModel(
                email="viewer@personal-fc.local",
                phone_number="09124444444",
                hashed_password=default_password,
                full_name="ناظر و بازبین (Read-Only Viewer)",
                role=SystemRole.VIEWER.value,
                is_active=True,
                is_verified=True,
            ),
        ]
        db.add_all(users)
        await db.flush()

        print("Seeding Accounts...")
        checking = AccountModel(
            user_id=users[1].id,  # admin user owns the demo accounts
            name="Primary Checking",
            account_type="checking",
            institution="Chase Bank",
            currency="USD",
            current_balance=Decimal("8450.0000"),
            account_number_mask="*8821",
            is_active=True,
        )
        savings = AccountModel(
            user_id=users[1].id,
            name="High Yield Savings",
            account_type="savings",
            institution="Marcus by Goldman Sachs",
            currency="USD",
            current_balance=Decimal("32500.0000"),
            account_number_mask="*4319",
            is_active=True,
        )
        brokerage = AccountModel(
            user_id=users[1].id,
            name="Taxable Investment Portfolio",
            account_type="brokerage",
            institution="Fidelity",
            currency="USD",
            current_balance=Decimal("14800.0000"),
            account_number_mask="*9024",
            is_active=True,
        )
        crypto_wallet = AccountModel(
            user_id=users[1].id,
            name="Hardware Vault",
            account_type="crypto",
            institution="Coldcard Ledger",
            currency="USD",
            current_balance=Decimal("1200.0000"),
            account_number_mask="*bc1q",
            is_active=True,
        )
        db.add_all([checking, savings, brokerage, crypto_wallet])
        await db.flush()

        print("Seeding Assets...")
        assets_data = [
            ("VOO", "Vanguard S&P 500 ETF", "equity", Decimal("512.4000")),
            ("QQQ", "Invesco QQQ Trust", "equity", Decimal("485.6000")),
            ("AAPL", "Apple Inc.", "equity", Decimal("228.5000")),
            ("MSFT", "Microsoft Corporation", "equity", Decimal("448.2000")),
            ("NVDA", "NVIDIA Corporation", "equity", Decimal("124.8000")),
            ("BND", "Vanguard Total Bond Market ETF", "fixed_income", Decimal("73.1500")),
            ("GLD", "SPDR Gold Shares", "commodity", Decimal("242.8000")),
            ("BRENT", "Brent Crude Oil", "commodity", Decimal("74.5000")),
            ("BTC", "Bitcoin", "crypto", Decimal("63400.0000")),
            ("ETH", "Ethereum", "crypto", Decimal("2650.0000")),
        ]
        created_assets = {}
        now = datetime.now(UTC)
        for sym, name, a_class, price in assets_data:
            a = AssetModel(
                symbol=sym,
                name=name,
                asset_class=a_class,
                currency="USD",
                current_price=price,
                price_updated_at=now,
            )
            db.add(a)
            created_assets[sym] = a
        await db.flush()

        print("Seeding Asset Positions...")
        positions_data = [
            (brokerage.id, created_assets["VOO"].id, Decimal("85.00000000"), Decimal("435.2000")),
            (brokerage.id, created_assets["QQQ"].id, Decimal("40.00000000"), Decimal("410.0000")),
            (brokerage.id, created_assets["AAPL"].id, Decimal("50.00000000"), Decimal("182.5000")),
            (brokerage.id, created_assets["MSFT"].id, Decimal("30.00000000"), Decimal("385.0000")),
            (brokerage.id, created_assets["NVDA"].id, Decimal("110.00000000"), Decimal("88.4000")),
            (brokerage.id, created_assets["BND"].id, Decimal("150.00000000"), Decimal("74.2000")),
            (brokerage.id, created_assets["GLD"].id, Decimal("45.00000000"), Decimal("205.0000")),
            (
                crypto_wallet.id,
                created_assets["BTC"].id,
                Decimal("0.75000000"),
                Decimal("46500.0000"),
            ),
            (
                crypto_wallet.id,
                created_assets["ETH"].id,
                Decimal("5.20000000"),
                Decimal("2350.0000"),
            ),
        ]
        for acc_id, ast_id, qty, cost in positions_data:
            pos = AssetPositionModel(
                account_id=acc_id,
                asset_id=ast_id,
                quantity=qty,
                average_cost_basis=cost,
            )
            db.add(pos)
        await db.flush()

        print("Seeding Liabilities...")
        mortgage = LiabilityModel(
            name="Primary Home Mortgage",
            liability_type="mortgage",
            lender="Wells Fargo Home Mortgage",
            original_principal=Decimal("420000.0000"),
            current_balance=Decimal("358400.0000"),
            interest_rate_percent=Decimal("3.875"),
            monthly_payment=Decimal("1975.4000"),
            start_date=date(2021, 6, 1),
            maturity_date=date(2051, 6, 1),
            currency="USD",
        )
        auto_loan = LiabilityModel(
            name="Model Y Vehicle Loan",
            liability_type="auto_loan",
            lender="Tesla Financial Services",
            original_principal=Decimal("48000.0000"),
            current_balance=Decimal("19500.0000"),
            interest_rate_percent=Decimal("3.990"),
            monthly_payment=Decimal("745.2000"),
            start_date=date(2023, 2, 15),
            maturity_date=date(2028, 2, 15),
            currency="USD",
        )
        student_loan = LiabilityModel(
            name="Graduate Student Loan",
            liability_type="student_loan",
            lender="Mohela / Dept of Ed",
            original_principal=Decimal("32000.0000"),
            current_balance=Decimal("7800.0000"),
            interest_rate_percent=Decimal("4.250"),
            monthly_payment=Decimal("310.0000"),
            start_date=date(2020, 9, 1),
            maturity_date=date(2027, 9, 1),
            currency="USD",
        )
        db.add_all([mortgage, auto_loan, student_loan])
        await db.flush()

        print("Seeding Cashflow Categories...")
        cat_salary = CashflowCategoryModel(
            name="Tech Salary", flow_type="income", color_hex="#10b981", icon="briefcase"
        )
        cat_dividends = CashflowCategoryModel(
            name="Dividends & Interest", flow_type="income", color_hex="#06b6d4", icon="trending-up"
        )
        cat_housing = CashflowCategoryModel(
            name="Housing & Utilities", flow_type="expense", color_hex="#6366f1", icon="home"
        )
        cat_groceries = CashflowCategoryModel(
            name="Groceries & Food", flow_type="expense", color_hex="#f59e0b", icon="shopping-cart"
        )
        cat_transport = CashflowCategoryModel(
            name="Transportation", flow_type="expense", color_hex="#ec4899", icon="car"
        )
        cat_health = CashflowCategoryModel(
            name="Health & Wellness", flow_type="expense", color_hex="#8b5cf6", icon="heart-pulse"
        )
        cat_leisure = CashflowCategoryModel(
            name="Travel & Leisure", flow_type="expense", color_hex="#14b8a6", icon="plane"
        )

        db.add_all(
            [
                cat_salary,
                cat_dividends,
                cat_housing,
                cat_groceries,
                cat_transport,
                cat_health,
                cat_leisure,
            ]
        )
        await db.flush()

        print("Seeding Cashflow Entries...")
        today = date.today()
        entries = [
            (
                cat_salary.id,
                "income",
                Decimal("11850.0000"),
                today - timedelta(days=2),
                "Bi-weekly Principal Engineering Salary",
            ),
            (
                cat_salary.id,
                "income",
                Decimal("11850.0000"),
                today - timedelta(days=16),
                "Bi-weekly Principal Engineering Salary",
            ),
            (
                cat_dividends.id,
                "income",
                Decimal("480.0000"),
                today - timedelta(days=5),
                "Quarterly VOO ETF Dividend",
            ),
            (
                cat_housing.id,
                "expense",
                Decimal("2250.0000"),
                today - timedelta(days=3),
                "Mortgage payment & HOA fee",
            ),
            (
                cat_groceries.id,
                "expense",
                Decimal("320.0000"),
                today - timedelta(days=4),
                "Whole Foods Organic groceries",
            ),
            (
                cat_groceries.id,
                "expense",
                Decimal("185.0000"),
                today - timedelta(days=11),
                "Trader Joe's pantry restock",
            ),
            (
                cat_transport.id,
                "expense",
                Decimal("745.2000"),
                today - timedelta(days=10),
                "Auto loan monthly installment",
            ),
            (
                cat_transport.id,
                "expense",
                Decimal("68.0000"),
                today - timedelta(days=7),
                "EV Supercharging network",
            ),
            (
                cat_health.id,
                "expense",
                Decimal("175.0000"),
                today - timedelta(days=8),
                "Equinox gym membership",
            ),
            (
                cat_leisure.id,
                "expense",
                Decimal("420.0000"),
                today - timedelta(days=12),
                "Weekend mountain lodge dining",
            ),
        ]
        for c_id, f_type, amt, e_date, desc in entries:
            entry = CashflowEntryModel(
                account_id=checking.id,
                category_id=c_id,
                flow_type=f_type,
                amount=amt,
                currency="USD",
                entry_date=e_date,
                description=desc,
                is_recurring=True,
            )
            db.add(entry)
        await db.flush()

        print("Seeding Financial Goals...")
        goals = [
            FinancialGoalModel(
                name="6-Month Emergency Reserve",
                category="emergency_fund",
                target_amount=Decimal("45000.0000"),
                current_amount=Decimal("32500.0000"),
                currency="USD",
                target_date=today + timedelta(days=120),
                monthly_contribution=Decimal("1500.0000"),
                status="in_progress",
                notes="Liquid cash in Marcus HYSA earning 4.4% APY.",
            ),
            FinancialGoalModel(
                name="Mountain Retreat Cabin Down Payment",
                category="home_purchase",
                target_amount=Decimal("80000.0000"),
                current_amount=Decimal("46000.0000"),
                currency="USD",
                target_date=today + timedelta(days=450),
                monthly_contribution=Decimal("2000.0000"),
                status="in_progress",
                notes="20% deposit target for timber cabin in Pacific Northwest.",
            ),
            FinancialGoalModel(
                name="First Million Invested Net Worth",
                category="retirement",
                target_amount=Decimal("1000000.0000"),
                current_amount=Decimal("245000.0000"),
                currency="USD",
                target_date=today + timedelta(days=1825),
                monthly_contribution=Decimal("3500.0000"),
                status="in_progress",
                notes="Compounding broad-market equity and index fund holdings.",
            ),
        ]
        db.add_all(goals)
        await db.flush()

        print("Seeding 90 Days of Historical Snapshots for Charts...")
        # Synthesize realistic historical progression over past 90 days
        base_assets = Decimal("210000.0000")
        base_liab = Decimal("395000.0000")
        for day_offset in range(90, -1, -3):
            snap_date = today - timedelta(days=day_offset)
            progress_ratio = Decimal(90 - day_offset) / Decimal(90)

            # Asset growth with slight market variance
            market_fluctuation = Decimal(str(round((((day_offset % 7) - 3) * 450), 2)))
            sim_assets = base_assets + (Decimal("48000.0000") * progress_ratio) + market_fluctuation
            sim_liab = base_liab - (Decimal("9300.0000") * progress_ratio)
            sim_nw = sim_assets - sim_liab
            sim_liquid = Decimal("28000.0000") + (Decimal("13000.0000") * progress_ratio)

            snap = HistoricalSnapshotModel(
                snapshot_date=snap_date,
                total_assets=sim_assets.quantize(Decimal("0.0001")),
                total_liabilities=sim_liab.quantize(Decimal("0.0001")),
                net_worth=sim_nw.quantize(Decimal("0.0001")),
                liquid_assets=sim_liquid.quantize(Decimal("0.0001")),
                currency="USD",
            )
            db.add(snap)

        print("Seeding Initial System Notifications & Market Alerts...")
        now = datetime.now(UTC)
        notifs = [
            NotificationModel(
                title="هشدار نوسان بازار: بیت‌کوین (BTC)",
                message="قیمت بیت‌کوین با رشد ۷.۴٪ در ۲۴ ساعت گذشته به ۶۳,۴۰۰ دلار رسید. پیشنهاد می‌شود پورتفولیو را جهت بازتنظیم سود و کنترل ریسک ارزیابی فرمایید.",
                notification_type="ASSET_VOLATILITY",
                severity="warning",
                data={"symbol": "BTC", "price": "63400.00", "change_percent": 7.4, "action": "rebalance"},
                is_read=False,
                created_at=now - timedelta(minutes=45),
            ),
            NotificationModel(
                title="هشدار بازار انرژی: نفت خام برنت (BRENT)",
                message="قیمت هر بشکه نفت برنت به ۷۴.۵۰ دلار تغییر یافت. تحلیل تاثیر آن بر دارایی‌های صندوق و تورم جهانی پیشنهاد می‌شود.",
                notification_type="ASSET_VOLATILITY",
                severity="info",
                data={"symbol": "BRENT", "price": "74.50", "action": "analyze"},
                is_read=False,
                created_at=now - timedelta(hours=2),
            ),
            NotificationModel(
                title="تحقق هدف مالی: صندوق ذخیره اضطراری",
                message="تبریک! هدف مالی «صندوق ذخیره اضطراری ۶ ماهه» به بیش از ۷۲٪ تحقق رسید و در مسیر دستیابی کامل قرار دارد.",
                notification_type="GOAL_REACHED",
                severity="success",
                data={"goal_name": "6-Month Emergency Reserve", "percent": 72.2},
                is_read=True,
                created_at=now - timedelta(days=1),
            ),
        ]
        db.add_all(notifs)

        await db.commit()
        print("[SUCCESS] Realistic financial seed data successfully committed!")


if __name__ == "__main__":
    asyncio.run(seed_data())
