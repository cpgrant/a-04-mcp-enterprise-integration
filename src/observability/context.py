"""Execution-scoped correlation identifiers."""

from contextlib import contextmanager
from contextvars import ContextVar


_current_ids: ContextVar[tuple[str, str] | None] = (
    ContextVar("a04_correlation_ids", default=None)
)


def get_correlation_ids() -> tuple[str, str] | None:
    """Return active trace and assessment IDs, if any."""
    return _current_ids.get()


@contextmanager
def correlation_scope(trace_id: str, assessment_id: str):
    """Bind IDs for the current async execution context."""
    token = _current_ids.set((trace_id, assessment_id))
    try:
        yield
    finally:
        _current_ids.reset(token)
