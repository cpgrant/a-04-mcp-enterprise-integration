# ADR-003: Enterprise Adapter Architecture

Status: Accepted

## Context
Enterprise systems use different APIs, schemas,
authentication mechanisms, and data models.

## Decision
Separate MCP tool definitions from enterprise-specific
adapters.

## Rationale
- Clear separation of concerns
- Easier testing and mocking
- Reusable integration interfaces
- Ability to replace underlying systems

## Consequences
Adapters require explicit contracts and error handling.
Business logic must not be duplicated across MCP tools.
