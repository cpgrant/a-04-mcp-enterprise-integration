"""Reusable, observable local MCP client for enterprise agents."""

import json
import os
import sys
from time import perf_counter

from mcp import Client, StdioServerParameters

from src.observability.context import get_correlation_ids
from src.observability.emitter import emit_event
from src.observability.events import (
    EventOutcome,
    EventType,
    ObservabilityEvent,
    new_assessment_id,
    new_trace_id,
)


class EnterpriseMCPClient:
    """Local MCP client with tool-level observability."""

    def __init__(
        self,
        role: str = "reader",
        trace_id: str | None = None,
        assessment_id: str | None = None,
        event_sink=None,
    ):
        self.role = role
        current = get_correlation_ids()
        self.trace_id = trace_id or (
            current[0] if current else new_trace_id()
        )
        self.assessment_id = assessment_id or (
            current[1] if current else new_assessment_id()
        )
        self.event_sink = event_sink or emit_event
        self.client = None

    def _record(
        self,
        event_type: EventType,
        outcome: EventOutcome,
        tool_name: str,
        duration_ms: float | None = None,
        error_type: str | None = None,
    ) -> None:
        event = ObservabilityEvent(
            trace_id=self.trace_id,
            assessment_id=self.assessment_id,
            event_type=event_type,
            outcome=outcome,
            component="mcp_client",
            operation="call_tool",
            tool_name=tool_name,
            duration_ms=duration_ms,
            error_type=error_type,
        )
        self.event_sink(event)

    async def __aenter__(self):
        server = StdioServerParameters(
            command=sys.executable,
            args=["-m", "src.server.main"],
            env={
                **os.environ,
                "AI_A04_ROLE": self.role,
            },
        )

        self.client = Client(server)
        await self.client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return await self.client.__aexit__(exc_type, exc, tb)

    async def discover_tools(self) -> list[str]:
        """Discover MCP tool names."""
        result = await self.client.list_tools()
        return [tool.name for tool in result.tools]

    async def call(
        self,
        tool_name: str,
        arguments: dict,
    ) -> dict:
        """Invoke an MCP tool with measured execution duration."""

        self._record(
            EventType.TOOL_STARTED,
            EventOutcome.STARTED,
            tool_name,
        )

        started = perf_counter()

        try:
            result = await self.client.call_tool(
                tool_name,
                arguments,
            )

            if result.is_error:
                raise RuntimeError(
                    f"MCP tool {tool_name} failed: "
                    f"{result.content}"
                )

            if result.structured_content is not None:
                data = result.structured_content
            else:
                data = None

                for block in result.content:
                    if block.type == "text":
                        data = json.loads(block.text)
                        break

            if not isinstance(data, dict):
                raise ValueError(
                    "Expected JSON object from MCP tool"
                )

        except Exception as exc:
            elapsed_ms = (perf_counter() - started) * 1000

            self._record(
                EventType.TOOL_FAILED,
                EventOutcome.FAILED,
                tool_name,
                duration_ms=elapsed_ms,
                error_type=type(exc).__name__,
            )
            raise

        elapsed_ms = (perf_counter() - started) * 1000

        self._record(
            EventType.TOOL_COMPLETED,
            EventOutcome.SUCCESS,
            tool_name,
            duration_ms=elapsed_ms,
        )

        return data
