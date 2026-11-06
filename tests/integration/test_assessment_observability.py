"""End-to-end assessment correlation validation."""

import asyncio

import src.agents.enterprise_assessment as agent
import src.client.enterprise_mcp as mcp_client

from src.agents.contracts import AssessmentRequest
from src.observability.events import EventType


def test_assessment_and_tool_correlation(monkeypatch):
    events = []

    monkeypatch.setattr(agent, "emit_event", events.append)
    monkeypatch.setattr(mcp_client, "emit_event", events.append)

    result = asyncio.run(
        agent.assess_enterprise(
            AssessmentRequest(
                customer_code="C001",
                as_of="2026-11-06",
            )
        )
    )

    assert result.status == "completed"

    assert len(events) == 8

    trace_ids = {event.trace_id for event in events}
    assessment_ids = {
        event.assessment_id for event in events
    }

    assert len(trace_ids) == 1
    assert len(assessment_ids) == 1

    assert events[0].event_type == EventType.ASSESSMENT_STARTED
    assert events[-1].event_type == EventType.ASSESSMENT_COMPLETED

    completed_tools = [
        event for event in events
        if event.event_type == EventType.TOOL_COMPLETED
    ]

    assert len(completed_tools) == 3
    assert all(
        event.duration_ms is not None
        for event in completed_tools
    )

    assert events[-1].duration_ms >= 0
