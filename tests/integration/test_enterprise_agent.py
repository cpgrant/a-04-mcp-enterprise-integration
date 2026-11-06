"""Enterprise assessment agent integration tests."""

import asyncio

import pytest

from src.agents.contracts import AssessmentRequest
from src.agents.enterprise_assessment import assess_enterprise


def run_assessment(customer="C001", role="reader"):
    return asyncio.run(
        assess_enterprise(
            AssessmentRequest(
                customer_code=customer,
                as_of="2026-11-06",
            ),
            role=role,
        )
    )


def test_successful_enterprise_assessment():
    result = run_assessment()

    assert result.status == "completed"
    assert result.customer_name == "ACME Corporation"
    assert len(result.evidence) == 3
    assert len(result.errors) == 0


def test_financial_evidence():
    result = run_assessment()

    findings = [o.finding for o in result.observations]

    assert any("7,612.50" in f for f in findings)
    assert any("6,527.50" in f for f in findings)

    assert any(
        o.category == "finance"
        and o.severity == "critical"
        for o in result.observations
    )


def test_unknown_customer():
    result = run_assessment(customer="UNKNOWN")

    assert result.status == "failed"
    assert result.customer_name == "Unknown"


def test_blocked_agent():
    result = run_assessment(role="blocked")

    assert result.status == "failed"
    assert len(result.errors) > 0


def test_invalid_calendar_date():
    with pytest.raises(ValueError):
        asyncio.run(
            assess_enterprise(
                AssessmentRequest(
                    customer_code="C001",
                    as_of="2026-02-30",
                )
            )
        )
