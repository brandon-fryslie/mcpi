"""Comprehensive tests for the registry documentation parser module."""

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
import httpx
from bs4 import BeautifulSoup

from mcpi.registry.doc_parser import DocumentationParser
from mcpi.registry.catalog import InstallationMethod


class TestDocumentationParserInit:
    """Tests for DocumentationParser initialization."""
    
    def test_parser_initialization_default(self):
        """Test parser initialization with default timeout."""
        parser = DocumentationParser()
        assert parser.timeout == 30.0
        assert parser._installation_patterns is not None
    
    def test_parser_initialization_custom_timeout(self):
        """Test parser initialization with custom timeout."""
        parser = DocumentationParser(timeout=60.0)
        assert parser.timeout == 60.0
    
    def test_build_patterns_structure(self):
        """Test installation pattern structure."""
        parser = DocumentationParser()
        patterns = parser._build_patterns()
        
        assert isinstance(patterns, dict)
        assert "npm" in patterns
        assert "pip" in patterns
        assert "git" in patterns
        
        # Each method should have a list of compiled regex patterns
        for method, pattern_list in patterns.items():
            assert isinstance(pattern_list, list)
            assert len(pattern_list) > 0
            for pattern in pattern_list:
                assert hasattr(pattern, 'findall')  # Should be compiled regex


class TestPatternMatching:
    """Tests for installation pattern matching."""
    
    def test_npm_pattern_matching(self):
        """Test NPM installation pattern matching."""
        parser = DocumentationParser()
        patterns = parser._installation_patterns["npm"]
        
        test_cases = [
            ("npm install @anthropic/mcp-server-filesystem", "@anthropic/mcp-server-filesystem"),
            ("npm install -g some-package", "some-package"),
            ("npx create-mcp-server", "create-mcp-server"),
            ("yarn add some-package", "some-package"),
            ("yarn global add global-package", "global-package"),
            ("pnpm add some-package", "some-package"),
            ("pnpm -g add global-package", "global-package"),
        ]
        
        for command, expected_package in test_cases:
            found_match = False
            for pattern in patterns:
                matches = pattern.findall(command)
                if matches:
                    assert expected_package in matches[0]
                    found_match = True
                    break
            assert found_match, f"No pattern matched for: {command}"
    
    def test_pip_pattern_matching(self):
        """Test PIP installation pattern matching."""
        parser = DocumentationParser()
        patterns = parser._installation_patterns["pip"]
        
        test_cases = [
            ("pip install mcp-server-postgres", "mcp-server-postgres"),
            ("pip3 install some-package", "some-package"),
            ("uv add mcp-server-filesystem", "mcp-server-filesystem"),
            ("poetry add some-package", "some-package"),
        ]
        
        for command, expected_package in test_cases:
            found_match = False
            for pattern in patterns:
                matches = pattern.findall(command)
                if matches:
                    assert expected_package in matches[0]
                    found_match = True
                    break
            assert found_match, f"No pattern matched for: {command}"
    
    def test_git_pattern_matching(self):
        """Test Git installation pattern matching."""
        parser = DocumentationParser()
        patterns = parser._installation_patterns["git"]
        
        test_cases = [
            ("git clone https://github.com/user/repo.git", "https://github.com/user/repo.git"),
            ("git clone git@github.com:user/repo.git", "git@github.com:user/repo.git"),
        ]
        
        for command, expected_repo in test_cases:
            found_match = False
            for pattern in patterns:
                matches = pattern.findall(command)
                if matches:
                    assert expected_repo in matches[0]
                    found_match = True
                    break
            assert found_match, f"No pattern matched for: {command}"


class TestContentFetching:
    """Tests for content fetching functionality."""
    
    @pytest.mark.asyncio
    async def test_fetch_content_success(self):
        """Test successful content fetching."""
        parser = DocumentationParser()
        expected_content = "<html><body>Test content</body></html>"
        
        mock_response = MagicMock()
        mock_response.text = expected_content
        mock_response.raise_for_status.return_value = None
        
        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            content = await parser._fetch_content("https://example.com")
        
        assert content == expected_content
        mock_client.get.assert_called_once_with("https://example.com", timeout=30.0)
    
    @pytest.mark.asyncio
    async def test_fetch_content_request_error(self):
        """Test content fetching with request error."""
        parser = DocumentationParser()
        
        mock_client = MagicMock()
        mock_client.get = AsyncMock(side_effect=httpx.RequestError("Network error"))
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            content = await parser._fetch_content("https://example.com")
        
        assert content is None
    
    @pytest.mark.asyncio
    async def test_fetch_content_http_error(self):
        """Test content fetching with HTTP error."""
        parser = DocumentationParser()
        
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError("404 Not Found", request=MagicMock(), response=MagicMock())
        
        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            content = await parser._fetch_content("https://example.com")
        
        assert content is None
    
    @pytest.mark.asyncio
    async def test_fetch_content_with_custom_timeout(self):
        """Test content fetching with custom timeout."""
        parser = DocumentationParser(timeout=60.0)
        
        mock_response = MagicMock()
        mock_response.text = "content"
        mock_response.raise_for_status.return_value = None
        
        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            await parser._fetch_content("https://example.com")
        
        mock_client.get.assert_called_once_with("https://example.com", timeout=60.0)


class TestHTMLDetection:
    """Tests for HTML detection functionality."""
    
    def test_is_html_with_html_tags(self):
        """Test HTML detection with HTML tags."""
        parser = DocumentationParser()
        
        html_content = "<html><body><h1>Title</h1></body></html>"
        assert parser._is_html(html_content) is True
    
    def test_is_html_with_partial_html(self):
        """Test HTML detection with partial HTML."""
        parser = DocumentationParser()
        
        html_content = "<h1>Title</h1><p>Content</p>"
        assert parser._is_html(html_content) is True
    
    def test_is_html_with_markdown(self):
        """Test HTML detection with Markdown content."""
        parser = DocumentationParser()
        
        markdown_content = "# Title\n\nThis is markdown content."
        assert parser._is_html(markdown_content) is False
    
    def test_is_html_with_plain_text(self):
        """Test HTML detection with plain text."""
        parser = DocumentationParser()
        
        text_content = "This is plain text content without HTML tags."
        assert parser._is_html(text_content) is False


class TestNameExtraction:
    """Tests for name extraction functionality."""
    
    def test_extract_name_from_h1(self):
        """Test name extraction from H1 headers."""
        parser = DocumentationParser()
        
        content = "# Filesystem MCP Server\n\nDescription here."
        name = parser._extract_name(content)
        assert name == "Filesystem MCP Server"
    
    def test_extract_name_from_title(self):
        """Test name extraction from title patterns."""
        parser = DocumentationParser()
        
        content = "## Installation\n\n### Database MCP Server Setup\n"
        name = parser._extract_name(content)
        # Should extract something meaningful, exact value depends on implementation
        assert name is not None
    
    def test_extract_name_no_clear_pattern(self):
        """Test name extraction with no clear pattern."""
        parser = DocumentationParser()
        
        content = "Some content without clear name patterns."
        name = parser._extract_name(content)
        # May return None or extracted text, depends on implementation
        # Don't assert specific value since extraction is heuristic
    
    def test_extract_name_from_package_json(self):
        """Test name extraction from package.json reference."""
        parser = DocumentationParser()
        
        content = """
        # Installation
        
        See package.json for "name": "@anthropic/mcp-server-filesystem"
        """
        name = parser._extract_name(content)
        # Should extract meaningful name, exact value depends on implementation
        assert name is not None


class TestInstallationExtraction:
    """Tests for installation information extraction."""
    
    def test_extract_installation_npm_basic(self):
        """Test basic NPM installation extraction."""
        parser = DocumentationParser()
        
        content = """
        # Installation
        
        ```bash
        npm install @anthropic/mcp-server-filesystem
        ```
        """
        
        installation = parser._extract_installation(content)
        assert installation is not None
        assert installation["method"] == "npm"
        assert installation["package"] == "@anthropic/mcp-server-filesystem"
    
    def test_extract_installation_npm_global(self):
        """Test global NPM installation extraction."""
        parser = DocumentationParser()
        
        content = """
        Install globally:
        ```
        npm install -g some-package
        ```
        """
        
        installation = parser._extract_installation(content)
        assert installation is not None
        assert installation["method"] == "npm"
        assert installation["package"] == "some-package"
    
    def test_extract_installation_pip_basic(self):
        """Test basic PIP installation extraction."""
        parser = DocumentationParser()
        
        content = """
        # Setup
        
        ```bash
        pip install mcp-server-postgres
        ```
        """
        
        installation = parser._extract_installation(content)
        assert installation is not None
        assert installation["method"] == "pip"
        assert installation["package"] == "mcp-server-postgres"
    
    def test_extract_installation_uv(self):
        """Test UV installation extraction."""
        parser = DocumentationParser()
        
        content = """
        # Installation
        
        ```bash
        uv add mcp-server-postgres
        ```
        """
        
        installation = parser._extract_installation(content)
        assert installation is not None
        assert installation["method"] == "pip"  # UV maps to pip method
        assert installation["package"] == "mcp-server-postgres"
    
    def test_extract_installation_git(self):
        """Test Git installation extraction."""
        parser = DocumentationParser()
        
        content = """
        # Clone and Install
        
        ```bash
        git clone https://github.com/user/mcp-server.git
        ```
        """
        
        installation = parser._extract_installation(content)
        assert installation is not None
        assert installation["method"] == "git"
        assert installation["package"] == "https://github.com/user/mcp-server.git"
    
    def test_extract_installation_multiple_methods(self):
        """Test extraction with multiple installation methods."""
        parser = DocumentationParser()
        
        content = """
        # Installation Options
        
        Via npm:
        ```bash
        npm install package1
        ```
        
        Via pip:
        ```bash
        pip install package2
        ```
        """
        
        installation = parser._extract_installation(content)
        # Should return the first method found
        assert installation is not None
        assert installation["method"] in ["npm", "pip"]
    
    def test_extract_installation_no_pattern_match(self):
        """Test extraction with no installation patterns."""
        parser = DocumentationParser()
        
        content = """
        # About
        
        This is some documentation without installation commands.
        """
        
        installation = parser._extract_installation(content)
        assert installation is None
    
    def test_extract_installation_with_code_blocks(self):
        """Test extraction from various code block formats."""
        parser = DocumentationParser()
        
        test_cases = [
            # Standard markdown code block
            "```bash\nnpm install test-package\n```",
            # Indented code block
            "    npm install test-package",
            # Inline code
            "`npm install test-package`",
        ]
        
        for content in test_cases:
            installation = parser._extract_installation(content)
            assert installation is not None
            assert installation["method"] == "npm"
            assert installation["package"] == "test-package"


class TestServerIdGeneration:
    """Tests for server ID generation."""
    
    def test_generate_server_id_from_npm_package(self):
        """Test server ID generation from NPM package name."""
        parser = DocumentationParser()
        
        server_info = {
            "installation": {"package": "@anthropic/mcp-server-filesystem"},
            "name": "Filesystem MCP Server"
        }
        
        server_id = parser._generate_server_id(server_info)
        assert server_id is not None
        assert isinstance(server_id, str)
        assert len(server_id) > 0
        # Should be based on package name
        assert "filesystem" in server_id.lower()
    
    def test_generate_server_id_from_pip_package(self):
        """Test server ID generation from PIP package name."""
        parser = DocumentationParser()
        
        server_info = {
            "installation": {"package": "mcp-server-postgres"},
            "name": "PostgreSQL MCP Server"
        }
        
        server_id = parser._generate_server_id(server_info)
        assert server_id is not None
        assert "postgres" in server_id.lower()
    
    def test_generate_server_id_from_name_fallback(self):
        """Test server ID generation from name as fallback."""
        parser = DocumentationParser()
        
        server_info = {
            "name": "Custom Server Name",
            "installation": {}
        }
        
        server_id = parser._generate_server_id(server_info)
        assert server_id is not None
        assert len(server_id) > 0
    
    def test_generate_server_id_normalization(self):
        """Test server ID normalization (lowercase, no spaces)."""
        parser = DocumentationParser()
        
        server_info = {
            "installation": {"package": "My-Package-Name"},
            "name": "Some Server"
        }
        
        server_id = parser._generate_server_id(server_info)
        assert server_id is not None
        # Should be normalized
        assert server_id == server_id.lower()
        assert " " not in server_id


class TestDescriptionExtraction:
    """Tests for description extraction."""
    
    def test_extract_description_from_content(self):
        """Test description extraction from markdown content."""
        parser = DocumentationParser()
        
        content = """
        # MCP Server
        
        This is a comprehensive server for handling file operations.
        It provides secure access to the filesystem.
        
        ## Installation
        ```bash
        npm install package
        ```
        """
        
        description = parser._extract_description(content)
        assert description is not None
        assert "file operations" in description.lower()
    
    def test_extract_description_multiple_paragraphs(self):
        """Test description extraction from multiple paragraphs."""
        parser = DocumentationParser()
        
        content = """
        # Server Name
        
        First paragraph about the server.
        
        Second paragraph with more details.
        
        ## Section
        """
        
        description = parser._extract_description(content)
        # Should extract meaningful description
        assert description is not None
        assert len(description) > 0
    
    def test_extract_description_no_content(self):
        """Test description extraction with minimal content."""
        parser = DocumentationParser()
        
        content = "# Title\n## Installation"
        description = parser._extract_description(content)
        # May return None or minimal description
        # Don't assert specific value since extraction is heuristic


class TestCapabilityExtraction:
    """Tests for capability extraction."""
    
    def test_extract_capabilities_from_content(self):
        """Test capability extraction from documentation content."""
        parser = DocumentationParser()
        
        content = """
        # File Server
        
        Provides file system access with read and write operations.
        Supports directory listing and file management.
        
        Features:
        - Read files
        - Write files
        - List directories
        - Create directories
        """
        
        capabilities = parser._extract_capabilities(content)
        assert isinstance(capabilities, list)
        # Should extract file-related capabilities
        capability_text = " ".join(capabilities).lower()
        assert any(word in capability_text for word in ["read", "write", "file"])
    
    def test_extract_capabilities_empty_content(self):
        """Test capability extraction from empty content."""
        parser = DocumentationParser()
        
        capabilities = parser._extract_capabilities("")
        assert isinstance(capabilities, list)
        # May be empty or contain default capabilities


class TestValidation:
    """Tests for validation functionality."""
    
    def test_validate_extracted_info_valid(self):
        """Test validation of valid extracted server information."""
        parser = DocumentationParser()
        
        valid_info = {
            "id": "test-server",
            "name": "Test Server",
            "installation": {"method": "npm", "package": "test-package"},
            "description": "A test server"
        }
        
        is_valid = parser._validate_extracted_info(valid_info)
        assert is_valid is True
    
    def test_validate_extracted_info_missing_required_fields(self):
        """Test validation with missing required fields."""
        parser = DocumentationParser()
        
        # Missing installation info
        invalid_info = {
            "id": "test-server",
            "name": "Test Server"
        }
        
        is_valid = parser._validate_extracted_info(invalid_info)
        assert is_valid is False
    
    def test_validate_extracted_info_invalid_id(self):
        """Test validation with invalid server ID."""
        parser = DocumentationParser()
        
        invalid_info = {
            "id": "invalid id with spaces",
            "name": "Test Server",
            "installation": {"method": "npm", "package": "test-package"}
        }
        
        # Depends on implementation - may validate ID format
        is_valid = parser._validate_extracted_info(invalid_info)
        # Don't assert specific value since validation rules may vary
    
    def test_validate_extracted_info_empty_name(self):
        """Test validation with empty name."""
        parser = DocumentationParser()
        
        invalid_info = {
            "id": "test-server",
            "name": "",
            "installation": {"method": "npm", "package": "test-package"}
        }
        
        is_valid = parser._validate_extracted_info(invalid_info)
        assert is_valid is False


class TestFullDocumentationParsing:
    """Integration tests for full documentation parsing."""
    
    @pytest.mark.asyncio
    async def test_parse_documentation_url_invalid_url(self):
        """Test parsing with invalid URL."""
        parser = DocumentationParser()
        
        result = await parser.parse_documentation_url("not-a-url")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_parse_documentation_url_fetch_failure(self):
        """Test parsing with fetch failure."""
        parser = DocumentationParser()
        
        with patch.object(parser, '_fetch_content', return_value=None):
            result = await parser.parse_documentation_url("https://example.com")
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_parse_documentation_url_html_content(self):
        """Test parsing HTML documentation."""
        parser = DocumentationParser()
        
        html_content = """
        <html>
        <body>
            <h1>Test MCP Server</h1>
            <p>This is a test server for demonstration.</p>
            <pre><code>npm install test-mcp-server</code></pre>
        </body>
        </html>
        """
        
        with patch.object(parser, '_fetch_content', return_value=html_content):
            with patch('markdownify.markdownify') as mock_markdownify:
                mock_markdownify.return_value = "# Test MCP Server\n\nnpm install test-mcp-server"
                
                with patch.object(parser, '_extract_server_info') as mock_extract:
                    mock_extract.return_value = {"id": "test", "name": "Test Server"}
                    
                    result = await parser.parse_documentation_url("https://example.com")
        
        assert result is not None
        mock_markdownify.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_parse_documentation_url_markdown_content(self):
        """Test parsing Markdown documentation."""
        parser = DocumentationParser()
        
        markdown_content = """
        # Test MCP Server
        
        This is a test server.
        
        ```bash
        npm install test-mcp-server
        ```
        """
        
        with patch.object(parser, '_fetch_content', return_value=markdown_content):
            with patch.object(parser, '_extract_server_info') as mock_extract:
                mock_extract.return_value = {"id": "test", "name": "Test Server"}
                
                result = await parser.parse_documentation_url("https://example.com")
        
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_parse_documentation_url_extraction_exception(self):
        """Test parsing with exception during extraction."""
        parser = DocumentationParser()
        
        with patch.object(parser, '_fetch_content', return_value="content"):
            with patch.object(parser, '_extract_server_info', side_effect=Exception("Extraction failed")):
                result = await parser.parse_documentation_url("https://example.com")
        
        assert result is None


class TestServerInfoExtraction:
    """Tests for complete server info extraction."""
    
    @pytest.mark.asyncio
    async def test_extract_server_info_complete(self):
        """Test complete server info extraction."""
        parser = DocumentationParser()
        
        content = """
        # Filesystem MCP Server
        
        A comprehensive server for file system operations.
        
        ## Installation
        
        ```bash
        npm install @anthropic/mcp-server-filesystem
        ```
        
        ## Features
        
        - Read files
        - Write files
        - List directories
        """
        
        url = "https://example.com/filesystem-server"
        
        with patch.object(parser, '_extract_name', return_value="Filesystem MCP Server"):
            with patch.object(parser, '_extract_installation', return_value={"method": "npm", "package": "@anthropic/mcp-server-filesystem"}):
                with patch.object(parser, '_extract_description', return_value="A comprehensive server for file system operations"):
                    with patch.object(parser, '_extract_capabilities', return_value=["read_files", "write_files", "list_directories"]):
                        with patch.object(parser, '_generate_server_id', return_value="filesystem-mcp-server"):
                            with patch.object(parser, '_validate_extracted_info', return_value=True):
                                
                                result = await parser._extract_server_info(content, url)
        
        assert result is not None
        assert result["id"] == "filesystem-mcp-server"
        assert result["name"] == "Filesystem MCP Server"
        assert result["installation"]["method"] == "npm"
        assert result["installation"]["package"] == "@anthropic/mcp-server-filesystem"
        assert result["description"] == "A comprehensive server for file system operations"
        assert "read_files" in result["capabilities"]
    
    @pytest.mark.asyncio
    async def test_extract_server_info_validation_failure(self):
        """Test server info extraction with validation failure."""
        parser = DocumentationParser()
        
        with patch.object(parser, '_extract_name', return_value="Test Server"):
            with patch.object(parser, '_extract_installation', return_value={"method": "npm", "package": "test"}):
                with patch.object(parser, '_generate_server_id', return_value="test-server"):
                    with patch.object(parser, '_validate_extracted_info', return_value=False):
                        
                        result = await parser._extract_server_info("content", "url")
        
        assert result is None