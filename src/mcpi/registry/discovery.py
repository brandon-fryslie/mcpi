"""MCP server discovery utilities."""

from typing import List, Optional, Dict, Any
from mcpi.registry.catalog import MCPServer, ServerCatalog


class ServerDiscovery:
    """Utilities for discovering and filtering MCP servers."""
    
    def __init__(self, catalog: Optional[ServerCatalog] = None):
        """Initialize discovery with a catalog.
        
        Args:
            catalog: Optional ServerCatalog instance
        """
        self.catalog = catalog or ServerCatalog()
        if not self.catalog._loaded:
            self.catalog.load_registry()
    
    def get_verified_servers(self) -> List[MCPServer]:
        """Get all verified servers.
        
        Returns:
            List of verified servers
        """
        return self.catalog.list_servers(verified_only=True)
    
    def get_servers_by_category(self, category: str) -> List[MCPServer]:
        """Get servers in a specific category.
        
        Args:
            category: Category name
            
        Returns:
            List of servers in the category
        """
        return self.catalog.list_servers(category=category)
    
    def get_core_servers(self) -> List[MCPServer]:
        """Get core/essential servers.
        
        Returns:
            List of core servers
        """
        return self.catalog.list_servers(category="core")
    
    def search(self, query: str) -> List[MCPServer]:
        """Search for servers.
        
        Args:
            query: Search query
            
        Returns:
            List of matching servers
        """
        return self.catalog.search_servers(query)
    
    def get_recommendations(self, use_case: Optional[str] = None) -> List[MCPServer]:
        """Get server recommendations based on use case.
        
        Args:
            use_case: Optional use case description
            
        Returns:
            List of recommended servers
        """
        if not use_case:
            # Return verified core servers as default recommendations
            return self.get_verified_servers()[:5]
        
        # Search for servers matching the use case
        results = self.search(use_case)
        
        # Prioritize verified servers
        verified = [s for s in results if s.verified]
        unverified = [s for s in results if not s.verified]
        
        return (verified + unverified)[:5]
    
    def get_categories(self) -> List[str]:
        """Get all available categories.
        
        Returns:
            List of category names
        """
        categories = set()
        for server in self.catalog.list_servers():
            categories.update(server.categories)
        return sorted(categories)
    
    def get_server_info(self, server_id: str) -> Optional[MCPServer]:
        """Get detailed information about a server.
        
        Args:
            server_id: Server ID
            
        Returns:
            Server information or None if not found
        """
        return self.catalog.get_server(server_id)
    
    def group_by_category(self) -> Dict[str, List[MCPServer]]:
        """Group all servers by their categories.
        
        Returns:
            Dictionary mapping category names to server lists
        """
        grouped: Dict[str, List[MCPServer]] = {}
        
        for server in self.catalog.list_servers():
            for category in server.categories:
                if category not in grouped:
                    grouped[category] = []
                grouped[category].append(server)
        
        # Sort servers within each category
        for category in grouped:
            grouped[category].sort(key=lambda x: (not x.verified, x.name))
        
        return grouped
    
    def get_installation_command(self, server_id: str, config: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """Get the installation command for a server.
        
        Args:
            server_id: Server ID
            config: Optional configuration parameters
            
        Returns:
            Installation command dict or None if server not found
        """
        server = self.catalog.get_server(server_id)
        if not server:
            return None
        
        try:
            return server.get_run_command(config)
        except ValueError as e:
            # Missing required config
            return None