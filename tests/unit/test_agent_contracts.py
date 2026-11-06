"""Tests for AI-A04 agent contracts."""

import pytest
from pydantic import ValidationError

from src.agents.contracts import (
    AssessmentRequest,
    BusinessObservation,
    EnterpriseAssessment,
    ToolEvidence,
)


def test_assessment_request():
    request = AssessmentRequest(
        customer_code="C001",
        as_of="2026-11-06",
    )

    assert request.customer_code == "C001"


def test_invalid_customer_code():
    with pytest.raises(ValidationError):
        AssessmentRequest(
            customer_code="../invalid",
            as_of="2026-11-06",
        )


def test_business_observation():
    observation = BusinessObservation(
        category="finance",
        severity="warning",
        finding="Outstanding invoices detected",
        evidence_tools=[
            "get_customer_financial_summary_db"
        ],
    )

    assert observation.severity == "warning"


def test_enterprise_assessment():
    assessment = EnterpriseAssessment(
        customer_code="C001",
        customer_name="ACME Corporation",
        as_of="2026-11-06",
        status="completed",
        observations=[],
        recommendations=[],
        evidence=[
            ToolEvidence(
                tool_name="get_customer_db",
                arguments={"customer_code": "C001"},
                source="postgresql.crm.customers",
                result={"found": True},
            )
        ],
    )

    assert assessment.status == "completed"
    assert len(assessment.evidence) == 1
