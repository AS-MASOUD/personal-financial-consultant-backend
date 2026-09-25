# Personal Finance & Investment Management Platform — Backend

A production-grade Modular Monolith built with FastAPI, SQLAlchemy 2.0, PostgreSQL, Redis, and Alembic following Clean/Hexagonal Architecture principles.

## Structure

- `src/app/`: Core application lifecycle, configuration, database session, middleware, and observability.
- `src/modules/`: Domain modules with explicit Hexagonal separation:
  - `accounts`: Bank, brokerage, and cash accounts.
  - `assets`: Equities, commodities, real estate, crypto holdings.
  - `portfolio`: Positions, cost-basis calculation, valuation.
  - `transactions`: Immutable transaction ledger and cash operations.
  - `liabilities`: Loans, mortgages, debt tracking, amortization.
  - `cashflow`: Income, expense tracking, and category budgeting.
  - `goals`: Financial targets and milestone projections.
  - `market_data`: Price quote ingestion and provider abstractions.
  - `analytics`: Historical snapshots, net worth trends, allocation analysis.
  - `scenarios`: Deterministic what-if simulations and stress testing.
  - `ai`: Financial reasoning engine with safe, controlled tool calling.
- `src/shared/`: Shared domain models (`Money`, `Currency`), utilities, and error types.
- `tests/`: Comprehensive unit, integration, and API test suites.

## Local Development

```bash
# Setup virtual environment and dependencies
uv venv
uv pip install -e ".[dev]"

# Run tests
pytest

# Run linter and type checker
ruff check .
pyright

# Run API server
uvicorn src.main:app --reload --port 8000
```
