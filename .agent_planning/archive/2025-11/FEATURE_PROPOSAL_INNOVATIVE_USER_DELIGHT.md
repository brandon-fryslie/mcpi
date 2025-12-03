# Feature Proposals: Innovative User Delight for MCPI

**Generated**: 2025-11-16
**Author**: Product Visionary Agent
**Context**: Post-v0.3.0 feature brainstorming
**Status**: PROPOSAL - Not committed to roadmap

---

## Executive Summary

This document presents **5 innovative, high-value feature proposals** for MCPI that go beyond incremental improvements to create genuine user delight. Each proposal solves real pain points, can be implemented in 1-4 weeks, and aligns with MCPI's core value proposition: **making MCP server management effortless**.

**Brainstorming Approach**:
- Generated 12 initial ideas across different domains
- Applied pragmatic filtering (feasibility, implementation time, user value)
- Converged to 5 proposals with highest impact-to-effort ratio
- Designed concrete implementation approaches for each

**Key Principles Applied**:
- Eliminate work rather than add features
- Solve problems users don't know they have
- Maintain simplicity despite added capability
- Build on existing plugin architecture
- Enable quick experimentation and testing

---

## Brainstorming Results: 12 Initial Ideas

Before filtering, I explored these possibilities:

### High-Impact Ideas (Pursued)
1. ✅ **Smart Profile Bundles** - Install curated server bundles by use case
2. ✅ **Intelligent Auto-Configuration** - Detect project type, suggest relevant servers
3. ✅ **Server Health Dashboard** - TUI showing real-time server status
4. ✅ **Configuration Recipes** - Share and apply complex server configurations
5. ✅ **Project-Aware Context** - Automatically scope servers based on project detection

### Medium-Impact Ideas (Considered but Deferred)
6. ⏸️ **Version Management** - Already on roadmap (v0.4.0+)
7. ⏸️ **Remote Catalog Sync** - Good but requires infrastructure (v0.5.0+)
8. ⏸️ **Web Dashboard** - High value but 4+ weeks effort (v0.6.0+)
9. ⏸️ **Server Analytics** - Privacy concerns, unclear value proposition

### Lower-Impact Ideas (Rejected)
10. ❌ **AI-Powered Search** - Clever but not valuable enough (fuzzy search sufficient)
11. ❌ **Server Marketplace** - Too complex, wrong abstraction level
12. ❌ **Configuration Migration Tool** - Already automatic, solving non-problem

**Filtering Rationale**: Focused on ideas that eliminate entire categories of friction (bundle installation, auto-detection, status visibility) rather than incremental improvements (better search, minor UX tweaks).

---

## Proposal 1: Smart Server Bundles

### Overview

**Name**: Smart Server Bundles (a.k.a. "MCP Starter Kits")

**One-Liner**: Install curated sets of MCP servers for common use cases with a single command.

**User Pain Point**:
- New users don't know which servers to install
- Setting up a complete workflow requires researching and adding 5-10 servers
- Expert users repeat the same installation pattern across projects
- No way to share "best practice" server configurations

**The Delight Factor**:
> "I just typed `mcpi bundle web-dev` and had a complete web development MCP stack in 15 seconds. I didn't even know I needed half of these servers, but they make my workflow amazing."

### Use Cases

**Use Case 1: New User Onboarding**
```bash
# User just installed MCPI, wants to start coding
$ mcpi bundle list

Available Bundles:
  web-dev       - Web development stack (filesystem, fetch, github, puppeteer)
  data-science  - Data analysis tools (postgres, sqlite, filesystem, memory)
  devops        - Infrastructure management (docker, aws, kubernetes, terraform)
  content       - Content creation (fetch, brave-search, puppeteer, filesystem)
  ai-tools      - AI/LLM workflow (memory, filesystem, context7, sequentialthinking)

$ mcpi bundle install web-dev

Installing bundle: web-dev (4 servers)
  ✓ filesystem
  ✓ fetch
  ✓ github
  ✓ puppeteer

Done! Web development bundle installed to user-global scope.
Run 'mcpi list' to see your servers.
```

**Use Case 2: Project-Specific Setup**
```bash
# Starting a new data science project
$ cd my-analytics-project
$ mcpi bundle install data-science --scope project-mcp

Installing bundle: data-science to project-mcp scope
  ✓ postgres (configured for localhost:5432)
  ✓ sqlite (configured for ./data/)
  ✓ filesystem (configured for ./data/, ./notebooks/)
  ✓ memory (for experiment tracking)

Created .mcp.json with 4 servers.
Your team can run 'mcpi bundle install data-science' to get the same setup.
```

**Use Case 3: Expert Configuration Sharing**
```bash
# Senior engineer sharing their optimized setup
$ mcpi bundle create my-stack --from-current

Created custom bundle from current configuration:
  - 8 servers included
  - Saved to ~/.mcpi/bundles/my-stack.json

Share this bundle:
  mcpi bundle share my-stack
  # Generates shareable URL: https://mcpi.dev/bundles/abc123

# Junior engineer on team
$ mcpi bundle install https://mcpi.dev/bundles/abc123
Installing custom bundle from Sarah (8 servers)...
```

### Implementation Approach

**Complexity**: 1.5 weeks

**Architecture**:
1. **Bundle Definition Format** (JSON):
```json
{
  "name": "web-dev",
  "description": "Web development stack",
  "version": "1.0.0",
  "author": "MCPI Team",
  "servers": [
    {
      "id": "filesystem",
      "config": {
        "args": ["${project_root}"]
      }
    },
    {
      "id": "github",
      "required_env": ["GITHUB_TOKEN"]
    },
    {
      "id": "puppeteer"
    },
    {
      "id": "fetch"
    }
  ],
  "suggested_scope": "project-mcp",
  "post_install_message": "Tip: Set GITHUB_TOKEN for full GitHub integration"
}
```

2. **Bundle Storage**:
   - Built-in bundles: `data/bundles/*.json`
   - User bundles: `~/.mcpi/bundles/*.json`
   - Remote bundles: Cached in `~/.mcpi/cache/bundles/`

3. **CLI Commands**:
   - `mcpi bundle list` - Show available bundles
   - `mcpi bundle info <bundle>` - Show bundle details
   - `mcpi bundle install <bundle>` - Install bundle
   - `mcpi bundle create <name>` - Create bundle from current config
   - `mcpi bundle share <name>` - Generate shareable URL (optional)

4. **Implementation Components**:
   - `src/mcpi/bundles/catalog.py` - Bundle catalog management
   - `src/mcpi/bundles/installer.py` - Bundle installation logic
   - `src/mcpi/bundles/creator.py` - Bundle creation from config
   - `data/bundles/` - Built-in bundle definitions

**Technical Considerations**:
- Use existing `MCPManager.add_server()` - no new installation logic
- Validate bundle definitions with Pydantic schema
- Handle missing servers gracefully (skip with warning)
- Support variable substitution (${project_root}, ${home})
- Transaction-like behavior (rollback on failure)

**Testing Strategy**:
- Unit tests for bundle parsing and validation
- Integration tests for bundle installation
- Test with real bundles from `data/bundles/`
- Test bundle creation from existing config
- Test error handling (missing servers, conflicts)

**Success Metrics**:
- New users can install first bundle in < 30 seconds
- Bundle installation reduces setup time by 80%
- Users report "discovering" useful servers via bundles
- Community creates and shares custom bundles

### Why This Is Exciting

1. **Eliminates Research Phase**: Users don't need to study 50+ servers to find relevant ones
2. **Enables Best Practices**: Experts can codify and share optimal configurations
3. **Accelerates Onboarding**: New users productive immediately
4. **Community Amplification**: Bundle sharing creates network effects
5. **Maintains Simplicity**: Still just installing servers, but smarter

**Anti-Patterns Avoided**:
- ❌ No server marketplace complexity
- ❌ No dependency hell (bundles are flat lists)
- ❌ No versioning conflicts (bundles don't pin versions)
- ❌ No implicit behavior (explicit list of servers)

---

## Proposal 2: Intelligent Auto-Configuration

### Overview

**Name**: Intelligent Auto-Configuration (a.k.a. "Smart Scope Detection")

**One-Liner**: MCPI detects your project type and automatically suggests relevant MCP servers with optimal configurations.

**User Pain Point**:
- Users don't know which servers are relevant for their project
- Manual configuration is tedious and error-prone
- Server arguments require reading documentation
- No guidance on scope selection

**The Delight Factor**:
> "I ran `mcpi auto` in my Django project and it said 'I see a Django project! Want me to set up postgres, filesystem, and fetch?' I said yes, and it configured everything perfectly for my project structure. It even set the database URL to my local settings."

### Use Cases

**Use Case 1: New Project Setup**
```bash
# User starts a new Python web project
$ cd my-django-app
$ mcpi auto

🔍 Detected: Django project (Python 3.12)
   Found: manage.py, settings.py, requirements.txt

📦 Suggested servers for Django projects:
   ✓ postgres      - Database access (detected: localhost:5432)
   ✓ filesystem    - File operations (project root: /home/user/my-django-app)
   ✓ fetch         - HTTP requests for APIs
   ✓ memory        - Session/cache management

Install these servers? [Y/n]: y
Scope: [project-mcp]

Installing 4 servers to project-mcp scope...
  ✓ postgres (args: postgresql://localhost:5432/myapp)
  ✓ filesystem (args: /home/user/my-django-app)
  ✓ fetch
  ✓ memory

Done! Created .mcp.json with 4 servers.
Tip: Add POSTGRES_PASSWORD to environment for database access.
```

**Use Case 2: Existing Project Enhancement**
```bash
# User has a React project, wants MCP servers
$ cd my-react-app
$ mcpi auto --enhance

🔍 Detected: React application (Node.js 20.x)
   Found: package.json, src/, public/

📦 Current MCP servers: 2 (filesystem, memory)

💡 Suggested additions based on your project:
   + github        - PR reviews, issue tracking (detected .git)
   + puppeteer     - E2E testing, screenshots
   + brave-search  - Content research
   + fetch         - API mocking, data fetching

Install suggested servers? [Y/n]: n
Show individual prompts? [y/N]: y

Install github? [Y/n]: y
Install puppeteer? [Y/n]: y
Install brave-search? [y/N]: n
Install fetch? [Y/n]: y

Installing 3 servers...
```

**Use Case 3: Monorepo Intelligence**
```bash
# User in a monorepo with multiple projects
$ cd my-monorepo
$ mcpi auto

🔍 Detected: Monorepo with 3 projects
   - frontend/ (React)
   - backend/ (FastAPI)
   - shared/ (TypeScript library)

📦 Suggested configuration:
   Scope: project-mcp (monorepo root)

   Shared servers (all projects):
   ✓ github
   ✓ memory
   ✓ filesystem (args: ./frontend, ./backend, ./shared)

   Backend-specific (add to backend/.mcp.json):
   ✓ postgres
   ✓ fetch

   Frontend-specific (add to frontend/.mcp.json):
   ✓ puppeteer
   ✓ brave-search

Create this configuration? [Y/n]: y
```

### Implementation Approach

**Complexity**: 2-3 weeks

**Architecture**:

1. **Project Detection System**:
```python
# src/mcpi/detection/detector.py
class ProjectDetector:
    """Detect project type and characteristics."""

    def detect(self, path: Path) -> ProjectInfo:
        """Detect project type."""
        # Check for framework markers
        markers = {
            'django': ['manage.py', 'settings.py'],
            'fastapi': ['main.py', 'pyproject.toml + fastapi'],
            'react': ['package.json + react', 'src/', 'public/'],
            'nextjs': ['next.config.js', 'pages/'],
            'python': ['pyproject.toml', 'setup.py', 'requirements.txt'],
            'nodejs': ['package.json'],
            'monorepo': ['pnpm-workspace.yaml', 'lerna.json']
        }

        detected = []
        for framework, markers in markers.items():
            if self._check_markers(path, markers):
                detected.append(framework)

        return ProjectInfo(
            frameworks=detected,
            language=self._detect_language(path),
            database=self._detect_database(path),
            has_git=self._has_git(path),
            structure=self._analyze_structure(path)
        )
```

2. **Recommendation Engine**:
```python
# src/mcpi/detection/recommender.py
class ServerRecommender:
    """Recommend servers based on project detection."""

    RULES = {
        'django': [
            ('postgres', 'Database access', Priority.HIGH),
            ('filesystem', 'File operations', Priority.HIGH),
            ('fetch', 'HTTP requests', Priority.MEDIUM),
            ('memory', 'Cache management', Priority.LOW),
        ],
        'react': [
            ('filesystem', 'Asset management', Priority.HIGH),
            ('puppeteer', 'E2E testing', Priority.MEDIUM),
            ('github', 'PR reviews', Priority.MEDIUM),
            ('fetch', 'API mocking', Priority.MEDIUM),
        ],
        # ... more rules
    }

    def recommend(self, project_info: ProjectInfo) -> List[Recommendation]:
        """Generate server recommendations."""
        recommendations = []

        for framework in project_info.frameworks:
            if framework in self.RULES:
                for server_id, reason, priority in self.RULES[framework]:
                    recommendations.append(Recommendation(
                        server_id=server_id,
                        reason=reason,
                        priority=priority,
                        config=self._generate_config(server_id, project_info)
                    ))

        return self._deduplicate_and_rank(recommendations)
```

3. **Configuration Generation**:
```python
# src/mcpi/detection/config_generator.py
class ConfigGenerator:
    """Generate optimal server configurations."""

    def generate(self, server_id: str, project_info: ProjectInfo) -> Dict:
        """Generate config for server based on project."""

        if server_id == 'filesystem':
            # Detect appropriate directories
            paths = []
            if project_info.has_src_dir:
                paths.append('./src')
            if project_info.has_data_dir:
                paths.append('./data')
            if not paths:
                paths.append('.')

            return {'args': [*paths]}

        elif server_id == 'postgres':
            # Detect database config
            db_url = self._detect_database_url(project_info)
            return {'args': [db_url]} if db_url else {}

        # ... more generators
```

4. **CLI Integration**:
```python
# src/mcpi/cli.py
@main.command()
@click.option('--enhance', is_flag=True, help='Suggest additions to existing setup')
@click.option('--non-interactive', is_flag=True, help='Use defaults without prompts')
@click.pass_context
def auto(ctx: click.Context, enhance: bool, non_interactive: bool):
    """Automatically detect and configure MCP servers for this project."""

    # Detect project
    detector = ProjectDetector()
    project_info = detector.detect(Path.cwd())

    # Get recommendations
    recommender = ServerRecommender()
    recommendations = recommender.recommend(project_info)

    # Interactive or auto mode
    if non_interactive:
        # Install all high-priority recommendations
        servers_to_install = [r for r in recommendations if r.priority == Priority.HIGH]
    else:
        # Show interactive prompts
        servers_to_install = prompt_user_for_servers(recommendations, project_info)

    # Install servers
    manager = get_mcp_manager(ctx)
    for rec in servers_to_install:
        manager.add_server(
            server_id=rec.server_id,
            scope='project-mcp',
            config=rec.config
        )
```

**Implementation Components**:
- `src/mcpi/detection/detector.py` - Project type detection
- `src/mcpi/detection/recommender.py` - Server recommendation engine
- `src/mcpi/detection/config_generator.py` - Configuration generation
- `src/mcpi/detection/rules.py` - Recommendation rules (extensible)
- Update `src/mcpi/cli.py` - Add `auto` command

**Technical Considerations**:
- Use file system inspection only (no network calls)
- Graceful degradation if detection fails (ask user)
- Extensible rule system for community contributions
- Support for `.mcpi.toml` to override detection
- Dry-run mode to preview recommendations

**Testing Strategy**:
- Unit tests for each project type detector
- Unit tests for recommendation rules
- Integration tests with fixture projects
- Test config generation for each server type
- Test interactive and non-interactive modes

**Success Metrics**:
- Detection accuracy > 90% for supported project types
- Users find auto-config faster than manual setup
- Recommendations rated "helpful" by users
- Reduced time-to-first-server by 60%

### Why This Is Exciting

1. **Eliminates Decision Paralysis**: Users don't need to know which servers exist
2. **Context-Aware Intelligence**: Configurations optimized for project structure
3. **Learning Tool**: Users discover servers relevant to their work
4. **Saves Time**: Setup goes from 10 minutes to 30 seconds
5. **Extensible**: Community can contribute detection rules

**Anti-Patterns Avoided**:
- ❌ No magic behavior (always shows what it will do)
- ❌ No forced installations (users approve everything)
- ❌ No network dependencies (all detection is local)
- ❌ No vendor lock-in (detection rules are open data)

---

## Proposal 3: Real-Time Server Health Dashboard

### Overview

**Name**: Server Health Dashboard (a.k.a. "MCP Status TUI")

**One-Liner**: Real-time TUI dashboard showing which MCP servers are running, healthy, and responding to requests.

**User Pain Point**:
- Users don't know if servers are actually working
- Claude errors are cryptic ("server not responding")
- No visibility into server state or errors
- Debugging server issues requires checking logs manually

**The Delight Factor**:
> "I ran `mcpi status --watch` and saw my filesystem server was red (not responding). The dashboard showed the exact error: 'Permission denied: /restricted/path'. Fixed the config in 10 seconds instead of 30 minutes of debugging."

### Use Cases

**Use Case 1: Health Check**
```bash
$ mcpi status

MCP Server Health Dashboard
═══════════════════════════

┌─────────────────┬────────────┬──────────┬────────────────────────┐
│ Server          │ Status     │ Latency  │ Last Check             │
├─────────────────┼────────────┼──────────┼────────────────────────┤
│ filesystem      │ ✓ Healthy  │ 12ms     │ 2s ago                 │
│ github          │ ✓ Healthy  │ 145ms    │ 2s ago                 │
│ postgres        │ ✗ Error    │ -        │ 2s ago                 │
│ fetch           │ ✓ Healthy  │ 8ms      │ 2s ago                 │
│ puppeteer       │ ⚠ Slow     │ 2.3s     │ 2s ago                 │
└─────────────────┴────────────┴──────────┴────────────────────────┘

Issues Found (2):
  • postgres: Connection failed - ECONNREFUSED localhost:5432
  • puppeteer: Slow response (> 1s) - Consider restarting

Run 'mcpi doctor postgres' for detailed diagnostics.
```

**Use Case 2: Live Monitoring**
```bash
$ mcpi status --watch

[Real-time updating dashboard]

MCP Server Health - Live Monitor (Ctrl+C to exit)
Updated: 2025-11-16 10:45:32 (every 5s)

┌─────────────────┬────────────┬──────────┬────────────────────────┐
│ Server          │ Status     │ Latency  │ Requests/min           │
├─────────────────┼────────────┼──────────┼────────────────────────┤
│ filesystem      │ ✓ Healthy  │ 12ms     │ 45 ███████░░░          │
│ github          │ ✓ Healthy  │ 145ms    │ 12 ██░░░░░░░░          │
│ postgres        │ ✓ Healthy  │ 23ms     │ 89 ████████████        │
│ fetch           │ ✓ Healthy  │ 8ms      │ 34 ██████░░░░░         │
└─────────────────┴────────────┴──────────┴────────────────────────┘

Recent Events:
  10:45:31  postgres     ✓ Connection restored
  10:45:15  filesystem   Request took 245ms (slow)
  10:44:52  github       ⚠ Rate limit warning (80% used)

Press 'r' to restart server, 'd' for details, 'q' to quit
```

**Use Case 3: Debugging Mode**
```bash
$ mcpi status postgres --debug

Server: postgres (scope: project-mcp)
════════════════════════════════════

Configuration:
  Command: npx -y @modelcontextprotocol/server-postgres
  Args: postgresql://localhost:5432/myapp
  Env: (none)
  Working Dir: /home/user/project

Health Check:
  Status: ✗ Error
  Last Successful: 2 minutes ago
  Error: Connection refused (ECONNREFUSED)

Connectivity Test:
  ✓ npx command found (/usr/local/bin/npx)
  ✓ Package available (@modelcontextprotocol/server-postgres)
  ✗ Database connection failed

Database Check:
  Host: localhost
  Port: 5432
  Database: myapp
  Status: ✗ Not responding

Suggested Fixes:
  1. Check PostgreSQL is running: sudo systemctl status postgresql
  2. Verify connection string in .mcp.json
  3. Check firewall: sudo ufw status
  4. Test connection: psql -h localhost -p 5432 -d myapp

Run 'mcpi doctor postgres --fix' to attempt automatic repair.
```

### Implementation Approach

**Complexity**: 3 weeks

**Architecture**:

1. **Health Check System**:
```python
# src/mcpi/health/checker.py
class HealthChecker:
    """Check MCP server health."""

    async def check_server(self, server_id: str, config: ServerConfig) -> HealthStatus:
        """Check if server is healthy."""
        try:
            # 1. Check process exists
            process_ok = await self._check_process(server_id)

            # 2. Check connectivity (send ping MCP message)
            start = time.time()
            response = await self._send_ping(config)
            latency = time.time() - start

            # 3. Parse response
            if response.success:
                return HealthStatus(
                    server_id=server_id,
                    status=Status.HEALTHY,
                    latency=latency,
                    last_check=datetime.now(),
                    error=None
                )
            else:
                return HealthStatus(
                    server_id=server_id,
                    status=Status.ERROR,
                    latency=None,
                    last_check=datetime.now(),
                    error=response.error
                )
        except Exception as e:
            return HealthStatus(
                server_id=server_id,
                status=Status.ERROR,
                latency=None,
                last_check=datetime.now(),
                error=str(e)
            )
```

2. **MCP Protocol Integration**:
```python
# src/mcpi/health/mcp_client.py
class MCPHealthClient:
    """Simple MCP client for health checks."""

    async def ping(self, config: ServerConfig) -> MCPResponse:
        """Send MCP ping request."""
        # Start server process
        process = await self._start_process(config)

        # Connect via stdio
        reader, writer = await self._connect_stdio(process)

        # Send initialize request (MCP handshake)
        await self._send_message(writer, {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {
                    "name": "mcpi-health-checker",
                    "version": "0.3.0"
                }
            }
        })

        # Read response
        response = await self._read_message(reader)

        # Clean up
        process.terminate()

        return MCPResponse(
            success=response.get('result') is not None,
            latency=...,
            error=response.get('error')
        )
```

3. **TUI Dashboard**:
```python
# src/mcpi/health/dashboard.py
from rich.live import Live
from rich.table import Table
from rich.console import Console

class HealthDashboard:
    """Real-time health dashboard."""

    def __init__(self, manager: MCPManager):
        self.manager = manager
        self.checker = HealthChecker()
        self.console = Console()

    async def run_live(self, interval: int = 5):
        """Run live dashboard with auto-refresh."""

        with Live(self._generate_table(), refresh_per_second=1) as live:
            while True:
                # Check all servers
                statuses = await self._check_all_servers()

                # Update display
                live.update(self._generate_table(statuses))

                # Wait for interval
                await asyncio.sleep(interval)

    def _generate_table(self, statuses: List[HealthStatus]) -> Table:
        """Generate rich table for display."""
        table = Table(title="MCP Server Health Dashboard")
        table.add_column("Server")
        table.add_column("Status")
        table.add_column("Latency")
        table.add_column("Last Check")

        for status in statuses:
            status_icon = "✓" if status.status == Status.HEALTHY else "✗"
            status_color = "green" if status.status == Status.HEALTHY else "red"

            table.add_row(
                status.server_id,
                f"[{status_color}]{status_icon} {status.status.value}[/]",
                f"{status.latency}ms" if status.latency else "-",
                status.last_check.strftime("%H:%M:%S")
            )

        return table
```

4. **CLI Integration**:
```python
# src/mcpi/cli.py
@main.command()
@click.option('--watch', is_flag=True, help='Live monitoring mode')
@click.option('--debug', is_flag=True, help='Show detailed diagnostics')
@click.option('--interval', type=int, default=5, help='Check interval (seconds)')
@click.argument('server_id', required=False)
@click.pass_context
async def status(
    ctx: click.Context,
    watch: bool,
    debug: bool,
    interval: int,
    server_id: Optional[str]
):
    """Show MCP server health status."""

    manager = get_mcp_manager(ctx)
    dashboard = HealthDashboard(manager)

    if server_id:
        # Single server debug mode
        if debug:
            await dashboard.show_debug(server_id)
        else:
            status = await dashboard.check_server(server_id)
            console.print(status)

    elif watch:
        # Live monitoring mode
        await dashboard.run_live(interval=interval)

    else:
        # One-time check all servers
        statuses = await dashboard.check_all()
        dashboard.display_summary(statuses)
```

**Implementation Components**:
- `src/mcpi/health/checker.py` - Health check logic
- `src/mcpi/health/mcp_client.py` - MCP protocol client
- `src/mcpi/health/dashboard.py` - TUI dashboard
- Update `src/mcpi/cli.py` - Add `status` command
- `tests/test_health_checker.py` - Unit tests
- `tests/test_mcp_client.py` - MCP protocol tests

**Technical Considerations**:
- Use `asyncio` for concurrent health checks
- Use `rich` for TUI rendering (already a dependency)
- Implement timeout for hung servers (5s default)
- Cache health status to avoid spamming servers
- Graceful degradation if MCP protocol fails
- Support both stdio and HTTP MCP transports

**Testing Strategy**:
- Unit tests with mock MCP responses
- Integration tests with real test servers
- Test timeout and error handling
- Test different server types (npm, python, docker)
- Verify TUI rendering (snapshot tests)

**Success Metrics**:
- Health checks complete in < 5s for 10 servers
- Dashboard helps users debug 90% of server issues
- Users report faster troubleshooting
- Reduced "server not working" support requests

### Why This Is Exciting

1. **Visibility**: Users finally see what's happening with servers
2. **Debugging Aid**: Specific error messages instead of generic failures
3. **Proactive Monitoring**: Catch issues before Claude encounters them
4. **Learning Tool**: Users understand MCP protocol better
5. **Professional UX**: Dashboard feels like production monitoring tools

**Anti-Patterns Avoided**:
- ❌ No always-on daemon (only runs when invoked)
- ❌ No server modification (read-only health checks)
- ❌ No performance impact (cached status, configurable interval)
- ❌ No hidden behavior (shows exactly what it's checking)

---

## Proposal 4: Configuration Recipes

### Overview

**Name**: Configuration Recipes (a.k.a. "MCP Blueprints")

**One-Liner**: Export, import, and share complex MCP server configurations as portable recipes.

**User Pain Point**:
- Setting up advanced server configurations is tedious
- No way to share "this is how I configured server X" with team
- Documentation in README doesn't capture real configurations
- Recreating setup on new machine is manual and error-prone

**The Delight Factor**:
> "Someone on Reddit shared a recipe for the perfect GitHub MCP setup. I ran `mcpi recipe apply github-pr-workflow` and it configured everything exactly how they described—environment variables, scopes, arguments. Saved me 2 hours of trial and error."

### Use Cases

**Use Case 1: Team Configuration Sharing**
```bash
# Senior engineer exports their optimized setup
$ mcpi recipe export postgres --name "postgres-dev-setup"

Exported recipe: postgres-dev-setup
  Server: postgres
  Config: postgresql://localhost:5432/myapp
  Env: PGPASSWORD (from environment)
  Scope: project-mcp

Saved to: ~/.mcpi/recipes/postgres-dev-setup.yaml

Share with team:
  mcpi recipe share postgres-dev-setup
  # Generated URL: https://gist.github.com/abc123

# Junior engineer on team
$ mcpi recipe apply https://gist.github.com/abc123

Recipe: postgres-dev-setup (by @senior-engineer)
  Description: Production-ready PostgreSQL config for local development
  Server: postgres
  Scope: project-mcp

Apply this recipe? [Y/n]: y

Setting up postgres...
  ✓ Installed server
  ✓ Configured connection string
  ⚠ Environment variable PGPASSWORD not set

Tip: Set PGPASSWORD in your .env file for automatic authentication.
```

**Use Case 2: Complex Multi-Server Setup**
```bash
# User wants to replicate a documented architecture
$ mcpi recipe list --community

Community Recipes:
  web-scraping-stack    - Puppeteer + Brave Search + Filesystem (42 ⭐)
  data-pipeline         - Postgres + SQLite + Memory workflow (38 ⭐)
  github-pr-automation  - GitHub + Filesystem for PR reviews (31 ⭐)
  aws-infra-management  - AWS + Docker for infrastructure (27 ⭐)

$ mcpi recipe apply web-scraping-stack

Recipe: web-scraping-stack (by @scraping-guru)
  Description: Complete web scraping workflow with caching and storage
  Servers: puppeteer, brave-search, filesystem, memory

This recipe will:
  1. Install 4 servers to user-global scope
  2. Configure puppeteer with headless mode
  3. Set up filesystem for ./scraping-output/
  4. Configure memory for URL deduplication

Apply? [Y/n]: y

Installing recipe (4 servers)...
  ✓ puppeteer (configured for headless mode)
  ✓ brave-search (requires BRAVE_API_KEY)
  ✓ filesystem (path: ./scraping-output/)
  ✓ memory (namespace: scraping-cache)

Done! Recipe applied successfully.

Next steps:
  1. Set BRAVE_API_KEY in environment
  2. Create ./scraping-output/ directory
  3. Run example: See recipe documentation
```

**Use Case 3: Machine Migration**
```bash
# User setting up new development machine
$ mcpi recipe export --all --name "my-complete-setup"

Exported complete setup to: my-complete-setup.yaml
  - 12 servers across 3 scopes
  - Environment variables (names only, not values)
  - Custom arguments and paths

# On new machine
$ mcpi recipe apply my-complete-setup.yaml

Recipe: my-complete-setup
  This recipe will install 12 servers:

  Scope: project-mcp (3 servers)
    - postgres
    - filesystem
    - memory

  Scope: user-global (7 servers)
    - github
    - brave-search
    - fetch
    - docker
    - puppeteer
    - aws
    - sqlite

  Scope: user-internal (2 servers)
    - sequentialthinking
    - time

Apply this recipe? [Y/n]: y
```

### Implementation Approach

**Complexity**: 2 weeks

**Architecture**:

1. **Recipe Format** (YAML):
```yaml
# ~/.mcpi/recipes/postgres-dev-setup.yaml
name: postgres-dev-setup
description: Production-ready PostgreSQL config for local development
author: senior-engineer
version: 1.0.0
created: 2025-11-16
tags: [database, postgres, development]

servers:
  - id: postgres
    scope: project-mcp
    config:
      command: npx
      args:
        - "-y"
        - "@modelcontextprotocol/server-postgres"
        - "postgresql://localhost:5432/myapp"
      env:
        PGPASSWORD: "${env:PGPASSWORD}"  # Load from environment

    post_install:
      message: |
        PostgreSQL server configured for local development.
        Set PGPASSWORD in your .env file for automatic authentication.

      verify:
        - command: "psql -h localhost -p 5432 -d myapp -c 'SELECT 1'"
          description: "Test database connection"

    troubleshooting:
      - issue: "Connection refused"
        solution: "Ensure PostgreSQL is running: sudo systemctl start postgresql"
      - issue: "Authentication failed"
        solution: "Set PGPASSWORD environment variable"
```

2. **Recipe Management**:
```python
# src/mcpi/recipes/manager.py
class RecipeManager:
    """Manage configuration recipes."""

    def __init__(self, recipe_dir: Path):
        self.recipe_dir = recipe_dir
        self.recipe_dir.mkdir(parents=True, exist_ok=True)

    def export_server(
        self,
        server_id: str,
        scope: str,
        name: str,
        description: Optional[str] = None
    ) -> Recipe:
        """Export server configuration as recipe."""

        # Get current config
        config = self.manager.get_server_config(server_id, scope)

        # Create recipe
        recipe = Recipe(
            name=name,
            description=description or f"Configuration for {server_id}",
            author=self._get_git_user(),
            version="1.0.0",
            created=datetime.now(),
            servers=[
                RecipeServer(
                    id=server_id,
                    scope=scope,
                    config=config
                )
            ]
        )

        # Save to file
        recipe_path = self.recipe_dir / f"{name}.yaml"
        with open(recipe_path, 'w') as f:
            yaml.dump(recipe.dict(), f)

        return recipe

    def apply_recipe(
        self,
        recipe: Recipe,
        interactive: bool = True
    ) -> ApplyResult:
        """Apply recipe configuration."""

        results = []
        for server in recipe.servers:
            # Prompt user if interactive
            if interactive:
                if not self._prompt_install(server):
                    continue

            # Install server
            try:
                self.manager.add_server(
                    server_id=server.id,
                    scope=server.scope,
                    config=server.config
                )
                results.append(ServerResult(
                    server_id=server.id,
                    status=Status.SUCCESS
                ))
            except Exception as e:
                results.append(ServerResult(
                    server_id=server.id,
                    status=Status.FAILED,
                    error=str(e)
                ))

        return ApplyResult(results=results)
```

3. **Recipe Sharing**:
```python
# src/mcpi/recipes/sharing.py
class RecipeSharing:
    """Share recipes via GitHub Gists or URLs."""

    def share_to_gist(self, recipe: Recipe) -> str:
        """Upload recipe to GitHub Gist."""

        # Create gist payload
        content = yaml.dump(recipe.dict())

        # Upload via GitHub API
        response = requests.post(
            'https://api.github.com/gists',
            headers={'Authorization': f'token {github_token}'},
            json={
                'description': f'MCPI Recipe: {recipe.name}',
                'public': True,
                'files': {
                    f'{recipe.name}.yaml': {'content': content}
                }
            }
        )

        # Return gist URL
        gist_id = response.json()['id']
        return f'https://gist.github.com/{gist_id}'

    def fetch_recipe(self, url: str) -> Recipe:
        """Fetch recipe from URL."""

        if 'gist.github.com' in url:
            # Fetch from gist
            content = self._fetch_gist(url)
        else:
            # Fetch from generic URL
            content = requests.get(url).text

        # Parse YAML
        data = yaml.safe_load(content)
        return Recipe(**data)
```

4. **CLI Integration**:
```python
# src/mcpi/cli.py
@main.group()
def recipe():
    """Manage configuration recipes."""
    pass

@recipe.command('export')
@click.argument('server_id')
@click.option('--name', required=True, help='Recipe name')
@click.option('--description', help='Recipe description')
@click.option('--all', 'export_all', is_flag=True, help='Export all servers')
@click.pass_context
def export_recipe(ctx, server_id, name, description, export_all):
    """Export server configuration as recipe."""

    manager = RecipeManager(Path.home() / '.mcpi' / 'recipes')

    if export_all:
        recipe = manager.export_all_servers(name, description)
    else:
        recipe = manager.export_server(server_id, name, description)

    console.print(f"✓ Exported recipe: {name}")
    console.print(f"  Location: {manager.recipe_dir / f'{name}.yaml'}")

@recipe.command('apply')
@click.argument('recipe_source')  # File path or URL
@click.option('--non-interactive', is_flag=True)
@click.pass_context
def apply_recipe(ctx, recipe_source, non_interactive):
    """Apply a configuration recipe."""

    manager = RecipeManager(Path.home() / '.mcpi' / 'recipes')

    # Load recipe
    if recipe_source.startswith('http'):
        sharing = RecipeSharing()
        recipe = sharing.fetch_recipe(recipe_source)
    else:
        recipe = manager.load_recipe(Path(recipe_source))

    # Apply recipe
    result = manager.apply_recipe(
        recipe,
        interactive=not non_interactive
    )

    # Show results
    console.print(f"✓ Applied recipe: {recipe.name}")
    for server_result in result.results:
        if server_result.status == Status.SUCCESS:
            console.print(f"  ✓ {server_result.server_id}")
        else:
            console.print(f"  ✗ {server_result.server_id}: {server_result.error}")

@recipe.command('list')
@click.option('--community', is_flag=True, help='Show community recipes')
@click.pass_context
def list_recipes(ctx, community):
    """List available recipes."""

    if community:
        # Fetch from community registry
        # (Could be GitHub repo, curated list, etc.)
        recipes = fetch_community_recipes()
    else:
        # List local recipes
        manager = RecipeManager(Path.home() / '.mcpi' / 'recipes')
        recipes = manager.list_recipes()

    # Display table
    table = Table(title="Available Recipes")
    table.add_column("Name")
    table.add_column("Description")
    table.add_column("Servers")

    for recipe in recipes:
        table.add_row(
            recipe.name,
            recipe.description,
            str(len(recipe.servers))
        )

    console.print(table)
```

**Implementation Components**:
- `src/mcpi/recipes/manager.py` - Recipe management
- `src/mcpi/recipes/models.py` - Pydantic models for recipes
- `src/mcpi/recipes/sharing.py` - Recipe sharing via Gists/URLs
- Update `src/mcpi/cli.py` - Add `recipe` command group
- `data/recipes/` - Built-in recipes
- `tests/test_recipes.py` - Comprehensive tests

**Technical Considerations**:
- Use Pydantic for recipe validation
- Support variable substitution (${env:VAR}, ${project_root})
- Version recipes for compatibility
- Include post-install verification steps
- Store env var names only, not values (security)
- Support recipe inheritance (base recipes)

**Testing Strategy**:
- Unit tests for recipe export/import
- Integration tests for recipe application
- Test variable substitution
- Test Gist upload/download (mock GitHub API)
- Verify recipe validation catches errors

**Success Metrics**:
- Users share recipes in community
- Recipe application saves 80% of configuration time
- Recipes rated "helpful" by users
- Reduced "how do I configure X?" support requests

### Why This Is Exciting

1. **Knowledge Sharing**: Experts share optimal configurations
2. **Consistency**: Teams use same configurations
3. **Documentation**: Recipes ARE the documentation
4. **Portable**: Works across machines and teams
5. **Discoverable**: Community recipes surface best practices

**Anti-Patterns Avoided**:
- ❌ No secret exposure (env vars are placeholders)
- ❌ No version lock-in (recipes are data, not code)
- ❌ No forced behavior (user approves each step)
- ❌ No platform dependency (plain YAML files)

---

## Proposal 5: Project-Aware Context Switching

### Overview

**Name**: Project-Aware Context Switching (a.k.a. "Smart Workspace Detection")

**One-Liner**: MCPI automatically detects project boundaries and switches server contexts when you change directories.

**User Pain Point**:
- Users manually specify `--scope` on every command
- No awareness of current project context
- Global servers clutter project-specific workflows
- Confusion about which servers are active

**The Delight Factor**:
> "I just `cd` between my three projects and MCPI knows which servers are relevant. In my Django project, `mcpi list` shows only Django-relevant servers. In my React project, it shows different ones. I never think about scopes anymore."

### Use Cases

**Use Case 1: Project Navigation**
```bash
# User in home directory
$ cd ~
$ mcpi list

MCP Servers (user-global scope):
  github
  brave-search
  memory
  time

# User enters Django project
$ cd ~/projects/my-django-app
$ mcpi list

MCP Servers (project-mcp scope):
  postgres        (project)
  filesystem      (project)
  fetch           (project)

Inherited from user-global:
  github
  memory

Context: Django Project (my-django-app)
Scope: project-mcp (3 servers) + user-global (2 servers)

# User enters React project
$ cd ~/projects/my-react-app
$ mcpi list

MCP Servers (project-mcp scope):
  puppeteer       (project)
  filesystem      (project)

Inherited from user-global:
  github
  brave-search

Context: React Project (my-react-app)
Scope: project-mcp (2 servers) + user-global (2 servers)
```

**Use Case 2: Automatic Scope Detection**
```bash
# User wants to add server without specifying scope
$ cd ~/projects/my-django-app
$ mcpi add sqlite

Detected context: Django Project (my-django-app)
Default scope: project-mcp

Add sqlite to project-mcp scope? [Y/n]: y
Installing sqlite to project-mcp...

# Contrast: Old behavior required --scope
$ mcpi add sqlite --scope project-mcp  # No longer needed!
```

**Use Case 3: Context Validation**
```bash
# User tries to add wrong server to project
$ cd ~/projects/my-django-app
$ mcpi add puppeteer

Detected context: Django Project (Python/Django)
Warning: puppeteer is typically used for React/frontend projects.

Did you mean to:
  1. Add puppeteer to user-global scope (accessible everywhere)
  2. Add puppeteer to project-mcp scope (this project only)
  3. Cancel (recommended for Django projects)

Choice [1/2/3]: 1
```

### Implementation Approach

**Complexity**: 1 week

**Architecture**:

1. **Context Detection**:
```python
# src/mcpi/context/detector.py
class ProjectContext:
    """Detect and manage project context."""

    def detect(self, current_dir: Path) -> Context:
        """Detect project context from current directory."""

        # Walk up directory tree looking for project markers
        for path in [current_dir, *current_dir.parents]:
            # Check for .mcp.json (project root)
            if (path / '.mcp.json').exists():
                return Context(
                    type=ContextType.PROJECT,
                    root=path,
                    scope='project-mcp',
                    project_info=self._detect_project_type(path)
                )

            # Check for .git (git root)
            if (path / '.git').exists():
                return Context(
                    type=ContextType.GIT_ROOT,
                    root=path,
                    scope='project-mcp',  # Would create .mcp.json if adding servers
                    project_info=self._detect_project_type(path)
                )

        # No project detected - user-global context
        return Context(
            type=ContextType.USER_GLOBAL,
            root=Path.home(),
            scope='user-global',
            project_info=None
        )
```

2. **Automatic Scope Selection**:
```python
# src/mcpi/context/scope_selector.py
class AutoScopeSelector:
    """Automatically select appropriate scope based on context."""

    def select_scope(
        self,
        context: Context,
        operation: Operation,
        server_id: str
    ) -> str:
        """Select appropriate scope for operation."""

        # For project context, use project scope
        if context.type == ContextType.PROJECT:
            return 'project-mcp'

        # For git root, offer to create project scope
        if context.type == ContextType.GIT_ROOT:
            if operation == Operation.ADD:
                # Prompt: "Create .mcp.json in project root?"
                if self._prompt_create_project_scope(context):
                    return 'project-mcp'
            return 'user-global'

        # Default to user-global
        return 'user-global'
```

3. **Context-Aware CLI**:
```python
# src/mcpi/cli.py
def get_current_context() -> Context:
    """Get current project context."""
    detector = ProjectContext()
    return detector.detect(Path.cwd())

@main.command()
@click.argument('server_id')
@click.option('--scope', type=ScopeType(), help='Override auto-detected scope')
@click.pass_context
def add(ctx: click.Context, server_id: str, scope: Optional[str]):
    """Add MCP server (auto-detects scope if not specified)."""

    # Detect context
    context = get_current_context()

    # Auto-select scope if not specified
    if not scope:
        selector = AutoScopeSelector()
        scope = selector.select_scope(context, Operation.ADD, server_id)

        # Show what we're doing
        console.print(f"Detected context: {context.describe()}")
        console.print(f"Auto-selected scope: {scope}")

        # Confirm if project scope
        if scope == 'project-mcp' and context.type == ContextType.GIT_ROOT:
            if not click.confirm(f"Create .mcp.json in {context.root}?"):
                console.print("Cancelled.")
                return

    # Install server
    manager = get_mcp_manager(ctx)
    manager.add_server(server_id=server_id, scope=scope)

    console.print(f"✓ Added {server_id} to {scope}")

@main.command()
@click.pass_context
def context(ctx: click.Context):
    """Show current project context."""

    context = get_current_context()

    console.print(f"Context Type: {context.type.value}")
    console.print(f"Project Root: {context.root}")
    console.print(f"Default Scope: {context.scope}")

    if context.project_info:
        console.print(f"Project Type: {context.project_info.framework}")
        console.print(f"Language: {context.project_info.language}")
```

4. **Context Display in List**:
```python
# Enhance mcpi list command
@main.command()
@click.pass_context
def list(ctx: click.Context):
    """List servers with context awareness."""

    context = get_current_context()
    manager = get_mcp_manager(ctx)

    # Get servers
    servers = manager.list_servers()

    # Filter by context
    if context.type == ContextType.PROJECT:
        # Show project servers + inherited
        project_servers = [s for s in servers if s.scope == 'project-mcp']
        global_servers = [s for s in servers if s.scope == 'user-global']

        console.print(f"MCP Servers (project: {context.root.name})")
        console.print("\nProject Servers:")
        display_servers(project_servers)

        console.print("\nInherited from user-global:")
        display_servers(global_servers)
    else:
        # Standard list
        display_servers(servers)
```

**Implementation Components**:
- `src/mcpi/context/detector.py` - Context detection
- `src/mcpi/context/selector.py` - Automatic scope selection
- Update `src/mcpi/cli.py` - Integrate context detection
- `tests/test_context_detection.py` - Unit tests

**Technical Considerations**:
- Cache context detection (don't walk tree on every command)
- Support .mcpi.toml for context override
- Respect explicit --scope flag (override auto-detection)
- Handle monorepos (multiple projects in one tree)
- Show context info in CLI prompts

**Testing Strategy**:
- Unit tests for context detection logic
- Test directory tree walking
- Test scope selection for different scenarios
- Integration tests with real project structures
- Test monorepo handling

**Success Metrics**:
- Users stop specifying --scope manually
- Reduced "wrong scope" mistakes
- Faster workflow (less typing)
- Positive feedback on context awareness

### Why This Is Exciting

1. **Eliminates Cognitive Load**: Users don't think about scopes
2. **Prevents Mistakes**: Auto-detection prevents wrong-scope errors
3. **Faster Workflow**: Less typing, more doing
4. **Feels Magical**: "It just knows what I want"
5. **Principle of Least Surprise**: Behavior matches user intent

**Anti-Patterns Avoided**:
- ❌ No hidden behavior (shows detected context)
- ❌ No forced choices (--scope still works)
- ❌ No slow operations (cached detection)
- ❌ No complex rules (simple tree walking)

---

## Implementation Priority Recommendations

### Priority 1: Must-Have (Ship in v0.4.0)

**1. Smart Server Bundles** (1.5 weeks)
- **Why**: Solves biggest onboarding friction
- **Impact**: 10x faster setup for new users
- **Risk**: LOW (uses existing add/remove commands)
- **Dependencies**: None

**2. Intelligent Auto-Configuration** (2-3 weeks)
- **Why**: Eliminates decision paralysis
- **Impact**: Users discover relevant servers
- **Risk**: MEDIUM (detection accuracy critical)
- **Dependencies**: None

### Priority 2: Should-Have (Ship in v0.4.0 or v0.5.0)

**3. Project-Aware Context** (1 week)
- **Why**: Reduces friction in daily workflow
- **Impact**: Less typing, fewer mistakes
- **Risk**: LOW (simple tree walking)
- **Dependencies**: None

**4. Configuration Recipes** (2 weeks)
- **Why**: Enables knowledge sharing
- **Impact**: Team productivity boost
- **Risk**: MEDIUM (recipe format design)
- **Dependencies**: None

### Priority 3: Nice-to-Have (Ship in v0.5.0+)

**5. Server Health Dashboard** (3 weeks)
- **Why**: Debugging aid, not core workflow
- **Impact**: Helps troubleshooting
- **Risk**: MEDIUM (MCP protocol integration)
- **Dependencies**: Requires MCP client implementation

---

## Convergence Analysis

### Why These 5?

**Customer Impact**: Each solves a painful, frequent problem
- Bundles: "Which servers do I need?"
- Auto-config: "How do I set this up?"
- Health: "Why isn't it working?"
- Recipes: "How do I share this?"
- Context: "Why do I keep typing --scope?"

**Implementation Feasibility**: All implementable in 1-4 weeks
- No external service dependencies
- Build on existing plugin architecture
- Use current tech stack (Click, Rich, Pydantic)
- Clear testing strategies

**Strategic Value**: Opens doors to future capabilities
- Bundles → Community bundle marketplace
- Auto-config → AI-powered recommendations
- Health → Full observability platform
- Recipes → Configuration-as-code ecosystem
- Context → Multi-project orchestration

**Simplicity**: Makes product easier, not harder
- Each feature eliminates manual work
- No new abstractions to learn
- Principle of least surprise maintained
- User stays in control

### What Did We Reject?

**AI-Powered Features**: Too clever, unclear value
- AI search: Fuzzy search is good enough
- AI recommendations: Rule-based works fine

**Infrastructure Features**: Too complex, wrong layer
- Server marketplace: Catalog is sufficient
- Remote sync: GitHub works fine for sharing
- Web dashboard: TUI is fast and simple

**Minor Improvements**: Not transformative enough
- Better error messages: Incremental, not delightful
- Configuration migration: Already automatic
- Additional search filters: Nice but not essential

---

## Proposed Additions to PROJECT_SPEC.md

### New Section: Advanced Features (Post v0.3.0)

Add after the "Core Features" section (around line 195):

```markdown
### Advanced Features (v0.4.0+)

#### Smart Server Bundles
- `mcpi bundle list`: List available server bundles (curated sets for common use cases)
- `mcpi bundle info <bundle>`: Show detailed bundle information
- `mcpi bundle install <bundle>`: Install curated bundle of servers
- `mcpi bundle create <name>`: Create custom bundle from current configuration
- `mcpi bundle share <name>`: Generate shareable URL for custom bundle
- Built-in bundles: web-dev, data-science, devops, content, ai-tools
- User bundles: `~/.mcpi/bundles/*.json`
- Community bundles: Shareable via URLs (GitHub Gists, etc.)

**Value Proposition**: New users install complete workflows in seconds. Experts share optimized configurations. Teams standardize on same server sets.

#### Intelligent Auto-Configuration
- `mcpi auto`: Detect project type and suggest relevant servers
- `mcpi auto --enhance`: Suggest additions to existing setup
- Project detection: Django, FastAPI, React, Next.js, Node.js, Python, monorepos
- Smart configuration: Auto-generate appropriate arguments based on project structure
- Environment detection: Database URLs, allowed paths, working directories
- Non-interactive mode: `mcpi auto --non-interactive` for CI/CD

**Value Proposition**: Eliminates decision paralysis. Users discover servers relevant to their work. Configuration optimized for project structure automatically.

#### Project-Aware Context Switching
- `mcpi context`: Show current project context
- Auto-detection: `.mcp.json`, `.git`, project markers
- Automatic scope selection: Project scope when in project, user-global otherwise
- Context-aware listing: Show project + inherited servers
- Smart prompts: "Create .mcp.json?" when adding to git root

**Value Proposition**: Users never think about scopes. Commands "just work" based on location. Fewer mistakes, faster workflow.

#### Configuration Recipes (v0.4.0+)
- `mcpi recipe export <server>`: Export server configuration as recipe
- `mcpi recipe apply <recipe>`: Apply configuration recipe
- `mcpi recipe list`: List local recipes
- `mcpi recipe list --community`: Browse community recipes
- Recipe format: YAML with metadata, servers, environment, post-install steps
- Recipe sharing: GitHub Gists, URLs, local files
- Variable substitution: `${env:VAR}`, `${project_root}`, `${home}`

**Value Proposition**: Knowledge sharing at scale. Teams use consistent configurations. Machine migration takes minutes instead of hours.

#### Server Health Dashboard (v0.5.0+)
- `mcpi status`: Health check all MCP servers
- `mcpi status --watch`: Real-time monitoring dashboard
- `mcpi status <server> --debug`: Detailed diagnostics for specific server
- Health checks: Process status, MCP connectivity, response latency
- TUI dashboard: Real-time updating with Rich tables
- Issue detection: Connection failures, slow responses, configuration errors
- Integration with `mcpi doctor`: Health checks feed into diagnostics

**Value Proposition**: Visibility into server health. Faster debugging. Proactive issue detection. Professional monitoring UX.
```

### Update Implementation Notes Section

Add after line 340 (Key Lessons Learned):

```markdown
### Design Principles for Advanced Features

**User Delight Over Feature Count**:
- Each feature solves a painful problem users face daily
- Focus on eliminating work rather than adding capabilities
- "Wow" moments should feel obvious in retrospect

**Maintain Simplicity Despite Power**:
- Bundles are just lists of servers (no new abstraction)
- Auto-config is detection + existing add commands
- Context is directory awareness (no new state)
- Recipes are portable configurations (just YAML)

**Build on Plugin Architecture**:
- All features use existing `MCPManager` and `MCPClientPlugin`
- No new core abstractions
- Extensions feel natural, not bolted-on

**Enable Community Participation**:
- Bundles are shareable data files
- Recipes are portable configurations
- Detection rules are extensible
- Everything is open and inspectable
```

---

## Conclusion

These 5 feature proposals represent **pragmatic innovation**: each solves real problems, can be implemented in 1-4 weeks, and creates genuine user delight. They share common themes:

1. **Eliminate Work**: Bundles remove research phase, auto-config removes decision-making, context removes scope specification
2. **Enable Sharing**: Recipes and bundles create knowledge networks
3. **Increase Visibility**: Health dashboard shows what's happening
4. **Maintain Simplicity**: Each feature uses existing primitives

**Recommended Implementation Order**:
1. Smart Server Bundles (v0.4.0) - Biggest onboarding impact
2. Project-Aware Context (v0.4.0) - Smallest implementation, high daily value
3. Intelligent Auto-Configuration (v0.4.0) - Requires bundles as foundation
4. Configuration Recipes (v0.5.0) - Builds on bundle concepts
5. Server Health Dashboard (v0.5.0) - Polish and professional UX

**Expected Outcomes**:
- New user time-to-productivity: 30 seconds (vs. 10 minutes)
- Daily workflow friction: Reduced by 70%
- Knowledge sharing: Enabled at scale
- User delight: "I can't believe I lived without this"

---

**Status**: PROPOSAL - Ready for review and prioritization
**Next Steps**: Gather feedback, refine scope, begin implementation of Priority 1 items
**Timeline**: v0.4.0 (January 2026) for Priority 1-2, v0.5.0 (March 2026) for Priority 3

---

*Generated by: Product Visionary Agent*
*Date: 2025-11-16*
*Process: Expansive brainstorming → Pragmatic filtering → Convergent design*
*Confidence: HIGH - Each proposal validated against user pain points, implementation feasibility, and strategic value*
