# AI-A04 — Day 3: Agent Consumption & Interoperability

## Objective

Demonstrate an enterprise assessment agent that consumes
MCP capabilities across CRM, ERP and Finance.

The initial workflow is deterministic rather than
LLM-planned, making execution reproducible and testable.

## Architecture

Business Assessment Request
    -> Enterprise Assessment Agent
    -> Reusable MCP Client
    -> MCP Server
    -> Server-Side Tool Policy
    -> Enterprise Adapters
    -> PostgreSQL (CRM / ERP / Finance)

## Agent Contracts

Defined in `src/agents/contracts.py`:

- AssessmentRequest
- ToolEvidence
- BusinessObservation
- EnterpriseAssessment

The final assessment contains:

- Customer identity and assessment date
- Execution status: completed, partial or failed
- Business observations and severity
- Recommendations
- Tool evidence and source identifiers
- Execution errors

## Reusable MCP Client

Module: `src/client/enterprise_mcp.py`

Responsibilities:

- Start a local MCP server subprocess
- Discover registered tools
- Invoke tools with arguments
- Decode MCP responses
- Surface tool execution failures

The subprocess role is selected by the trusted local
launcher for demonstration purposes.

## Enterprise Assessment Agent

Module: `src/agents/enterprise_assessment.py`

The workflow:

1. Validate assessment date
2. Discover MCP tool capabilities
3. Retrieve customer information
4. Retrieve customer orders
5. Retrieve financial exposure
6. Evaluate available evidence
7. Produce observations and recommendations
8. Return structured status and evidence

Required tools:

- get_customer_db
- get_customer_orders_db
- get_customer_financial_summary_db

The MCP server exposes nine tools overall.

## Demonstration Scenario

Customer: C001 — ACME Corporation

Reference date: 2026-11-06

Expected results from the synthetic dataset:

- Four customer orders
- EUR 7,612.50 outstanding
- EUR 6,527.50 overdue

These results are derived from the synthetic
enterprise database and are not real customer data.

## Failure Handling

Tested scenarios include:

- Missing required MCP tool
- Tool invocation failure
- Unavailable customer
- Denied tool access
- MCP connection startup failure
- Asynchronous exception group
- Invalid calendar date

Where customer identity is verified but other
evidence is unavailable, the agent can return
a partial assessment.

Where customer identity cannot be established,
the assessment is marked failed.

## Validation

41 automated tests passed at the completion
of the Day 3 implementation.

## Running the Demonstration

Prerequisites:

- Python virtual environment activated
- PostgreSQL container running
- Database initialized and seeded
- Read-only database role provisioned

Run:

    python -m src.agents.demo

Run tests:

    python -m pytest tests/ -q

## Security Limitations

Local launcher roles are not authenticated
remote identities.

The database account is restricted to read-only
operations.

Production deployment requires authenticated
identity propagation, stronger authorization
controls and durable audit storage.

## Architectural Limitations

- Agent planning is deterministic.
- Recommendations use predefined rules.
- Full LLM-based tool selection is not implemented.
- Financial as-of semantics are not historical snapshots.
- No production deployment or recovery orchestration.
- No live connection to AI-A02 or AI-A03 yet.

## Next Steps

Day 4 will focus on operational validation,
observability, failure recovery, deployment
considerations and final architecture reporting.

Future cross-project work may connect:

- AI-A02: agent orchestration
- AI-A03: enterprise RAG
- AI-A05: governance and policy enforcement
