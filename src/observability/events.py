"""Typed observability events for AI-A04."""

from datetime import datetime, timezone
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field


class EventType(str, Enum):
    ASSESSMENT_STARTED = "assessment_started"
    ASSESSMENT_COMPLETED = "assessment_completed"
    TOOL_STARTED = "tool_started"
    TOOL_COMPLETED = "tool_completed"
    TOOL_FAILED = "tool_failed"


class EventOutcome(str, Enum):
    STARTED = "started"
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    DENIED = "denied"


class ObservabilityEvent(BaseModel):
    """Privacy-conscious structured execution event."""

    event_id: str = Field(
        default_factory=lambda: str(uuid4())
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    trace_id: str
    assessment_id: str

    event_type: EventType
    outcome: EventOutcome

    component: str
    operation: str

    tool_name: str | None = None
    duration_ms: float | None = Field(
        default=None,
        ge=0,
    )

    error_type: str | None = None


def new_trace_id() -> str:
    return uuid4().hex


def new_assessment_id() -> str:
    return str(uuid4())
