"""E2E test configuration and shared fixtures.

These tests exercise the actual mcpi CLI via subprocess calls with
isolated HOME directories. They validate real file I/O and CLI behavior.
"""

import os

import pytest


@pytest.fixture(scope="session")
def e2e_mode():
    """Ensure E2E mode is enabled.

    E2E tests require MCPI_E2E_MODE=1 because they:
    - Call the real mcpi CLI via subprocess
    - Create real files in temp directories
    - May be slower than unit tests

    Skip if not explicitly enabled.
    """
    if not os.environ.get("MCPI_E2E_MODE"):
        pytest.skip(
            "E2E tests require MCPI_E2E_MODE=1 environment variable. "
            "Run with: MCPI_E2E_MODE=1 pytest e2e-tests/"
        )


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "e2e: mark test as end-to-end test")
    config.addinivalue_line("markers", "tier1: mark test as Tier 1 (CLI with isolated HOME)")
    config.addinivalue_line("markers", "tier2: mark test as Tier 2 (Docker + MCP protocol)")
    config.addinivalue_line("markers", "slow: mark test as slow running")
