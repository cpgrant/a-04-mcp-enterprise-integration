---
title: 'AI-A04 — MCP & Enterprise Integration'
subtitle: 'Comprehensive Technical Project Report | Four-Day Architecture, Engineering and Validation Record'
author: 'Christian Grant | DeepAIMind'
date: '6 November 2026'
---

# AI-A04 — MCP & Enterprise Integration

**Comprehensive Technical Project Report**
**Scope:** Architecture foundation, enterprise adapters, agent consumption, governance, observability and operational validation
**Repository:** <https://github.com/cpgrant/a-04-mcp-enterprise-integration>
**Baseline:** `main`, commit `12b75f5` (6 November 2026)
**Document status:** Consolidated technical retrospective, prepared from the published repository and the recorded project execution.
**Classification:** Public portfolio documentation; all demonstration business data is synthetic.

\newpage

# Executive summary

AI-A04 is a four-day, deliberately bounded engineering project exploring how an enterprise AI agent can use the **Model Context Protocol (MCP)** to access business systems through a governed interface. The work began with a minimal MCP server and two synthetic customer tools, extended that foundation into PostgreSQL-backed CRM/ERP/Finance adapters, added a typed enterprise assessment agent, and concluded with observability, measured latency, database authorization tests, and a formal acceptance run.

The final prototype exposes **nine MCP tools**: two original in-memory examples and seven PostgreSQL-backed business tools. It uses **three logical business schemas, nine relational tables, and 715 reproducible synthetic records**. A deterministic assessment agent invokes three of those tools to verify a customer, inspect orders, and evaluate financial exposure. The implementation separates business observations and recommendations from the tool results that support them. Its use of MCP is concrete: the agent discovers tools, invokes the local server over stdio, decodes responses, and produces typed evidence-backed output.

Governance is enforced twice. A server-side, default-deny tool policy controls what a locally selected role may invoke; PostgreSQL independently restricts the application account `a04_reader` to read access. Structured audit events record role, tool and outcome. On Day 4, additional client-side and agent-side events provided correlated identifiers and timings. A standard assessment generated **eight correlated agent/client events**. The separate server audit stream was **not** fully correlated, which remains an explicit limitation.

The final regression suite passed **56 tests**; the final acceptance script passed **five of five checks**. A local benchmark comprised two warm-up assessments and ten measured assessments, with median complete assessment latency of **594.41 ms**, median MCP startup latency **496.10 ms**, median discovery **1.59 ms**, and median combined three-tool latency **21.65 ms**. The largest measured cost was repeatedly launching the Python MCP subprocess, not the business tool calls.

The artifact is an **operationally validated local proof of concept**, not a production authorization framework, a general-purpose autonomous agent, or a high-throughput MCP service. Its value is to establish a reference pattern for future work connecting AI-A02 orchestration, AI-A03 knowledge, AI-A05 governance, and autonomous-enterprise application experiments.

## Key results at a glance

| Dimension | Delivered outcome | Evidence |
|---|---|---|
| MCP interoperability | Local server/client discovery and stdio calls | `src/server/main.py`; client demos |
| Enterprise integration | CRM, ERP, Finance; 7 database tools | Day 2 report; adapters |
| Tool catalog | 9 registered tools overall | MCP server; Day 2 report |
| Agent | Deterministic three-tool customer assessment | `src/agents/enterprise_assessment.py` |
| Data protection | Default-deny tool role policy; restricted DB reader | `src/governance/`; security tests |
| Observability | Assessment/tool events, shared identifiers and timings | `src/observability/`; integration tests |
| Test coverage | 56 passing tests | `results/day4_acceptance.json` |
| Acceptance | 5/5 checks | `results/day4_acceptance.json` |
| Performance | 594.41 ms assessment median over 10 runs | `results/day4_benchmark.json` |
| Presentation | Four 16:9 project infographics and Mermaid diagrams | `infographics/`; `diagrams/` |

# 1. Report purpose, evidence and method

## 1.1 Why produce a comprehensive record?

The original repository README is an entry point, while `AI-A04-Complete-Architecture-Report.md` is a concise architecture summary. Neither was designed to explain, in sequence, the experiments performed, the source modules introduced, the decisions made, and the verification results. This report fills that gap. It is intended both as a reproducible engineering narrative and as evidence of hands-on enterprise AI architecture competence.

The report follows an implementation lifecycle rather than an idealized platform architecture. For each day it records (a) the problem to solve, (b) the component boundary, (c) the code and data developed, (d) validation, (e) what changed in the architecture, and (f) the remaining limitations. It also identifies what is supported directly by the public repository and what is a recommended next experiment rather than a delivered feature.

## 1.2 Evidence hierarchy

The most authoritative evidence for implementation is the source itself: `src/server/main.py`, `src/client/enterprise_mcp.py`, `src/agents/enterprise_assessment.py`, `src/adapters/db.py`, `src/governance/policy.py`, and the observability and testing modules. The Day 2–4 implementation reports provide the chronological interpretation. The Day 4 JSON files are the authoritative local measurements and final acceptance record. The published README and its commit history support project status and navigation.

Day 1 has no separate published implementation report. Its account is consequently derived from the README, the Day 1 sections retained in the server, the initial client demonstrations, and the architecture evolution. This report does **not** claim to reconstruct every keystroke or exact duration of each day's work.

## 1.3 Boundaries and terminology

- **MCP tool** means a discoverable, callable capability exposed by the MCP server; it is not necessarily an autonomous agent.
- **Adapter** means Python code translating a tool request into domain-specific database access and result structures.
- **Assessment agent** means the deterministic orchestration module developed on Day 3, not an LLM planning or deciding freely.
- **Evidence** means recorded tool results and source references used to justify observations, not cryptographically attested data provenance.
- **Audit event** means the separate server-side log entry for tool, role, and outcome; **observability event** is the Day 4 typed client/agent event.
- **Point-in-time assessment** uses an `as_of` parameter, but the finance implementation does not reconstruct full historical payment state.

## 1.4 Portfolio acceptance standard

The acceptance standard was architecture fidelity, a working local proof of concept, automated tests and inspectable outputs—not production service-level objectives. The project deliberately avoided OAuth federation, a centralized telemetry backend, distributed deployment and LLM-directed tool planning. The security and latency findings must be read within that scope.

# 2. Architecture context and design

## 2.1 Problem statement

Enterprise agents need context from operational applications but should not embed direct database credentials, database-specific SQL, and system access logic into their reasoning code. Without an interface boundary, coupling increases: changing a backend schema can break an agent; access policies are duplicated; diagnostics cannot easily distinguish a failed tool from a failed business inference. AI-A04 experiments with MCP as that boundary.

The design asks four practical questions. Can a conventional Python process discover and invoke enterprise capabilities through MCP? Can a single tool interface span CRM, ERP and finance without collapsing their schemas? Can policy and least-privilege database access be enforced before business execution? And can the resulting call chain be tested, traced and measured sufficiently to assess future architecture trade-offs?

## 2.2 Logical component map

```text
Assessment request (customer_code, as_of)
             |
             v
  Deterministic assessment agent
    |  typed request / evidence / report
    |  assessment_id + trace_id
             v
     Reusable MCP client
    | tool discovery; invoke/parse; timings
             |  stdio / MCP
             v
        MCP server process
    | tool registry and resource catalog
    | default-deny local role policy
    | server audit events -> stderr
             v
   Domain-specific adapters
    +---------+-----------+
    |         |           |
   CRM        ERP       Finance
    +---------+-----------+
              |
    PostgreSQL 17, 3 schemas
    a04_reader: SELECT only
```

This is a **logical** map. The MCP server is launched as a separate subprocess by the reusable client in the assessed workflow; it is not a network-accessible production cluster. The operational event stream is emitted by the agent and client, while the server's audit stream is distinct. There is no distributed trace carrier crossing the protocol boundary in the Day 4 baseline.

## 2.3 Responsibilities and separation of concerns

| Component | Main responsibility | What it deliberately does not own |
|---|---|---|
| Assessment request | Customer/date input contract | Credentials or SQL |
| Assessment agent | Fixed business sequence and interpretation | Direct SQL or dynamic LLM planning |
| MCP client | Process lifecycle, discovery, calls and decoding | Business authorization policy |
| MCP server | Public capability surface and tool registration | Enterprise database ownership |
| Tool policy | Server-side allow/deny before tool execution | Authenticated federation |
| Adapters | Data access and domain responses | Agent business recommendations |
| PostgreSQL reader | Least-privilege retrieval | Business write authority |
| Observability | Execution events and timing | Durable central tracing backend |

## 2.4 Trust boundaries

The main trust crossings are (1) request input to assessment contract; (2) assessment into the MCP tool boundary; (3) tool request into policy enforcement; and (4) adapter into the restricted database login. The local role is passed through environment variable `AI_A04_ROLE` by the trusted launcher. This is adequate for a constrained demonstration only: an untrusted client controlling that environment cannot be treated as securely authenticated. A production design would authenticate and bind caller identity to tool authorization with an explicit trust model.

The database boundary is stronger and independently tested. `src/adapters/db.py` uses a dedicated role, parameterized connections, a configured read-only transaction default, a five-second statement timeout and a five-second connect timeout. In addition, the role's underlying table privileges were tested for lack of INSERT, UPDATE, DELETE and TRUNCATE.

## 2.5 Technology choices

The published `pyproject.toml` specifies Python 3.12+, MCP SDK `>=2.3.0,<2.4.0`, Psycopg 3, `python-dotenv`, and pytest as a development dependency. Docker Compose runs PostgreSQL 17, with the container named `a04-postgres` and host binding `127.0.0.1:55432`. The chosen architecture is deliberately local, inspectable and compatible with WSL2. `Pydantic` is used for typed assessment and observability contracts. Mermaid source and PNG/SVG renders document system context, container boundaries, tool invocation, and trust boundaries.

# 3. Day 1 — MCP architecture and foundation

## 3.1 Day 1 objective

The Day 1 goal was to demonstrate MCP interoperability before introducing enterprise databases or agent orchestration. The smallest useful scenario was a discoverable catalog and two callable customer functions. This isolates protocol mechanics from later application complexity. The central acceptance question was whether both an in-process and a separate-process client could discover and call functions registered on the server.

## 3.2 The initial server

The main server module retains an in-memory `CUSTOMERS` dictionary with two synthetic entries, `C001` / ACME Corporation and `C002` / Northwind Trading. It registers `get_customer(customer_id)` and `list_customers()` through `@mcp.tool()` and exposes the resource URI `enterprise://catalog` via `@mcp.resource`. These examples are intentionally not database-backed. Their continued presence after Day 2 helps distinguish the transport and discovery demonstration from the actual enterprise adapter path.

The server is defined using `MCPServer("AI-A04 Enterprise Integration")` and runs with `mcp.run(transport="stdio")` when executed directly. The tool functions are wrapped with the server policy decorator `@require_tool(...)`; by Day 2 this imposes policy checks on both the in-memory and database-facing tools. Tool discovery and tool execution are separate concepts: a client can list names and schemas, but an attempted call may still fail authorization.

## 3.3 Transport experiments

The README records two client demonstrations: `python -m src.client.demo` for the in-process path and `python -m src.client.stdio_demo` for independent-process communication. The stdio path is the foundation for Day 3: a Python client launches a Python MCP server and communicates through the standard MCP protocol rather than calling the adapter functions directly. Using stdout for MCP framing requires non-protocol logging to remain off stdout. The project therefore uses stderr for audit and operational event output.

The difference matters. A direct Python import tests code behavior; an MCP client/server test also exercises protocol discovery, serialization, process lifecycle and response handling. Those additional boundaries are the meaningful architectural product of Day 1.

## 3.4 Architecture documentation established

The repository contains four Mermaid source diagrams: `01-system-context.mmd`, `02-container-architecture.mmd`, `03-tool-invocation.mmd` and `04-trust-boundaries.mmd`, with rendered assets in `diagrams/rendered/`. The project also includes architecture decision records addressing the official MCP SDK, transport strategy, enterprise adapter separation, server-side authorization and audit/observability. This gave Day 2 a documented foundation to extend rather than redesign.

## 3.5 Day 1 validation and learning

Day 1 established tool discovery, tool invocation, resource discovery, in-process communication and separate-process stdio communication. It also identified an early discipline: the protocol boundary must remain independent of enterprise-specific storage. The in-memory functions should be retained as instructional examples rather than mistaken for production CRM adapters. Day 2's database-backed tools would be added alongside them rather than silently replacing them.

**Day 1 engineering insight:** prove the protocol contract first, then attach domain integration. This makes failures easier to attribute: protocol vs. policy vs. adapter vs. persistence.

# 4. Day 2 — PostgreSQL integration, domain tools and governance

## 4.1 Day 2 objective

Day 2 took the initial working MCP surface and made it useful for a representative enterprise information request. The specific task was to expose database-backed CRM, ERP and finance capabilities while preserving clear adapter boundaries and adding practical access controls. The design favored deterministic, synthetic and reviewable data over broad external connectivity.

## 4.2 Data model and synthetic dataset

The database is `a04_enterprise`. Three schemas group nine relational tables:

| Domain | Tables | Role in the prototype |
|---|---|---|
| CRM | `customers`, `contacts` | Customer identity and relationships |
| ERP | `products`, `sales_orders`, `order_lines`, `inventory` | Sales commitments, lines, product availability |
| Finance | `invoices`, `invoice_lines`, `payments` | Billing, payment and exposure calculations |

The source report records **715 reproducible synthetic records**. The data model is relational and business-oriented: it can answer customer existence, order history, product availability and invoice exposure with separate, traceable sources. It is not a live ERP connection, not a real customer dataset and not an enterprise digital twin.

## 4.3 Database deployment

`compose.yaml` defines a PostgreSQL 17 service with the container name `a04-postgres`, `.env`-supplied database configuration, a persistent `postgres_data` volume, a local-only host port mapping (`127.0.0.1:55432:5432`) and a `pg_isready` health check. The local-only binding reduces accidental network exposure but is not a replacement for host/network security controls. PostgreSQL initialization and synthetic seeding are kept under `database/`; role provisioning is handled by `scripts/provision_reader.py`.

The adapter loader reads the project-root `.env` via `load_dotenv`. This explains a notable validation observation: database environment variables were not exported in the terminal shell, yet adapter calls worked because the application loaded `.env`. The repository does not publish that secret file; the expected convention is to provide it locally from the example configuration.

## 4.4 Enterprise adapter design

The CRM adapter provides customer lookup and listing. The ERP adapter provides customer order summaries, order details and SKU inventory status. The finance adapter lists customer invoices and calculates customer financial totals. Functions are exposed through `src/server/main.py` wrappers whose names end in `_db` to distinguish them from the Day 1 in-memory tools. The wrapper response includes source identifiers such as `postgresql.crm.customers`, `postgresql.erp.sales_orders` and `postgresql.finance`.

The finance implementation uses `Decimal` arithmetic for money and derives invoice balances from invoice lines and payment data. This is preferable to binary floating-point arithmetic for financial totals. There is an important temporal limitation: a requested `as_of` date does not currently imply a complete historical cut-off for the underlying payments; therefore, the results should not be marketed as an audited historical financial snapshot.

## 4.5 Nine-tool inventory

| MCP tool | Source | Function |
|---|---|---|
| `get_customer` | In-memory | Retrieve Day 1 synthetic customer |
| `list_customers` | In-memory | List Day 1 synthetic customers |
| `get_customer_db` | CRM | Retrieve persisted customer |
| `list_customers_db` | CRM | List persisted customers with limit |
| `get_customer_orders_db` | ERP | Retrieve bounded customer order list |
| `get_order_details_db` | ERP | Retrieve order and order lines |
| `get_inventory_status_db` | ERP | Inspect stock for SKU |
| `list_customer_invoices_db` | Finance | Retrieve customer invoices by reference date |
| `get_customer_financial_summary_db` | Finance | Calculate billed, paid, outstanding and overdue totals |

The tool catalog is a contract surface, not nine separate processes. All nine names are registered on the same local MCP server. The initial pair remains useful for transport smoke tests; the seven `_db` functions provide the enterprise database path.

## 4.6 Server-side authorization

`src/governance/policy.py` defines `CUSTOMER_TOOLS`, `ERP_TOOLS`, `FINANCE_TOOLS`, and a `ROLE_PERMISSIONS` map. The demonstration roles are `reader` (all listed tools), `finance_reader` (customer plus finance but not ERP), and `blocked` (none). `is_allowed` returns false for absent roles or absent permissions. The `require_tool` decorator reads `AI_A04_ROLE` and checks permission before calling the wrapped function. It logs `denied`, `error` or `success` through `src/governance/audit.py`.

This is server-enforced **local role policy**, not a remotely authenticated identity solution. In particular, the role is supplied through the trusted launcher environment, so it should not be described as tenant isolation or externally verifiable authorization. The value of the implementation is the location of the decision: tool protection is enforced at invocation time and is testable independently of the agent.

## 4.7 Least privilege at the database boundary

`src/adapters/db.py` connects as `a04_reader` and applies `default_transaction_read_only=on` and `statement_timeout=5000`. The provisioning script grants CONNECT, schema USAGE, and SELECT on tables in CRM, ERP and Finance. Day 4 later verified the underlying effective privileges: INSERT, UPDATE, DELETE and TRUNCATE were all absent, and a deliberately non-matching DELETE was rejected with insufficient privilege. The distinction is important: application-side read-only mode alone is weaker than an independently restricted SQL role.

## 4.8 Day 2 validation result

The Day 2 implementation report records **26 passing tests**, covering cross-domain integration, MCP stdio, local policy and database reader behavior. The enterprise demonstration `python -m src.client.enterprise_demo` retrieves examples of customer, order, inventory and financial information through MCP. The scope was broad enough to demonstrate the major boundaries but intentionally limited to a small synthetic environment.

**Day 2 engineering insight:** governance needs to be positioned at both the capability and persistence boundaries. MCP provides the interface; it does not by itself confer least privilege or guarantee a safe database role.

# 5. Day 3 — MCP-consuming enterprise assessment agent

## 5.1 Why an assessment agent?

The first two days proved that tools and databases can communicate. Day 3 established a higher-level consumer: a business workflow that gathers evidence from multiple enterprise domains and transforms it into a coherent assessment. The value lies in the **composition** of calls, not the novelty of the individual SQL queries. A user asks about a customer; the assessment agent resolves identity, operational commitments and financial exposure through the MCP boundary and returns a structured answer.

Crucially, the implementation uses a **fixed execution plan**. It does not ask a language model to decide which tool to invoke. This preserves straightforward reproducibility and makes missing-tool, denied-role and partial-evidence behavior easier to validate. It also separates the architectural question—can an agent consume governed enterprise tools?—from the separate question of whether a model can plan safely.

## 5.2 Typed business contracts

`src/agents/contracts.py` defines four Pydantic models. `AssessmentRequest` accepts an uppercase alphanumeric/hyphen `customer_code` of length 1–20 and an ISO-shaped `as_of` string. A second check with `date.fromisoformat` rejects impossible calendar dates before tool invocation. `ToolEvidence` stores the tool name, arguments, source and returned result; `BusinessObservation` stores a category, severity, human-readable finding and evidence-tool references; `EnterpriseAssessment` stores customer identity, status, observations, recommendations, evidence and errors.

The status contract limits results to `completed`, `partial`, or `failed`. The categories are CRM, ERP and finance; severities are `info`, `warning` and `critical`. These enumerated values make both testing and downstream presentation more reliable than unconstrained prose alone. The evidence object, however, includes arguments and complete results in the returned assessment; it is not appropriate to assume the assessment payload is automatically safe to expose to every consumer.

### Contract excerpt — source structure

```python
class BusinessObservation(BaseModel):
    category: Literal["crm", "erp", "finance"]
    severity: Literal["info", "warning", "critical"]
    finding: str
    evidence_tools: list[str]

class EnterpriseAssessment(BaseModel):
    customer_code: str
    customer_name: str
    as_of: str
    status: Literal["completed", "partial", "failed"]
    observations: list[BusinessObservation]
    recommendations: list[str]
    evidence: list[ToolEvidence]
    errors: list[str] = Field(default_factory=list)
```

*Source: `src/agents/contracts.py`; excerpt preserves the field design and omits surrounding imports.*

## 5.3 Reusable MCP client

`src/client/enterprise_mcp.py` wraps MCP connection lifecycle in an asynchronous context manager. It constructs `StdioServerParameters` with the current Python interpreter and `-m src.server.main`, passes the configured local role through `AI_A04_ROLE`, and opens the client with `Client(server)`. `discover_tools()` uses the MCP tool list; `call()` invokes a tool and decodes structured content or JSON text content. It surfaces MCP-declared errors as exceptions and requires a dictionary result for the assessment path.

This provides a narrow, reusable protocol adapter for future agent implementations. The caller need not construct subprocess arguments or parse protocol-specific content blocks. As of Day 4 the same client also emits tool timing and outcome events; those later changes preserve the central Day 3 interface.

The current client launches a separate MCP server in its `__aenter__` method. That is simple and isolated but means each assessment pays Python process and MCP initialization cost. This trade-off became measurable on Day 4.

## 5.4 Fixed plan and execution sequence

The agent's `_assess_connected` routine first discovers the tool catalog. It then iterates over exactly three planned calls:

1. `get_customer_db(customer_code)` to establish that the customer exists and retrieve a name.
2. `get_customer_orders_db(customer_code, limit=20)` to obtain bounded operational order evidence.
3. `get_customer_financial_summary_db(customer_code, as_of)` to obtain exposure and overdue figures.

Before invoking each call, the routine checks whether the required tool name is present in the discovery result. Missing tools cause an error entry rather than a speculative substitute. Each successful tool call creates a `ToolEvidence` record with `source` and the returned dictionary. Individual tool exceptions are recorded as typed error descriptions. A failed or missing customer lookup is decisive: without verified identity, the assessment returns `failed`. If identity is established but some other tools fail, the result may return `partial` with the available evidence. Otherwise, it is `completed`.

The plan is sequential and intentionally predictable. It is not parallelized, does not browse arbitrary MCP resources, and does not delegate to an external A2A agent. These are legitimate extensions but were not part of AI-A04's Day 3 acceptance criteria.

## 5.5 Evidence to observations

Once the customer result is verified, the agent generates a CRM observation. If the ERP order result is available, it reports the number of returned customer orders. If the financial result is available, it uses `Decimal` to parse outstanding and overdue values. Positive outstanding balances receive warning severity; positive overdue balances become critical observations. Recommendations are rule-based: review overdue invoices, check credit exposure before new commitments, and review open order/fulfillment commitments with operations when orders exist.

These outputs are **interpretations of structured synthetic data**, not independent financial advice or AI-generated discoveries. Their usefulness is architectural: the system shows exactly which tools support each finding and makes result completeness visible through status and errors.

## 5.6 ACME demonstration case

The documented Day 3 demonstration uses customer `C001` (ACME Corporation) and `as_of` date `2026-11-06`. The synthetic dataset returns **four orders**, **EUR 7,612.50 outstanding**, and **EUR 6,527.50 overdue**. These values demonstrate that the same assessment can combine master data, operational data, and financial data while keeping evidence references attached. They do not represent an actual company ledger or verified historical financial position.

| Input or output | Demonstration value |
|---|---|
| Customer code | C001 |
| Customer | ACME Corporation (synthetic) |
| Assessment date | 2026-11-06 |
| Orders | 4 |
| Total outstanding | EUR 7,612.50 |
| Overdue balance | EUR 6,527.50 |
| Evidence domains | CRM, ERP and Finance |
| Assessment pattern | Deterministic three-tool plan |

The outputs give a good narrative for demos: identify a customer, inspect commitments, identify financial risk, and recommend human follow-up. They do not demonstrate forecasting, credit underwriting, settlement or business transaction execution.

## 5.7 Failure and partial-result model

The Day 3 tests address missing required tools, tool invocation failures, unavailable customer, denied role, MCP connection startup failure, asynchronous exception groups and invalid calendar date. The exception boundary around `assess_enterprise` catches transport/startup failures and returns a failed typed result rather than an unhandled business response. Other unexpected exceptions are not silently swallowed; Day 4 instrumentation records failure before re-raising them.

| Condition | Intended response | Why it matters |
|---|---|---|
| Customer verified; all tools work | `completed` | Full evidence-backed assessment |
| Customer verified; ERP/finance unavailable | `partial` | Prevent false completeness |
| Customer cannot be verified | `failed` | Avoid attributing financial data to wrong identity |
| Required tool not advertised | Error recorded | No invented service substitute |
| Tool returns an MCP error | Error recorded | Tool failure is distinguishable from missing data |
| Server cannot start | Failed transport assessment | Controlled interface failure |
| Invalid date | Input rejected | Avoid invalid cross-domain requests |
| Role denied | Tool call rejected | Governance remains at tool boundary |

One important security consideration: catching tool failures and generating a partial result is not equivalent to authorization bypass. If essential customer verification fails, the result is failed, not partially authoritative. Tests use both real MCP interactions and simulated failure conditions; passing simulated tests alone would not establish deployment recovery under every fault mode.

## 5.8 Day 3 validation

At completion of Day 3 the regression suite passed **41 automated tests**. Tests cover contracts, MCP client integration, agent success, resilience and connection failures. The published demonstration is `python -m src.agents.demo`; the script asserts a completed assessment with three evidence records and prints `PASS: Enterprise assessment agent` on success. This demonstrates functional composition and data-grounded output while keeping the workflow deliberately non-autonomous.

**Day 3 engineering insight:** an enterprise 'agent' is useful even without unconstrained LLM planning when it can compose governed tools, preserve evidence and accurately report partial failure. The distinction makes the architecture easier to extend later without overclaiming its present capabilities.

# 6. Day 4 — Observability, benchmarking, reliability and acceptance

## 6.1 Day 4 objective

Day 4 asked whether the implementation could be measured, diagnosed and accepted as a reproducible local prototype. The work did not add another data domain or another independent agent; it instrumented the execution that already existed, tested concurrency context isolation, measured latency across repeated runs, verified underlying PostgreSQL privileges and consolidated final acceptance evidence.

## 6.2 Typed operational event schema

`src/observability/events.py` defines the event types `assessment_started`, `assessment_completed`, `tool_started`, `tool_completed` and `tool_failed`. Outcomes include `started`, `success`, `partial`, `failed` and `denied`. Each `ObservabilityEvent` includes a UUID event ID, UTC timestamp, trace ID, assessment ID, component, operation, optional tool name, optional nonnegative `duration_ms`, and optional error type.

These fields are deliberately operational. The emitter writes event JSON to **stderr**, and the event schema omits raw customer records, invoice totals, credentials and raw tool-call arguments. That reduces data exposure in operational logs. It does not guarantee that the rest of the returned business assessment or server log streams contain no sensitive information, so production log policy remains a separate design task.

## 6.3 Correlation scope

`src/observability/context.py` uses a Python `ContextVar` holding a `(trace_id, assessment_id)` tuple and a context manager that restores the previous token when the scope exits. The assessment wrapper creates both IDs and opens a correlation scope around `_assess_connected`. When the MCP client is initialized inside that scope, it inherits the IDs unless explicit client IDs were passed. Tests verify that a scope restores its previous values, nested scopes restore their parents and independently scheduled asynchronous workers maintain separate IDs.

This is **in-process context propagation** from the agent to the MCP client. It does **not** propagate IDs into the independently launched MCP server via MCP message metadata, and it does not connect the separate `mcp_tool_execution` audit events back to the same trace. That is a known and documented gap, not a hidden implementation detail.

## 6.4 Tool lifecycle instrumentation

The client records `tool_started` before invoking `Client.call_tool`, starts a `perf_counter` timer, then emits `tool_completed` on success or `tool_failed` with the exception class on failure. It measures tool invocation plus response decoding from the client boundary. The assessment wrapper records the assessment start and end, capturing end-to-end duration around the three-tool sequence and client process lifecycle.

For a standard three-tool assessment, the expected correlated client/agent event sequence contains eight entries:

```text
assessment_started
  tool_started(get_customer_db)
  tool_completed(get_customer_db)
  tool_started(get_customer_orders_db)
  tool_completed(get_customer_orders_db)
  tool_started(get_customer_financial_summary_db)
  tool_completed(get_customer_financial_summary_db)
assessment_completed
```

The final acceptance test checks that these eight events exist and share one trace ID and one assessment ID. Because separate server-side audit records lack those IDs, the correct claim is **correlated agent/client execution**, not fully distributed end-to-end tracing.

## 6.5 Initial single-run observation

An interactive Day 4 demonstration showed three tool durations of approximately 9.68, 6.89 and 6.93 ms and a complete assessment duration of 588.59 ms. The combined call time was roughly 23.50 ms. This immediate discrepancy suggested that runtime outside the actual tool calls—especially process initialization—was significant. A repeated benchmark was then added to test that hypothesis. One run alone was not used as the final performance baseline.

## 6.6 Repeatable benchmark methodology

`scripts/benchmark_day4.py` runs **two warm-ups plus ten measured customer assessments**. It substitutes a subclassed MCP client for timing `__aenter__` (startup) and `discover_tools` while capturing structured assessment and tool events. It verifies that every assessment returns `completed` and that each measured run has one completion event and three tool completion events. It writes all ten raw run records and summary statistics to `results/day4_benchmark.json`.

The statistical summary includes minimum, median, maximum, mean and a nearest-rank p95. With ten observations, this p95 equals the largest observed value; it is not a statistically robust tail-latency estimate. Times are local to the WSL2/Docker development environment, and the measured categories are not necessarily additive: scope boundaries and shutdown overhead differ. Re-running the script overwrites the results file and produces a new local benchmark sample.

## 6.7 Recorded results

| Metric | Minimum | Median | Mean | p95 / Max | Unit |
|---|---:|---:|---:|---:|---|
| End-to-end assessment | 584.91 | **594.41** | 595.34 | 606.63 | ms |
| MCP startup | 485.69 | **496.10** | 496.56 | 505.58 | ms |
| Tool discovery | 1.43 | **1.59** | 1.59 | 1.86 | ms |
| Three-tool total | 19.94 | **21.65** | 21.51 | 22.02 | ms |

The ratio of the two reported medians is approximately **83.5%** (496.10 / 594.41). Because this is a ratio of medians from related measurements, it is an **indicative contribution**, not a precisely decomposed fraction of any individual execution. The remaining time includes processing, connection setup/teardown and operations not measured as tool calls. The experiment does **not** demonstrate that MCP as a protocol intrinsically requires half a second; the local implementation starts a new Python subprocess per assessment.

## 6.8 Architectural performance interpretation

The benchmark reveals a high-leverage extension: reuse the MCP connection across assessments, or compare local subprocess transport with an appropriately secured persistent server transport. Such a comparison would need to measure steady-state latency, amortized startup, concurrency, failure recovery and authorization semantics. The current results support **investigating** persistent connectivity; they do not establish its final performance or security properties.

The modest roughly 22 ms median time for three enterprise calls also means optimization should not begin by rewriting trivial SQL or prematurely parallelizing the fixed plan. The first bottleneck to examine is client/server process lifecycle. The small dataset may make backend query latency unrealistically favorable relative to larger real systems.

## 6.9 Database authorization: measured, not assumed

The Day 4 security tests connect through the real `src.adapters.db.get_connection()` function and discover enterprise tables under CRM, ERP and Finance. They check that tables can be selected, that the effective SQL role lacks INSERT/UPDATE/DELETE/TRUNCATE privileges, and that an attempted `DELETE ... WHERE FALSE` is rejected as insufficient privilege even when explicitly asking for a read-write transaction. The false predicate prevents rows from matching; the test targets privilege enforcement rather than data mutation.

The separate security query confirmed `current_user = a04_reader`, `default_transaction_read_only = on` and `statement_timeout = 5s`. These checks are stronger than merely asserting that a source file contains a read-only configuration flag. They exercise the live PostgreSQL permission boundary in the current local setup.

## 6.10 Correlation isolation and reliability tests

Day 4 adds explicit tests for event contracts, JSON serialization, nonnegative timing, scope cleanup, nested context restoration, concurrent scope isolation, MCP tool success/failure events and full assessment correlation. Existing Day 3 failure tests remain part of regression. The project does not claim automated recovery, retry with backoff, durable queues, circuit breakers, load testing or zero-downtime fault tolerance. Its reliability evidence demonstrates controlled results and exception boundaries for a defined subset of scenarios.

## 6.11 Final acceptance automation

`scripts/validate_project.py` runs the full pytest suite, executes the ACME demonstration, parses agent/client events from stderr, checks for eight correlated events, connects to PostgreSQL to verify the reader identity and read-only defaults, and validates the presence and structure of the ten-run benchmark. It writes `results/day4_acceptance.json` and exits nonzero if any check fails. The run dated 6 November 2026 recorded:

| Final acceptance item | Reported result |
|---|---|
| Regression suite | PASS — 56 tests |
| Enterprise assessment | PASS — ACME demo completed |
| Execution correlation | PASS — 8 client-side events |
| Database security configuration | PASS — `a04_reader`, read-only on |
| Performance benchmark evidence | PASS — 10 measured runs |

The acceptance script validates that benchmark evidence exists and has the expected schema; it does **not** independently rerun the benchmark during acceptance. This distinction matters for reproducibility, elapsed time and interpretation of the five checks.

## 6.12 Day 4 completion result

The suite grew from 41 tests at the close of Day 3 to **56 passing tests** at the close of Day 4. Increments came from event contract tests, MCP event integration, assessment correlation, context isolation and database privilege checks. `python -m pip check` reported no broken requirements. The completed Day 4 implementation, report, results and fourth infographic were pushed to GitHub. The subsequent README correction was committed under `12b75f5`, leaving `main` synchronized and the working tree clean in the recorded terminal session.

**Day 4 engineering insight:** operational evidence can overturn a casual performance assumption. The key result is not just 'fast tools'; it is that per-assessment subprocess startup dominated the observed runtime while the governed business queries themselves were a small fraction of the total.

# 7. Engineering design decisions and rationale

## 7.1 Why MCP rather than direct adapter imports?

Direct Python calls would be simpler within one process, but they would not test the separation between agent and enterprise capability server. MCP introduces a stable discovery/invocation surface, an opportunity to centralize tool governance, and a transport that can later be replaced without requiring the business workflow to know SQL details. The cost is more process/protocol complexity and the measured startup latency. For an architecture portfolio, the trade-off is valuable because both benefits and costs are visible in executable code.

## 7.2 Why retain the Day 1 in-memory tools?

The pair of in-memory customer tools tests protocol mechanics without depending on PostgreSQL. This supports fault isolation and educational clarity. It also makes the server's nine-tool count potentially confusing, so the report consistently distinguishes **two in-memory** from **seven database-backed** tools. The former are not an alternate source of authoritative customer master data for the Day 3 assessment.

## 7.3 Why deterministic agent logic?

A fixed plan makes it possible to assert tool sequence, evidence count, failure behavior and recommendation rules. Introducing a model planner would create another variable—model output and decision quality—while the integration boundary was still under test. The deterministic design is thus an engineering choice, not evidence that the system already provides open-ended autonomous decision making.

## 7.4 Why independent governance and SQL privilege checks?

Server-side authorization prevents a forbidden tool invocation; the SQL reader role reduces the consequence of errors that reach the adapter or database. Together they demonstrate defense in depth, but neither implements full enterprise authentication. Production identity propagation, tenant isolation, access reviews, policy versioning and tamper-evident audits remain unsolved.

## 7.5 Why JSON-to-stderr observability?

The local process protocol uses stdout for communication. JSON stderr events are easy to inspect, parse and assert in tests without deploying a telemetry stack. The cost is that process-local logs lack a centralized trace repository or retention guarantees, and the server audit records are not linked with the agent trace. A future design could add OpenTelemetry, protocol-safe context propagation and structured backend capture after defining the desired trust and privacy model.

## 7.6 Why synthetic data?

Synthetic business records permit reproducible integrations and security tests without exposing customer data. The limitation is equally important: production systems introduce stale values, inconsistent identifiers, malformed records, operational timeouts, changing schemas and real access boundaries. The Day 4 latency figures cannot be extrapolated to real enterprise volumes without further testing.

# 8. Source-level walkthrough and code map

## 8.1 Module responsibilities

| Path | Responsibility | Principal day |
|---|---|---|
| `src/server/main.py` | MCP server, tools, resource, run loop | Days 1–2 |
| `src/client/demo.py` | In-process MCP demonstration | Day 1 |
| `src/client/stdio_demo.py` | Separate process MCP demonstration | Day 1 |
| `src/adapters/db.py` | Restricted PostgreSQL connection | Day 2 |
| `src/adapters/crm/` | Customer master-data access | Day 2 |
| `src/adapters/erp/` | Orders, lines and inventory | Day 2 |
| `src/adapters/finance/` | Invoice and exposure logic | Day 2 |
| `src/governance/policy.py` | Local default-deny tool permissions | Day 2 |
| `src/governance/audit.py` | Server-side audit JSON | Day 2 |
| `src/agents/contracts.py` | Typed request/evidence/output | Day 3 |
| `src/agents/enterprise_assessment.py` | Three-domain assessment | Days 3–4 |
| `src/client/enterprise_mcp.py` | Reusable observable stdio client | Days 3–4 |
| `src/observability/events.py` | Event model and IDs | Day 4 |
| `src/observability/context.py` | Async correlation context | Day 4 |
| `src/observability/emitter.py` | JSON stderr emission | Day 4 |
| `scripts/benchmark_day4.py` | Repeated performance measurement | Day 4 |
| `scripts/validate_project.py` | Five-item acceptance gate | Day 4 |
| `scripts/provision_reader.py` | Restricted SQL role provisioning | Day 2 |

## 8.2 Connection security example

```python
return psycopg.connect(
    host=os.getenv("POSTGRES_HOST", "127.0.0.1"),
    port=int(os.getenv("POSTGRES_PORT", "55432")),
    dbname=os.getenv("POSTGRES_DB", "a04_enterprise"),
    user="a04_reader",
    password=password,
    row_factory=dict_row,
    connect_timeout=5,
    options="-c default_transaction_read_only=on "
            "-c statement_timeout=5000",
)
```

*Source: `src/adapters/db.py`. The password is read from the local `.env` configuration and is not reproduced in this report.*

## 8.3 Default-deny policy example

```python
ROLE_PERMISSIONS = {
    "reader": ALL_TOOLS,
    "finance_reader": CUSTOMER_TOOLS | FINANCE_TOOLS,
    "blocked": set(),
}

def is_allowed(role: str, tool_name: str) -> bool:
    return tool_name in ROLE_PERMISSIONS.get(role, set())
```

*Source: `src/governance/policy.py`. The fallback empty set is the local default-deny behavior.*

## 8.4 Correlation context example

```python
_current_ids: ContextVar[tuple[str, str] | None] = (
    ContextVar("a04_correlation_ids", default=None)
)

@contextmanager
def correlation_scope(trace_id: str, assessment_id: str):
    token = _current_ids.set((trace_id, assessment_id))
    try:
        yield
    finally:
        _current_ids.reset(token)
```

*Source: `src/observability/context.py`. `finally` restores earlier context even after an error.*

## 8.5 Tool response handling

The client first checks `result.is_error`. It prefers `result.structured_content` when present; otherwise it searches MCP content blocks for a text block and parses JSON. It then verifies that the result is a dictionary. This is a deliberate compatibility strategy for the current tool return format. It does not implement a universal renderer for every possible MCP content type, binary attachment or future schema.

## 8.6 Assessment result status rules

A verified customer is required for an authoritative assessment. Missing ERP or Finance evidence can yield `partial`, with an explicit error list. The agent's business messages are built from returned structured figures and `Decimal` conversions. It does not invent missing balances or backfill unavailable results by querying an unrelated in-memory tool.

## 8.7 Structured audit versus operational events

The audit writer includes `timestamp`, `event_type=mcp_tool_execution`, `tool`, `role`, `outcome`. The Day 4 operational writer includes `event_id`, `timestamp`, `trace_id`, `assessment_id`, event type, outcome, component, operation, optional tool and duration, optional error type. The two log shapes are intentionally different. Treating them as a single distributed trace without additional linkage would misrepresent the code.

# 9. Testing strategy, evidence and gaps

## 9.1 Layered verification model

The test suite is partitioned into `tests/unit/`, `tests/integration/` and `tests/security/`. Unit tests validate typed contracts, deterministic logic and policy decisions; integration tests connect the MCP client and server or exercise the assessment against the synthetic database; security tests cover application policy and real PostgreSQL permissions. The final acceptance script calls all tests and then performs independent demo, correlation and database configuration checks.

## 9.2 Test progression

| Milestone | Total passing tests | What was added |
|---|---:|---|
| End of Day 2 | 26 | Adapter, stdio and policy baseline |
| End of Day 3 | 41 | Agent contracts, consumption, resilience and failures |
| Day 4 observability contracts | 46 | Typed events, serialization, validation |
| Day 4 MCP event integration | 49 | Started/completed/failed events and identifiers |
| Day 4 full correlation | 50 | Eight-event assessment integration |
| Day 4 context isolation | 53 | Nested and concurrent context tests |
| Day 4 SQL privilege validation | 56 | SELECT, missing write grants and denied DELETE |

These counts are milestone snapshots from the recorded terminal sessions; they are not separate additional test suites to sum together. The final 56 is the total number of passing tests.

## 9.3 What the final suite proves

The test evidence establishes working behavior for defined local scenarios: MCP discovery and invocation, typed assessment contracts, partial/failure states, application policy decisions, event schema behavior, asynchronous context isolation, and database read-only enforcement. It also verifies that the project can still run its earlier functionality after Day 4 instrumentation changes.

The test evidence does not establish generalized fault tolerance, security against all adversarial inputs, data correctness over every temporal scenario, high-load throughput or a production service-level agreement. These missing claims are not defects in the document; they are boundaries of a four-day proof of concept.

## 9.4 Evidence files

- `results/day4_benchmark.json` contains raw per-run times and summary statistics, including mean, median, minimum, maximum and nearest-rank p95.
- `results/day4_acceptance.json` contains the five final checks with pass/fail status and details.
- Day 2–4 implementation reports in `docs/` contain milestone interpretation and limitations.
- Tests under `tests/` are executable verification and should be reviewed together with the corresponding modules.
- Commit `12b75f5` is the final recorded README completion state. The preceding operational delivery commit was `f9c6794`.

# 10. Reproducing the project

## 10.1 Prerequisites

Use Python 3.12 or newer, Docker with Compose, a running local PostgreSQL 17 container, and a local project `.env` configured using `.env.example`. Work from the repository root in a virtual environment. The published example uses WSL2 Ubuntu. The host port `55432` is bound to loopback. Consult the actual `database/` initialization and seed scripts for the project's schema-load order; this report intentionally does not invent filenames or commands that have not been verified from the repository.

## 10.2 Bootstrap and dependencies

```bash
git clone https://github.com/cpgrant/a-04-mcp-enterprise-integration.git
cd a-04-mcp-enterprise-integration
python -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Review `.env.example` and provide local environment values before starting PostgreSQL. Do not put credentials in the published README or shell history; never commit `.env`.

## 10.3 Start database and load synthetic data

```bash
docker compose up -d
docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
```

Initialize and seed the business schemas using the repository SQL scripts in `database/` and provision the `a04_reader` account with `scripts/provision_reader.py` according to its prerequisites. The provisioning script expects administrative database variables as well as `POSTGRES_READ_PASSWORD`. Provisioning is a privileged setup operation; the running adapters use the restricted reader. Existing database volumes should not be destroyed or recreated merely to reproduce the read-only demonstration.

## 10.4 Run protocol and enterprise demonstrations

```bash
python -m src.client.demo
python -m src.client.stdio_demo
python -m src.client.enterprise_demo
python -m src.agents.demo
```

The final command should print `PASS: Enterprise assessment agent`. It uses synthetic `C001` and the documented reference date. Depending on the client, JSON audit events and operational events are written to stderr. Process stdout remains reserved for MCP protocol communication where applicable.

## 10.5 Run tests and acceptance

```bash
python -m pytest tests/ -q
python -m pip check
python -m scripts.validate_project
```

The published Day 4 baseline is 56 passing tests and 5/5 acceptance checks. These numbers depend on the configured database and unchanged test suite. The acceptance script reads `results/day4_benchmark.json`; if it is missing, rerun the benchmark first.

## 10.6 Re-run the benchmark separately

```bash
python -m scripts.benchmark_day4 \
    2> /tmp/a04-benchmark-stderr.log
python -m scripts.validate_project
```

Use module execution (`python -m scripts.benchmark_day4`) from the project root. Running the file as `python scripts/benchmark_day4.py` previously produced `ModuleNotFoundError: No module named 'src'` because of import-path behavior. The module form resolves project imports consistently and is now the documented route.

## 10.7 Troubleshooting guide

| Symptom | Check | Likely resolution |
|---|---|---|
| `No module named src` | Invocation form and current directory | Run `python -m scripts.benchmark_day4` at repo root |
| Benchmark JSON missing | Benchmark process exit code / stderr | Run benchmark, inspect `/tmp/a04-benchmark-stderr.log` |
| Reader password unavailable | `.env` presence and `load_dotenv` path | Configure local `.env`; do not print secrets |
| PostgreSQL refused connection | Docker health and loopback port | Check `docker ps` and Compose health |
| Permission denied on tool | Local role selected for server | Check `AI_A04_ROLE` and policy; never bypass policy silently |
| SQL write denied | Reader role and read-only default | This is expected for `a04_reader` |
| Tool error during assessment | MCP stderr/audit plus error list | Distinguish denied tool, missing tool and adapter failure |
| Incomplete distributed trace | Server audit lacks shared IDs | Current known limitation; do not claim full cross-process correlation |

## 10.8 Clean Git publication

The project is kept as a normal source repository; credentials stay local. Before publishing a documentation revision, inspect `git status -sb`, run tests and `git diff --check`, stage only intended source and reports, and push once the branch is clean. The Day 4 operational commit was followed by a README correction commit because the original status still said Day 4 was planned. This is a useful example of documentation being a maintained engineering artifact rather than a one-time export.

# 11. Risks, constraints and technical debt

| Risk or limitation | Current status | Recommended future control |
|---|---|---|
| Local role environment can be set by launcher | Demonstration-only authorization | Authenticated identity and server-verified claims |
| Server audit lacks agent trace IDs | Distinct audit and operational streams | Cross-process trace context and durable audit indexing |
| New server subprocess for each assessment | Dominates latency | Persistent connection benchmark and lifecycle policy |
| Finance `as_of` is not full historical snapshot | Payment cutoff incomplete | Temporal ledger semantics and historical queries |
| Synthetic datasets are small | Limited performance realism | Volume, skew, missing-value and concurrency tests |
| Agent runs a fixed plan | No model planner | Governed optional planner with explicit tool constraints |
| Business results contain evidence payload | Access policy on returned data not modeled | Output filtering, least-privilege evidence and data classification |
| No real-world identity federation | Local prototype | OAuth/OIDC and policy decision service |
| No durable telemetry backend | Logs emitted locally | Event collection, retention and correlation |
| No writes to business systems | Intentionally read-only | Human approvals, transaction controls and audit for actions |

## 11.1 Suggested next technical experiments

A focused continuation would compare two otherwise identical assessment paths: (a) one new stdio server process per request and (b) a reused persistent connection. Record warm and cold throughput, per-assessment latency, failure/restart behavior and role-binding implications. A second experiment could send a correlation identifier across the MCP request into the server audit stream and assert that the trace spans both processes. Neither enhancement is necessary to establish the present project's declared scope.

## 11.2 Integration roadmap across the portfolio

**AI-A02:** bring the MCP client into the agent orchestration architecture, distinguishing supervisor delegation from data-access tools. **AI-A03:** expose an enterprise knowledge retrieval function through MCP, retaining provenance and retrieval freshness metadata. **AI-A05:** replace the illustrative launcher role with more comprehensive policy decision/enforcement, identity context, approval workflows and audit semantics. **Autonomous Enterprise:** progressively combine business state, governed tool access, simulation and human authorization without assuming tool connectivity alone equals autonomy.

# 12. Lessons learned and architecture implications

## 12.1 Interface-first implementation reduces ambiguity

Building the small Day 1 server before connecting PostgreSQL helped isolate the protocol problem. The Day 2 adapters could be added as an increment rather than becoming entangled with an unresolved client/server communication design. Keeping the original in-memory tools makes that development step visible.

## 12.2 Enterprise data access is not just an LLM prompt

Day 3 shows that a credible business assessment requires typed identity, explicit tool contracts, returned evidence, source identifiers, partial-failure semantics and domain rules. Natural-language fluency by itself would not supply those guarantees. The project is therefore a useful precursor to introducing a reasoning model, not a substitute for tested enterprise integration.

## 12.3 Permission models need two independent checks

The default-deny MCP policy addresses which business capabilities are available to the local role. The PostgreSQL reader role restricts the underlying database even when adapter code is exercised. Testing both boundaries yields stronger practical evidence than asserting one configuration switch.

## 12.4 Observability must match process topology

The Day 4 correlation work is meaningful because it follows the actual Python agent and client execution context. The fact that server audit events lack those IDs is also meaningful: the process boundary interrupts the trace. An architecture diagram should reflect this rather than draw a continuous trace that the code has not implemented.

## 12.5 Benchmarks should test the whole workflow

Three tool calls that take roughly 22 ms collectively can coexist with a roughly 594 ms full assessment. Only end-to-end measurement and startup instrumentation revealed the major cost. An operational architecture needs both granular and holistic measurements, interpreted with correct statistical caution.

## 12.6 Completion criteria are not production readiness

The final 56-test suite and five acceptance checks establish a successful, bounded local outcome. Production readiness would need additional threat modeling, stronger identity, recovery, data governance, scale, deployment, service-level targets, and operational ownership. Explicit boundaries make the portfolio case stronger by preserving engineering credibility.

# 13. Architecture artifact and documentation index

## 13.1 Source documentation

| Artifact | Repository path | Purpose |
|---|---|---|
| README | `README.md` | Project narrative and quick start |
| Architecture summary | `docs/AI-A04-Complete-Architecture-Report.md` | Concise 14-section design summary |
| Day 2 record | `docs/AI-A04-Day2-Implementation.md` | Database and governance implementation |
| Day 3 record | `docs/AI-A04-Day3-Implementation.md` | Agent and MCP client implementation |
| Day 4 record | `docs/AI-A04-Day4-Implementation.md` | Observability, benchmark, security |
| Architecture decisions | `docs/adr/` | Decisions and rationale |
| Benchmark | `results/day4_benchmark.json` | Raw and summary local timings |
| Acceptance | `results/day4_acceptance.json` | Final five-check record |

## 13.2 Diagram and infographic index

| Visual | Repository path | Intended use |
|---|---|---|
| System context | `diagrams/rendered/01-system-context.png` | External actors and boundaries |
| Container architecture | `diagrams/rendered/02-container-architecture.png` | Running components |
| Tool invocation | `diagrams/rendered/03-tool-invocation.png` | Protocol execution path |
| Trust boundaries | `diagrams/rendered/04-trust-boundaries.png` | Governance interpretation |
| AI-A04-1 | `infographics/AI-A04-1-MCP-Architecture-Foundation.png` | Day 1 presentation |
| AI-A04-2 | `infographics/AI-A04-2-Enterprise-Integration-Governance.png` | Day 2 presentation |
| AI-A04-3 | `infographics/AI-A04-3-Agent-Consumption-Interoperability.png` | Day 3 presentation |
| AI-A04-4 | `infographics/AI-A04-4-Operational-Validation-Observability.png` | Day 4 presentation |

## 13.3 GitHub references

Repository: <https://github.com/cpgrant/a-04-mcp-enterprise-integration>
Architecture summary: <https://github.com/cpgrant/a-04-mcp-enterprise-integration/blob/main/docs/AI-A04-Complete-Architecture-Report.md>
Day 4 benchmark: <https://github.com/cpgrant/a-04-mcp-enterprise-integration/blob/main/results/day4_benchmark.json>
Day 4 acceptance: <https://github.com/cpgrant/a-04-mcp-enterprise-integration/blob/main/results/day4_acceptance.json>
Final documented README commit: `12b75f5`.

# 14. Conclusion

Across four incremental days, AI-A04 progressed from protocol proof through governed, PostgreSQL-backed enterprise integration to a deterministic assessment agent and finally a measured, validated operational demonstration. The strongest evidence is concrete: nine MCP tools, three business schemas, synthetic relational data, typed assessment contracts, server-side tool policy, independently restricted database access, 56 passing tests, five acceptance checks, eight correlated agent/client events and ten measured benchmark runs.

The principal architectural lesson is that **MCP provides an interface boundary, while usable enterprise AI requires contracts, domain semantics, authorization, evidence, resilience and observability around that boundary**. The implementation is explicitly local and limited, but it is sufficiently structured to support focused extensions into orchestration, knowledge retrieval and enterprise governance. As a portfolio artifact, its value lies not only in the final diagrams but in the visible decisions, trade-offs, implementation path and test evidence.

---

# Appendix A — Four-day milestone summary

| Day | Question answered | Implementation evidence | Milestone tests |
|---|---|---|---:|
| 1 | Can a client discover and invoke MCP capabilities? | Server, resource, in-process and stdio demos | Initial baseline |
| 2 | Can one MCP boundary span governed CRM/ERP/Finance data? | Adapters, PostgreSQL, reader, policy/audit | 26 |
| 3 | Can an agent turn three enterprise tools into evidence-backed output? | Contracts, agent, reusable MCP client | 41 |
| 4 | Can the behavior be traced, measured and accepted? | Event model, benchmark, privilege tests, acceptance | 56 |

# Appendix B — Detailed source-level acceptance inventory

**Protocol:** register tools and a catalog resource; discover tools; invoke both original and database-backed capabilities; exchange responses over stdio. **Integration:** execute real read-only CRM, ERP and finance queries against local synthetic data and maintain source fields. **Policy:** verify role matrix, deny unknown and blocked roles, and prevent unauthorized tool function execution. **Agent:** verify request validation, customer verification, order/financial evidence, recommendations and status transitions for partial or failed dependencies. **Observability:** validate event model, timestamps, serialized outcomes, nonnegative durations, per-tool events and full assessment correlation. **Concurrency:** verify that parallel asynchronous correlation contexts do not contaminate one another. **Data security:** assert SELECT access, absence of table write privileges, and a rejected DELETE even when a transaction requests read-write mode. **Acceptance:** run the complete suite, agent demo, correlation check, role/default read-only query and benchmark evidence validation.

# Appendix C — Reproduction and evidence checklist

- [ ] Repository cloned at expected branch and virtual environment activated.
- [ ] `.env` configured locally without exposing or committing credentials.
- [ ] PostgreSQL 17 service healthy on loopback port 55432.
- [ ] CRM, ERP and finance tables loaded with synthetic seed data.
- [ ] `a04_reader` provisioned and select-only access verified.
- [ ] In-process and stdio demonstrations run.
- [ ] Enterprise domain demonstration run.
- [ ] ACME assessment returns completed status and three evidence items.
- [ ] Complete pytest suite passes.
- [ ] Eight client/agent execution events share IDs.
- [ ] Benchmark JSON exists and contains ten measured runs.
- [ ] Acceptance JSON records five passing checks.
- [ ] Diagram/infographic paths resolve in README.
- [ ] Architecture limitations remain visible in published documentation.

# Appendix D — Evidence accuracy and non-claims

This report uses direct repository source and published JSON where accessible. Exact claims of production service behavior, persistent connection performance, authenticated remote user identity, distributed tracing, automatic financial risk decisions, production data freshness and full historical financial semantics would exceed the available evidence. The described ACME balances are synthetic and specific to the seeded local environment. The 56 test count and benchmark statistics are recorded outputs from 6 November 2026 rather than fresh executions by the report author. This retrospective does not change the repository or silently certify the environment at a later date.
