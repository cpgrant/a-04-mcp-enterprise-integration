"""Repeatable AI-A04 assessment performance benchmark."""

import asyncio
import json
import math
import statistics
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from unittest.mock import patch

import src.agents.enterprise_assessment as agent
import src.client.enterprise_mcp as mcp_module

from src.agents.contracts import AssessmentRequest
from src.observability.events import EventType


WARMUPS = 2
RUNS = 10
measurements = []
current_timing = {}


class TimedMCPClient(mcp_module.EnterpriseMCPClient):
    async def __aenter__(self):
        start = perf_counter()
        result = await super().__aenter__()
        current_timing["startup_ms"] = (
            perf_counter() - start
        ) * 1000
        return result

    async def discover_tools(self):
        start = perf_counter()
        result = await super().discover_tools()
        current_timing["discovery_ms"] = (
            perf_counter() - start
        ) * 1000
        return result


async def measure():
    request = AssessmentRequest(
        customer_code="C001",
        as_of="2026-11-06",
    )

    for index in range(WARMUPS + RUNS):
        events = []
        current_timing.clear()

        with (
            patch.object(
                agent, "EnterpriseMCPClient", TimedMCPClient
            ),
            patch.object(agent, "emit_event", events.append),
            patch.object(mcp_module, "emit_event", events.append),
        ):
            result = await agent.assess_enterprise(request)

        completed = [
            e for e in events
            if e.event_type == EventType.ASSESSMENT_COMPLETED
        ]
        tools = [
            e for e in events
            if e.event_type == EventType.TOOL_COMPLETED
        ]

        if result.status != "completed":
            raise RuntimeError(
                f"Benchmark run {index} failed: {result.errors}"
            )

        if len(completed) != 1 or len(tools) != 3:
            raise RuntimeError(
                "Incomplete observability events"
            )

        record = {
            "assessment_ms": completed[0].duration_ms,
            "startup_ms": current_timing["startup_ms"],
            "discovery_ms": current_timing["discovery_ms"],
            "tool_total_ms": sum(
                e.duration_ms for e in tools
            ),
            "tool_calls": {
                e.tool_name: e.duration_ms for e in tools
            },
        }

        phase = "warmup" if index < WARMUPS else "measured"
        print(
            f"{phase:8} {index + 1:02} "
            f"assessment={record['assessment_ms']:.2f} ms "
            f"startup={record['startup_ms']:.2f} ms"
        )

        if index >= WARMUPS:
            measurements.append(record)


def stats(values):
    ordered = sorted(values)
    return {
        "min_ms": min(ordered),
        "median_ms": statistics.median(ordered),
        "p95_ms": ordered[math.ceil(0.95 * len(ordered)) - 1],
        "max_ms": max(ordered),
        "mean_ms": statistics.mean(ordered),
    }


asyncio.run(measure())

summary = {
    key: stats([r[key] for r in measurements])
    for key in (
        "assessment_ms",
        "startup_ms",
        "discovery_ms",
        "tool_total_ms",
    )
}

report = {
    "project": "AI-A04",
    "benchmark": "Day 4 enterprise assessment",
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "warmups": WARMUPS,
    "measured_runs": RUNS,
    "customer": "synthetic C001",
    "summary": summary,
    "runs": measurements,
}

path = Path("results/day4_benchmark.json")
path.write_text(json.dumps(report, indent=2) + "\n")

print("\n=== Benchmark Summary ===")
for name, metric in summary.items():
    print(
        f"{name:18} "
        f"median={metric['median_ms']:.2f} ms "
        f"p95={metric['p95_ms']:.2f} ms"
    )

print(f"\nSaved: {path}")
print("PASS: Day 4 performance benchmark")
