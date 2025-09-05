"""MCP server discovery utilities."""

import platform
from typing import List, Optional, Dict, Any
from mcpi.registry.catalog import MCPServer, Platform


class ServerDiscovery:
    """Utilities for discovering and filtering MCP servers."""
    
    @staticmethod
    def get_current_platform() -> Platform:
        """Get the current platform.
        
        Returns:
            Platform enum value for current system
        """
        system = platform.system().lower()
        
        if system == "linux":
            return Platform.LINUX
        elif system == "darwin":
            return Platform.DARWIN
        elif system == "windows":
            return Platform.WINDOWS
        else:
            # Default to Linux for unknown platforms
            return Platform.LINUX
    
    @staticmethod
    def is_platform_compatible(server: MCPServer) -> bool:
        """Check if server is compatible with current platform.
        
        Args:
            server: MCP server to check
            
        Returns:
            True if compatible, False otherwise
        """
        current_platform = ServerDiscovery.get_current_platform()
        return current_platform in server.platforms
    
    @staticmethod
    def filter_compatible_servers(servers: List[MCPServer]) -> List[MCPServer]:
        """Filter servers compatible with current platform.
        
        Args:
            servers: List of servers to filter
            
        Returns:
            List of compatible servers
        """
        return [s for s in servers if ServerDiscovery.is_platform_compatible(s)]
    
    @staticmethod
    def group_servers_by_category(servers: List[MCPServer]) -> Dict[str, List[MCPServer]]:
        """Group servers by their categories.
        
        Args:
            servers: List of servers to group
            
        Returns:
            Dictionary mapping category names to server lists
        """
        categories: Dict[str, List[MCPServer]] = {}
        
        for server in servers:
            for category in server.category:
                if category not in categories:
                    categories[category] = []
                categories[category].append(server)
        
        # Sort servers within each category
        for category in categories:
            categories[category].sort(key=lambda x: x.name)
        
        return categories
    
    @staticmethod
    def get_server_recommendations(
        servers: List[MCPServer], 
        use_case: Optional[str] = None,
        limit: int = 5
    ) -> List[MCPServer]:
        """Get server recommendations based on use case.
        
        Args:
            servers: Available servers to choose from
            use_case: Use case description for recommendations
            limit: Maximum number of recommendations
            
        Returns:
            List of recommended servers
        """
        if not use_case:
            # Return most popular/essential servers
            essential_categories = ["filesystem", "database", "development"]
            recommendations = []
            
            for category in essential_categories:
                category_servers = [
                    s for s in servers 
                    if category in s.category and ServerDiscovery.is_platform_compatible(s)
                ]
                if category_servers:
                    recommendations.extend(category_servers[:2])  # Top 2 from each category
                    
            return recommendations[:limit]
        
        # Simple keyword-based recommendations
        use_case_lower = use_case.lower()
        recommendations = []
        
        # Direct category matches
        for server in servers:
            if any(cat.lower() in use_case_lower for cat in server.category):
                if ServerDiscovery.is_platform_compatible(server):
                    recommendations.append((server, 3))  # High score
        
        # Capability matches
        for server in servers:
            if any(cap.lower() in use_case_lower for cap in server.capabilities):
                if ServerDiscovery.is_platform_compatible(server):
                    recommendations.append((server, 2))  # Medium score
        
        # Description matches
        for server in servers:
            if any(word in server.description.lower() for word in use_case_lower.split()):
                if ServerDiscovery.is_platform_compatible(server):
                    recommendations.append((server, 1))  # Low score
        
        # Remove duplicates and sort by score
        seen_ids = set()
        unique_recommendations = []
        for server, score in recommendations:
            if server.id not in seen_ids:
                unique_recommendations.append((server, score))
                seen_ids.add(server.id)
        
        unique_recommendations.sort(key=lambda x: (-x[1], x[0].name))
        return [rec[0] for rec in unique_recommendations[:limit]]
    
    @staticmethod
    def analyze_server_dependencies(server: MCPServer) -> Dict[str, Any]:
        """Analyze server dependencies and requirements.
        
        Args:
            server: Server to analyze
            
        Returns:
            Dictionary with dependency analysis
        """
        analysis = {
            "installation_method": server.installation.method,
            "has_system_dependencies": bool(server.installation.system_dependencies),
            "system_dependencies": server.installation.system_dependencies,
            "has_python_dependencies": bool(server.installation.python_dependencies),
            "python_dependencies": server.installation.python_dependencies,
            "requires_configuration": bool(server.configuration.required_params),
            "complexity": "low"
        }
        
        # Determine complexity
        complexity_score = 0
        if analysis["has_system_dependencies"]:
            complexity_score += len(server.installation.system_dependencies)
        if analysis["has_python_dependencies"]:
            complexity_score += len(server.installation.python_dependencies)
        if analysis["requires_configuration"]:
            complexity_score += len(server.configuration.required_params)
        
        if complexity_score == 0:
            analysis["complexity"] = "low"
        elif complexity_score <= 3:
            analysis["complexity"] = "medium"
        else:
            analysis["complexity"] = "high"
        
        return analysis