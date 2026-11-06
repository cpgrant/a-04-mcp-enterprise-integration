"""Structured operational event emission."""

import sys

from src.observability.events import ObservabilityEvent


def emit_event(event: ObservabilityEvent) -> None:
    """Write one JSON event to stderr without business payloads."""
    print(event.model_dump_json(), file=sys.stderr, flush=True)
