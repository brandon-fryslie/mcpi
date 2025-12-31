"""MCP Protocol testing utilities.

Provides helpers for validating MCP servers respond correctly
to protocol messages.
"""

import json
import os
import subprocess
from typing import Any, Optional


class MCPServerTester:
    """Test MCP server protocol compliance.

    Starts an MCP server process and validates it responds
    to the MCP protocol initialize handshake.

    Usage:
        tester = MCPServerTester("npx", ["-y", "@anthropic/mcp-server-memory"])
        if tester.start():
            print("Server responds to MCP protocol")
        tester.stop()
    """

    def __init__(
        self,
        command: str,
        args: list[str],
        env: Optional[dict[str, str]] = None,
    ):
        """Initialize server tester.

        Args:
            command: Server command (e.g., "npx", "python")
            args: Command arguments
            env: Additional environment variables
        """
        self.command = command
        self.args = args
        self.env = env or {}
        self.proc: Optional[subprocess.Popen] = None
        self._response: Optional[dict] = None

    def start(self, timeout: float = 30.0) -> bool:
        """Start server and verify it responds to initialize.

        Sends MCP initialize request and waits for response.

        Args:
            timeout: Seconds to wait for response

        Returns:
            True if server responded with valid MCP response
        """
        # Build environment
        full_env = os.environ.copy()
        full_env.update(self.env)

        try:
            self.proc = subprocess.Popen(
                [self.command, *self.args],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=full_env,
            )

            # Send MCP initialize request
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "mcpi-e2e-test", "version": "1.0.0"},
                },
            }

            request_line = json.dumps(init_request) + "\n"
            self.proc.stdin.write(request_line.encode())
            self.proc.stdin.flush()

            # Wait for response with timeout
            import select
            import sys

            if sys.platform == "win32":
                # Windows doesn't support select on pipes
                # Use communicate with timeout instead
                try:
                    stdout, _ = self.proc.communicate(timeout=timeout)
                    if stdout:
                        # Try to parse first line as JSON
                        first_line = stdout.decode().split("\n")[0]
                        self._response = json.loads(first_line)
                        return "result" in self._response or "error" in self._response
                except subprocess.TimeoutExpired:
                    return False
            else:
                # Unix: use select for non-blocking read
                ready, _, _ = select.select([self.proc.stdout], [], [], timeout)
                if not ready:
                    return False

                response_line = self.proc.stdout.readline()
                if not response_line:
                    return False

                self._response = json.loads(response_line.decode())
                return "result" in self._response or "error" in self._response

        except (json.JSONDecodeError, OSError, subprocess.SubprocessError):
            return False

        return False

    def stop(self) -> None:
        """Stop the server process."""
        if self.proc:
            try:
                self.proc.terminate()
                self.proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait()
            finally:
                self.proc = None

    @property
    def response(self) -> Optional[dict]:
        """Get the initialize response if available."""
        return self._response

    def get_server_info(self) -> Optional[dict[str, Any]]:
        """Extract server info from initialize response.

        Returns:
            Server info dict with name, version, etc.
        """
        if self._response and "result" in self._response:
            return self._response["result"].get("serverInfo")
        return None

    def get_capabilities(self) -> Optional[dict[str, Any]]:
        """Extract capabilities from initialize response.

        Returns:
            Capabilities dict
        """
        if self._response and "result" in self._response:
            return self._response["result"].get("capabilities")
        return None

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensure cleanup."""
        self.stop()
        return False
