from typing import Any

from src.modules.ai.domain.interfaces import IAIProvider


class MockAIProvider(IAIProvider):
    """
    High-fidelity deterministic AI financial reasoning engine.
    Interprets calculated metrics, detects imbalances, and formulates
    actionable insights based strictly on verified domain calculations.
    """

    async def generate_response(
        self,
        messages: list[dict[str, str]],
        tools_context: dict[str, Any] | None = None,
    ) -> str:
        last_message = messages[-1]["content"].lower() if messages else ""
        context = tools_context or {}

        net_worth = context.get("net_worth", "0.00")
        total_assets = context.get("total_assets", "0.00")
        total_liabilities = context.get("total_liabilities", "0.00")
        liquid_cash = context.get("liquid_cash", "0.00")
        monthly_free_cashflow = context.get("monthly_free_cashflow", "0.00")
        allocations = context.get("asset_allocation", [])

        if (
            "net worth" in last_message
            or "position" in last_message
            or "where am i" in last_message
        ):
            return (
                f"### Financial Position Overview\n\n"
                f"- **Current Net Worth:** ${float(net_worth):,.2f}\n"
                f"- **Total Assets:** ${float(total_assets):,.2f}\n"
                f"- **Total Liabilities:** ${float(total_liabilities):,.2f}\n"
                f"- **Liquid Cash Reserves:** ${float(liquid_cash):,.2f}\n\n"
                f"Your balance sheet reflects a debt-to-asset ratio of "
                f"{(float(total_liabilities) / float(total_assets) * 100) if float(total_assets) > 0 else 0:.1f}%. "
                f"Your liquid cash constitutes "
                f"{(float(liquid_cash) / float(total_assets) * 100) if float(total_assets) > 0 else 0:.1f}% "
                f"of overall holdings."
            )

        if "cash flow" in last_message or "income" in last_message or "surplus" in last_message:
            return (
                f"### Monthly Cash Flow Assessment\n\n"
                f"Based on recent transactions, your **monthly free cash flow** is **${float(monthly_free_cashflow):,.2f}** "
                f"after accounting for living expenses and debt service obligations.\n\n"
                f"**Recommendation:** With a positive cashflow surplus, consider directing 60% of free funds toward high-interest liabilities or priority financial goals, while maintaining liquid buffers."
            )

        if (
            "concentration" in last_message
            or "allocation" in last_message
            or "where is my money" in last_message
        ):
            alloc_summary = "\n".join(
                [
                    f"- **{a.get('category')}:** {a.get('percentage', 0):.1f}% (${a.get('amount', 0):,.2f})"
                    for a in allocations
                ]
            )
            return (
                f"### Portfolio Allocation Breakdown\n\n"
                f"{alloc_summary}\n\n"
                f"Maintaining a diversified split across uncorrelated asset classes helps buffer against market volatility."
            )

        if "debt" in last_message or "loan" in last_message or "owe" in last_message:
            return (
                f"### Debt & Obligations Diagnostic\n\n"
                f"Your total outstanding debt stands at **${float(total_liabilities):,.2f}**.\n\n"
                f"Prioritize debts by interest rate (the avalanche method) to minimize cumulative borrowing costs over time."
            )

        # Default contextual synthesis
        return (
            f"### Financial Command Center Intelligence\n\n"
            f"Here is a summary of your financial health:\n"
            f"- **Net Worth:** ${float(net_worth):,.2f}\n"
            f"- **Liquid Cash Buffer:** ${float(liquid_cash):,.2f}\n"
            f"- **Monthly Free Cash Flow:** ${float(monthly_free_cashflow):,.2f}\n"
            f"- **Total Outstanding Liabilities:** ${float(total_liabilities):,.2f}\n\n"
            f"You can ask me to analyze specific scenarios, review portfolio concentration, or explain repayment timelines."
        )
