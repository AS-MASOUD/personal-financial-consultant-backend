from decimal import Decimal

import pytest
from httpx import ASGITransport, AsyncClient

from src.main import app


@pytest.mark.asyncio
async def test_overview_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/analytics/overview")
        assert response.status_code == 200
        data = response.json()
        assert "net_worth" in data
        assert "total_assets" in data
        assert "liquid_cash" in data
        assert "asset_allocation" in data
        assert len(data["asset_allocation"]) > 0
        assert "attention_items" in data


@pytest.mark.asyncio
async def test_accounts_endpoints():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # List
        response = await client.get("/api/v1/accounts")
        assert response.status_code == 200
        accounts = response.json()
        assert len(accounts) >= 4

        # Create
        create_payload = {
            "name": "Test Vault",
            "account_type": "savings",
            "institution": "Ally",
            "currency": "USD",
            "initial_balance": "5000.00",
            "account_number_mask": "*9999",
        }
        res_create = await client.post("/api/v1/accounts", json=create_payload)
        assert res_create.status_code == 201
        acc_data = res_create.json()
        assert acc_data["name"] == "Test Vault"
        acc_id = acc_data["id"]

        # Delete
        res_del = await client.delete(f"/api/v1/accounts/{acc_id}")
        assert res_del.status_code == 204


@pytest.mark.asyncio
async def test_assets_and_positions():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res_assets = await client.get("/api/v1/assets")
        assert res_assets.status_code == 200
        assets = res_assets.json()
        assert len(assets) >= 7

        res_positions = await client.get("/api/v1/assets/positions")
        assert res_positions.status_code == 200
        positions = res_positions.json()
        assert len(positions) >= 7
        assert "unrealized_pnl" in positions[0]
        assert "current_value" in positions[0]


@pytest.mark.asyncio
async def test_liabilities_and_schedule():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/liabilities")
        assert res.status_code == 200
        liabilities = res.json()
        assert len(liabilities) >= 3

        # Schedule calculation
        res_sched = await client.get(
            "/api/v1/liabilities/calculate-schedule?principal=10000&interest_rate=5.0&term_months=12"
        )
        assert res_sched.status_code == 200
        schedule = res_sched.json()
        assert len(schedule) == 12
        assert Decimal(str(schedule[-1]["remaining_balance"])) == Decimal("0.00")


@pytest.mark.asyncio
async def test_cashflow_summary():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/cashflow/summary")
        assert res.status_code == 200
        data = res.json()
        assert "total_income" in data
        assert "total_expenses" in data
        assert "savings_rate_percent" in data


@pytest.mark.asyncio
async def test_scenarios_simulation():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        sim_payload = {
            "name": "Promotion + Loan Payoff",
            "horizon_months": 24,
            "monthly_income_delta": "1500.00",
            "monthly_expense_delta": "-300.00",
            "asset_growth_rate_annual": "8.0",
            "new_loan_amount": "0",
            "one_time_windfall": "10000.00",
        }
        res = await client.post("/api/v1/scenarios/simulate", json=sim_payload)
        assert res.status_code == 200
        data = res.json()
        assert len(data["monthly_projections"]) == 24
        assert Decimal(str(data["net_worth_delta"])) > 0


@pytest.mark.asyncio
async def test_ai_chat():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        chat_payload = {
            "content": "Explain my current net worth and portfolio allocation.",
        }
        res = await client.post("/api/v1/ai/chat", json=chat_payload)
        assert res.status_code == 201
        data = res.json()
        assert data["role"] == "assistant"
        assert "Net Worth" in data["content"] or "Financial" in data["content"]
