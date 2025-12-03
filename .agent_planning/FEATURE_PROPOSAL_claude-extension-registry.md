# Feature Proposal: MCPI as Universal Claude Extension Registry

**Date**: 2025-11-25
**Version**: 1.0
**Status**: Proposal (For Discussion)
**Author**: Product Visionary Agent
**Target Release**: v3.0 (Q2 2026)

---

## Executive Summary

Transform MCPI from an MCP server manager into **"npm for Claude extensions"** - a universal package manager for the entire Claude Code extensibility ecosystem. This evolution positions MCPI as the central distribution and management platform for commands, hooks, skills, agents, plugins, and MCP servers.

**Why This Matters**: Claude Code's plugin system is creating an explosion of extensibility formats. Users face fragmentation, duplication, and discovery problems. MCPI can become the single source of truth that makes Claude extensions as easy to discover, install, and manage as npm packages.

**Core Vision**: One catalog, one CLI, one ecosystem - for everything that extends Claude Code.

**Phased Approach**: Start with commands (easiest), progressively add hooks, skills, agents, and finally full plugin bundles. Each phase delivers immediate value while building toward the complete vision.

**Key Differentiator**: MCPI already has a working catalog system, configuration management, scope handling, and user trust. This proposal leverages existing architecture to expand horizontally across extension types rather than rebuilding from scratch.

---

## Problem Statement

### Current Pain Points

**1. Extension Discovery is Fragmented**

Users currently find Claude extensions through:
- GitHub awesome lists (no quality control)
- Twitter/Reddit posts (ephemeral)
- Documentation sites (outdated)
- Word of mouth (limited reach)

There's no single place to discover "What can Claude Code do?"

**2. Installation is Manual and Error-Prone**

Installing extensions today requires:
- Finding the correct repository
- Reading setup instructions (often unclear)
- Manually editing JSON/Markdown files
- Troubleshooting configuration errors
- Understanding scope semantics

A simple slash command install takes 5-15 minutes. It should take 30 seconds.

**3. Extension Management is Non-Existent**

Users have no way to:
- See what extensions they have installed
- Update extensions when new versions ship
- Disable extensions temporarily
- Uninstall extensions cleanly
- Understand dependencies between extensions

**4. Quality and Security are Unknown**

Users cannot determine:
- Is this extension safe?
- Is it well-maintained?
- Has anyone reviewed the code?
- Are there known security issues?
- What permissions does it need?

**5. Ecosystem Growth is Inhibited**

Extension authors face:
- No distribution channel beyond GitHub
- No usage metrics or feedback loops
- No way to reach potential users
- No standardized package format
- No versioning or dependency management

### The Opportunity

Claude Code plugins launched October 2025 with a vision: **bundle commands, agents, MCP servers, and hooks into shareable packages**. But the ecosystem needs infrastructure:

1. **A Registry** - Where extensions live and are discovered
2. **A CLI** - How users install and manage extensions
3. **A Package Format** - How extensions are defined and distributed
4. **A Quality System** - How users trust extensions

**MCPI can be all four**. We already have 1, 2, and the start of 3. We just need to expand horizontally.

### Validation

Evidence this problem is real:

- **awesome-claude-code-plugins** repo has 500+ stars (strong interest)
- **claude-code-plugins** GitHub org has multiple curated lists
- Users complain about manual setup in Discord/Reddit
- Anthropic's plugin docs mention "install with a single command" but don't provide the registry
- MCP server count grew from ~20 to ~200 in 3 months (explosive growth, fragmentation risk)

**User Need**: "I want to type `mcpi install <extension-name>` and have it just work, regardless of extension type."

---

## Proposed Solution

### Vision Statement

**MCPI becomes the npm of Claude extensions** - a universal package manager that makes discovering, installing, and managing ALL Claude Code extensibility points as simple as:

```bash
mcpi search testing
mcpi install test-runner-command
mcpi install pytest-automation-hook
mcpi install github-pr-agent
mcpi list
mcpi update --all
```

### Phased Rollout

**Phase 1: Commands (v3.0) - Q1 2026**
- Add commands to catalog
- Install .md files to `.claude/commands/`
- Search, install, remove, update commands
- **Immediate Value**: 100+ useful commands installable in seconds

**Phase 2: Hooks (v3.1) - Q2 2026**
- Add hooks to catalog
- Merge hook configs into `settings.json`
- Manage hook lifecycle
- **Immediate Value**: Automated workflows without manual JSON editing

**Phase 3: Skills & Agents (v3.2) - Q3 2026**
- Add skills and agents to catalog
- Install agent configurations
- Manage agent dependencies
- **Immediate Value**: Pre-configured agents for common tasks

**Phase 4: Plugin Bundles (v4.0) - Q4 2026**
- Support full Claude Code plugin format
- Install multi-component bundles
- Resolve dependencies across types
- **Complete Vision**: One-command plugin installation

---

## Technical Architecture

### 1. Unified Package Manifest

Extend the current catalog format to support all extension types with a unified schema:

```yaml
# Unified manifest: data/catalog.json (extended)
{
  "modelcontextprotocol/postgres": {
    "type": "mcp-server",
    "description": "Query and manage PostgreSQL databases",
    "command": "npx",
    "args": ["-y", "@modelcontextprotocol/server-postgres"],
    "repository": "https://github.com/modelcontextprotocol/servers",
    "categories": ["database", "sql"],
    "version": "1.0.0",
    "author": "Model Context Protocol",
    "requires": [],
    "templates": ["local-development", "docker", "production"]
  },

  "test-runner/pytest": {
    "type": "command",
    "description": "Run pytest with automatic test discovery",
    "content": "Run pytest tests in this project...",
    "repository": "https://github.com/claude-extensions/test-runner",
    "categories": ["testing", "python"],
    "version": "1.2.0",
    "author": "Claude Extensions Org",
    "requires": [],
    "install": {
      "scope": "project-commands",
      "filename": "pytest.md"
    }
  },

  "automation/format-on-save": {
    "type": "hook",
    "description": "Auto-format code after file writes",
    "repository": "https://github.com/claude-extensions/automation",
    "categories": ["automation", "formatting"],
    "version": "1.0.0",
    "author": "Claude Extensions Org",
    "requires": ["filesystem-access"],
    "install": {
      "scope": "user-global",
      "hook_type": "after_write",
      "command": "black",
      "args": ["${file}"]
    }
  },

  "agents/github-pr-reviewer": {
    "type": "agent",
    "description": "AI agent that reviews GitHub PRs",
    "repository": "https://github.com/claude-extensions/agents",
    "categories": ["code-review", "github"],
    "version": "2.0.0",
    "author": "Claude Extensions Org",
    "requires": ["github-mcp", "code-analysis-skill"],
    "install": {
      "scope": "user-global",
      "agent_config": {
        "name": "PR Reviewer",
        "description": "Reviews pull requests for code quality",
        "tools": ["github_list_prs", "github_get_diff", "github_comment"]
      }
    }
  },

  "bundles/full-stack-dev": {
    "type": "plugin-bundle",
    "description": "Complete full-stack development environment",
    "repository": "https://github.com/claude-plugins/full-stack-dev",
    "categories": ["development", "bundle"],
    "version": "1.0.0",
    "author": "Claude Plugins Org",
    "requires": [],
    "components": [
      {
        "type": "mcp-server",
        "package": "modelcontextprotocol/postgres"
      },
      {
        "type": "mcp-server",
        "package": "modelcontextprotocol/github"
      },
      {
        "type": "command",
        "package": "test-runner/pytest"
      },
      {
        "type": "hook",
        "package": "automation/format-on-save"
      },
      {
        "type": "agent",
        "package": "agents/github-pr-reviewer"
      }
    ]
  }
}
```

**Key Design Decisions**:

1. **Type Discrimination**: `type` field determines extension category
2. **Common Fields**: All types share: `description`, `repository`, `categories`, `version`, `author`, `requires`
3. **Type-Specific Fields**: Each type has an `install` object with type-specific configuration
4. **Dependency Graph**: `requires` field enables cross-type dependencies
5. **Versioning**: Semantic versioning for updates and compatibility
6. **Templates**: Commands/hooks can have templates like MCP servers do

### 2. Type-Specific Installers

Create an installer for each extension type following the existing pattern:

```python
# src/mcpi/installers/base.py (existing pattern)
class ExtensionInstaller(Protocol):
    """Protocol for extension installers."""

    def validate(self, config: ExtensionConfig) -> bool:
        """Validate extension configuration."""
        ...

    def install(self, extension_id: str, config: ExtensionConfig, scope: str) -> OperationResult:
        """Install extension to specified scope."""
        ...

    def remove(self, extension_id: str, scope: str) -> OperationResult:
        """Remove extension from scope."""
        ...

    def update(self, extension_id: str, scope: str) -> OperationResult:
        """Update extension to latest version."""
        ...
```

```python
# src/mcpi/installers/command.py (NEW)
class CommandInstaller:
    """Install slash commands to .claude/commands/."""

    def install(self, extension_id: str, config: CommandConfig, scope: str) -> OperationResult:
        """
        Install command by writing .md file to correct location.

        Scopes:
        - project-commands: .claude/commands/
        - user-commands: ~/.claude/commands/
        """
        # Determine target directory based on scope
        target_dir = self._get_commands_dir(scope)

        # Write markdown file
        filename = config.install.filename
        content = config.content

        target_path = target_dir / filename
        target_path.write_text(content)

        return OperationResult.success(f"Installed command: {extension_id}")
```

```python
# src/mcpi/installers/hook.py (NEW)
class HookInstaller:
    """Install hooks by merging into settings.json."""

    def install(self, extension_id: str, config: HookConfig, scope: str) -> OperationResult:
        """
        Install hook by merging configuration into settings.json.

        Hooks are defined in settings.json under "hooks" key:
        {
          "hooks": {
            "after_write": [
              {"command": "black", "args": ["${file}"]}
            ]
          }
        }
        """
        # Load settings file for scope
        settings = self._load_settings(scope)

        # Ensure hooks section exists
        if "hooks" not in settings:
            settings["hooks"] = {}

        # Add hook to appropriate lifecycle
        hook_type = config.install.hook_type
        if hook_type not in settings["hooks"]:
            settings["hooks"][hook_type] = []

        # Add hook config
        hook_entry = {
            "command": config.install.command,
            "args": config.install.args,
            "extension_id": extension_id  # Track which extension added this
        }
        settings["hooks"][hook_type].append(hook_entry)

        # Save settings
        self._save_settings(scope, settings)

        return OperationResult.success(f"Installed hook: {extension_id}")
```

```python
# src/mcpi/installers/agent.py (NEW)
class AgentInstaller:
    """Install agents by configuring agent definitions."""

    def install(self, extension_id: str, config: AgentConfig, scope: str) -> OperationResult:
        """
        Install agent by adding configuration to agents section.

        Agents are defined in settings.json under "agents" key or
        in separate .claude/agents/ directory depending on Claude Code version.
        """
        # Check Claude Code version to determine format
        # For now, assume settings.json format

        settings = self._load_settings(scope)

        if "agents" not in settings:
            settings["agents"] = []

        agent_entry = {
            "id": extension_id,
            "name": config.install.agent_config.name,
            "description": config.install.agent_config.description,
            "tools": config.install.agent_config.tools
        }

        settings["agents"].append(agent_entry)
        self._save_settings(scope, settings)

        return OperationResult.success(f"Installed agent: {extension_id}")
```

```python
# src/mcpi/installers/bundle.py (NEW)
class BundleInstaller:
    """Install plugin bundles by recursively installing components."""

    def __init__(self, installer_registry: Dict[str, ExtensionInstaller]):
        self.installers = installer_registry

    def install(self, extension_id: str, config: BundleConfig, scope: str) -> OperationResult:
        """
        Install bundle by installing each component.

        Handles dependency order and rollback on failure.
        """
        installed_components = []

        try:
            # Resolve dependency order
            ordered_components = self._resolve_dependencies(config.components)

            # Install each component
            for component in ordered_components:
                installer = self.installers[component.type]
                result = installer.install(component.package, component.config, scope)

                if not result.success:
                    raise InstallationError(f"Failed to install {component.package}: {result.error}")

                installed_components.append(component)

            return OperationResult.success(f"Installed bundle: {extension_id}")

        except Exception as e:
            # Rollback on failure
            for component in reversed(installed_components):
                installer = self.installers[component.type]
                installer.remove(component.package, scope)

            return OperationResult.failure(f"Bundle installation failed: {e}")
```

### 3. Extended Catalog Manager

Extend the existing `ServerCatalog` to become `ExtensionCatalog`:

```python
# src/mcpi/registry/catalog.py (REFACTOR)
class ExtensionCatalog:
    """Universal catalog for all Claude extensions."""

    def __init__(self, catalog_path: Path, validate_with_cue: bool = True):
        """Initialize catalog with path to unified manifest."""
        self.catalog_path = catalog_path
        self._registry: Optional[ExtensionRegistry] = None
        self._loaded = False
        self.validate_with_cue = validate_with_cue

    def get_extension(self, extension_id: str) -> Optional[Extension]:
        """Get extension by ID (works for any type)."""
        if not self._loaded:
            self.load_catalog()
        return self._registry.get_extension(extension_id)

    def list_extensions(self, extension_type: Optional[str] = None) -> List[tuple[str, Extension]]:
        """List all extensions, optionally filtered by type."""
        if not self._loaded:
            self.load_catalog()

        extensions = self._registry.list_extensions()

        if extension_type:
            extensions = [
                (ext_id, ext) for ext_id, ext in extensions
                if ext.type == extension_type
            ]

        return extensions

    def search_extensions(self, query: str, extension_type: Optional[str] = None) -> List[tuple[str, Extension]]:
        """Search extensions by query across all types."""
        if not self._loaded:
            self.load_catalog()

        # Search description, categories, and ID
        results = []
        for ext_id, ext in self.list_extensions(extension_type):
            if (
                query.lower() in ext_id.lower() or
                query.lower() in ext.description.lower() or
                any(query.lower() in cat.lower() for cat in ext.categories)
            ):
                results.append((ext_id, ext))

        return results
```

### 4. CLI Extensions

Extend the CLI to support all extension types:

```bash
# Phase 1: Commands (v3.0)
mcpi search "test runner" --type command
mcpi install test-runner/pytest --scope project-commands
mcpi list --type command
mcpi remove test-runner/pytest --scope project-commands

# Phase 2: Hooks (v3.1)
mcpi search "format" --type hook
mcpi install automation/format-on-save --scope user-global
mcpi list --type hook
mcpi disable automation/format-on-save

# Phase 3: Skills & Agents (v3.2)
mcpi search "code review" --type agent
mcpi install agents/github-pr-reviewer --scope user-global
mcpi list --type agent

# Phase 4: Bundles (v4.0)
mcpi search "full stack" --type bundle
mcpi install bundles/full-stack-dev --scope project
mcpi list --show-components  # Show all components in bundles
mcpi update --all  # Update all extensions

# Universal commands (work for any type)
mcpi search database
mcpi list
mcpi info modelcontextprotocol/postgres
mcpi update modelcontextprotocol/postgres
```

**Key CLI Design Principles**:

1. **Type-Agnostic**: Most commands work across all types
2. **Type Filtering**: `--type` flag when you need specificity
3. **Scope Awareness**: Scopes work the same way they do today
4. **Backward Compatible**: All existing MCP commands continue to work
5. **Progressive Disclosure**: Simple commands for simple cases, flags for advanced use

### 5. Dependency Resolution

Implement a dependency resolver for cross-type dependencies:

```python
# src/mcpi/dependency_resolver.py (NEW)
class DependencyResolver:
    """Resolve dependencies across extension types."""

    def __init__(self, catalog: ExtensionCatalog):
        self.catalog = catalog

    def resolve_dependencies(self, extension_id: str) -> List[str]:
        """
        Resolve all dependencies for an extension.

        Returns ordered list of extension IDs that must be installed first.
        """
        visited = set()
        ordered = []

        def visit(ext_id: str):
            if ext_id in visited:
                return

            visited.add(ext_id)
            extension = self.catalog.get_extension(ext_id)

            if not extension:
                raise DependencyError(f"Unknown dependency: {ext_id}")

            # Visit dependencies first
            for dep_id in extension.requires:
                visit(dep_id)

            ordered.append(ext_id)

        visit(extension_id)
        return ordered

    def check_conflicts(self, extension_id: str, installed: List[str]) -> List[str]:
        """Check for conflicts with already-installed extensions."""
        conflicts = []
        extension = self.catalog.get_extension(extension_id)

        # Check for conflicting versions
        for installed_id in installed:
            installed_ext = self.catalog.get_extension(installed_id)

            # Conflict if same base package but incompatible versions
            if (
                self._same_base_package(extension_id, installed_id) and
                not self._versions_compatible(extension.version, installed_ext.version)
            ):
                conflicts.append(f"{installed_id} (version conflict)")

        return conflicts
```

### 6. Version Management

Add versioning and update capabilities:

```python
# src/mcpi/version_manager.py (NEW)
class VersionManager:
    """Manage extension versions and updates."""

    def __init__(self, catalog: ExtensionCatalog):
        self.catalog = catalog

    def check_updates(self, installed_extensions: Dict[str, str]) -> Dict[str, str]:
        """
        Check for available updates.

        Args:
            installed_extensions: Dict of extension_id -> current_version

        Returns:
            Dict of extension_id -> latest_version for extensions with updates
        """
        updates = {}

        for ext_id, current_version in installed_extensions.items():
            extension = self.catalog.get_extension(ext_id)

            if not extension:
                continue  # Extension removed from catalog

            latest_version = extension.version

            if self._is_newer(latest_version, current_version):
                updates[ext_id] = latest_version

        return updates

    def update_extension(
        self,
        extension_id: str,
        target_version: Optional[str] = None
    ) -> OperationResult:
        """
        Update extension to specified version or latest.

        Handles breaking changes and migration if needed.
        """
        # Get current installation
        current_install = self._get_current_install(extension_id)

        if not current_install:
            return OperationResult.failure(f"Extension not installed: {extension_id}")

        # Determine target version
        if target_version is None:
            extension = self.catalog.get_extension(extension_id)
            target_version = extension.version

        # Check if breaking change
        if self._is_breaking_change(current_install.version, target_version):
            # Prompt user for confirmation
            confirmed = self._confirm_breaking_update(extension_id, target_version)
            if not confirmed:
                return OperationResult.failure("Update cancelled by user")

        # Uninstall old version
        self._uninstall(extension_id, current_install.scope)

        # Install new version
        result = self._install(extension_id, target_version, current_install.scope)

        if result.success:
            return OperationResult.success(
                f"Updated {extension_id} from {current_install.version} to {target_version}"
            )
        else:
            # Rollback on failure
            self._install(extension_id, current_install.version, current_install.scope)
            return OperationResult.failure(f"Update failed: {result.error}")
```

---

## Phase 1 Detailed Plan: Commands (v3.0)

### Scope

Add slash commands to MCPI catalog and enable install/remove/list operations.

### Why Start with Commands?

1. **Simplest Format**: Commands are just markdown files
2. **No Dependencies**: Commands don't typically depend on other extensions
3. **Immediate Value**: 100+ useful commands can be packaged quickly
4. **Low Risk**: Installing a .md file is safe and reversible
5. **Proof of Concept**: Validates the unified catalog approach

### Implementation Steps

**Step 1: Extend Catalog Schema (1 week)**

```yaml
# Add command entries to data/catalog.json
{
  "commands/pytest": {
    "type": "command",
    "description": "Run pytest with automatic test discovery",
    "content": "# Pytest Test Runner\n\nRun pytest tests...",
    "repository": "https://github.com/claude-extensions/commands",
    "categories": ["testing", "python"],
    "version": "1.0.0",
    "author": "Claude Extensions",
    "requires": [],
    "install": {
      "scope": "project-commands",
      "filename": "pytest.md"
    }
  }
}
```

**Acceptance Criteria**:
- [ ] Schema supports `type: "command"` entries
- [ ] Pydantic model `CommandExtension` created
- [ ] CUE validation schema updated
- [ ] 10 example commands added to catalog
- [ ] Tests pass for new schema

**Step 2: Create CommandInstaller (1 week)**

```python
# src/mcpi/installers/command.py
class CommandInstaller:
    """Install slash commands to .claude/commands/."""

    def install(self, extension_id: str, config: CommandConfig, scope: str) -> OperationResult:
        """Write markdown file to commands directory."""
        target_dir = self._resolve_scope_dir(scope)
        target_path = target_dir / config.install.filename

        # Create directory if needed
        target_dir.mkdir(parents=True, exist_ok=True)

        # Write content
        target_path.write_text(config.content)

        return OperationResult.success(f"Installed command: {extension_id}")

    def remove(self, extension_id: str, scope: str) -> OperationResult:
        """Remove command file."""
        # Find and delete the .md file
        ...

    def _resolve_scope_dir(self, scope: str) -> Path:
        """Resolve scope to commands directory."""
        if scope == "project-commands":
            return Path.cwd() / ".claude" / "commands"
        elif scope == "user-commands":
            return Path.home() / ".claude" / "commands"
        else:
            raise ValueError(f"Invalid command scope: {scope}")
```

**Acceptance Criteria**:
- [ ] CommandInstaller class created
- [ ] Implements ExtensionInstaller protocol
- [ ] Supports project-commands and user-commands scopes
- [ ] Unit tests with 80%+ coverage
- [ ] Integration tests with real file system

**Step 3: Extend CLI (1 week)**

```python
# src/mcpi/cli.py (extend existing commands)
@click.command()
@click.argument("extension_id")
@click.option("--scope", help="Installation scope")
@click.option("--type", help="Extension type filter")
@click.pass_context
def install(ctx, extension_id, scope, type):
    """Install an extension (MCP server, command, etc)."""
    catalog = get_extension_catalog(ctx)
    manager = get_extension_manager(ctx)

    # Get extension from catalog
    extension = catalog.get_extension(extension_id)

    if not extension:
        console.print(f"[red]Extension not found: {extension_id}[/red]")
        raise click.Abort()

    # Get appropriate installer for type
    installer = manager.get_installer(extension.type)

    # Determine scope (use default for type if not specified)
    if not scope:
        scope = extension.install.scope

    # Install
    result = installer.install(extension_id, extension, scope)

    if result.success:
        console.print(f"[green]✓[/green] {result.message}")
    else:
        console.print(f"[red]✗[/red] {result.error}")
        raise click.Abort()
```

**Acceptance Criteria**:
- [ ] `mcpi install` supports commands
- [ ] `mcpi remove` supports commands
- [ ] `mcpi list` shows commands with type indicator
- [ ] `mcpi search --type command` works
- [ ] `mcpi info` shows command content
- [ ] CLI tests updated
- [ ] All tests pass

**Step 4: Seed Catalog with Commands (1 week)**

Create a curated collection of 50-100 useful commands:

**Testing Commands**:
- pytest, jest, vitest, unittest, rspec
- test-coverage, test-watch, test-debug

**Git Commands**:
- git-commit-smart, git-pr-create, git-branch-cleanup
- git-rebase-interactive, git-cherry-pick

**Build Commands**:
- npm-install, npm-build, npm-test
- docker-build, docker-compose-up

**Code Quality**:
- format-all, lint-fix, type-check
- security-scan, dependency-audit

**Documentation**:
- generate-api-docs, update-readme, generate-changelog

**Acceptance Criteria**:
- [ ] 50+ commands added to catalog
- [ ] Each command has clear description
- [ ] Each command has example usage in content
- [ ] Commands organized by category
- [ ] All commands tested manually
- [ ] Documentation updated with command examples

**Step 5: Documentation and Release (1 week)**

- [ ] Update CLAUDE.md with commands section
- [ ] Create COMMANDS.md guide
- [ ] Write blog post announcing feature
- [ ] Create video tutorial
- [ ] Update README with examples
- [ ] Tag v3.0 release

### Success Metrics for Phase 1

**Technical Metrics**:
- [ ] 50+ commands in catalog
- [ ] 80%+ test coverage for new code
- [ ] Zero regressions in existing MCP functionality
- [ ] <100ms overhead for catalog loading

**User Metrics** (90 days post-release):
- [ ] 1000+ command installations
- [ ] 100+ users install at least one command
- [ ] <5% error rate on command installations
- [ ] <3 support tickets per week about commands

**Quality Metrics**:
- [ ] 4.0+ star rating on feedback
- [ ] <1% of commands reported as broken
- [ ] 90%+ users say "this is easier than manual install"

---

## Phase 2 Plan: Hooks (v3.1)

### Scope

Add hooks to MCPI catalog and enable lifecycle automation.

### Why Hooks Are Next?

1. **High Value**: Automation without manual trigger
2. **JSON Merging**: Builds on existing config management
3. **Clear Use Cases**: Format-on-save, lint-on-commit, etc
4. **Moderate Complexity**: More complex than commands, less than bundles

### Implementation Overview

```yaml
# Hook catalog entry
{
  "hooks/format-on-save": {
    "type": "hook",
    "description": "Auto-format code after file writes",
    "repository": "https://github.com/claude-extensions/hooks",
    "categories": ["automation", "formatting"],
    "version": "1.0.0",
    "requires": [],
    "install": {
      "scope": "user-global",
      "hook_type": "after_write",
      "command": "black",
      "args": ["${file}"],
      "conditions": {
        "file_pattern": "*.py"
      }
    }
  }
}
```

**Key Features**:
- Lifecycle hooks: `before_read`, `after_write`, `before_commit`, `after_test`
- Conditional execution: file patterns, exit codes
- Variable substitution: `${file}`, `${project_root}`, `${changed_files}`

**Success Criteria**:
- 20+ hooks in catalog
- Zero interference with user workflow
- <50ms hook execution overhead
- Clear error messages when hooks fail

**Timeline**: 1 month after v3.0 ships

---

## Phase 3 Plan: Skills & Agents (v3.2)

### Scope

Add skills and agents to MCPI catalog for specialized capabilities.

### Why Skills & Agents?

1. **Composability**: Agents depend on skills and MCP servers
2. **Pre-Configured Workflows**: One-command setup for complex tasks
3. **Ecosystem Growth**: Enable agent marketplace

### Implementation Overview

```yaml
# Agent catalog entry
{
  "agents/github-pr-reviewer": {
    "type": "agent",
    "description": "AI agent that reviews GitHub PRs",
    "repository": "https://github.com/claude-extensions/agents",
    "categories": ["code-review", "github"],
    "version": "1.0.0",
    "requires": [
      "modelcontextprotocol/github",  # MCP server dependency
      "skills/code-analysis"           # Skill dependency
    ],
    "install": {
      "scope": "user-global",
      "agent_config": {
        "name": "PR Reviewer",
        "description": "Reviews pull requests for code quality",
        "tools": ["github_list_prs", "github_get_diff"],
        "prompt_template": "You are a code reviewer..."
      }
    }
  }
}
```

**Key Features**:
- Dependency resolution across types
- Agent configuration templating
- Skill composition

**Success Criteria**:
- 10+ agents in catalog
- Dependency resolver handles complex graphs
- Clear error messages for missing dependencies
- Rollback on installation failure

**Timeline**: 1 month after v3.1 ships

---

## Phase 4 Plan: Plugin Bundles (v4.0)

### Scope

Support full Claude Code plugin format with multi-component bundles.

### Why Bundles Are Last?

1. **Highest Complexity**: Orchestrates all other types
2. **Depends on Previous Phases**: Must have commands, hooks, agents working
3. **Largest Risk**: Bundle failures are most complex to debug

### Implementation Overview

```yaml
# Bundle catalog entry
{
  "bundles/full-stack-dev": {
    "type": "plugin-bundle",
    "description": "Complete full-stack development environment",
    "repository": "https://github.com/claude-plugins/full-stack-dev",
    "categories": ["development", "bundle"],
    "version": "1.0.0",
    "components": [
      {"type": "mcp-server", "package": "modelcontextprotocol/postgres"},
      {"type": "mcp-server", "package": "modelcontextprotocol/github"},
      {"type": "command", "package": "commands/pytest"},
      {"type": "hook", "package": "hooks/format-on-save"},
      {"type": "agent", "package": "agents/github-pr-reviewer"}
    ],
    "install": {
      "scope": "project",
      "post_install_message": "Full-stack dev environment ready!"
    }
  }
}
```

**Key Features**:
- Recursive installation
- Atomic transactions (all or nothing)
- Rollback on failure
- Post-install hooks

**Success Criteria**:
- 5+ curated bundles in catalog
- 100% success rate for atomic installs
- <30 second install time for 5-component bundle
- Clear progress indicators during install

**Timeline**: 1 month after v3.2 ships

---

## Backward Compatibility

### Maintaining Existing Functionality

**Zero Breaking Changes for MCP Servers**:

1. **Catalog Format**: MCP servers remain valid in extended schema
2. **CLI Commands**: All existing commands work unchanged
3. **Configuration Files**: No changes to MCP config format
4. **Scopes**: Existing scopes continue to work

**Migration Path**:

```python
# Old code (still works)
catalog = create_default_catalog()  # Now returns ExtensionCatalog
server = catalog.get_server("postgres")  # Deprecated but functional

# New code (recommended)
catalog = create_default_catalog()
extension = catalog.get_extension("modelcontextprotocol/postgres")
if extension.type == "mcp-server":
    server = extension.as_mcp_server()
```

**Deprecation Timeline**:

- v3.0: Old APIs work with deprecation warnings
- v3.5: Old APIs still work, warnings louder
- v4.0: Old APIs removed (major version bump)

### Testing Strategy

**Compatibility Test Suite**:
- All existing tests must pass unchanged
- Integration tests verify MCP servers work as before
- CLI smoke tests ensure no UX regressions

**Quality Gates**:
- 100% of existing tests pass
- Zero new warnings in user-facing output
- Performance within 10% of v2.0 benchmarks

---

## Security and Quality

### Extension Safety

**1. Catalog Curation**

- **Official Catalog**: Curated by MCPI maintainers (read-only)
- **Community Catalog**: User-submitted, reviewed before merge
- **Local Catalog**: User's personal catalog (full control)

**2. Code Review Process**

- All catalog additions require PR review
- Automated security scanning (GitHub CodeQL)
- Manual review checklist:
  - [ ] No arbitrary code execution
  - [ ] No network calls to unknown domains
  - [ ] No file system access outside project
  - [ ] Clear permission requirements documented
  - [ ] Source code available and auditable

**3. Permission System**

Extensions declare required permissions:

```yaml
{
  "commands/deploy-prod": {
    "type": "command",
    "permissions": {
      "filesystem": "write",
      "network": "https://api.production.com",
      "env_vars": ["AWS_ACCESS_KEY"]
    },
    "security_risk": "high"
  }
}
```

Users are prompted before installing high-risk extensions:

```
⚠️  WARNING: This extension requires high-risk permissions:
   - Write access to file system
   - Network access to https://api.production.com
   - Access to AWS credentials

Only install if you trust the author: @trusted-dev

Install anyway? [y/N]:
```

**4. Sandboxing (Future)**

Long-term: Run extensions in isolated environments with explicit permission grants.

### Quality Metrics

**Catalog Quality**:
- [ ] Each extension has clear description
- [ ] Each extension has example usage
- [ ] Each extension has tested installation
- [ ] Each extension has known author
- [ ] Each extension has version number
- [ ] Each extension has category tags

**User Trust**:
- [ ] Download counts visible
- [ ] User ratings and reviews
- [ ] Last updated date
- [ ] Maintenance status (active/deprecated)
- [ ] Security scan results

---

## Risk Analysis

### Technical Risks

**Risk 1: Catalog Size Explosion**

**Problem**: Catalog file becomes too large (>10MB) with 1000+ extensions.

**Mitigation**:
- Lazy loading of extension details
- Split catalog into multiple files by type
- CDN for catalog distribution
- Local caching with TTL

**Likelihood**: Medium | **Impact**: Medium | **Severity**: Medium

---

**Risk 2: Dependency Hell**

**Problem**: Complex dependency graphs create version conflicts.

**Mitigation**:
- Semantic versioning enforcement
- Clear dependency conflict messages
- Version pinning in bundles
- Rollback on conflict detection

**Likelihood**: High | **Impact**: High | **Severity**: High

**Note**: This is the biggest technical risk. Phase 3 must nail dependency resolution.

---

**Risk 3: Installation Failures**

**Problem**: Extensions fail to install due to environment differences.

**Mitigation**:
- Pre-installation validation checks
- Clear error messages with fixes
- Automatic rollback on failure
- Dry-run mode for testing

**Likelihood**: High | **Impact**: Medium | **Severity**: Medium

---

**Risk 4: Performance Degradation**

**Problem**: Catalog operations slow down with 1000+ extensions.

**Mitigation**:
- Indexed search (sqlite FTS)
- Pagination for list operations
- Lazy loading of extension content
- Caching of common queries

**Likelihood**: Medium | **Impact**: Medium | **Severity**: Medium

---

### Ecosystem Risks

**Risk 5: Fragmentation**

**Problem**: Multiple competing registries emerge, fragmenting the ecosystem.

**Mitigation**:
- Strong first-mover advantage
- Official endorsement by Anthropic (if possible)
- Easiest installation experience
- Best catalog quality

**Likelihood**: Medium | **Impact**: High | **Severity**: High

**Note**: Ecosystem risks are strategic, not technical. Speed to market matters.

---

**Risk 6: Malicious Extensions**

**Problem**: Attacker publishes malicious extension to steal credentials.

**Mitigation**:
- Mandatory code review for catalog inclusion
- Security scanning automation
- Permission system with warnings
- User reporting mechanism
- Quick removal process

**Likelihood**: Medium | **Impact**: Critical | **Severity**: High

**Note**: Security is non-negotiable. Err on the side of caution.

---

**Risk 7: Anthropic Competition**

**Problem**: Anthropic launches their own official registry, making MCPI obsolete.

**Mitigation**:
- Maintain compatibility with official registry
- Offer value-adds (curation, templates, tooling)
- Pivot to complementary tool if needed
- Build strong community quickly

**Likelihood**: High | **Impact**: Critical | **Severity**: Critical

**Note**: This is existential. MCPI must be indispensable before Anthropic moves.

---

## Success Metrics

### Technical Success (v3.0)

**Must Have**:
- [ ] 50+ commands in catalog
- [ ] <5% installation failure rate
- [ ] 80%+ test coverage
- [ ] Zero regressions in MCP functionality
- [ ] <200ms catalog load time

**Nice to Have**:
- [ ] 100+ commands in catalog
- [ ] <1% installation failure rate
- [ ] 90%+ test coverage
- [ ] <100ms catalog load time

### User Success (90 days post-v3.0)

**Must Have**:
- [ ] 500+ installations across all extensions
- [ ] 50+ users install at least one extension
- [ ] 4.0+ star rating on average
- [ ] <10 support tickets per week

**Nice to Have**:
- [ ] 2000+ installations
- [ ] 200+ users install extensions
- [ ] 4.5+ star rating
- [ ] Community contributions start flowing

### Ecosystem Success (6 months post-v3.0)

**Must Have**:
- [ ] 10+ community-contributed extensions
- [ ] 3+ independent authors
- [ ] 1+ bundle created by community
- [ ] GitHub awesome list features MCPI

**Nice to Have**:
- [ ] 50+ community extensions
- [ ] 10+ active contributors
- [ ] Official Anthropic acknowledgment
- [ ] Conference talk about MCPI ecosystem

---

## Alternative Approaches Considered

### Alternative 1: Build Separate Tool

**Idea**: Create "claude-extension-manager" as a separate project.

**Pros**:
- Clean slate, no legacy constraints
- Can optimize for extension use case
- Different name/branding

**Cons**:
- Duplicates 90% of MCPI functionality
- Users have two tools to learn
- Splits ecosystem
- Wastes existing MCPI user base

**Decision**: REJECTED. Evolving MCPI is far more efficient.

---

### Alternative 2: Use Claude's Native Plugin System

**Idea**: Wait for Anthropic to add registry, just build on top.

**Pros**:
- Official support
- Less maintenance burden
- Natural ecosystem alignment

**Cons**:
- No timeline from Anthropic
- May never happen
- Users suffer until then
- Miss first-mover advantage

**Decision**: REJECTED. Build now, adapt later if needed.

---

### Alternative 3: GitHub-Based Registry

**Idea**: Use GitHub repos as the registry (like Homebrew).

**Pros**:
- Distributed, no central server
- Git for versioning
- GitHub's security features

**Cons**:
- Slow for search/discovery
- Requires internet access
- Complex dependency resolution
- No offline support

**Decision**: REJECTED. Catalog file is faster and works offline.

---

### Alternative 4: Focus Only on Commands

**Idea**: Only support commands, leave other types for later tools.

**Pros**:
- Simpler scope
- Faster to market
- Less risk

**Cons**:
- Misses "npm for Claude" vision
- Someone else builds the full solution
- Users need multiple tools

**Decision**: REJECTED. The vision requires all types. Phasing handles risk.

---

## Next Steps

### Immediate Actions (This Week)

1. **Get User Feedback**: Share this proposal in MCPI GitHub Discussions
2. **Validate Assumptions**: Interview 5-10 Claude Code users about pain points
3. **Technical Spike**: Prototype command installer (2 days)
4. **Estimate Effort**: Break down Phase 1 into detailed tasks with time estimates

### Short-Term (This Month)

1. **Create RFC**: Write detailed RFC for catalog schema extensions
2. **Design Review**: Get feedback on installer architecture
3. **Security Review**: Get security expert to review permission system
4. **Community Engagement**: Post to Claude Code Discord about the vision

### Medium-Term (Next Quarter)

1. **Phase 1 Implementation**: Build commands support (4-5 weeks)
2. **Seed Catalog**: Create 50-100 curated commands
3. **Alpha Testing**: Get 10 users to test before public release
4. **v3.0 Release**: Ship commands support publicly

### Long-Term (Next 6 Months)

1. **Phase 2**: Hooks support
2. **Phase 3**: Skills & Agents support
3. **Phase 4**: Plugin bundles support
4. **Ecosystem Growth**: Community contributions, partnerships

---

## Appendix A: Catalog Schema

### Full Schema Definition

```typescript
// TypeScript definition for reference (implemented in Python/Pydantic)

type ExtensionType =
  | "mcp-server"
  | "command"
  | "hook"
  | "skill"
  | "agent"
  | "plugin-bundle";

interface BaseExtension {
  type: ExtensionType;
  description: string;
  repository: string;
  categories: string[];
  version: string;  // Semantic versioning
  author: string;
  requires: string[];  // Dependency IDs
  permissions?: {
    filesystem?: "read" | "write" | "none";
    network?: string[];  // Allowed domains
    env_vars?: string[];  // Required env vars
  };
  security_risk?: "low" | "medium" | "high";
}

interface MCPServerExtension extends BaseExtension {
  type: "mcp-server";
  command: string;
  args: string[];
  env?: Record<string, string>;
  templates?: string[];
}

interface CommandExtension extends BaseExtension {
  type: "command";
  content: string;  // Markdown content
  install: {
    scope: "project-commands" | "user-commands";
    filename: string;  // e.g., "pytest.md"
  };
}

interface HookExtension extends BaseExtension {
  type: "hook";
  install: {
    scope: string;
    hook_type: "before_read" | "after_write" | "before_commit" | "after_test";
    command: string;
    args: string[];
    conditions?: {
      file_pattern?: string;
      exit_code?: number;
    };
  };
}

interface AgentExtension extends BaseExtension {
  type: "agent";
  install: {
    scope: string;
    agent_config: {
      name: string;
      description: string;
      tools: string[];
      prompt_template?: string;
    };
  };
}

interface BundleExtension extends BaseExtension {
  type: "plugin-bundle";
  components: Array<{
    type: ExtensionType;
    package: string;  // Extension ID
  }>;
  install: {
    scope: string;
    post_install_message?: string;
  };
}

type Extension =
  | MCPServerExtension
  | CommandExtension
  | HookExtension
  | AgentExtension
  | BundleExtension;
```

---

## Appendix B: Example Commands

### Sample Command Catalog Entries

```json
{
  "commands/pytest": {
    "type": "command",
    "description": "Run pytest with automatic test discovery and coverage",
    "content": "# Run Pytest\n\nRun pytest tests with coverage reporting.\n\n```bash\npytest --cov=src --cov-report=term\n```\n\nOptions:\n- Add `-v` for verbose output\n- Add `-x` to stop at first failure\n- Add `-k <pattern>` to run specific tests",
    "repository": "https://github.com/claude-extensions/testing",
    "categories": ["testing", "python"],
    "version": "1.2.0",
    "author": "Claude Extensions",
    "requires": [],
    "install": {
      "scope": "project-commands",
      "filename": "pytest.md"
    }
  },

  "commands/git-smart-commit": {
    "type": "command",
    "description": "Generate intelligent commit messages based on staged changes",
    "content": "# Smart Git Commit\n\nAnalyze staged changes and generate a conventional commit message.\n\n1. Run `git diff --staged` to see changes\n2. Generate a conventional commit message following format:\n   - `feat:` for new features\n   - `fix:` for bug fixes\n   - `docs:` for documentation\n   - `refactor:` for refactoring\n3. Ask user to confirm or edit\n4. Execute `git commit -m \"<message>\"`",
    "repository": "https://github.com/claude-extensions/git-tools",
    "categories": ["git", "automation"],
    "version": "1.0.0",
    "author": "Claude Extensions",
    "requires": [],
    "permissions": {
      "filesystem": "write"
    },
    "install": {
      "scope": "user-commands",
      "filename": "git-smart-commit.md"
    }
  }
}
```

---

## Appendix C: Extension Authoring Guide

### Creating a Command Extension

1. **Write the Command Markdown**

```markdown
# My Awesome Command

Brief description of what this command does.

## Usage

Explain how to use the command with examples.

## Options

- Option 1: Description
- Option 2: Description

## Examples

Show concrete examples of the command in action.
```

2. **Create Catalog Entry**

```json
{
  "my-org/my-command": {
    "type": "command",
    "description": "One-line description",
    "content": "<full markdown content>",
    "repository": "https://github.com/my-org/my-command",
    "categories": ["category1", "category2"],
    "version": "1.0.0",
    "author": "My Name",
    "requires": [],
    "install": {
      "scope": "project-commands",
      "filename": "my-command.md"
    }
  }
}
```

3. **Submit Pull Request**

- Fork MCPI repository
- Add entry to `data/catalog.json`
- Add tests if applicable
- Submit PR with template filled out
- Wait for review

4. **Review Checklist**

Before submitting, ensure:
- [ ] Description is clear and concise
- [ ] Command is well-documented
- [ ] Examples are provided
- [ ] Categories are appropriate
- [ ] No malicious code
- [ ] Follows naming conventions

---

## Conclusion

MCPI has a rare opportunity to become the **npm of Claude extensions**. The architecture is already 70% there - we just need to expand horizontally across extension types.

**The time is now**:
- Claude Code plugins launched 1 month ago (October 2025)
- Ecosystem is forming but fragmented
- No dominant registry exists yet
- MCPI has first-mover advantage

**The path is clear**:
- Phase 1 (Commands) proves the concept
- Phase 2 (Hooks) adds automation value
- Phase 3 (Agents) enables composition
- Phase 4 (Bundles) completes the vision

**The risks are manageable**:
- Technical risks have known mitigations
- Ecosystem risks require speed and quality
- Security risks require diligence and process

**The reward is significant**:
- MCPI becomes essential infrastructure
- Strong moat through network effects
- Community growth and contributions
- Potential official Anthropic partnership

**Recommendation**: Proceed with Phase 1 implementation. Start with commands, validate the approach, then expand to full vision.

---

**Prepared by**: Product Visionary Agent
**Date**: 2025-11-25
**Next Review**: After user feedback and technical spike

---

## Sources

Research for this proposal drew from:

- [Customize Claude Code with plugins | Claude](https://www.anthropic.com/news/claude-code-plugins)
- [Slash commands - Claude Code Docs](https://code.claude.com/docs/en/slash-commands)
- [Understanding Claude Code: Skills vs Commands vs Subagents vs Plugins](https://www.youngleaders.tech/p/claude-skills-commands-subagents-plugins)
- [GitHub - hesreallyhim/awesome-claude-code](https://github.com/hesreallyhim/awesome-claude-code)
- [GitHub - ccplugins/awesome-claude-code-plugins](https://github.com/ccplugins/awesome-claude-code-plugins)
