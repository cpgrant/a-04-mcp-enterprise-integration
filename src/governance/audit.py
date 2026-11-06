"""Structured local audit events for AI-A04."""

import json
import logging
import sys
from datetime import datetime, timezone


logger = logging.getLogger("ai_a04.audit")
logger.setLevel(logging.INFO)
logger.propagate = False

if not logger.handlers:
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)


def record_event(tool: str, role: str, outcome: str):
    """Emit a structured audit event without tool arguments."""

    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": "mcp_tool_execution",
        "tool": tool,
        "role": role,
        "outcome": outcome,
    }

    logger.info(json.dumps(event))
