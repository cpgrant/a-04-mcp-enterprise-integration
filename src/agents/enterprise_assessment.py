"""Deterministic, evidence-backed enterprise assessment agent."""

from datetime import date
from time import perf_counter
from decimal import Decimal

from src.agents.contracts import (
    AssessmentRequest,
    BusinessObservation,
    EnterpriseAssessment,
    ToolEvidence,
)
from src.client.enterprise_mcp import EnterpriseMCPClient

from src.observability.context import correlation_scope
from src.observability.emitter import emit_event
from src.observability.events import (
    EventOutcome,
    EventType,
    ObservabilityEvent,
    new_assessment_id,
    new_trace_id,
)



REQUIRED_TOOLS = (
    "get_customer_db",
    "get_customer_orders_db",
    "get_customer_financial_summary_db",
)


async def _assess_connected(
    request: AssessmentRequest,
    role: str = "reader",
) -> EnterpriseAssessment:
    """Assess a customer using governed MCP enterprise tools."""

    # Reject invalid calendar dates before invoking any tools.
    date.fromisoformat(request.as_of)

    evidence = []
    observations = []
    recommendations = []
    errors = []
    results = {}

    async with EnterpriseMCPClient(role=role) as client:
        available = set(await client.discover_tools())

        plan = [
            ("get_customer_db", {
                "customer_code": request.customer_code,
            }),
            ("get_customer_orders_db", {
                "customer_code": request.customer_code,
                "limit": 20,
            }),
            ("get_customer_financial_summary_db", {
                "customer_code": request.customer_code,
                "as_of": request.as_of,
            }),
        ]

        for tool_name, arguments in plan:
            if tool_name not in available:
                errors.append(f"Required tool unavailable: {tool_name}")
                continue

            try:
                result = await client.call(tool_name, arguments)

                results[tool_name] = result

                evidence.append(
                    ToolEvidence(
                        tool_name=tool_name,
                        arguments=arguments,
                        source=result.get("source", "unknown"),
                        result=result,
                    )
                )
            except Exception as exc:
                errors.append(
                    f"{tool_name} failed: {type(exc).__name__}"
                )

    customer_result = results.get("get_customer_db")

    if not customer_result or not customer_result.get("found"):
        errors.append("Customer could not be verified")

        return EnterpriseAssessment(
            customer_code=request.customer_code,
            customer_name="Unknown",
            as_of=request.as_of,
            status="failed",
            observations=[],
            recommendations=[],
            evidence=evidence,
            errors=errors,
        )

    customer_name = customer_result["customer"]["customer_name"]

    observations.append(
        BusinessObservation(
            category="crm",
            severity="info",
            finding=f"Customer verified: {customer_name}.",
            evidence_tools=["get_customer_db"],
        )
    )

    orders = results.get("get_customer_orders_db")

    if orders is not None:
        count = orders["count"]

        observations.append(
            BusinessObservation(
                category="erp",
                severity="info",
                finding=f"{count} customer orders returned.",
                evidence_tools=["get_customer_orders_db"],
            )
        )

    finance = results.get("get_customer_financial_summary_db")

    if finance is not None:
        outstanding = Decimal(finance["total_outstanding"])
        overdue = Decimal(finance["overdue_balance"])
        overdue_count = finance["overdue_invoice_count"]

        observations.append(
            BusinessObservation(
                category="finance",
                severity="warning" if outstanding > 0 else "info",
                finding=(
                    f"Outstanding balance: EUR {outstanding:,.2f}."
                ),
                evidence_tools=[
                    "get_customer_financial_summary_db"
                ],
            )
        )

        if overdue > 0:
            observations.append(
                BusinessObservation(
                    category="finance",
                    severity="critical",
                    finding=(
                        f"Overdue balance: EUR {overdue:,.2f} "
                        f"across {overdue_count} invoices."
                    ),
                    evidence_tools=[
                        "get_customer_financial_summary_db"
                    ],
                )
            )

            recommendations.append(
                "Review overdue invoices with the finance team "
                "and confirm the customer's payment position."
            )

        if outstanding > 0:
            recommendations.append(
                "Review customer credit exposure before "
                "making new financial commitments."
            )

    if orders is not None and orders["count"] > 0:
        recommendations.append(
            "Review open orders and fulfillment commitments "
            "with operations."
        )

    return EnterpriseAssessment(
        customer_code=request.customer_code,
        customer_name=customer_name,
        as_of=request.as_of,
        status="partial" if errors else "completed",
        observations=observations,
        recommendations=recommendations,
        evidence=evidence,
        errors=errors,
    )




async def assess_enterprise(
    request: AssessmentRequest,
    role: str = "reader",
) -> EnterpriseAssessment:
    """Run and observe one enterprise assessment."""

    date.fromisoformat(request.as_of)

    trace_id = new_trace_id()
    assessment_id = new_assessment_id()
    started = perf_counter()

    def record(event_type, outcome, duration_ms=None, error_type=None):
        emit_event(
            ObservabilityEvent(
                trace_id=trace_id,
                assessment_id=assessment_id,
                event_type=event_type,
                outcome=outcome,
                component="assessment_agent",
                operation="assess_enterprise",
                duration_ms=duration_ms,
                error_type=error_type,
            )
        )

    record(EventType.ASSESSMENT_STARTED, EventOutcome.STARTED)

    with correlation_scope(trace_id, assessment_id):
        try:
            result = await _assess_connected(request, role=role)

        except (
            OSError,
            TimeoutError,
            ConnectionError,
            ExceptionGroup,
        ) as exc:
            result = EnterpriseAssessment(
                customer_code=request.customer_code,
                customer_name="Unknown",
                as_of=request.as_of,
                status="failed",
                observations=[],
                recommendations=[],
                evidence=[],
                errors=[
                    "MCP connection failed: "
                    + type(exc).__name__
                ],
            )

        except Exception as exc:
            record(
                EventType.ASSESSMENT_COMPLETED,
                EventOutcome.FAILED,
                duration_ms=(perf_counter() - started) * 1000,
                error_type=type(exc).__name__,
            )
            raise

    outcome = {
        "completed": EventOutcome.SUCCESS,
        "partial": EventOutcome.PARTIAL,
        "failed": EventOutcome.FAILED,
    }[result.status]

    record(
        EventType.ASSESSMENT_COMPLETED,
        outcome,
        duration_ms=(perf_counter() - started) * 1000,
    )

    return result
