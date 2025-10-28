"""Test package for mcpi."""

# Export test harness components for easy import
# noqa comment prevents Black from removing these "unused" imports
from .test_harness import (  # noqa: F401
    MCPTestHarness,
    mcp_harness,
    mcp_manager_with_harness,
    mcp_test_dir,
    prepopulated_harness,
)

__all__ = [
    "MCPTestHarness",
    "mcp_test_dir",
    "mcp_harness",
    "mcp_manager_with_harness",
    "prepopulated_harness",
]
