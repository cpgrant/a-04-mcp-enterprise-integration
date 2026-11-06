"""Simulated partial-failure scenarios for the AI-A04 agent."""

import asyncio

import pytest

import src.agents.enterprise_assessment as agent_module
from src.agents.contracts import AssessmentRequest


class FakeMCPClient:
    """Controlled MCP client for failure simulation."""

    missing_tools = set()
    failing_tools = set()

    def __init__(self, role="reader"):
        self.role = role

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def discover_tools(self):
        return [
            name for name in agent_module.REQUIRED_TOOLS
            if name not in self.missing_tools
        ]

    async def call(self, tool_name, arguments):
        if tool_name in self.failing_tools:
            raise RuntimeError("Simulated enterprise service failure")

        if tool_name == "get_customer_db":
            return {
                "found": True,
                "customer": {
                    "customer_code": "C001",
                    "customer_name": "ACME Corporation",
                },
                "source": "simulated.crm",
            }

        if tool_name == "get_customer_orders_db":
            return {
                "count": 2,
                "orders": [],
                "source": "simulated.erp",
            }

        if tool_name == "get_customer_financial_summary_db":
            return {
                "total_outstanding": "1000.00",
                "overdue_balance": "250.00",
                "overdue_invoice_count": 1,
                "source": "simulated.finance",
            }

        raise ValueError(f"Unexpected tool: {tool_name}")


def assess():
    return asyncio.run(
        agent_module.assess_enterprise(
            AssessmentRequest(
                customer_code="C001",
                as_of="2026-11-06",
            )
        )
    )


def test_missing_finance_tool(monkeypatch):
    class MissingFinance(FakeMCPClient):
        missing_tools = {"get_customer_financial_summary_db"}

    monkeypatch.setattr(
        agent_module,
        "EnterpriseMCPClient",
        MissingFinance,
    )

    result = assess()

    assert result.status == "partial"
    assert len(result.evidence) == 2
    assert any("unavailable" in error for error in result.errors)


def test_finance_service_failure(monkeypatch):
    class FailingFinance(FakeMCPClient):
        failing_tools = {"get_customer_financial_summary_db"}

    monkeypatch.setattr(
        agent_module,
        "EnterpriseMCPClient",
        FailingFinance,
    )

    result = assess()

    assert result.status == "partial"
    assert len(result.evidence) == 2
    assert any(
        "get_customer_financial_summary_db failed" in error
        for error in result.errors
    )


def test_all_services_healthy(monkeypatch):
    monkeypatch.setattr(
        agent_module,
        "EnterpriseMCPClient",
        FakeMCPClient,
    )

    result = assess()

    assert result.status == "completed"
    assert len(result.evidence) == 3
    assert len(result.errors) == 0
