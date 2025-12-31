# E2E Test Framework Proposal

## Executive Summary

Create a Docker-based end-to-end test framework that validates real user workflows with actual package managers, file systems, and MCP servers. This ensures mcpi works correctly in production environments, not just with mocks.

---

## Current State Analysis

### Existing Test Infrastructure (1331 tests)

**Strengths:**
- `MCPTestHarness` provides isolated temp directories
- Good coverage of file operations and scope management
- Tests use real JSON parsing and file I/O
- Well-structured workflow tests in `test_e2e_workflows.py`

**Limitations:**
- Package installation is mocked (no real npm/pip calls)
- No validation that installed servers actually work
- No testing with real Claude Code client
- No cross-platform verification
- Config file paths are overridden, not real locations

### External Dependencies

mcpi interacts with these external systems:

| System | Purpose | Currently Tested? |
|--------|---------|-------------------|
| npm/npx | Install npm-based MCP servers | Mocked |
| pip/uv | Install Python-based MCP servers | Mocked |
| git | Clone git-based MCP servers | Mocked |
| fzf | Interactive TUI browser | Not tested |
| Claude CLI | Discovery mode, catalog add | Mocked |
| File system | Config files (~/.claude/, .mcp.json) | Temp dirs |
| MCP servers | Actually running servers | Never tested |

---

## Proposed E2E Test Tiers

### Tier 1: Integration Tests (No Docker)
**What:** Real package managers, temp config directories
**Run time:** 2-5 minutes
**CI:** On every PR

```
┌─────────────────────────────────────┐
│  Tier 1: Integration (Local)        │
├─────────────────────────────────────┤
│  - Real npm/pip/uv commands         │
│  - Real catalog lookups             │
│  - Temp config directories          │
│  - Verify files created correctly   │
│  - Skip if package manager missing  │
└─────────────────────────────────────┘
```

**Tests:**
- `mcpi add filesystem` → npm install @modelcontextprotocol/server-filesystem
- `mcpi add mcp-server-git` → pip install mcp-server-git
- `mcpi list` → shows installed servers
- `mcpi disable/enable` → toggles work correctly
- `mcpi rescope` → moves between scopes

### Tier 2: Docker E2E Tests
**What:** Complete environment with all dependencies
**Run time:** 10-20 minutes
**CI:** Nightly or pre-release

```
┌─────────────────────────────────────────────────────┐
│  Tier 2: Docker E2E                                  │
├─────────────────────────────────────────────────────┤
│  Docker Container:                                   │
│  ┌─────────────────────────────────────────────┐    │
│  │  - Node.js 20+ (npm, npx)                   │    │
│  │  - Python 3.12+ (pip, uv)                   │    │
│  │  - Git                                       │    │
│  │  - fzf                                       │    │
│  │  - Claude Code (optional, for discovery)    │    │
│  │  - Home directory structure (~/.claude/)    │    │
│  │  - mcpi installed from source               │    │
│  └─────────────────────────────────────────────┘    │
│                                                      │
│  Tests run INSIDE container with real paths:        │
│  - ~/.claude/settings.json                          │
│  - ~/.config/claude/settings.json                   │
│  - ./.mcp.json (project scope)                      │
│  - Real package installations                        │
│  - MCP server process verification                   │
└─────────────────────────────────────────────────────┘
```

**Tests:**
- Full user journey: search → info → add → verify running → disable → remove
- Multi-client: add to Claude Code, verify in Cursor
- Scope precedence: project overrides user
- Real MCP server health checks (can server respond?)
- Cross-scope rescope operations

### Tier 3: MCP Server Validation
**What:** Verify installed servers actually work
**Run time:** 5-10 minutes per server
**CI:** Weekly or on catalog changes

```
┌─────────────────────────────────────────────────────┐
│  Tier 3: Server Validation                           │
├─────────────────────────────────────────────────────┤
│  For each cataloged server:                          │
│  1. mcpi add <server>                               │
│  2. Start server process                             │
│  3. Send MCP protocol handshake                      │
│  4. Verify tools/resources advertised                │
│  5. Stop server, verify cleanup                      │
└─────────────────────────────────────────────────────┘
```

---

## Docker Architecture

### Dockerfile

```dockerfile
# e2e-tests/Dockerfile
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    fzf \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs

# Install uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Create test user with home directory
RUN useradd -m testuser
USER testuser
WORKDIR /home/testuser

# Create Claude Code directory structure
RUN mkdir -p ~/.claude ~/.config/claude

# Copy mcpi source
COPY --chown=testuser:testuser . /home/testuser/mcpi

# Install mcpi
WORKDIR /home/testuser/mcpi
RUN uv sync --dev

# Set entrypoint
ENTRYPOINT ["uv", "run", "pytest"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  e2e-tests:
    build:
      context: .
      dockerfile: e2e-tests/Dockerfile
    volumes:
      - ./e2e-tests:/home/testuser/mcpi/e2e-tests:ro
      - e2e-npm-cache:/home/testuser/.npm
      - e2e-uv-cache:/home/testuser/.cache/uv
    environment:
      - HOME=/home/testuser
      - MCPI_E2E_MODE=1
    command: ["e2e-tests/", "-v", "--tb=short"]

  # Optional: Run specific test matrix
  e2e-python312:
    extends: e2e-tests
    build:
      args:
        PYTHON_VERSION: "3.12"

  e2e-python313:
    extends: e2e-tests
    build:
      args:
        PYTHON_VERSION: "3.13"

volumes:
  e2e-npm-cache:
  e2e-uv-cache:
```

---

## E2E Test Structure

### Directory Layout

```
e2e-tests/
├── Dockerfile
├── docker-compose.yml
├── conftest.py              # E2E-specific fixtures
├── test_user_journeys.py    # Complete user workflows
├── test_package_install.py  # Real package installation
├── test_multi_client.py     # Cross-client operations
├── test_server_health.py    # MCP protocol validation
└── fixtures/
    ├── project/             # Sample project with .mcp.json
    └── servers/             # Known-good server configs
```

### Key Fixtures

```python
# e2e-tests/conftest.py
import pytest
import os
import subprocess

@pytest.fixture(scope="session")
def e2e_mode():
    """Ensure we're running in E2E mode (Docker or explicit)."""
    if not os.environ.get("MCPI_E2E_MODE"):
        pytest.skip("E2E tests require MCPI_E2E_MODE=1")

@pytest.fixture
def clean_home(tmp_path, monkeypatch):
    """Isolated home directory with real structure."""
    home = tmp_path / "home"
    home.mkdir()
    (home / ".claude").mkdir()
    (home / ".config" / "claude").mkdir(parents=True)
    monkeypatch.setenv("HOME", str(home))
    return home

@pytest.fixture
def mcpi_cli():
    """Run mcpi CLI and return result."""
    def run(*args, check=True):
        result = subprocess.run(
            ["mcpi", *args],
            capture_output=True,
            text=True,
        )
        if check and result.returncode != 0:
            raise RuntimeError(f"mcpi {args} failed: {result.stderr}")
        return result
    return run

@pytest.fixture
def verify_server_responds():
    """Verify an MCP server can respond to protocol messages."""
    def verify(command, args):
        # Start server process
        proc = subprocess.Popen(
            [command, *args],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Send MCP initialize request
        init_request = '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"1.0"}}\n'
        proc.stdin.write(init_request.encode())
        proc.stdin.flush()

        # Wait for response (with timeout)
        import select
        ready, _, _ = select.select([proc.stdout], [], [], 5.0)
        if not ready:
            proc.kill()
            return False

        response = proc.stdout.readline()
        proc.kill()

        # Verify valid JSON response
        import json
        try:
            data = json.loads(response)
            return "result" in data or "error" in data
        except:
            return False

    return verify
```

### Sample E2E Test

```python
# e2e-tests/test_user_journeys.py
import json
import pytest

class TestCompleteServerInstallation:
    """Test the complete user journey of installing an MCP server."""

    def test_install_filesystem_server(self, e2e_mode, clean_home, mcpi_cli, verify_server_responds):
        """
        User Journey: Install and verify filesystem MCP server

        1. Search catalog for filesystem server
        2. View server info
        3. Add server to user scope
        4. Verify config file created
        5. Verify server responds to MCP protocol
        6. Disable server
        7. Enable server
        8. Remove server
        """
        # Step 1: Search (verify server exists)
        result = mcpi_cli("catalog", "search", "filesystem")
        assert "filesystem" in result.stdout

        # Step 2: Info
        result = mcpi_cli("catalog", "info", "filesystem")
        assert "command" in result.stdout

        # Step 3: Add
        result = mcpi_cli("add", "filesystem", "--client", "claude-code", "--scope", "user-internal")
        assert "Added" in result.stdout or "success" in result.stdout.lower()

        # Step 4: Verify config file
        config_path = clean_home / ".claude" / ".claude.json"
        assert config_path.exists(), f"Config should exist at {config_path}"

        config = json.loads(config_path.read_text())
        assert "mcpServers" in config
        assert "filesystem" in config["mcpServers"]

        server_config = config["mcpServers"]["filesystem"]
        assert "command" in server_config
        assert "args" in server_config

        # Step 5: Verify server responds (REAL E2E!)
        assert verify_server_responds(
            server_config["command"],
            server_config["args"]
        ), "Server should respond to MCP protocol"

        # Step 6: Disable
        result = mcpi_cli("disable", "filesystem")
        assert "disabled" in result.stdout.lower()

        # Verify removed from config
        config = json.loads(config_path.read_text())
        assert "filesystem" not in config.get("mcpServers", {})

        # Step 7: Enable
        result = mcpi_cli("enable", "filesystem")
        assert "enabled" in result.stdout.lower()

        # Verify back in config
        config = json.loads(config_path.read_text())
        assert "filesystem" in config["mcpServers"]

        # Step 8: Remove
        result = mcpi_cli("remove", "filesystem", "--client", "claude-code")
        assert "removed" in result.stdout.lower() or "success" in result.stdout.lower()

        # Verify config empty
        config = json.loads(config_path.read_text())
        assert "filesystem" not in config.get("mcpServers", {})
```

---

## CI/CD Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/e2e-tests.yml
name: E2E Tests

on:
  push:
    branches: [main, develop]
  pull_request:
  schedule:
    - cron: '0 0 * * *'  # Nightly

jobs:
  tier1-integration:
    name: Tier 1 - Integration Tests
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, macos-latest]
        python: ['3.12', '3.13']
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python }}
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
      - name: Install uv
        run: curl -LsSf https://astral.sh/uv/install.sh | sh
      - name: Install mcpi
        run: uv sync --dev
      - name: Run Tier 1 Tests
        env:
          MCPI_E2E_MODE: 1
        run: uv run pytest e2e-tests/tier1/ -v --tb=short

  tier2-docker:
    name: Tier 2 - Docker E2E Tests
    runs-on: ubuntu-latest
    needs: tier1-integration
    steps:
      - uses: actions/checkout@v4
      - name: Build E2E Docker image
        run: docker-compose -f e2e-tests/docker-compose.yml build
      - name: Run E2E Tests
        run: docker-compose -f e2e-tests/docker-compose.yml run e2e-tests
      - name: Upload logs on failure
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: e2e-logs
          path: e2e-tests/*.log

  tier3-server-validation:
    name: Tier 3 - Server Validation
    runs-on: ubuntu-latest
    if: github.event_name == 'schedule' || contains(github.event.head_commit.message, '[validate-servers]')
    steps:
      - uses: actions/checkout@v4
      - name: Build validation image
        run: docker build -f e2e-tests/Dockerfile.validation -t mcpi-validation .
      - name: Validate catalog servers
        run: docker run mcpi-validation python validate_servers.py
        timeout-minutes: 60
```

---

## Implementation Phases

### Phase 1: Foundation (Complexity: Low)
- Create `e2e-tests/` directory structure
- Add Dockerfile with basic dependencies
- Create `conftest.py` with core fixtures
- Write 3-5 basic installation tests
- Add `pytest.mark.e2e` marker for selection

### Phase 2: Core Workflows (Complexity: Medium)
- Test all major CLI commands with real operations
- Add multi-client tests (Claude Code, Cursor)
- Add scope management tests
- Add error handling tests (missing npm, bad permissions)
- Integrate with CI (Tier 1 only initially)

### Phase 3: Server Validation (Complexity: Medium)
- Create MCP protocol verification fixture
- Test that installed servers actually respond
- Add server health check tests
- Create catalog validation script

### Phase 4: Full CI Integration (Complexity: Low)
- Add Docker-based tests to CI
- Add nightly server validation
- Add cross-platform matrix (Linux, macOS)
- Add Python version matrix (3.12, 3.13)

---

## Test Selection

```bash
# Run only e2e tests
pytest e2e-tests/ -v

# Run specific tier
pytest e2e-tests/tier1/ -v  # Fast, no Docker
pytest e2e-tests/tier2/ -v  # Docker required

# Run with Docker
docker-compose -f e2e-tests/docker-compose.yml run e2e-tests

# Run server validation only
docker-compose -f e2e-tests/docker-compose.yml run e2e-tests e2e-tests/test_server_health.py

# Skip e2e in normal test runs
pytest tests/ --ignore=e2e-tests/
```

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Tier 1 test count | 20+ tests |
| Tier 2 test count | 15+ tests |
| Tier 3 coverage | All catalog servers validated |
| CI run time (Tier 1) | < 5 minutes |
| CI run time (Tier 2) | < 20 minutes |
| Flakiness rate | < 1% |

---

## Risks and Mitigations

| Risk | Mitigation |
|------|------------|
| Flaky tests from network issues | Cache npm/pip packages, retry logic |
| Slow test runs | Parallel execution, tier separation |
| Docker not available on all CI runners | Tier 1 tests work without Docker |
| Package manager version differences | Pin versions in Dockerfile |
| MCP server changes breaking tests | Weekly validation, auto-issue creation |

---

## Decision Points

Before implementation, need to clarify:

1. **Scope of Tier 3**: Test ALL catalog servers, or just "reference" servers?
2. **CI resources**: How many minutes/month for Docker builds?
3. **Cross-platform**: Test Windows? (Docker for Windows is complex)
4. **Claude CLI testing**: Mock or skip discovery mode tests?

---

*Generated: 2025-12-09*
*Status: PROPOSAL - Awaiting review*
