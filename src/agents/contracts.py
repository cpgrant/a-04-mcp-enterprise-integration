"""Typed contracts for AI-A04 enterprise agents."""

from typing import Any, Literal

from pydantic import BaseModel, Field


class AssessmentRequest(BaseModel):
    customer_code: str = Field(
        min_length=1,
        max_length=20,
        pattern=r"^[A-Z0-9-]+$",
    )
    as_of: str = Field(
        pattern=r"^\d{4}-\d{2}-\d{2}$",
    )


class ToolEvidence(BaseModel):
    tool_name: str
    arguments: dict[str, Any]
    source: str
    result: dict[str, Any]


class BusinessObservation(BaseModel):
    category: Literal["crm", "erp", "finance"]
    severity: Literal["info", "warning", "critical"]
    finding: str
    evidence_tools: list[str]


class EnterpriseAssessment(BaseModel):
    customer_code: str
    customer_name: str
    as_of: str
    status: Literal["completed", "partial", "failed"]
    observations: list[BusinessObservation]
    recommendations: list[str]
    evidence: list[ToolEvidence]
    errors: list[str] = Field(default_factory=list)
