"""Tests for AI-A04 observability contracts."""

import json

import pytest
from pydantic import ValidationError

from src.observability.events import (
    EventOutcome,
    EventType,
    ObservabilityEvent,
    new_assessment_id,
    new_trace_id,
)


def make_event(**overrides):
    data = {
        "trace_id": new_trace_id(),
        "assessment_id": new_assessment_id(),
        "event_type": EventType.TOOL_COMPLETED,
        "outcome": EventOutcome.SUCCESS,
        "component": "mcp_client",
        "operation": "call_tool",
        "tool_name": "get_customer_db",
        "duration_ms": 12.5,
    }

    data.update(overrides)
    return ObservabilityEvent(**data)


def test_event_creation():
    event = make_event()

    assert event.event_id
    assert event.trace_id
    assert event.assessment_id
    assert event.duration_ms == 12.5


def test_json_serialization():
    event = make_event()

    payload = json.loads(event.model_dump_json())

    assert payload["event_type"] == "tool_completed"
    assert payload["outcome"] == "success"
    assert payload["tool_name"] == "get_customer_db"


def test_unique_correlation_ids():
    assert new_trace_id() != new_trace_id()
    assert new_assessment_id() != new_assessment_id()


def test_negative_duration_rejected():
    with pytest.raises(ValidationError):
        make_event(duration_ms=-1)


def test_invalid_outcome_rejected():
    with pytest.raises(ValidationError):
        make_event(outcome="unknown")
