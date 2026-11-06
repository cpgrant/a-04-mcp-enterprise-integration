# ADR-004: Server-Side Authorization

Status: Accepted

## Context
AI agents may request access to confidential information
or privileged enterprise operations.

## Decision
Enforce authorization at the MCP server and enterprise
system boundaries.

## Requirements
- Least privilege
- Explicit tool authorization
- Input validation
- Read-only credentials for initial data access
- Audit of sensitive operations
- No reliance on LLM instructions as security controls

## Consequences
Production deployment requires trusted identity propagation,
policy enforcement, and secure secret management.
