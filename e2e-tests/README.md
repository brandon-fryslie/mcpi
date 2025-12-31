# E2E Tests for mcpi

True end-to-end tests that exercise the actual mcpi CLI via subprocess calls.

## What Makes These "True" E2E Tests

1. **Isolated HOME directory** - Each test gets a temp directory set as `$HOME`
2. **Real CLI via subprocess** - Tests call `mcpi add`, `mcpi list`, etc. as shell commands
3. **Assert against actual files** - Tests read and validate the JSON config files written to disk

This validates the complete user experience from command line to file output.

## Test Structure

```
e2e-tests/
├── conftest.py              # e2e_mode fixture (requires MCPI_E2E_MODE=1)
├── tier1/
│   └── test_basic_install.py  # CLI tests with isolated HOME
└── tier2/                     # Future: Docker + MCP protocol tests
```

## Running Tests

### Prerequisites
- mcpi installed: `uv sync`
- Python 3.12+

### Run Tier 1 Tests

```bash
MCPI_E2E_MODE=1 uv run pytest e2e-tests/tier1/ -v
```

### What Gets Tested

| Test Class | What It Does |
|------------|--------------|
| TestCLISearch | `mcpi search -q filesystem` returns results |
| TestCLIInfo | `mcpi info @anthropic/filesystem` shows server details |
| TestCLIAdd | `mcpi add` creates config files with correct JSON |
| TestCLIRemove | `mcpi remove` deletes server from config file |
| TestCLIList | `mcpi list` shows installed servers |
| TestCLIEnableDisable | `mcpi disable/enable` modifies config files correctly |
| TestCLIDryRun | `mcpi add --dry-run` doesn't create files |

## How Isolation Works

Each test:
1. Creates a temp directory (`/tmp/pytest-xxx/test_xxx/home/`)
2. Sets up Claude directory structure (`.claude/`, `.config/claude/`)
3. Sets `HOME` environment variable to point to temp directory
4. Runs mcpi CLI via subprocess - Path.home() returns the temp directory
5. Asserts against files in the temp directory

```python
@pytest.fixture
def e2e_home(tmp_path):
    """Create isolated HOME with Claude structure."""
    home = tmp_path / "home"
    home.mkdir()
    (home / ".claude").mkdir()
    return home

@pytest.fixture
def run_mcpi(e2e_home):
    """Run mcpi with isolated HOME."""
    def run(*args):
        env = {"HOME": str(e2e_home), ...}
        return subprocess.run(["mcpi", *args], env=env)
    return run
```

## Adding New Tests

```python
@pytest.mark.e2e
@pytest.mark.tier1
class TestNewFeature:
    def test_something(self, e2e_mode, run_mcpi, claude_config_path):
        # Call CLI
        result = run_mcpi("some-command", "--option", "value")
        assert result.returncode == 0

        # Verify actual file contents
        config = json.loads(claude_config_path.read_text())
        assert "expected_key" in config
```

## CI Integration

Tier 1 tests run on every PR:

```yaml
- name: Run E2E Tests
  env:
    MCPI_E2E_MODE: "1"
  run: uv run pytest e2e-tests/tier1/ -v --tb=short
```
