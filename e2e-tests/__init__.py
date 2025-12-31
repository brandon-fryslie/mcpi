"""E2E test suite for mcpi.

This package contains end-to-end tests that validate real user workflows
with actual package managers, file systems, and MCP servers.

Test Tiers:
- tier1/: Integration tests (no Docker required)
- tier2/: Docker-based E2E tests with MCP protocol validation

Run with: MCPI_E2E_MODE=1 pytest e2e-tests/ -v
"""
