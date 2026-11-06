"""Run the AI-A04 enterprise assessment agent."""

import asyncio

from src.agents.contracts import AssessmentRequest
from src.agents.enterprise_assessment import assess_enterprise


async def main():
    request = AssessmentRequest(
        customer_code="C001",
        as_of="2026-11-06",
    )

    result = await assess_enterprise(request)

    print("\n=== AI-A04 Enterprise Assessment ===")
    print(result.model_dump_json(indent=2))

    assert result.status == "completed"
    assert result.customer_name == "ACME Corporation"
    assert len(result.evidence) == 3

    print("\nPASS: Enterprise assessment agent")


if __name__ == "__main__":
    asyncio.run(main())
