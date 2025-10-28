"""Tests for registry categories command."""

import pytest
from click.testing import CliRunner
from mcpi.cli import main
from mcpi.registry.catalog import ServerCatalog, MCPServer
from pathlib import Path
import json
import tempfile


def test_categories_command_empty_categories(tmp_path):
    """Test categories command with servers that have no categories."""
    # Create a registry with servers but no categories
    registry_data = {
        "filesystem": {
            "description": "Access and manage local filesystem operations",
            "command": "npx",
            "args": ["-y", "@anthropic/mcp-server-filesystem"],
            "repository": "https://github.com/anthropics/mcp-filesystem-server",
            "categories": []
        },
        "fetch": {
            "description": "Make HTTP requests",
            "command": "npx",
            "args": ["-y", "@anthropic/mcp-server-fetch"],
            "categories": []
        }
    }
    
    registry_file = tmp_path / "registry.json"
    with open(registry_file, 'w') as f:
        json.dump(registry_data, f)
    
    # Create catalog with test registry
    catalog = ServerCatalog(registry_path=registry_file, validate_with_cue=False)
    
    runner = CliRunner()
    result = runner.invoke(main, ['registry', 'categories'], obj={'catalog': catalog})
    
    assert result.exit_code == 0
    assert "No categories found" in result.output


def test_categories_command_with_categories(tmp_path):
    """Test categories command with servers that have categories."""
    # Create a registry with categories
    registry_data = {
        "filesystem": {
            "description": "Access and manage local filesystem operations",
            "command": "npx",
            "args": ["-y", "@anthropic/mcp-server-filesystem"],
            "categories": ["filesystem", "storage"]
        },
        "fetch": {
            "description": "Make HTTP requests",
            "command": "npx",
            "args": ["-y", "@anthropic/mcp-server-fetch"],
            "categories": ["networking", "api"]
        },
        "sqlite": {
            "description": "SQLite database",
            "command": "npx",
            "args": ["-y", "@anthropic/mcp-server-sqlite"],
            "categories": ["database", "storage"]
        }
    }
    
    registry_file = tmp_path / "registry.json"
    with open(registry_file, 'w') as f:
        json.dump(registry_data, f)
    
    # Create catalog with test registry
    catalog = ServerCatalog(registry_path=registry_file, validate_with_cue=False)
    
    runner = CliRunner()
    result = runner.invoke(main, ['registry', 'categories'], obj={'catalog': catalog})
    
    assert result.exit_code == 0
    assert "MCP Server Categories" in result.output
    # Check that categories appear
    assert "filesystem" in result.output
    assert "storage" in result.output
    assert "networking" in result.output
    assert "api" in result.output
    assert "database" in result.output
    # Check counts (storage appears twice: filesystem + sqlite)
    assert "Total categories: 5" in result.output


def test_catalog_list_categories_method():
    """Test the ServerCatalog.list_categories() method directly."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        registry_file = Path(tmp_dir) / "registry.json"
        
        registry_data = {
            "server1": {
                "description": "Test server 1",
                "command": "npx",
                "categories": ["cat1", "cat2"]
            },
            "server2": {
                "description": "Test server 2",
                "command": "npx",
                "categories": ["cat1", "cat3"]
            },
            "server3": {
                "description": "Test server 3",
                "command": "npx",
                "categories": ["cat2"]
            }
        }
        
        with open(registry_file, 'w') as f:
            json.dump(registry_data, f)
        
        catalog = ServerCatalog(registry_path=registry_file, validate_with_cue=False)
        catalog.load_registry()
        
        categories = catalog.list_categories()
        
        # cat1 appears in 2 servers
        assert categories.get("cat1") == 2
        # cat2 appears in 2 servers
        assert categories.get("cat2") == 2
        # cat3 appears in 1 server
        assert categories.get("cat3") == 1
        # Total of 3 unique categories
        assert len(categories) == 3
