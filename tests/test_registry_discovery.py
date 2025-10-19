"""Comprehensive tests for the registry discovery module."""

import platform
import pytest
from unittest.mock import patch, MagicMock

from mcpi.registry.discovery import ServerDiscovery
from mcpi.registry.catalog import MCPServer, Platform, ServerInstallation, ServerConfiguration, InstallationMethod


class TestServerDiscovery:
    """Tests for ServerDiscovery class."""
    
    def test_get_current_platform_linux(self):
        """Test platform detection for Linux."""
        with patch('platform.system', return_value='Linux'):
            platform_result = ServerDiscovery.get_current_platform()
            assert platform_result == Platform.LINUX
    
    def test_get_current_platform_darwin(self):
        """Test platform detection for macOS."""
        with patch('platform.system', return_value='Darwin'):
            platform_result = ServerDiscovery.get_current_platform()
            assert platform_result == Platform.DARWIN
    
    def test_get_current_platform_windows(self):
        """Test platform detection for Windows."""
        with patch('platform.system', return_value='Windows'):
            platform_result = ServerDiscovery.get_current_platform()
            assert platform_result == Platform.WINDOWS
    
    def test_get_current_platform_unknown_defaults_to_linux(self):
        """Test platform detection for unknown systems defaults to Linux."""
        with patch('platform.system', return_value='Unknown'):
            platform_result = ServerDiscovery.get_current_platform()
            assert platform_result == Platform.LINUX
    
    def test_get_current_platform_case_insensitive(self):
        """Test platform detection is case insensitive."""
        with patch('platform.system', return_value='LINUX'):
            platform_result = ServerDiscovery.get_current_platform()
            assert platform_result == Platform.LINUX


class TestServerCompatibility:
    """Tests for server platform compatibility."""
    
    def create_mock_server(self, platforms):
        """Create a mock server with specified platforms."""
        server = MagicMock(spec=MCPServer)
        server.platforms = platforms
        return server
    
    def test_is_platform_compatible_single_platform(self):
        """Test compatibility check with single platform."""
        server = self.create_mock_server([Platform.LINUX])
        
        with patch.object(ServerDiscovery, 'get_current_platform', return_value=Platform.LINUX):
            assert ServerDiscovery.is_platform_compatible(server) is True
        
        with patch.object(ServerDiscovery, 'get_current_platform', return_value=Platform.DARWIN):
            assert ServerDiscovery.is_platform_compatible(server) is False
    
    def test_is_platform_compatible_multiple_platforms(self):
        """Test compatibility check with multiple platforms."""
        server = self.create_mock_server([Platform.LINUX, Platform.DARWIN])
        
        with patch.object(ServerDiscovery, 'get_current_platform', return_value=Platform.LINUX):
            assert ServerDiscovery.is_platform_compatible(server) is True
        
        with patch.object(ServerDiscovery, 'get_current_platform', return_value=Platform.DARWIN):
            assert ServerDiscovery.is_platform_compatible(server) is True
        
        with patch.object(ServerDiscovery, 'get_current_platform', return_value=Platform.WINDOWS):
            assert ServerDiscovery.is_platform_compatible(server) is False
    
    def test_is_platform_compatible_empty_platforms(self):
        """Test compatibility check with empty platforms list."""
        server = self.create_mock_server([])
        
        with patch.object(ServerDiscovery, 'get_current_platform', return_value=Platform.LINUX):
            assert ServerDiscovery.is_platform_compatible(server) is False
    
    def test_filter_compatible_servers_mixed_compatibility(self):
        """Test filtering servers with mixed platform compatibility."""
        linux_server = self.create_mock_server([Platform.LINUX])
        darwin_server = self.create_mock_server([Platform.DARWIN])
        cross_platform_server = self.create_mock_server([Platform.LINUX, Platform.DARWIN, Platform.WINDOWS])
        windows_only_server = self.create_mock_server([Platform.WINDOWS])
        
        servers = [linux_server, darwin_server, cross_platform_server, windows_only_server]
        
        with patch.object(ServerDiscovery, 'get_current_platform', return_value=Platform.LINUX):
            compatible = ServerDiscovery.filter_compatible_servers(servers)
            assert len(compatible) == 2
            assert linux_server in compatible
            assert cross_platform_server in compatible
            assert darwin_server not in compatible
            assert windows_only_server not in compatible
    
    def test_filter_compatible_servers_empty_list(self):
        """Test filtering empty server list."""
        compatible = ServerDiscovery.filter_compatible_servers([])
        assert compatible == []
    
    def test_filter_compatible_servers_no_compatible(self):
        """Test filtering when no servers are compatible."""
        windows_server = self.create_mock_server([Platform.WINDOWS])
        servers = [windows_server]
        
        with patch.object(ServerDiscovery, 'get_current_platform', return_value=Platform.LINUX):
            compatible = ServerDiscovery.filter_compatible_servers(servers)
            assert compatible == []


class TestServerGrouping:
    """Tests for server grouping functionality."""
    
    def create_mock_server(self, name, categories):
        """Create a mock server with name and categories."""
        server = MagicMock(spec=MCPServer)
        server.name = name
        server.category = categories
        return server
    
    def test_group_servers_by_category_single_category(self):
        """Test grouping servers with single categories."""
        server1 = self.create_mock_server("Server1", ["filesystem"])
        server2 = self.create_mock_server("Server2", ["database"])
        server3 = self.create_mock_server("Server3", ["filesystem"])
        
        servers = [server1, server2, server3]
        grouped = ServerDiscovery.group_servers_by_category(servers)
        
        assert len(grouped) == 2
        assert "filesystem" in grouped
        assert "database" in grouped
        assert len(grouped["filesystem"]) == 2
        assert len(grouped["database"]) == 1
        assert server1 in grouped["filesystem"]
        assert server3 in grouped["filesystem"]
        assert server2 in grouped["database"]
    
    def test_group_servers_by_category_multiple_categories(self):
        """Test grouping servers with multiple categories."""
        server1 = self.create_mock_server("Server1", ["filesystem", "development"])
        server2 = self.create_mock_server("Server2", ["database", "development"])
        
        servers = [server1, server2]
        grouped = ServerDiscovery.group_servers_by_category(servers)
        
        assert len(grouped) == 3
        assert "filesystem" in grouped
        assert "database" in grouped
        assert "development" in grouped
        assert len(grouped["filesystem"]) == 1
        assert len(grouped["database"]) == 1
        assert len(grouped["development"]) == 2
        assert server1 in grouped["filesystem"]
        assert server1 in grouped["development"]
        assert server2 in grouped["database"]
        assert server2 in grouped["development"]
    
    def test_group_servers_by_category_sorting(self):
        """Test that servers within categories are sorted by name."""
        server1 = self.create_mock_server("ZServer", ["filesystem"])
        server2 = self.create_mock_server("AServer", ["filesystem"])
        server3 = self.create_mock_server("MServer", ["filesystem"])
        
        servers = [server1, server2, server3]
        grouped = ServerDiscovery.group_servers_by_category(servers)
        
        filesystem_servers = grouped["filesystem"]
        assert len(filesystem_servers) == 3
        assert filesystem_servers[0].name == "AServer"
        assert filesystem_servers[1].name == "MServer"
        assert filesystem_servers[2].name == "ZServer"
    
    def test_group_servers_by_category_empty_list(self):
        """Test grouping empty server list."""
        grouped = ServerDiscovery.group_servers_by_category([])
        assert grouped == {}
    
    def test_group_servers_by_category_empty_categories(self):
        """Test grouping servers with empty categories."""
        server = self.create_mock_server("Server1", [])
        servers = [server]
        grouped = ServerDiscovery.group_servers_by_category(servers)
        assert grouped == {}


class TestServerRecommendations:
    """Tests for server recommendation functionality."""
    
    def create_mock_server(self, name, categories, capabilities=None, description="", server_id=None, platforms=None):
        """Create a mock server with specified attributes."""
        server = MagicMock(spec=MCPServer)
        server.name = name
        server.category = categories
        server.capabilities = capabilities or []
        server.description = description
        server.id = server_id or f"{name.lower()}-server"
        server.platforms = platforms or [Platform.LINUX]
        return server
    
    @patch.object(ServerDiscovery, 'is_platform_compatible', return_value=True)
    def test_get_server_recommendations_no_use_case(self, mock_compatible):
        """Test recommendations with no specific use case."""
        # Create servers for essential categories
        fs_server1 = self.create_mock_server("FileSystem1", ["filesystem"])
        fs_server2 = self.create_mock_server("FileSystem2", ["filesystem"])
        fs_server3 = self.create_mock_server("FileSystem3", ["filesystem"])
        db_server1 = self.create_mock_server("Database1", ["database"])
        db_server2 = self.create_mock_server("Database2", ["database"])
        dev_server1 = self.create_mock_server("Development1", ["development"])
        other_server = self.create_mock_server("Other", ["other"])
        
        servers = [fs_server1, fs_server2, fs_server3, db_server1, db_server2, dev_server1, other_server]
        
        recommendations = ServerDiscovery.get_server_recommendations(servers)
        
        # Should get top 2 from each essential category, limited to 5 total
        assert len(recommendations) == 5
        # Should include filesystem, database, and development servers
        categories_found = set()
        for server in recommendations:
            categories_found.update(server.category)
        
        assert "filesystem" in categories_found
        assert "database" in categories_found
        assert "development" in categories_found
    
    @patch.object(ServerDiscovery, 'is_platform_compatible', return_value=True)
    def test_get_server_recommendations_category_match(self, mock_compatible):
        """Test recommendations with use case matching categories."""
        fs_server = self.create_mock_server("FileSystem", ["filesystem"], server_id="fs-server")
        db_server = self.create_mock_server("Database", ["database"], server_id="db-server")
        web_server = self.create_mock_server("Web", ["web"], server_id="web-server")
        
        servers = [fs_server, db_server, web_server]
        
        recommendations = ServerDiscovery.get_server_recommendations(servers, use_case="filesystem management")
        
        # Should prioritize filesystem server
        assert len(recommendations) > 0
        assert fs_server in recommendations
    
    @patch.object(ServerDiscovery, 'is_platform_compatible', return_value=True)
    def test_get_server_recommendations_capability_match(self, mock_compatible):
        """Test recommendations with use case matching capabilities."""
        # Use capability that contains the search term
        server1 = self.create_mock_server("Server1", ["other"], capabilities=["file", "writer"], server_id="server1")
        server2 = self.create_mock_server("Server2", ["other"], capabilities=["database_query"], server_id="server2")
        
        servers = [server1, server2]
        
        recommendations = ServerDiscovery.get_server_recommendations(servers, use_case="file")
        
        assert len(recommendations) > 0
        assert server1 in recommendations
    
    @patch.object(ServerDiscovery, 'is_platform_compatible', return_value=True)
    def test_get_server_recommendations_description_match(self, mock_compatible):
        """Test recommendations with use case matching descriptions."""
        server1 = self.create_mock_server("Server1", ["other"], description="Manage file operations", server_id="server1")
        server2 = self.create_mock_server("Server2", ["other"], description="Database management tool", server_id="server2")
        
        servers = [server1, server2]
        
        recommendations = ServerDiscovery.get_server_recommendations(servers, use_case="file operations")
        
        assert len(recommendations) > 0
        assert server1 in recommendations
    
    @patch.object(ServerDiscovery, 'is_platform_compatible', return_value=True)
    def test_get_server_recommendations_scoring_priority(self, mock_compatible):
        """Test recommendations scoring and priority."""
        # Category match (score 3)
        category_server = self.create_mock_server("Category", ["filesystem"], server_id="category-server")
        # Capability match (score 2)
        capability_server = self.create_mock_server("Capability", ["other"], capabilities=["filesystem"], server_id="capability-server")
        # Description match (score 1)
        description_server = self.create_mock_server("Description", ["other"], description="filesystem tools", server_id="description-server")
        
        servers = [description_server, capability_server, category_server]
        
        recommendations = ServerDiscovery.get_server_recommendations(servers, use_case="filesystem")
        
        # Category match should come first due to higher score
        assert len(recommendations) >= 1
        assert recommendations[0] == category_server
    
    @patch.object(ServerDiscovery, 'is_platform_compatible', return_value=True)
    def test_get_server_recommendations_deduplication(self, mock_compatible):
        """Test recommendations remove duplicates."""
        server = self.create_mock_server("Server", ["filesystem"], capabilities=["filesystem"], description="filesystem tool", server_id="server1")
        
        servers = [server]
        
        recommendations = ServerDiscovery.get_server_recommendations(servers, use_case="filesystem")
        
        # Should only appear once despite matching multiple criteria
        assert len(recommendations) == 1
        assert recommendations[0] == server
    
    @patch.object(ServerDiscovery, 'is_platform_compatible', return_value=False)
    def test_get_server_recommendations_platform_filtering(self, mock_compatible):
        """Test recommendations filter out incompatible platforms."""
        server = self.create_mock_server("Server", ["filesystem"])
        servers = [server]
        
        recommendations = ServerDiscovery.get_server_recommendations(servers, use_case="filesystem")
        
        # Should be empty since server is not platform compatible
        assert len(recommendations) == 0
    
    def test_get_server_recommendations_limit(self):
        """Test recommendations respect limit parameter."""
        servers = [
            self.create_mock_server(f"Server{i}", ["filesystem"], server_id=f"server{i}")
            for i in range(10)
        ]
        
        with patch.object(ServerDiscovery, 'is_platform_compatible', return_value=True):
            recommendations = ServerDiscovery.get_server_recommendations(servers, use_case="filesystem", limit=3)
        
        assert len(recommendations) == 3


class TestDependencyAnalysis:
    """Tests for server dependency analysis."""
    
    def create_mock_server(self, installation_method=InstallationMethod.NPM, system_deps=None, python_deps=None, required_params=None):
        """Create a mock server with specified dependencies."""
        server = MagicMock(spec=MCPServer)
        
        # Mock installation
        installation = MagicMock(spec=ServerInstallation)
        installation.method = installation_method
        installation.system_dependencies = system_deps or []
        installation.python_dependencies = python_deps or []
        server.installation = installation
        
        # Mock configuration
        configuration = MagicMock(spec=ServerConfiguration)
        configuration.required_params = required_params or []
        server.configuration = configuration
        
        return server
    
    def test_analyze_server_dependencies_basic_npm(self):
        """Test dependency analysis for basic NPM server."""
        server = self.create_mock_server(InstallationMethod.NPM)
        analysis = ServerDiscovery.analyze_server_dependencies(server)
        
        assert analysis["installation_method"] == InstallationMethod.NPM
        assert analysis["has_system_dependencies"] is False
        assert analysis["system_dependencies"] == []
        assert analysis["has_python_dependencies"] is False
        assert analysis["python_dependencies"] == []
        assert analysis["requires_configuration"] is False
        assert analysis["complexity"] == "low"
    
    def test_analyze_server_dependencies_with_system_deps(self):
        """Test dependency analysis with system dependencies."""
        server = self.create_mock_server(
            system_deps=["python3", "nodejs", "git"]
        )
        analysis = ServerDiscovery.analyze_server_dependencies(server)
        
        assert analysis["has_system_dependencies"] is True
        assert analysis["system_dependencies"] == ["python3", "nodejs", "git"]
        assert analysis["complexity"] == "medium"  # 3 system deps
    
    def test_analyze_server_dependencies_with_python_deps(self):
        """Test dependency analysis with Python dependencies."""
        server = self.create_mock_server(
            python_deps=["requests", "sqlalchemy"]
        )
        analysis = ServerDiscovery.analyze_server_dependencies(server)
        
        assert analysis["has_python_dependencies"] is True
        assert analysis["python_dependencies"] == ["requests", "sqlalchemy"]
        assert analysis["complexity"] == "medium"  # 2 python deps (1-3 = medium)
    
    def test_analyze_server_dependencies_with_config(self):
        """Test dependency analysis with required configuration."""
        server = self.create_mock_server(
            required_params=["database_url", "api_key"]
        )
        analysis = ServerDiscovery.analyze_server_dependencies(server)
        
        assert analysis["requires_configuration"] is True
        assert analysis["complexity"] == "medium"  # 2 config params (1-3 = medium)
    
    def test_analyze_server_dependencies_complex(self):
        """Test dependency analysis for complex server."""
        server = self.create_mock_server(
            system_deps=["python3", "nodejs"],
            python_deps=["requests", "sqlalchemy", "pandas"],
            required_params=["database_url", "api_key", "secret_key"]
        )
        analysis = ServerDiscovery.analyze_server_dependencies(server)
        
        assert analysis["has_system_dependencies"] is True
        assert analysis["has_python_dependencies"] is True
        assert analysis["requires_configuration"] is True
        # 2 system + 3 python + 3 config = 8 total (> 3, so high complexity)
        assert analysis["complexity"] == "high"
    
    def test_analyze_server_dependencies_medium_complexity(self):
        """Test dependency analysis for medium complexity server."""
        server = self.create_mock_server(
            system_deps=["python3"],
            python_deps=["requests"],
            required_params=["api_key"]
        )
        analysis = ServerDiscovery.analyze_server_dependencies(server)
        
        # 1 system + 1 python + 1 config = 3 total (== 3, so medium complexity)
        assert analysis["complexity"] == "medium"
    
    def test_analyze_server_dependencies_pip_method(self):
        """Test dependency analysis for PIP installation method."""
        server = self.create_mock_server(InstallationMethod.PIP)
        analysis = ServerDiscovery.analyze_server_dependencies(server)
        
        assert analysis["installation_method"] == InstallationMethod.PIP
    
    def test_analyze_server_dependencies_git_method(self):
        """Test dependency analysis for Git installation method."""
        server = self.create_mock_server(InstallationMethod.GIT)
        analysis = ServerDiscovery.analyze_server_dependencies(server)
        
        assert analysis["installation_method"] == InstallationMethod.GIT