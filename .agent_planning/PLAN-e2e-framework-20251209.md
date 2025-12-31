# E2E Test Framework Implementation Plan

**Date:** 2025-12-09
**Status:** READY FOR IMPLEMENTATION
**Complexity:** Medium (4 phases, ~20-30 files)

---

## Research Decisions Applied

| Decision | Choice | Impact |
|----------|--------|--------|
| Tier 3 Scope | 6 reference servers | Fast validation (~5 min) |
| Windows | Native Tier 1 only | Simpler CI, full coverage |
| Auth Testing | Startup validation | No credential burden |

**Reference Servers:** filesystem, memory, sqlite, time, sequentialthinking, context7

---

## Phase 1: Foundation

**Goal:** Establish e2e test infrastructure with basic tests

### Files to Create

```
e2e-tests/
├── __init__.py
├── conftest.py              # Core fixtures
├── pytest.ini               # E2E-specific pytest config
├── Dockerfile               # Test environment
├── docker-compose.yml       # Container orchestration
├── README.md                # Usage documentation
└── tier1/
    ├── __init__.py
    └── test_basic_install.py  # First 5 tests
```

### Key Implementation: conftest.py

```python
import os
import json
import subprocess
import pytest
from pathlib import Path

@pytest.fixture(scope="session")
def e2e_mode():
    """Skip if not in E2E mode."""
    if not os.environ.get("MCPI_E2E_MODE"):
        pytest.skip("E2E tests require MCPI_E2E_MODE=1")

@pytest.fixture
def clean_home(tmp_path, monkeypatch):
    """Isolated home directory with Claude structure."""
    home = tmp_path / "home"
    home.mkdir()
    (home / ".claude").mkdir()
    (home / ".config" / "claude").mkdir(parents=True)
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))  # Windows
    return home

@pytest.fixture
def mcpi_cli(clean_home):
    """Run mcpi CLI commands."""
    def run(*args, check=True, timeout=60):
        result = subprocess.run(
            ["mcpi", *args],
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ, "HOME": str(clean_home)},
        )
        if check and result.returncode != 0:
            raise RuntimeError(f"mcpi {' '.join(args)} failed:\n{result.stderr}")
        return result
    return run

@pytest.fixture
def config_path(clean_home):
    """Get path to Claude config file."""
    return clean_home / ".claude" / ".claude.json"
```

### Key Implementation: Dockerfile

```dockerfile
FROM python:3.12-slim

# System deps
RUN apt-get update && apt-get install -y \
    curl git && rm -rf /var/lib/apt/lists/*

# Node.js 20
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs

# uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Test user
RUN useradd -m testuser
USER testuser
WORKDIR /home/testuser

# Claude directories
RUN mkdir -p ~/.claude ~/.config/claude

# Copy and install
COPY --chown=testuser:testuser . /home/testuser/mcpi
WORKDIR /home/testuser/mcpi
RUN uv sync

ENTRYPOINT ["uv", "run", "pytest"]
CMD ["e2e-tests/", "-v"]
```

### Key Implementation: test_basic_install.py

```python
import json
import pytest

class TestBasicInstallation:
    """Basic installation workflow tests."""

    def test_catalog_search_works(self, e2e_mode, mcpi_cli):
        """Verify catalog search returns results."""
        result = mcpi_cli("catalog", "search", "filesystem")
        assert "filesystem" in result.stdout

    def test_catalog_info_works(self, e2e_mode, mcpi_cli):
        """Verify catalog info shows server details."""
        result = mcpi_cli("catalog", "info", "@anthropic/filesystem")
        assert "command" in result.stdout or "npx" in result.stdout

    def test_add_server_creates_config(self, e2e_mode, mcpi_cli, config_path):
        """Verify adding server creates config file."""
        mcpi_cli("add", "@anthropic/filesystem",
                 "--client", "claude-code",
                 "--scope", "user-internal")

        assert config_path.exists(), f"Config should exist at {config_path}"
        config = json.loads(config_path.read_text())
        assert "mcpServers" in config

    def test_list_shows_added_server(self, e2e_mode, mcpi_cli, config_path):
        """Verify list command shows installed servers."""
        # Add server first
        mcpi_cli("add", "@anthropic/filesystem",
                 "--client", "claude-code",
                 "--scope", "user-internal")

        result = mcpi_cli("list")
        assert "filesystem" in result.stdout

    def test_remove_server_cleans_config(self, e2e_mode, mcpi_cli, config_path):
        """Verify remove cleans up config."""
        # Add then remove
        mcpi_cli("add", "@anthropic/filesystem",
                 "--client", "claude-code",
                 "--scope", "user-internal")
        mcpi_cli("remove", "@anthropic/filesystem", "--client", "claude-code")

        config = json.loads(config_path.read_text())
        servers = config.get("mcpServers", {})
        assert "filesystem" not in servers
```

### Acceptance Criteria
- [ ] `e2e-tests/` directory exists with all files
- [ ] `MCPI_E2E_MODE=1 pytest e2e-tests/tier1/ -v` passes
- [ ] Docker build succeeds: `docker build -f e2e-tests/Dockerfile .`
- [ ] All 5 basic tests pass locally

---

## Phase 2: Core Workflows

**Goal:** Complete user journey and multi-client tests

### Files to Create

```
e2e-tests/
└── tier1/
    ├── test_user_journeys.py    # Complete workflows
    ├── test_scope_management.py # Scope operations
    ├── test_enable_disable.py   # Enable/disable cycle
    └── test_error_handling.py   # Error cases
```

### Test Coverage

| Test File | Tests | Coverage |
|-----------|-------|----------|
| test_user_journeys.py | 4 | search→info→add→list→remove |
| test_scope_management.py | 4 | scope list, scope precedence, rescope |
| test_enable_disable.py | 3 | disable, enable, state persistence |
| test_error_handling.py | 4 | missing npm, bad server, permission errors |

### Key Implementation: test_user_journeys.py

```python
class TestCompleteUserJourney:
    """Test complete user workflows from start to finish."""

    def test_first_time_installation(self, e2e_mode, mcpi_cli, config_path):
        """
        Journey: New user installs their first MCP server.

        1. Search catalog for a server
        2. View server details
        3. Add server to config
        4. Verify in list
        5. Use server (verify file created)
        """
        # 1. Search
        result = mcpi_cli("catalog", "search", "time")
        assert "time" in result.stdout

        # 2. Info
        result = mcpi_cli("catalog", "info", "modelcontextprotocol/time")
        assert "npx" in result.stdout

        # 3. Add
        result = mcpi_cli("add", "modelcontextprotocol/time",
                         "--client", "claude-code",
                         "--scope", "user-internal")
        assert result.returncode == 0

        # 4. List
        result = mcpi_cli("list")
        assert "time" in result.stdout

        # 5. Verify config structure
        config = json.loads(config_path.read_text())
        assert "time" in str(config)

    def test_multi_server_workflow(self, e2e_mode, mcpi_cli, config_path):
        """Install multiple servers, verify coexistence."""
        servers = ["@anthropic/filesystem", "@anthropic/memory"]

        for server in servers:
            mcpi_cli("add", server,
                    "--client", "claude-code",
                    "--scope", "user-internal")

        result = mcpi_cli("list")
        for server in servers:
            assert server.split("/")[-1] in result.stdout
```

### Acceptance Criteria
- [ ] 15+ Tier 1 tests pass
- [ ] All user journeys covered
- [ ] Error cases handled gracefully
- [ ] Tests complete in < 3 minutes

---

## Phase 3: Server Validation (Tier 2/3)

**Goal:** Verify MCP servers actually work

### Files to Create

```
e2e-tests/
├── tier2/
│   ├── __init__.py
│   ├── conftest.py              # MCP protocol fixtures
│   └── test_server_health.py    # Server validation
└── fixtures/
    └── mcp_protocol.py          # Protocol helpers
```

### Key Implementation: MCP Protocol Fixture

```python
# e2e-tests/fixtures/mcp_protocol.py
import json
import subprocess
import select
from typing import Optional

class MCPServerTester:
    """Test MCP server protocol compliance."""

    def __init__(self, command: str, args: list, env: dict = None):
        self.command = command
        self.args = args
        self.env = env or {}
        self.proc = None

    def start(self, timeout: float = 10.0) -> bool:
        """Start server and verify it responds."""
        import os
        full_env = {**os.environ, **self.env}

        self.proc = subprocess.Popen(
            [self.command, *self.args],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=full_env,
        )

        # Send initialize request
        init_msg = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "mcpi-e2e-test", "version": "1.0.0"}
            }
        }

        try:
            self.proc.stdin.write((json.dumps(init_msg) + "\n").encode())
            self.proc.stdin.flush()

            # Wait for response
            ready, _, _ = select.select([self.proc.stdout], [], [], timeout)
            if not ready:
                return False

            response = self.proc.stdout.readline()
            data = json.loads(response)
            return "result" in data

        except Exception:
            return False

    def stop(self):
        """Stop the server."""
        if self.proc:
            self.proc.terminate()
            self.proc.wait(timeout=5)


# conftest.py fixture
@pytest.fixture
def mcp_tester():
    """Factory for MCP server testers."""
    testers = []

    def create(command, args, env=None):
        tester = MCPServerTester(command, args, env)
        testers.append(tester)
        return tester

    yield create

    # Cleanup
    for t in testers:
        t.stop()
```

### Key Implementation: test_server_health.py

```python
import pytest

# Reference servers (no auth required)
REFERENCE_SERVERS = [
    ("@anthropic/filesystem", "npx", ["-y", "@anthropic/mcp-server-filesystem", "/tmp"]),
    ("@anthropic/memory", "npx", ["-y", "@anthropic/mcp-server-memory"]),
    ("modelcontextprotocol/time", "npx", ["-y", "@modelcontextprotocol/server-time"]),
]

class TestServerHealth:
    """Verify reference servers respond to MCP protocol."""

    @pytest.mark.parametrize("name,command,args", REFERENCE_SERVERS)
    def test_server_responds_to_initialize(self, e2e_mode, mcp_tester, name, command, args):
        """Server should respond to MCP initialize request."""
        tester = mcp_tester(command, args)
        assert tester.start(timeout=30), f"{name} should respond to initialize"

    def test_installed_server_works(self, e2e_mode, mcpi_cli, config_path, mcp_tester):
        """Server installed via mcpi should actually work."""
        # Install
        mcpi_cli("add", "@anthropic/memory",
                "--client", "claude-code",
                "--scope", "user-internal")

        # Read config
        config = json.loads(config_path.read_text())
        server_config = config["mcpServers"]["@anthropic/memory"]

        # Test it works
        tester = mcp_tester(
            server_config["command"],
            server_config["args"],
            server_config.get("env", {})
        )
        assert tester.start(), "Installed server should respond"
```

### Acceptance Criteria
- [ ] MCP protocol tester works
- [ ] 6 reference servers validate successfully
- [ ] Installed servers verified working
- [ ] Tier 2 tests complete in < 10 minutes

---

## Phase 4: CI Integration

**Goal:** Automated testing in GitHub Actions

### Files to Create

```
.github/workflows/
└── e2e-tests.yml
```

### Key Implementation: e2e-tests.yml

```yaml
name: E2E Tests

on:
  push:
    branches: [main, develop]
  pull_request:
  schedule:
    - cron: '0 0 * * *'  # Nightly

env:
  MCPI_E2E_MODE: "1"

jobs:
  tier1:
    name: Tier 1 - Integration
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
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
        uses: astral-sh/setup-uv@v4

      - name: Install dependencies
        run: uv sync --dev

      - name: Run Tier 1 Tests
        run: uv run pytest e2e-tests/tier1/ -v --tb=short

  tier2:
    name: Tier 2 - Docker E2E
    runs-on: ubuntu-latest
    needs: tier1
    steps:
      - uses: actions/checkout@v4

      - name: Build Docker image
        run: docker build -f e2e-tests/Dockerfile -t mcpi-e2e .

      - name: Run E2E Tests
        run: |
          docker run --rm \
            -e MCPI_E2E_MODE=1 \
            mcpi-e2e \
            e2e-tests/tier2/ -v --tb=short

  tier3-nightly:
    name: Tier 3 - Server Validation
    runs-on: ubuntu-latest
    if: github.event_name == 'schedule'
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: '20'

      - name: Install uv
        uses: astral-sh/setup-uv@v4

      - name: Install dependencies
        run: uv sync --dev

      - name: Validate Reference Servers
        run: uv run pytest e2e-tests/tier2/test_server_health.py -v
        timeout-minutes: 20
```

### Acceptance Criteria
- [ ] Tier 1 passes on all platforms
- [ ] Tier 2 Docker tests pass
- [ ] Nightly server validation runs
- [ ] Total CI time < 15 minutes

---

## Implementation Order

```
Phase 1 (Foundation)     → PR #1
    ↓
Phase 2 (Workflows)      → PR #2
    ↓
Phase 3 (Validation)     → PR #3
    ↓
Phase 4 (CI)             → PR #4
```

Each phase is independently mergeable and valuable.

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Tier 1 tests | 15+ |
| Tier 2 tests | 10+ |
| Tier 3 coverage | 6 reference servers |
| Tier 1 CI time | < 5 min |
| Tier 2 CI time | < 15 min |
| Flakiness | < 1% |

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| npm install slow | Cache node_modules in CI |
| Server startup timeout | 30s timeout, retry once |
| Platform differences | Test on all 3 OS in Tier 1 |
| Docker build slow | Layer caching, slim base image |

---

*Plan complete. Ready for implementation.*
