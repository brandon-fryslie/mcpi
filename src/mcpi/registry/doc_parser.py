"""Documentation parser for extracting MCP server installation information."""

import re
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urlparse
import httpx
from bs4 import BeautifulSoup
from markdownify import markdownify

from mcpi.registry.catalog import MCPServer, InstallationMethod
from mcpi.utils.validation import validate_url, validate_server_id, validate_package_name


class DocumentationParser:
    """Parser for extracting MCP server information from documentation URLs."""
    
    def __init__(self, timeout: float = 30.0):
        """Initialize documentation parser.
        
        Args:
            timeout: HTTP request timeout in seconds
        """
        self.timeout = timeout
        self._installation_patterns = self._build_patterns()
    
    def _build_patterns(self) -> Dict[str, List[re.Pattern]]:
        """Build regex patterns for detecting installation commands.
        
        Returns:
            Dictionary mapping installation methods to regex patterns
        """
        return {
            "npm": [
                re.compile(r'npm\s+install\s+(?:-g\s+)?([^\s\n]+)', re.IGNORECASE | re.MULTILINE),
                re.compile(r'npx\s+([^\s\n]+)', re.IGNORECASE | re.MULTILINE),
                re.compile(r'yarn\s+(?:global\s+)?add\s+([^\s\n]+)', re.IGNORECASE | re.MULTILINE),
                re.compile(r'pnpm\s+(?:-g\s+)?(?:add\s+)?([^\s\n]+)', re.IGNORECASE | re.MULTILINE),
            ],
            "pip": [
                re.compile(r'pip\s+install\s+([^\s\n]+)', re.IGNORECASE | re.MULTILINE),
                re.compile(r'pip3\s+install\s+([^\s\n]+)', re.IGNORECASE | re.MULTILINE),
                re.compile(r'uv\s+add\s+([^\s\n]+)', re.IGNORECASE | re.MULTILINE),
                re.compile(r'poetry\s+add\s+([^\s\n]+)', re.IGNORECASE | re.MULTILINE),
            ],
            "git": [
                re.compile(r'git\s+clone\s+([^\s\n]+)', re.IGNORECASE | re.MULTILINE),
            ]
        }
    
    async def parse_documentation_url(self, url: str) -> Optional[Dict[str, Any]]:
        """Parse documentation URL to extract server information.
        
        Args:
            url: URL to documentation page
            
        Returns:
            Extracted server information or None if parsing failed
        """
        if not validate_url(url):
            return None
        
        try:
            # Fetch the content
            content = await self._fetch_content(url)
            if not content:
                return None
            
            # Convert HTML to markdown for easier parsing
            if self._is_html(content):
                markdown_content = markdownify(content)
            else:
                markdown_content = content
            
            # Extract server information
            server_info = await self._extract_server_info(markdown_content, url)
            
            return server_info
            
        except Exception:
            return None
    
    async def _fetch_content(self, url: str) -> Optional[str]:
        """Fetch content from URL.
        
        Args:
            url: URL to fetch
            
        Returns:
            Content string or None if failed
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, timeout=self.timeout)
                response.raise_for_status()
                return response.text
        except (httpx.RequestError, httpx.HTTPStatusError):
            return None
    
    def _is_html(self, content: str) -> bool:
        """Check if content is HTML.
        
        Args:
            content: Content to check
            
        Returns:
            True if content appears to be HTML
        """
        return '<html' in content.lower() or '<!doctype html' in content.lower()
    
    async def _extract_server_info(self, content: str, source_url: str) -> Dict[str, Any]:
        """Extract server information from content.
        
        Args:
            content: Markdown content to parse
            source_url: Source URL for reference
            
        Returns:
            Dictionary with extracted server information
        """
        # Extract basic information
        server_info = {
            "source_url": source_url,
            "name": self._extract_name(content),
            "description": self._extract_description(content),
            "installation": self._extract_installation(content),
            "repository": self._extract_repository(content, source_url),
            "author": self._extract_author(content, source_url),
            "license": self._extract_license(content),
            "capabilities": self._extract_capabilities(content),
            "category": self._infer_categories(content),
            "platforms": ["linux", "darwin", "windows"],  # Default assumption
        }
        
        # Generate server ID
        server_info["id"] = self._generate_server_id(server_info)
        
        # Set defaults for missing fields
        self._set_defaults(server_info)
        
        return server_info
    
    def _extract_name(self, content: str) -> Optional[str]:
        """Extract server name from content.
        
        Args:
            content: Content to parse
            
        Returns:
            Server name or None
        """
        # Look for common title patterns
        patterns = [
            r'^#\s+(.+?)(?:\s+MCP\s+Server)?$',  # Main heading
            r'^##\s+(.+?)(?:\s+MCP\s+Server)?$', # Subheading
            r'(?:^|\s)([A-Z][a-zA-Z\s]+)\s+MCP\s+Server',  # "Name MCP Server"
            r'MCP\s+Server:\s*(.+?)(?:\n|$)',  # "MCP Server: Name"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.MULTILINE | re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                if len(name) > 3 and not name.lower().startswith('mcp'):
                    return name
        
        return None
    
    def _extract_description(self, content: str) -> Optional[str]:
        """Extract server description from content.
        
        Args:
            content: Content to parse
            
        Returns:
            Server description or None
        """
        # Look for description patterns
        patterns = [
            r'(?:^|\n)>\s*(.+?)(?:\n|$)',  # Blockquote description
            r'(?:^|\n)(?:Description|Summary):\s*(.+?)(?:\n|$)',  # Description: line
            r'(?:^|\n)(?:This|The)\s+(?:server|tool|package)\s+(.+?)(?:\.|$)',  # "This server..."
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.MULTILINE | re.IGNORECASE)
            if match:
                desc = match.group(1).strip()
                if len(desc) > 10:
                    return desc
        
        # Fall back to first paragraph after title
        lines = content.split('\n')
        in_content = False
        for line in lines:
            line = line.strip()
            if line.startswith('#'):
                in_content = True
                continue
            if in_content and line and not line.startswith('#'):
                if len(line) > 20:
                    return line
        
        return None
    
    def _extract_installation(self, content: str) -> Dict[str, Any]:
        """Extract installation information from content.
        
        Args:
            content: Content to parse
            
        Returns:
            Installation information dictionary
        """
        installation_info = {
            "method": None,
            "package": None,
            "system_dependencies": [],
            "python_dependencies": []
        }
        
        # Try to find installation commands
        for method, patterns in self._installation_patterns.items():
            for pattern in patterns:
                matches = pattern.findall(content)
                if matches:
                    # Take the first valid match
                    package = matches[0].strip()
                    if validate_package_name(package, method):
                        installation_info["method"] = method
                        installation_info["package"] = package
                        break
            if installation_info["method"]:
                break
        
        # Extract system dependencies
        sys_deps = self._extract_system_dependencies(content)
        if sys_deps:
            installation_info["system_dependencies"] = sys_deps
        
        return installation_info
    
    def _extract_system_dependencies(self, content: str) -> List[str]:
        """Extract system dependencies from content.
        
        Args:
            content: Content to parse
            
        Returns:
            List of system dependencies
        """
        deps = []
        
        # Common patterns for system dependencies
        patterns = [
            r'(?:requires?|needs?|depends? on)\s+([a-zA-Z0-9-]+(?:\s+[0-9.]+)?)',
            r'sudo\s+apt-get\s+install\s+([a-zA-Z0-9-]+)',
            r'brew\s+install\s+([a-zA-Z0-9-]+)',
            r'yum\s+install\s+([a-zA-Z0-9-]+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches:
                dep = match.strip()
                if dep and dep not in deps:
                    deps.append(dep)
        
        return deps
    
    def _extract_repository(self, content: str, source_url: str) -> Optional[str]:
        """Extract repository URL from content.
        
        Args:
            content: Content to parse
            source_url: Source URL for context
            
        Returns:
            Repository URL or None
        """
        # If source URL is already a GitHub repo, use it
        if 'github.com' in source_url and '/blob/' not in source_url:
            return source_url.split('/blob/')[0] if '/blob/' in source_url else source_url
        
        # Look for GitHub links in content
        github_pattern = r'https://github\.com/[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+'
        matches = re.findall(github_pattern, content)
        if matches:
            return matches[0]
        
        return None
    
    def _extract_author(self, content: str, source_url: str) -> str:
        """Extract author information.
        
        Args:
            content: Content to parse
            source_url: Source URL for context
            
        Returns:
            Author name
        """
        # Extract from GitHub URL
        if 'github.com' in source_url:
            parts = source_url.split('/')
            if len(parts) > 3:
                return parts[3]  # GitHub username
        
        # Look for author patterns in content
        patterns = [
            r'(?:Author|By|Created by):\s*(.+?)(?:\n|$)',
            r'(?:^|\n)Author:\s*(.+?)(?:\n|$)',
            r'(?:^|\n)By:\s*(.+?)(?:\n|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.MULTILINE | re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return "Community"
    
    def _extract_license(self, content: str) -> str:
        """Extract license information.
        
        Args:
            content: Content to parse
            
        Returns:
            License name
        """
        patterns = [
            r'(?:License|Licensed under):\s*([A-Z][A-Z0-9.-]*)',
            r'(?:^|\n)License:\s*([A-Z][A-Z0-9.-]*)',
            r'\[([A-Z][A-Z0-9.-]*)\s+License\]',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.MULTILINE)
            if match:
                license_name = match.group(1).strip()
                if license_name.upper() in ['MIT', 'APACHE', 'GPL', 'BSD']:
                    return license_name.upper()
                return license_name
        
        return "MIT"  # Default assumption
    
    def _extract_capabilities(self, content: str) -> List[str]:
        """Extract server capabilities from content.
        
        Args:
            content: Content to parse
            
        Returns:
            List of capabilities
        """
        capabilities = []
        
        # Look for feature lists
        feature_patterns = [
            r'(?:Features|Capabilities|What it does):\s*\n((?:[-*]\s*.+\n?)+)',
            r'(?:^|\n)[-*]\s+([A-Z][^.\n]+)',
        ]
        
        for pattern in feature_patterns:
            matches = re.findall(pattern, content, re.MULTILINE | re.IGNORECASE)
            for match in matches:
                if isinstance(match, str):
                    # Clean up and extract capability
                    cap = re.sub(r'^[-*]\s*', '', match.strip())
                    cap = re.sub(r'\s+', '_', cap.lower())
                    if cap and len(cap) < 50:
                        capabilities.append(cap)
        
        return capabilities[:10]  # Limit to 10 capabilities
    
    def _infer_categories(self, content: str) -> List[str]:
        """Infer server categories from content.
        
        Args:
            content: Content to parse
            
        Returns:
            List of inferred categories
        """
        categories = []
        content_lower = content.lower()
        
        # Category keywords mapping
        category_keywords = {
            "filesystem": ["file", "directory", "folder", "path", "storage"],
            "database": ["database", "sql", "query", "table", "schema", "postgres", "mysql", "sqlite"],
            "api": ["api", "rest", "http", "endpoint", "request"],
            "web": ["web", "browser", "html", "url", "scrape"],
            "development": ["git", "github", "code", "repo", "commit", "development"],
            "communication": ["slack", "discord", "chat", "message", "notification"],
            "cloud": ["aws", "azure", "gcp", "cloud", "s3", "bucket"],
            "container": ["docker", "container", "kubernetes", "k8s"],
            "search": ["search", "find", "query", "index"],
            "ai": ["ai", "ml", "machine learning", "openai", "anthropic"],
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                categories.append(category)
        
        # Add community tag for non-official servers
        if not any(auth in content_lower for auth in ["anthropic", "official"]):
            categories.append("community")
        
        return categories[:5]  # Limit to 5 categories
    
    def _generate_server_id(self, server_info: Dict[str, Any]) -> str:
        """Generate a unique server ID.
        
        Args:
            server_info: Server information
            
        Returns:
            Generated server ID
        """
        # Try to extract from package name
        if server_info.get("installation", {}).get("package"):
            package = server_info["installation"]["package"]
            
            # Clean up npm scoped packages
            if package.startswith("@"):
                package = package.split("/")[-1]
            
            # Remove common prefixes/suffixes
            package = re.sub(r'^mcp-server-?', '', package)
            package = re.sub(r'-?mcp-?server$', '', package)
            package = re.sub(r'^server-?', '', package)
            
            # Clean up the ID
            server_id = re.sub(r'[^a-z0-9-]', '-', package.lower())
            server_id = re.sub(r'-+', '-', server_id).strip('-')
            
            if validate_server_id(server_id):
                return server_id
        
        # Fall back to name-based ID
        if server_info.get("name"):
            name = server_info["name"]
            name = re.sub(r'\s+mcp\s+server', '', name, flags=re.IGNORECASE)
            server_id = re.sub(r'[^a-z0-9-]', '-', name.lower())
            server_id = re.sub(r'-+', '-', server_id).strip('-')
            
            if validate_server_id(server_id):
                return server_id
        
        # Generate from URL
        if server_info.get("source_url"):
            url_parts = urlparse(server_info["source_url"]).path.split('/')
            for part in reversed(url_parts):
                if part and part != "README.md":
                    server_id = re.sub(r'[^a-z0-9-]', '-', part.lower())
                    server_id = re.sub(r'-+', '-', server_id).strip('-')
                    if validate_server_id(server_id):
                        return server_id
        
        # Final fallback
        return "unknown-server"
    
    def _set_defaults(self, server_info: Dict[str, Any]) -> None:
        """Set default values for missing fields.
        
        Args:
            server_info: Server information to update
        """
        defaults = {
            "name": "Unknown MCP Server",
            "description": "MCP server with unknown functionality",
            "category": ["unknown", "community"],
            "author": "Community",
            "versions": {"latest": "1.0.0", "supported": ["1.0.0"]},
            "configuration": {"required_params": [], "optional_params": []},
            "capabilities": ["unknown_operations"],
            "platforms": ["linux", "darwin", "windows"],
            "license": "MIT"
        }
        
        for key, value in defaults.items():
            if not server_info.get(key):
                server_info[key] = value
        
        # Ensure installation info has required fields
        if not server_info.get("installation"):
            server_info["installation"] = {
                "method": "unknown",
                "package": "unknown",
                "system_dependencies": [],
                "python_dependencies": []
            }
    
    def validate_extracted_info(self, server_info: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate extracted server information.
        
        Args:
            server_info: Server information to validate
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        # Check required fields
        required_fields = ["id", "name", "description", "installation"]
        for field in required_fields:
            if not server_info.get(field):
                errors.append(f"Missing required field: {field}")
        
        # Validate server ID
        server_id = server_info.get("id")
        if server_id and not validate_server_id(server_id):
            errors.append(f"Invalid server ID: {server_id}")
        
        # Validate installation info
        installation = server_info.get("installation", {})
        if installation.get("method") not in ["npm", "pip", "git"]:
            errors.append("Installation method must be npm, pip, or git")
        
        package = installation.get("package")
        method = installation.get("method")
        if package and method and not validate_package_name(package, method):
            errors.append(f"Invalid package name for {method}: {package}")
        
        return len(errors) == 0, errors