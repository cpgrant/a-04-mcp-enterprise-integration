"""Validate correlation context isolation and restoration."""

import asyncio

from src.observability.context import (
    correlation_scope,
    get_correlation_ids,
)


def test_scope_restores_previous_state():
    assert get_correlation_ids() is None

    with correlation_scope("trace-1", "assessment-1"):
        assert get_correlation_ids() == (
            "trace-1", "assessment-1"
        )

    assert get_correlation_ids() is None


def test_nested_scope_restores_parent():
    with correlation_scope("outer", "assessment-outer"):
        with correlation_scope("inner", "assessment-inner"):
            assert get_correlation_ids() == (
                "inner", "assessment-inner"
            )

        assert get_correlation_ids() == (
            "outer", "assessment-outer"
        )


def test_concurrent_assessments_isolated():
    async def worker(trace_id):
        with correlation_scope(trace_id, "assessment"):
            await asyncio.sleep(0)
            return get_correlation_ids()

    async def run():
        return await asyncio.gather(
            worker("trace-A"),
            worker("trace-B"),
        )

    results = asyncio.run(run())

    assert results == [
        ("trace-A", "assessment"),
        ("trace-B", "assessment"),
    ]
