# ADR-002: MCP Transport Strategy

Status: Accepted

## Context
The integration architecture must support both local
development and distributed deployment.

## Decision
Use in-process MCP sessions for initial functional testing,
stdio for independent local processes, and Streamable HTTP
for future networked integrations.

## Rationale
- Simple local development
- Clear separation between client and server
- Path toward distributed enterprise deployment

## Consequences
Networked deployment requires authentication,
authorization, TLS, and deployment security controls.
