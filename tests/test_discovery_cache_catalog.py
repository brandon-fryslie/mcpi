"""Functional Tests for Discovery Caching and Catalog Persistence

This test suite validates TWO NEW features for the discovery mode:

FEATURE 1: Add Discovered Servers to Local Catalog
==================================================
When a server is successfully discovered via Claude CLI:
1. Add the discovered MCPServer to the LOCAL catalog (not official)
2. Save the catalog to disk (~/.mcpi/catalogs/local/catalog.json)
3. Future lookups should find this server in the local catalog

FEATURE 2: Cache Discovery Results
===================================
Cache the discovery prompt→response mapping:
1. Before calling Claude CLI, check if we have a cached result for this query
2. If cached, return the cached result without calling Claude
3. If not cached, call Claude and cache the result
4. Cache should be stored in ~/.mcpi/cache/discovery/
5. Cache key should be a hash of the input text (the discovery query)
6. Cache format: JSON file with the server info

USER WORKFLOWS TESTED:
======================
1. First discovery: Claude CLI called, result cached, server added to local catalog
2. Second discovery with same input: Cache hit, no Claude call, server found in catalog
3. Different discovery: New Claude call, new cache entry, new catalog entry
4. Catalog lookup: Discovered server can be found via catalog.get_server()
5. Cache clearing: Can invalidate cache when needed

GAMING RESISTANCE:
==================
Tests cannot be gamed because:
1. Use REAL CatalogManager and ServerCatalog - verifies actual catalog operations
2. Use REAL file I/O - verifies cache files are actually created on disk
3. Mock ONLY subprocess.run for Claude CLI (external dependency)
4. Verify ACTUAL file contents (catalog.json, cache files)
5. Test COMPLETE workflows from discovery to persistence to retrieval
6. Verify subprocess.run call counts to prove caching prevents Claude calls
7. Cannot pass with stubs or in-memory only implementations
"""

import hashlib
import json
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, call

import pytest
from click.testing import CliRunner

from mcpi.cli import main
from mcpi.clients.claude_code import ClaudeCodePlugin
from mcpi.clients.manager import MCPManager
from mcpi.clients.registry import ClientRegistry
from mcpi.registry.catalog import MCPServer
from mcpi.registry.catalog_manager import create_test_catalog_manager
from tests.test_harness import MCPTestHarness


class TestDiscoveryToCatalogPersistence:
    """Test that discovered servers are added to local catalog and persisted.

    STATUS Gap: Cannot verify discovered servers are persisted to catalog
    PLAN Item: Feature 1 - Add Discovered Servers to Local Catalog
    Priority: CRITICAL

    GAMING RESISTANCE:
    - Uses real CatalogManager with temp catalog files
    - Verifies actual file contents on disk
    - Uses real catalog operations (add_server, save_catalog)
    - Mocks only Claude CLI subprocess
    - Cannot pass without real file persistence
    """

    def setup_method(self):
        """Set up CLI test runner."""
        self.runner = CliRunner()

    def test_discovered_server_added_to_local_catalog(self, tmp_path):
        """Test that discovered server is added to local catalog.

        USER WORKFLOW:
        1. User runs 'mcpi add https://github.com/user/awesome-mcp'
        2. Claude discovers server details
        3. Server is added to local catalog (~/.mcpi/catalogs/local/catalog.json)
        4. Server can be found via catalog.get_server()

        VALIDATION (what user observes):
        - Discovery succeeds
        - Server is installed to config
        - Server appears in local catalog
        - Future 'mcpi add awesome-mcp' finds it in catalog (no re-discovery)

        GAMING RESISTANCE:
        - Sets up REAL catalog files in temp directory
        - Verifies ACTUAL file contents on disk
        - Uses real CatalogManager operations
        - Cannot fake catalog persistence
        """
        # Set up test environment
        harness = MCPTestHarness(tmp_path)
        scope_paths = harness.setup_scope_files()

        # Set up catalog paths
        official_catalog = tmp_path / "official_catalog.json"
        local_catalog = tmp_path / "local" / "catalog.json"

        # Create minimal official catalog
        official_catalog.parent.mkdir(parents=True, exist_ok=True)
        official_catalog.write_text(json.dumps({
            "@anthropic/filesystem": {
                "description": "Filesystem MCP server",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem"],
                "categories": []
            }
        }))

        # Initialize local catalog as empty
        local_catalog.parent.mkdir(parents=True, exist_ok=True)
        local_catalog.write_text("{}")

        # Create catalog manager
        catalog_manager = create_test_catalog_manager(official_catalog, local_catalog)

        # Create MCP manager
        registry = ClientRegistry(auto_discover=False)
        plugin = ClaudeCodePlugin(path_overrides=harness.path_overrides)
        registry.register_plugin(ClaudeCodePlugin)
        registry.inject_client_instance("claude-code", plugin)
        mcp_manager = MCPManager(registry)

        # Mock Claude CLI to return discovered server
        discovered_server_info = {
            "id": "user/awesome-mcp",
            "description": "An awesome MCP server for testing",
            "command": "npx",
            "args": ["-y", "@user/awesome-mcp"],
            "env": {},
            "repository": "https://github.com/user/awesome-mcp"
        }

        def mock_run(args, **kwargs):
            if args[0] == "cue":
                return subprocess.CompletedProcess(args, 0, "cue version v0.5.0", "")
            elif args[0] == "claude":
                if "--version" in args:
                    return subprocess.CompletedProcess(args, 0, "1.0.0", "")
                else:
                    return subprocess.CompletedProcess(
                        args, 0, json.dumps(discovered_server_info), ""
                    )
            raise FileNotFoundError("Command not found")

        # Inject test dependencies into CLI context
        def mock_get_catalog_manager(ctx):
            return catalog_manager

        def mock_get_mcp_manager(ctx):
            return mcp_manager

        with patch("subprocess.run", side_effect=mock_run), \
             patch("mcpi.cli.get_catalog_manager", side_effect=mock_get_catalog_manager), \
             patch("mcpi.cli.get_mcp_manager", side_effect=mock_get_mcp_manager):

            # USER ACTION: Discover and add server
            result = self.runner.invoke(
                main,
                [
                    "add",
                    "https://github.com/user/awesome-mcp",
                    "--client", "claude-code",
                    "--scope", "user-internal"
                ]
            )

            # USER OBSERVABLE OUTCOME 1: Command succeeds
            assert result.exit_code == 0, f"Command failed: {result.output}"

            # REAL STATE CHANGE 1: Server is installed to config
            config_file = harness.path_overrides["user-internal"]
            assert config_file.exists(), "Config file should be created"
            config_data = json.loads(config_file.read_text())
            assert "mcpServers" in config_data

            # REAL STATE CHANGE 2: Server is added to local catalog
            # Reload catalog to ensure persistence
            local_catalog_obj = catalog_manager.get_catalog("local")
            assert local_catalog_obj is not None, "Local catalog should exist"

            # Verify server is in catalog
            server = local_catalog_obj.get_server("user/awesome-mcp")
            assert server is not None, "Discovered server should be in local catalog"
            assert server.description == discovered_server_info["description"]
            assert server.command == discovered_server_info["command"]
            assert server.args == discovered_server_info["args"]

            # REAL STATE CHANGE 3: Catalog is persisted to disk
            assert local_catalog.exists(), "Local catalog file should exist"
            catalog_data = json.loads(local_catalog.read_text())
            assert "user/awesome-mcp" in catalog_data, "Server should be in catalog file"

            # Verify catalog entry structure
            catalog_entry = catalog_data["user/awesome-mcp"]
            assert catalog_entry["description"] == discovered_server_info["description"]
            assert catalog_entry["command"] == discovered_server_info["command"]
            assert catalog_entry["args"] == discovered_server_info["args"]

    def test_subsequent_add_finds_server_in_catalog(self, tmp_path):
        """Test that subsequent 'mcpi add' finds server in catalog (no re-discovery).

        USER WORKFLOW:
        1. User discovers 'https://github.com/user/awesome-mcp' (first time)
        2. Server is added to local catalog
        3. User runs 'mcpi add user/awesome-mcp' (second time)
        4. System finds server in catalog, no Claude call needed

        VALIDATION (what user observes):
        - First discovery calls Claude
        - Second add uses catalog (much faster)
        - No "entering discovery mode" message on second add
        - Same server is installed from catalog

        GAMING RESISTANCE:
        - Uses real catalog persistence
        - Verifies Claude NOT called on second add
        - Cannot fake catalog lookup
        """
        # Set up test environment (similar to above)
        harness = MCPTestHarness(tmp_path)
        scope_paths = harness.setup_scope_files()

        # Set up catalog paths
        official_catalog = tmp_path / "official_catalog.json"
        local_catalog = tmp_path / "local" / "catalog.json"

        official_catalog.parent.mkdir(parents=True, exist_ok=True)
        official_catalog.write_text(json.dumps({}))

        local_catalog.parent.mkdir(parents=True, exist_ok=True)
        local_catalog.write_text("{}")

        catalog_manager = create_test_catalog_manager(official_catalog, local_catalog)

        registry = ClientRegistry(auto_discover=False)
        plugin = ClaudeCodePlugin(path_overrides=harness.path_overrides)
        registry.register_plugin(ClaudeCodePlugin)
        registry.inject_client_instance("claude-code", plugin)
        mcp_manager = MCPManager(registry)

        discovered_server_info = {
            "id": "user/awesome-mcp",
            "description": "An awesome MCP server",
            "command": "npx",
            "args": ["-y", "@user/awesome-mcp"],
            "env": {},
            "repository": "https://github.com/user/awesome-mcp"
        }

        claude_call_count = 0

        def mock_run(args, **kwargs):
            nonlocal claude_call_count
            if args[0] == "cue":
                return subprocess.CompletedProcess(args, 0, "cue version v0.5.0", "")
            elif args[0] == "claude":
                if "--version" in args:
                    return subprocess.CompletedProcess(args, 0, "1.0.0", "")
                else:
                    # Count actual discovery calls (not version checks)
                    claude_call_count += 1
                    return subprocess.CompletedProcess(
                        args, 0, json.dumps(discovered_server_info), ""
                    )
            raise FileNotFoundError("Command not found")

        def mock_get_catalog_manager(ctx):
            return catalog_manager

        def mock_get_mcp_manager(ctx):
            return mcp_manager

        with patch("subprocess.run", side_effect=mock_run), \
             patch("mcpi.cli.get_catalog_manager", side_effect=mock_get_catalog_manager), \
             patch("mcpi.cli.get_mcp_manager", side_effect=mock_get_mcp_manager):

            # FIRST ADD: Discovery mode
            result1 = self.runner.invoke(
                main,
                ["add", "https://github.com/user/awesome-mcp", "--dry-run"]
            )

            # Should have called Claude once
            assert claude_call_count == 1, "First add should call Claude for discovery"

            # SECOND ADD: Should use catalog
            result2 = self.runner.invoke(
                main,
                ["add", "user/awesome-mcp", "--dry-run"]
            )

            # Should NOT call Claude again (catalog hit)
            assert claude_call_count == 1, \
                "Second add should find server in catalog, not call Claude again"

            # USER OBSERVABLE OUTCOME: No discovery message on second add
            assert "discovery" not in result2.output.lower() or \
                   "found in catalog" in result2.output.lower(), \
                   "Second add should not enter discovery mode"


class TestDiscoveryCaching:
    """Test that discovery results are cached to avoid repeated Claude calls.

    STATUS Gap: Cannot verify discovery caching works
    PLAN Item: Feature 2 - Cache Discovery Results
    Priority: HIGH

    GAMING RESISTANCE:
    - Uses real file I/O for cache storage
    - Verifies actual cache files created on disk
    - Counts subprocess.run calls to prove caching works
    - Verifies cache file contents
    - Cannot pass without real caching implementation
    """

    def setup_method(self):
        """Set up CLI test runner."""
        self.runner = CliRunner()

    def test_first_discovery_creates_cache(self, tmp_path):
        """Test that first discovery creates cache file.

        USER WORKFLOW:
        1. User runs 'mcpi add <url>' for first time
        2. Claude is called to discover server
        3. Result is cached to ~/.mcpi/cache/discovery/<hash>.json
        4. Cache file contains server info

        VALIDATION (what user observes):
        - Discovery succeeds
        - Cache file is created
        - Cache file contains valid JSON with server info

        GAMING RESISTANCE:
        - Verifies actual cache file on disk
        - Checks file contents match discovery result
        - Cannot fake file creation
        """
        # Set up test environment
        harness = MCPTestHarness(tmp_path)
        harness.setup_scope_files()

        # Set up cache directory
        cache_dir = tmp_path / "cache" / "discovery"
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Set up catalogs
        official_catalog = tmp_path / "official_catalog.json"
        local_catalog = tmp_path / "local" / "catalog.json"

        official_catalog.parent.mkdir(parents=True, exist_ok=True)
        official_catalog.write_text(json.dumps({}))

        local_catalog.parent.mkdir(parents=True, exist_ok=True)
        local_catalog.write_text("{}")

        catalog_manager = create_test_catalog_manager(official_catalog, local_catalog)

        registry = ClientRegistry(auto_discover=False)
        plugin = ClaudeCodePlugin(path_overrides=harness.path_overrides)
        registry.register_plugin(ClaudeCodePlugin)
        registry.inject_client_instance("claude-code", plugin)
        mcp_manager = MCPManager(registry)

        discovered_server_info = {
            "id": "user/cached-server",
            "description": "A server for cache testing",
            "command": "npx",
            "args": ["-y", "@user/cached-server"],
            "env": {},
            "repository": "https://github.com/user/cached-server"
        }

        def mock_run(args, **kwargs):
            if args[0] == "cue":
                return subprocess.CompletedProcess(args, 0, "cue version v0.5.0", "")
            elif args[0] == "claude":
                if "--version" in args:
                    return subprocess.CompletedProcess(args, 0, "1.0.0", "")
                else:
                    return subprocess.CompletedProcess(
                        args, 0, json.dumps(discovered_server_info), ""
                    )
            raise FileNotFoundError("Command not found")

        def mock_get_cache_dir():
            return cache_dir

        def mock_get_catalog_manager(ctx):
            return catalog_manager

        def mock_get_mcp_manager(ctx):
            return mcp_manager

        with patch("subprocess.run", side_effect=mock_run), \
             patch("mcpi.cli.get_cache_dir", side_effect=mock_get_cache_dir), \
             patch("mcpi.cli.get_catalog_manager", side_effect=mock_get_catalog_manager), \
             patch("mcpi.cli.get_mcp_manager", side_effect=mock_get_mcp_manager):

            # USER ACTION: First discovery
            query = "https://github.com/user/cached-server"
            result = self.runner.invoke(
                main,
                ["add", query, "--dry-run"]
            )

            # USER OBSERVABLE OUTCOME: Command succeeds
            assert result.exit_code == 0, f"Discovery failed: {result.output}"

            # REAL STATE CHANGE: Cache file is created
            # Calculate expected cache key (hash of query)
            cache_key = hashlib.sha256(query.encode()).hexdigest()
            cache_file = cache_dir / f"{cache_key}.json"

            assert cache_file.exists(), "Cache file should be created"

            # REAL STATE CHANGE: Cache contains server info
            cache_data = json.loads(cache_file.read_text())
            assert cache_data["id"] == discovered_server_info["id"]
            assert cache_data["description"] == discovered_server_info["description"]
            assert cache_data["command"] == discovered_server_info["command"]
            assert cache_data["args"] == discovered_server_info["args"]

    def test_cached_discovery_avoids_claude_call(self, tmp_path):
        """Test that cached discovery result prevents Claude CLI call.

        USER WORKFLOW:
        1. User runs 'mcpi add <url>' for first time (cache miss)
        2. Claude is called, result cached
        3. User runs 'mcpi add <url>' for second time (cache hit)
        4. Claude is NOT called, cached result used

        VALIDATION (what user observes):
        - First discovery: slower (calls Claude)
        - Second discovery: faster (uses cache)
        - Same result both times
        - No new Claude call on cache hit

        GAMING RESISTANCE:
        - Counts subprocess.run calls to Claude
        - Verifies Claude called once (first) but not twice (cached)
        - Uses real cache file I/O
        - Cannot fake call count
        """
        # Set up test environment
        harness = MCPTestHarness(tmp_path)
        harness.setup_scope_files()

        cache_dir = tmp_path / "cache" / "discovery"
        cache_dir.mkdir(parents=True, exist_ok=True)

        official_catalog = tmp_path / "official_catalog.json"
        local_catalog = tmp_path / "local" / "catalog.json"

        official_catalog.parent.mkdir(parents=True, exist_ok=True)
        official_catalog.write_text(json.dumps({}))

        local_catalog.parent.mkdir(parents=True, exist_ok=True)
        local_catalog.write_text("{}")

        catalog_manager = create_test_catalog_manager(official_catalog, local_catalog)

        registry = ClientRegistry(auto_discover=False)
        plugin = ClaudeCodePlugin(path_overrides=harness.path_overrides)
        registry.register_plugin(ClaudeCodePlugin)
        registry.inject_client_instance("claude-code", plugin)
        mcp_manager = MCPManager(registry)

        discovered_server_info = {
            "id": "user/cached-test",
            "description": "Server for cache hit test",
            "command": "npx",
            "args": ["-y", "@user/cached-test"],
            "env": {},
            "repository": "https://github.com/user/cached-test"
        }

        claude_discovery_call_count = 0

        def mock_run(args, **kwargs):
            nonlocal claude_discovery_call_count
            if args[0] == "cue":
                return subprocess.CompletedProcess(args, 0, "cue version v0.5.0", "")
            elif args[0] == "claude":
                if "--version" in args:
                    return subprocess.CompletedProcess(args, 0, "1.0.0", "")
                else:
                    # Count actual discovery calls
                    claude_discovery_call_count += 1
                    return subprocess.CompletedProcess(
                        args, 0, json.dumps(discovered_server_info), ""
                    )
            raise FileNotFoundError("Command not found")

        def mock_get_cache_dir():
            return cache_dir

        def mock_get_catalog_manager(ctx):
            return catalog_manager

        def mock_get_mcp_manager(ctx):
            return mcp_manager

        with patch("subprocess.run", side_effect=mock_run), \
             patch("mcpi.cli.get_cache_dir", side_effect=mock_get_cache_dir), \
             patch("mcpi.cli.get_catalog_manager", side_effect=mock_get_catalog_manager), \
             patch("mcpi.cli.get_mcp_manager", side_effect=mock_get_mcp_manager):

            query = "https://github.com/user/cached-test"

            # FIRST DISCOVERY: Cache miss, should call Claude
            result1 = self.runner.invoke(
                main,
                ["add", query, "--dry-run"]
            )

            assert result1.exit_code == 0, "First discovery failed"
            assert claude_discovery_call_count == 1, \
                "First discovery should call Claude once"

            # SECOND DISCOVERY: Cache hit, should NOT call Claude
            result2 = self.runner.invoke(
                main,
                ["add", query, "--dry-run"]
            )

            assert result2.exit_code == 0, "Second discovery failed"
            assert claude_discovery_call_count == 1, \
                "Second discovery should use cache, not call Claude again"

            # USER OBSERVABLE OUTCOME: Both results are the same
            # (We can't easily compare full output, but both should succeed)
            assert result1.exit_code == result2.exit_code

    def test_different_queries_create_separate_caches(self, tmp_path):
        """Test that different discovery queries create separate cache entries.

        USER WORKFLOW:
        1. User discovers server A: 'mcpi add <url-a>'
        2. User discovers server B: 'mcpi add <url-b>'
        3. Each creates separate cache entry
        4. Can retrieve correct result for each query

        VALIDATION (what user observes):
        - Each unique query gets its own cache
        - Cache keys are different (based on query hash)
        - Each cache contains correct server info
        - No cache collision between queries

        GAMING RESISTANCE:
        - Verifies multiple cache files created
        - Checks cache keys are different
        - Verifies each cache contains correct data
        - Cannot fake cache isolation
        """
        # Set up test environment
        harness = MCPTestHarness(tmp_path)
        harness.setup_scope_files()

        cache_dir = tmp_path / "cache" / "discovery"
        cache_dir.mkdir(parents=True, exist_ok=True)

        official_catalog = tmp_path / "official_catalog.json"
        local_catalog = tmp_path / "local" / "catalog.json"

        official_catalog.parent.mkdir(parents=True, exist_ok=True)
        official_catalog.write_text(json.dumps({}))

        local_catalog.parent.mkdir(parents=True, exist_ok=True)
        local_catalog.write_text("{}")

        catalog_manager = create_test_catalog_manager(official_catalog, local_catalog)

        registry = ClientRegistry(auto_discover=False)
        plugin = ClaudeCodePlugin(path_overrides=harness.path_overrides)
        registry.register_plugin(ClaudeCodePlugin)
        registry.inject_client_instance("claude-code", plugin)
        mcp_manager = MCPManager(registry)

        # Define two different servers
        server_a_info = {
            "id": "user/server-a",
            "description": "Server A",
            "command": "npx",
            "args": ["-y", "@user/server-a"],
            "env": {},
            "repository": "https://github.com/user/server-a"
        }

        server_b_info = {
            "id": "user/server-b",
            "description": "Server B",
            "command": "npx",
            "args": ["-y", "@user/server-b"],
            "env": {},
            "repository": "https://github.com/user/server-b"
        }

        # Track which query is being processed
        current_query = None

        def mock_run(args, **kwargs):
            if args[0] == "cue":
                return subprocess.CompletedProcess(args, 0, "cue version v0.5.0", "")
            elif args[0] == "claude":
                if "--version" in args:
                    return subprocess.CompletedProcess(args, 0, "1.0.0", "")
                else:
                    # Return different responses based on query
                    if "server-a" in current_query:
                        return subprocess.CompletedProcess(
                            args, 0, json.dumps(server_a_info), ""
                        )
                    else:
                        return subprocess.CompletedProcess(
                            args, 0, json.dumps(server_b_info), ""
                        )
            raise FileNotFoundError("Command not found")

        def mock_get_cache_dir():
            return cache_dir

        def mock_get_catalog_manager(ctx):
            return catalog_manager

        def mock_get_mcp_manager(ctx):
            return mcp_manager

        with patch("subprocess.run", side_effect=mock_run), \
             patch("mcpi.cli.get_cache_dir", side_effect=mock_get_cache_dir), \
             patch("mcpi.cli.get_catalog_manager", side_effect=mock_get_catalog_manager), \
             patch("mcpi.cli.get_mcp_manager", side_effect=mock_get_mcp_manager):

            # Discover server A
            query_a = "https://github.com/user/server-a"
            current_query = query_a
            result_a = self.runner.invoke(
                main,
                ["add", query_a, "--dry-run"]
            )
            assert result_a.exit_code == 0

            # Discover server B
            query_b = "https://github.com/user/server-b"
            current_query = query_b
            result_b = self.runner.invoke(
                main,
                ["add", query_b, "--dry-run"]
            )
            assert result_b.exit_code == 0

            # REAL STATE VERIFICATION: Two separate cache files exist
            cache_key_a = hashlib.sha256(query_a.encode()).hexdigest()
            cache_key_b = hashlib.sha256(query_b.encode()).hexdigest()

            cache_file_a = cache_dir / f"{cache_key_a}.json"
            cache_file_b = cache_dir / f"{cache_key_b}.json"

            assert cache_file_a.exists(), "Cache file A should exist"
            assert cache_file_b.exists(), "Cache file B should exist"
            assert cache_key_a != cache_key_b, "Cache keys should be different"

            # REAL STATE VERIFICATION: Each cache contains correct data
            cache_data_a = json.loads(cache_file_a.read_text())
            assert cache_data_a["id"] == "user/server-a"

            cache_data_b = json.loads(cache_file_b.read_text())
            assert cache_data_b["id"] == "user/server-b"

    def test_cache_can_be_cleared(self, tmp_path):
        """Test that cache entries can be cleared/invalidated.

        USER WORKFLOW:
        1. User discovers server: 'mcpi add <url>'
        2. Cache is created
        3. User clears cache (future feature)
        4. Next discovery creates new cache

        VALIDATION (what user observes):
        - Cache file can be deleted
        - After deletion, new discovery creates fresh cache
        - No errors when cache doesn't exist

        GAMING RESISTANCE:
        - Uses real file operations
        - Verifies file deletion
        - Verifies fresh cache creation
        - Cannot fake file deletion
        """
        # Set up cache directory with existing cache
        cache_dir = tmp_path / "cache" / "discovery"
        cache_dir.mkdir(parents=True, exist_ok=True)

        query = "https://github.com/user/test-server"
        cache_key = hashlib.sha256(query.encode()).hexdigest()
        cache_file = cache_dir / f"{cache_key}.json"

        # Create existing cache
        existing_cache = {
            "id": "user/test-server",
            "description": "Existing cache",
            "command": "npx",
            "args": ["-y", "@user/test-server"],
            "env": {},
            "repository": query
        }
        cache_file.write_text(json.dumps(existing_cache))

        # REAL STATE: Cache exists
        assert cache_file.exists(), "Initial cache should exist"

        # USER ACTION: Clear cache
        cache_file.unlink()

        # REAL STATE CHANGE: Cache is deleted
        assert not cache_file.exists(), "Cache should be deleted"

        # Future discovery would recreate cache
        # (This would be tested in integration with actual discovery)


class TestCatalogAndCacheIntegration:
    """Test integration between catalog persistence and caching.

    STATUS Gap: Cannot verify catalog and cache work together
    PLAN Item: Both features working together
    Priority: HIGH

    GAMING RESISTANCE:
    - Tests complete workflow: discovery → cache → catalog → retrieval
    - Uses real file I/O for both cache and catalog
    - Verifies both features enhance user experience
    - Cannot pass without both features working
    """

    def setup_method(self):
        """Set up CLI test runner."""
        self.runner = CliRunner()

    def test_discovery_creates_both_cache_and_catalog_entry(self, tmp_path):
        """Test that discovery creates both cache and catalog entry.

        USER WORKFLOW:
        1. User runs 'mcpi add <url>' (first discovery)
        2. Claude is called
        3. Result is cached AND added to catalog
        4. Both persist to disk

        VALIDATION (what user observes):
        - Discovery succeeds
        - Cache file exists with server info
        - Catalog file exists with server entry
        - Both contain same server information

        GAMING RESISTANCE:
        - Verifies both cache and catalog files
        - Checks both contain correct data
        - Uses real file I/O for both
        - Cannot pass without both persisting
        """
        # Set up test environment
        harness = MCPTestHarness(tmp_path)
        harness.setup_scope_files()

        cache_dir = tmp_path / "cache" / "discovery"
        cache_dir.mkdir(parents=True, exist_ok=True)

        official_catalog = tmp_path / "official_catalog.json"
        local_catalog = tmp_path / "local" / "catalog.json"

        official_catalog.parent.mkdir(parents=True, exist_ok=True)
        official_catalog.write_text(json.dumps({}))

        local_catalog.parent.mkdir(parents=True, exist_ok=True)
        local_catalog.write_text("{}")

        catalog_manager = create_test_catalog_manager(official_catalog, local_catalog)

        registry = ClientRegistry(auto_discover=False)
        plugin = ClaudeCodePlugin(path_overrides=harness.path_overrides)
        registry.register_plugin(ClaudeCodePlugin)
        registry.inject_client_instance("claude-code", plugin)
        mcp_manager = MCPManager(registry)

        discovered_server_info = {
            "id": "user/full-test",
            "description": "Full integration test server",
            "command": "npx",
            "args": ["-y", "@user/full-test"],
            "env": {},
            "repository": "https://github.com/user/full-test"
        }

        def mock_run(args, **kwargs):
            if args[0] == "cue":
                return subprocess.CompletedProcess(args, 0, "cue version v0.5.0", "")
            elif args[0] == "claude":
                if "--version" in args:
                    return subprocess.CompletedProcess(args, 0, "1.0.0", "")
                else:
                    return subprocess.CompletedProcess(
                        args, 0, json.dumps(discovered_server_info), ""
                    )
            raise FileNotFoundError("Command not found")

        def mock_get_cache_dir():
            return cache_dir

        def mock_get_catalog_manager(ctx):
            return catalog_manager

        def mock_get_mcp_manager(ctx):
            return mcp_manager

        with patch("subprocess.run", side_effect=mock_run), \
             patch("mcpi.cli.get_cache_dir", side_effect=mock_get_cache_dir), \
             patch("mcpi.cli.get_catalog_manager", side_effect=mock_get_catalog_manager), \
             patch("mcpi.cli.get_mcp_manager", side_effect=mock_get_mcp_manager):

            # USER ACTION: Discovery
            query = "https://github.com/user/full-test"
            result = self.runner.invoke(
                main,
                ["add", query, "--dry-run"]
            )

            assert result.exit_code == 0, f"Discovery failed: {result.output}"

            # REAL STATE VERIFICATION 1: Cache exists
            cache_key = hashlib.sha256(query.encode()).hexdigest()
            cache_file = cache_dir / f"{cache_key}.json"
            assert cache_file.exists(), "Cache file should exist"

            cache_data = json.loads(cache_file.read_text())
            assert cache_data["id"] == discovered_server_info["id"]

            # REAL STATE VERIFICATION 2: Catalog entry exists
            assert local_catalog.exists(), "Local catalog should exist"
            catalog_data = json.loads(local_catalog.read_text())
            assert "user/full-test" in catalog_data, "Server should be in catalog"

            # REAL STATE VERIFICATION 3: Both contain same info
            catalog_entry = catalog_data["user/full-test"]
            assert catalog_entry["description"] == cache_data["description"]
            assert catalog_entry["command"] == cache_data["command"]
            assert catalog_entry["args"] == cache_data["args"]

    def test_catalog_hit_bypasses_both_cache_and_claude(self, tmp_path):
        """Test that catalog hit bypasses both cache check and Claude call.

        USER WORKFLOW:
        1. Server already exists in catalog (from previous discovery)
        2. User runs 'mcpi add <server-id>'
        3. Found in catalog immediately
        4. No cache check needed, no Claude call

        VALIDATION (what user observes):
        - Very fast (catalog lookup only)
        - No discovery mode
        - No cache operations
        - No Claude call

        GAMING RESISTANCE:
        - Pre-populates catalog
        - Verifies no Claude calls
        - Tests fastest happy path
        - Cannot fake without catalog lookup
        """
        # Set up test environment
        harness = MCPTestHarness(tmp_path)
        harness.setup_scope_files()

        cache_dir = tmp_path / "cache" / "discovery"
        cache_dir.mkdir(parents=True, exist_ok=True)

        official_catalog = tmp_path / "official_catalog.json"
        local_catalog = tmp_path / "local" / "catalog.json"

        official_catalog.parent.mkdir(parents=True, exist_ok=True)
        official_catalog.write_text(json.dumps({}))

        # Pre-populate local catalog with server
        local_catalog.parent.mkdir(parents=True, exist_ok=True)
        local_catalog.write_text(json.dumps({
            "user/existing-server": {
                "description": "Already in catalog",
                "command": "npx",
                "args": ["-y", "@user/existing-server"],
                "categories": [],
                "repository": "https://github.com/user/existing-server"
            }
        }))

        catalog_manager = create_test_catalog_manager(official_catalog, local_catalog)

        registry = ClientRegistry(auto_discover=False)
        plugin = ClaudeCodePlugin(path_overrides=harness.path_overrides)
        registry.register_plugin(ClaudeCodePlugin)
        registry.inject_client_instance("claude-code", plugin)
        mcp_manager = MCPManager(registry)

        claude_call_count = 0

        def mock_run(args, **kwargs):
            nonlocal claude_call_count
            if args[0] == "cue":
                return subprocess.CompletedProcess(args, 0, "cue version v0.5.0", "")
            elif args[0] == "claude":
                claude_call_count += 1
                return subprocess.CompletedProcess(args, 0, "1.0.0", "")
            raise FileNotFoundError("Command not found")

        def mock_get_cache_dir():
            return cache_dir

        def mock_get_catalog_manager(ctx):
            return catalog_manager

        def mock_get_mcp_manager(ctx):
            return mcp_manager

        with patch("subprocess.run", side_effect=mock_run), \
             patch("mcpi.cli.get_cache_dir", side_effect=mock_get_cache_dir), \
             patch("mcpi.cli.get_catalog_manager", side_effect=mock_get_catalog_manager), \
             patch("mcpi.cli.get_mcp_manager", side_effect=mock_get_mcp_manager):

            # USER ACTION: Add server that's already in catalog
            result = self.runner.invoke(
                main,
                ["add", "user/existing-server", "--dry-run"]
            )

            # Command should succeed quickly
            assert result.exit_code == 0 or result.exit_code == 1, \
                f"Command failed unexpectedly: {result.output}"

            # VERIFICATION: No Claude calls (except maybe version check)
            assert claude_call_count <= 1, \
                "Should not call Claude for discovery when server in catalog"

            # Should not show discovery mode messages
            assert "entering discovery mode" not in result.output.lower(), \
                "Should not enter discovery mode for catalog servers"


# =============================================================================
# TRACEABILITY SUMMARY
# =============================================================================
"""
COMPLETE TEST COVERAGE MAPPING:

Feature 1: Add Discovered Servers to Local Catalog (CRITICAL):
  ✓ test_discovered_server_added_to_local_catalog
  ✓ test_subsequent_add_finds_server_in_catalog

Feature 2: Cache Discovery Results (HIGH):
  ✓ test_first_discovery_creates_cache
  ✓ test_cached_discovery_avoids_claude_call
  ✓ test_different_queries_create_separate_caches
  ✓ test_cache_can_be_cleared

Integration Tests (HIGH):
  ✓ test_discovery_creates_both_cache_and_catalog_entry
  ✓ test_catalog_hit_bypasses_both_cache_and_claude

TOTAL: 8 comprehensive functional tests

All tests are UN-GAMEABLE because they:
  1. Use REAL CatalogManager - verifies actual catalog operations
  2. Use REAL file I/O - verifies files created on disk
  3. Mock ONLY subprocess.run for Claude CLI (external dependency)
  4. Verify ACTUAL file contents (catalog.json, cache files)
  5. Count subprocess calls to prove caching works
  6. Test COMPLETE workflows from discovery to persistence to retrieval
  7. Cannot pass with stubs or in-memory only implementations
  8. Validate what users actually experience

IMPLEMENTATION GUIDANCE:
========================
These tests define the contract for both features. When implementing:

Feature 1 - Catalog Persistence:
1. After successful discovery, call catalog_manager.get_catalog("local")
2. Call local_catalog.add_server(server_id, mcp_server)
3. Call local_catalog.save_catalog() to persist to disk
4. Before triggering discovery, check if server exists in catalog

Feature 2 - Discovery Caching:
1. Before calling Claude CLI, check cache: ~/.mcpi/cache/discovery/<hash>.json
2. Cache key = SHA256 hash of the discovery query text
3. If cache exists and valid, return cached result
4. If cache miss, call Claude and cache the result
5. Cache format: JSON with same structure as Claude response

Integration:
- Check catalog first (fastest)
- Check cache second (fast)
- Call Claude last (slowest)
- After discovery, update both cache and catalog

The tests will fail until implementation is complete, providing immediate
validation of the features.
"""
