"""Tests for HttpServer model with headers support."""

import os
from unittest.mock import patch

import pytest

from mcpi.registry.catalog import HttpServer, parse_mcp_server


class TestHttpServerModel:
    """Tests for HttpServer Pydantic model."""

    def test_basic_http_server(self):
        """Test creating basic HTTP server without headers."""
        server = HttpServer(
            description="Test API server",
            url="https://api.example.com/mcp",
        )
        assert server.type == "http"
        assert server.url == "https://api.example.com/mcp"
        assert server.headers == {}

    def test_http_server_with_headers(self):
        """Test creating HTTP server with headers."""
        server = HttpServer(
            description="Test API server",
            url="https://api.example.com/mcp",
            headers={
                "Authorization": "Bearer ${API_KEY}",
                "X-Custom": "value",
            },
        )
        assert server.headers == {
            "Authorization": "Bearer ${API_KEY}",
            "X-Custom": "value",
        }

    def test_parse_http_server_from_dict(self):
        """Test parsing HTTP server from dictionary."""
        data = {
            "type": "http",
            "description": "Remote API",
            "url": "https://api.example.com",
            "headers": {"Authorization": "Bearer token"},
        }
        server = parse_mcp_server(data)
        assert isinstance(server, HttpServer)
        assert server.headers == {"Authorization": "Bearer token"}

    def test_parse_http_server_without_headers(self):
        """Test parsing HTTP server without headers defaults to empty dict."""
        data = {
            "type": "http",
            "description": "Remote API",
            "url": "https://api.example.com",
        }
        server = parse_mcp_server(data)
        assert isinstance(server, HttpServer)
        assert server.headers == {}

    def test_url_validation_requires_http(self):
        """Test that URL must start with http:// or https://."""
        with pytest.raises(ValueError, match="must start with http"):
            HttpServer(
                description="Bad URL",
                url="ftp://example.com",
            )

    def test_url_validation_not_empty(self):
        """Test that URL cannot be empty."""
        with pytest.raises(ValueError, match="cannot be empty"):
            HttpServer(
                description="Empty URL",
                url="",
            )


class TestHttpServerGetRunCommand:
    """Tests for HttpServer.get_run_command() method."""

    def test_get_run_command_basic(self):
        """Test get_run_command without headers."""
        server = HttpServer(
            description="Test server",
            url="https://api.example.com/mcp",
        )
        config = server.get_run_command()
        assert config == {
            "type": "http",
            "url": "https://api.example.com/mcp",
        }

    def test_get_run_command_with_headers(self):
        """Test get_run_command includes headers."""
        server = HttpServer(
            description="Test server",
            url="https://api.example.com/mcp",
            headers={"Authorization": "Bearer ${API_KEY}"},
        )
        config = server.get_run_command()
        assert config == {
            "type": "http",
            "url": "https://api.example.com/mcp",
            "headers": {"Authorization": "Bearer ${API_KEY}"},
        }

    def test_get_run_command_resolve_env_false(self):
        """Test that resolve_env=False preserves variable patterns."""
        server = HttpServer(
            description="Test server",
            url="https://api.example.com/mcp",
            headers={"Authorization": "Bearer ${API_KEY}"},
        )
        with patch.dict(os.environ, {"API_KEY": "secret123"}):
            config = server.get_run_command(resolve_env=False)
            assert config["headers"]["Authorization"] == "Bearer ${API_KEY}"

    def test_get_run_command_resolve_env_true(self):
        """Test that resolve_env=True substitutes variable patterns."""
        server = HttpServer(
            description="Test server",
            url="https://api.example.com/mcp",
            headers={"Authorization": "Bearer ${API_KEY}"},
        )
        with patch.dict(os.environ, {"API_KEY": "secret123"}):
            config = server.get_run_command(resolve_env=True)
            assert config["headers"]["Authorization"] == "Bearer secret123"

    def test_get_run_command_resolve_missing_env(self):
        """Test that missing env vars become empty strings."""
        server = HttpServer(
            description="Test server",
            url="https://api.example.com/mcp",
            headers={"Authorization": "Bearer ${MISSING_VAR}"},
        )
        with patch.dict(os.environ, {}, clear=True):
            config = server.get_run_command(resolve_env=True)
            assert config["headers"]["Authorization"] == "Bearer "

    def test_get_run_command_headers_copy(self):
        """Test that returned headers are a copy, not the original."""
        server = HttpServer(
            description="Test server",
            url="https://api.example.com/mcp",
            headers={"Auth": "value"},
        )
        config = server.get_run_command()
        config["headers"]["Auth"] = "modified"
        # Original should be unchanged
        assert server.headers["Auth"] == "value"


class TestHttpServerSerialization:
    """Tests for HttpServer serialization."""

    def test_model_dump_includes_headers(self):
        """Test that model_dump includes headers."""
        server = HttpServer(
            description="Test server",
            url="https://api.example.com",
            headers={"Auth": "Bearer token"},
        )
        data = server.model_dump()
        assert data["headers"] == {"Auth": "Bearer token"}

    def test_model_dump_empty_headers(self):
        """Test that model_dump includes empty headers dict."""
        server = HttpServer(
            description="Test server",
            url="https://api.example.com",
        )
        data = server.model_dump()
        assert data["headers"] == {}
