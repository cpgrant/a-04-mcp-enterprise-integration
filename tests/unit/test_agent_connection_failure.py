"""MCP transport failure tests for AI-A04."""

import asyncio

import src.agents.enterprise_assessment as agent_module
from src.agents.contracts import AssessmentRequest


class UnavailableMCPClient:
    def __init__(self, role="reader"):
        self.role = role

    async def __aenter__(self):
        raise OSError("Simulated unavailable MCP server")

    async def __aexit__(self, exc_type, exc, tb):
        return False


class GroupFailureMCPClient(UnavailableMCPClient):
    async def __aenter__(self):
        raise ExceptionGroup(
            "MCP startup failed",
            [OSError("Server executable unavailable")],
        )


def run_assessment():
    return asyncio.run(
        agent_module.assess_enterprise(
            AssessmentRequest(
                customer_code="C001",
                as_of="2026-11-06",
            )
        )
    )


def test_mcp_server_unavailable(monkeypatch):
    monkeypatch.setattr(
        agent_module,
        "EnterpriseMCPClient",
        UnavailableMCPClient,
    )

    result = run_assessment()

    assert result.status == "failed"
    assert len(result.evidence) == 0
    assert any(
        "MCP connection failed" in error
        for error in result.errors
    )


def test_mcp_startup_exception_group(monkeypatch):
    monkeypatch.setattr(
        agent_module,
        "EnterpriseMCPClient",
        GroupFailureMCPClient,
    )

    result = run_assessment()

    assert result.status == "failed"
    assert len(result.evidence) == 0
    assert result.errors
