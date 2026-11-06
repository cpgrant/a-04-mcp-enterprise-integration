# ADR-001: Adopt the Official MCP Python SDK

Status: Accepted

## Context
Enterprise AI agents require standardized access to external
systems, tools, resources, and application capabilities.

## Decision
Use the official Model Context Protocol Python SDK v2.

The initial implementation uses MCPServer and Client.

## Rationale
- Standards-based protocol
- Tool and resource discovery
- Typed integration interfaces
- Reusable enterprise capabilities
- Interoperability with MCP-compatible hosts

## Consequences
The system depends on MCP SDK interfaces and protocol
compatibility. SDK versions must be tested and pinned.
