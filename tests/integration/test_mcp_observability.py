"""MCP client instrumentation integration tests."""

import asyncio

from src.client.enterprise_mcp import EnterpriseMCPClient
from src.observability.events import EventType


async def successful_call():
    events = []

    async with EnterpriseMCPClient(
        trace_id="trace-test-001",
        assessment_id="assessment-test-001",
        event_sink=events.append,
    ) as client:
        result = await client.call(
            "get_customer_db",
            {"customer_code": "C001"},
        )

    return result, events


def test_successful_tool_events():
    result, events = asyncio.run(successful_call())

    assert result["found"] is True
    assert len(events) == 2

    assert events[0].event_type == EventType.TOOL_STARTED
    assert events[1].event_type == EventType.TOOL_COMPLETED

    assert events[1].duration_ms >= 0


def test_event_correlation():
    _, events = asyncio.run(successful_call())

    assert all(
        event.trace_id == "trace-test-001"
        for event in events
    )

    assert all(
        event.assessment_id == "assessment-test-001"
        for event in events
    )


async def denied_call():
    events = []

    async with EnterpriseMCPClient(
        role="blocked",
        event_sink=events.append,
    ) as client:
        try:
            await client.call(
                "get_customer_db",
                {"customer_code": "C001"},
            )
        except RuntimeError:
            pass
        else:
            raise AssertionError("Blocked role unexpectedly succeeded")

    return events


def test_failed_tool_event():
    events = asyncio.run(denied_call())

    assert len(events) == 2
    assert events[1].event_type == EventType.TOOL_FAILED
    assert events[1].error_type == "RuntimeError"
    assert events[1].duration_ms >= 0
