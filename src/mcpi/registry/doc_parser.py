"""Documentation parser for extracting MCP server installation information."""

import re
import asyncio
import json
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
                re.compile(r'npm\s+install\s+(?:-g\s+)?([^\s\n<]+)', re.IGNORECASE | re.MULTILINE),
                re.compile(r'npx\s+([^\s\n<]+)', re.IGNORECASE | re.MULTILINE),
                re.compile(r'yarn\s+(?:global\s+)?add\s+([^\s\n<]+)', re.IGNORECASE | re.MULTILINE),
                re.compile(r'pnpm\s+(?:-g\s+)?(?:add\s+)?([^\s\n<]+)', re.IGNORECASE | re.MULTILINE),
            ],
            "pip": [
                re.compile(r'pip\s+install\s+([^\s\n<]+)', re.IGNORECASE | re.MULTILINE),
                re.compile(r'pip3\s+install\s+([^\s\n<]+)', re.IGNORECASE | re.MULTILINE),
                re.compile(r'uv\s+add\s+([^\s\n<]+)', re.IGNORECASE | re.MULTILINE),
                re.compile(r'poetry\s+add\s+([^\s\n<]+)', re.IGNORECASE | re.MULTILINE),
            ],
            "git": [
                re.compile(r'git\s+clone\s+([^\s\n<]+)', re.IGNORECASE | re.MULTILINE),
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
                raise RuntimeError(f"ERROR: Could not fetch URL: {url}")
                return None

            # Parse HTML content using BeautifulSoup
            soup = BeautifulSoup(content, 'html.parser')

            # Extract server information based on the website structure
            if 'mcpmarket.com' in url:
                server_info = await self._parse_mcp_market(soup, url)
            elif 'github.com' in url:
                server_info = await self._parse_github(soup, url)
            else:
                # Generic parsing approach
                server_info = await self._parse_generic(soup, content, url)

            return server_info

        except Exception as e:
            print(f"Error parsing documentation: {e}")
            return None

    async def _parse_mcp_market(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Parse MCP Market server page with enhanced extraction for RunConfig and GitHub integration.

        Args:
            soup: BeautifulSoup object of the page
            url: Source URL

        Returns:
            Extracted server information
        """
        server_info = {"source_url": url}

        # Generate server ID from URL (mcpmarket.com/server/screenshot-9 -> mcpmarket.com/screenshot-9)
        parsed_url = urlparse(url)
        if '/server/' in parsed_url.path:
            # Extract the server identifier from the path
            server_identifier = parsed_url.path.split('/server/')[-1]
            server_info["id"] = f"mcpmarket.com/{server_identifier}"
        
        # Extract title/name
        title_elem = soup.find('h1') or soup.find('title')
        if title_elem:
            name = title_elem.get_text().strip()
            # Clean up common suffixes
            name = re.sub(r'\s*-\s*MCP\s*Market.*$', '', name, flags=re.IGNORECASE)
            server_info["name"] = name

        # Extract description from various possible selectors
        desc_selectors = [
            'meta[name="description"]',
            '[class*="description"]',
            '.description',
            '[data-testid*="description"]',
            'p:first-of-type',
            '.summary',
            '.content p:first-child',
        ]

        for selector in desc_selectors:
            desc_elem = soup.select_one(selector)
            if desc_elem:
                if desc_elem.name == 'meta':
                    description = desc_elem.get('content', '').strip()
                else:
                    description = desc_elem.get_text().strip()

                if description and len(description) > 10:
                    server_info["description"] = description
                    break

        # Extract GitHub repository URL
        repo_links = soup.find_all('a', href=True)
        github_links = []
        for link in repo_links:
            href = link.get('href', '')
            if 'github.com' in href and '/blob/' not in href and '/issues/' not in href:
                # Clean up the GitHub URL
                clean_url = re.sub(r'#.*$', '', href)  # Remove fragment
                clean_url = re.sub(r'\?.*$', '', clean_url)  # Remove query params
                clean_url = clean_url.rstrip('/')
                if clean_url not in github_links:
                    github_links.append(clean_url)

        if github_links:
            server_info["repository"] = github_links[0]
            
            # Extract author from repository URL
            repo_url = github_links[0]
            parts = repo_url.rstrip('/').split('/')
            if len(parts) >= 4:
                server_info["author"] = parts[-2]  # Username before repo name
            
            # Fetch additional GitHub data (license, documentation)
            github_data = await self._fetch_github_data(github_links[0])
            if github_data:
                if github_data.get("license"):
                    server_info["license"] = github_data["license"]
                if github_data.get("documentation"):
                    server_info["documentation"] = github_data["documentation"]

        # Extract RunConfig from the page content
        run_config = await self._extract_run_config_from_content(soup)
        if run_config:
            server_info["run_config"] = run_config

        # Look for installation instructions (but we'll use repository for actual installation)
        installation_info = self._extract_installation_from_soup(soup)
        if installation_info.get("method") and installation_info.get("package"):
            server_info["installation"] = installation_info
        elif server_info.get("repository"):
            # Default to git installation using the repository
            server_info["installation"] = {
                "method": "git",
                "package": server_info["repository"],
                "system_dependencies": []
            }

        # Set defaults and finalize
        self._set_defaults(server_info)
        
        # Use generated ID if not already set
        if not server_info.get("id"):
            server_info["id"] = self._generate_server_id(server_info)

        return server_info

    async def _extract_run_config_from_content(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """Extract RunConfig information from webpage content.
        
        Args:
            soup: BeautifulSoup object of the page
            
        Returns:
            RunConfig dictionary with command, args, env or None
        """
        # Look for JSON configuration blocks that contain mcpServers
        code_blocks = soup.find_all(['code', 'pre', 'script'])
        
        for block in code_blocks:
            content = block.get_text()
            
            # Look for JSON-like content with mcpServers
            try:
                # Try to find JSON objects containing mcpServers
                json_pattern = r'\{[^}]*"mcpServers"[^}]*\{[^}]*\}[^}]*\}'
                matches = re.findall(json_pattern, content, re.DOTALL | re.IGNORECASE)
                
                for match in matches:
                    try:
                        # Clean up the JSON and try to parse it
                        json_str = match.strip()
                        config = json.loads(json_str)
                        
                        if "mcpServers" in config:
                            # Extract the first server configuration
                            servers = config["mcpServers"]
                            if servers:
                                first_server = next(iter(servers.values()))
                                if "command" in first_server:
                                    run_config = {
                                        "command": first_server.get("command", ""),
                                        "args": first_server.get("args", []),
                                        "env": first_server.get("env", {})
                                    }
                                    return run_config
                    except (json.JSONDecodeError, KeyError):
                        continue
                        
            except Exception:
                continue
        
        # Look for patterns like command: "something", args: [...] in the text
        full_text = soup.get_text()
        
        # Pattern for command extraction
        command_patterns = [
            r'"command":\s*"([^"]+)"',
            r"'command':\s*'([^']+)'",
            r'command:\s*"([^"]+)"',
            r'command:\s*\'([^\']+)\'',
        ]
        
        # Pattern for args extraction
        args_patterns = [
            r'"args":\s*\[([^\]]+)\]',
            r"'args':\s*\[([^\]]+)\]",
            r'args:\s*\[([^\]]+)\]',
        ]
        
        # Pattern for env extraction
        env_patterns = [
            r'"env":\s*\{([^}]+)\}',
            r"'env':\s*\{([^}]+)\}",
            r'env:\s*\{([^}]+)\}',
        ]
        
        command = None
        args = []
        env = {}
        
        # Extract command
        for pattern in command_patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                command = match.group(1).strip()
                break
        
        # Extract args
        for pattern in args_patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                args_str = match.group(1).strip()
                # Parse the args array
                try:
                    # Simple parsing of array elements
                    args_items = re.findall(r'"([^"]+)"|\'([^\']+)\'', args_str)
                    args = [item[0] or item[1] for item in args_items]
                except:
                    args = []
                break
        
        # Extract env
        for pattern in env_patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                env_str = match.group(1).strip()
                # Simple parsing of key-value pairs
                try:
                    env_items = re.findall(r'"([^"]+)":\s*"([^"]+)"|\'([^\']+)\':\s*\'([^\']+)\'', env_str)
                    env = {item[0] or item[2]: item[1] or item[3] for item in env_items}
                except:
                    env = {}
                break
        
        if command:
            return {
                "command": command,
                "args": args,
                "env": env
            }
        
        return None

    async def _fetch_github_data(self, repo_url: str) -> Optional[Dict[str, Any]]:
        """Fetch additional data from GitHub repository.
        
        Args:
            repo_url: GitHub repository URL
            
        Returns:
            Dictionary with license and documentation info
        """
        try:
            # Convert GitHub repo URL to API URL
            parsed = urlparse(repo_url)
            path_parts = parsed.path.strip('/').split('/')
            if len(path_parts) >= 2:
                owner, repo = path_parts[0], path_parts[1]
                api_url = f"https://api.github.com/repos/{owner}/{repo}"
                
                headers = {
                    'User-Agent': 'MCPI-Registry-Parser/1.0',
                    'Accept': 'application/vnd.github.v3+json'
                }
                
                async with httpx.AsyncClient(headers=headers) as client:
                    response = await client.get(api_url, timeout=self.timeout)
                    if response.status_code == 200:
                        data = response.json()
                        
                        result = {}
                        
                        # Extract license
                        license_info = data.get('license')
                        if license_info and license_info.get('name'):
                            result['license'] = license_info['name']
                        else:
                            result['license'] = 'None'
                        
                        # Set documentation URL to README
                        result['documentation'] = f"{repo_url}/blob/main/README.md"
                        
                        return result
                        
        except Exception as e:
            print(f"Error fetching GitHub data: {e}")
        
        return None

    async def _parse_github(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Parse GitHub repository page.

        Args:
            soup: BeautifulSoup object of the page
            url: Source URL

        Returns:
            Extracted server information
        """
        server_info = {"source_url": url, "repository": url}

        # Extract repository name and convert to readable name
        repo_elem = soup.select_one('[data-testid="AppHeader-context-item-label"]') or soup.find('h1')
        if repo_elem:
            repo_name = repo_elem.get_text().strip()
            # Convert kebab-case to title case
            readable_name = repo_name.replace('-', ' ').replace('_', ' ').title()
            server_info["name"] = readable_name

        # Extract description
        desc_elem = soup.select_one('[data-testid="repository-topic-suggestions"] + p') or soup.select_one('.f4.my-3')
        if desc_elem:
            server_info["description"] = desc_elem.get_text().strip()

        # Extract author from URL
        parsed_url = urlparse(url)
        path_parts = parsed_url.path.strip('/').split('/')
        if len(path_parts) >= 2:
            server_info["author"] = path_parts[0]

        # Look for installation instructions in README and other content
        installation_info = await self._extract_installation_from_github(soup, url)
        if installation_info.get("method") and installation_info.get("package"):
            server_info["installation"] = installation_info

        # Set defaults and generate server ID
        self._set_defaults(server_info)
        server_info["id"] = self._generate_server_id(server_info)

        return server_info

    async def _parse_generic(self, soup: BeautifulSoup, content: str, url: str) -> Dict[str, Any]:
        """Parse generic documentation page.

        Args:
            soup: BeautifulSoup object of the page
            content: Raw HTML content
            url: Source URL

        Returns:
            Extracted server information
        """
        # Convert HTML to markdown for easier parsing
        markdown_content = markdownify(content)
        return await self._extract_server_info(markdown_content, url)

    async def _extract_installation_from_github(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract installation information from GitHub repository.

        Args:
            soup: BeautifulSoup object
            url: GitHub repository URL

        Returns:
            Installation information dictionary
        """
        installation_info = {
            "method": None,
            "package": None,
            "system_dependencies": []
        }

        # Try to fetch README content directly
        try:
            readme_url = url.rstrip('/') + '/raw/main/README.md'
            readme_content = await self._fetch_content(readme_url)
            if not readme_content:
                readme_url = url.rstrip('/') + '/raw/master/README.md'
                readme_content = await self._fetch_content(readme_url)

            if readme_content:
                parsed_install = self._extract_installation(readme_content)
                if parsed_install.get("method") and parsed_install.get("package"):
                    return parsed_install
        except:
            pass

        # Fall back to parsing the GitHub page content
        return self._extract_installation_from_soup(soup)

    def _extract_installation_from_soup(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract installation information from BeautifulSoup object.

        Args:
            soup: BeautifulSoup object

        Returns:
            Installation information dictionary
        """
        installation_info = {
            "method": None,
            "package": None,
            "system_dependencies": []
        }

        # Get all text content
        content = soup.get_text()

        # Try each installation method
        for method, patterns in self._installation_patterns.items():
            for pattern in patterns:
                match = pattern.search(content)
                if match:
                    package = match.group(1).strip()
                    # Clean up package name
                    package = package.strip('"\'`')
                    if package and not package.startswith('http') and len(package) < 100:
                        installation_info["method"] = method
                        installation_info["package"] = package
                        return installation_info

        # Look for common code blocks that might contain installation commands
        code_blocks = soup.find_all(['code', 'pre'])
        for block in code_blocks:
            block_text = block.get_text()
            for method, patterns in self._installation_patterns.items():
                for pattern in patterns:
                    match = pattern.search(block_text)
                    if match:
                        package = match.group(1).strip().strip('"\'`')
                        if package and not package.startswith('http') and len(package) < 100:
                            installation_info["method"] = method
                            installation_info["package"] = package
                            return installation_info

        return installation_info

    async def _fetch_content(self, url: str) -> Optional[str]:
        """Fetch content from URL.

        Args:
            url: URL to fetch

        Returns:
            Content string or None if failed
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }

            async with httpx.AsyncClient(headers=headers) as client:
                response = await client.get(url, timeout=self.timeout, follow_redirects=True)
                response.raise_for_status()
                return response.text
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            print(f"Error fetching {url}: {e}")
            return None

    def _is_html(self, content: str) -> bool:
        """Check if content is HTML.

        Args:
            content: Content to check

        Returns:
            True if content appears to be HTML
        """
        content_lower = content.lower().strip()
        # Check for HTML doctype, html tags, or common HTML elements
        html_indicators = [
            '<!doctype html',
            '<html',
            '<head>',
            '<body>',
            '<div',
            '<p>',
            '<h1>',
            '<script',
            '<style'
        ]
        return any(indicator in content_lower for indicator in html_indicators)

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

        # Validate extracted information
        if not self._validate_extracted_info(server_info):
            return server_info  # Return anyway, let validation handle it

        return server_info

    def _extract_name(self, content: str) -> Optional[str]:
        """Extract server name from content.

        Args:
            content: Content to parse

        Returns:
            Extracted name or None
        """
        # Try to extract from H1 headers
        h1_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
        if h1_match:
            name = h1_match.group(1).strip()
            if name:
                return name

        # Try to extract from package.json references
        package_json_match = re.search(r'"name":\s*"([^"]+)"', content)
        if package_json_match:
            package_name = package_json_match.group(1)
            # Convert package name to readable name
            readable_name = package_name.replace('-', ' ').replace('_', ' ')
            readable_name = re.sub(r'^@[\w-]+/', '', readable_name)  # Remove scope
            return readable_name.title()

        # Try to extract from title-like patterns
        title_patterns = [
            r'(?:^|\n)([\w\s]+(?:MCP|Server)[\w\s]*)',
            r'(?:^|\n)([A-Z][a-zA-Z\s]+Server)',
            r'(?:^|\n)#\s*([^\n]+)',
            r'title:\s*([^\n]+)',
        ]

        for pattern in title_patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
            if match:
                name = match.group(1).strip()
                if name and len(name) > 2 and len(name) < 100:
                    return name

        return None

    def _extract_description(self, content: str) -> Optional[str]:
        """Extract description from content.

        Args:
            content: Content to parse

        Returns:
            Extracted description or None
        """
        # Look for description after H1 header
        desc_patterns = [
            r'^#\s+.+\n+(.+?)(?:\n\n|$)',
            r'## Description\s*\n+(.+?)(?:\n#|$)',
            r'> (.+)',  # Blockquote
            r'^\*\*Description:\*\*\s*(.+)$',
            r'description:\s*(.+)$',
            r'^([A-Z][^.!?]*[.!?])\s*$',  # First sentence
        ]

        for pattern in desc_patterns:
            match = re.search(pattern, content, re.MULTILINE | re.DOTALL)
            if match:
                desc = match.group(1).strip()
                # Clean up markdown formatting
                desc = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', desc)  # Remove links
                desc = re.sub(r'\*\*([^*]+)\*\*', r'\1', desc)  # Remove bold
                desc = re.sub(r'\*([^*]+)\*', r'\1', desc)  # Remove italic
                desc = re.sub(r'`([^`]+)`', r'\1', desc)  # Remove code formatting
                if desc and len(desc) > 10:
                    return desc[:200] + "..." if len(desc) > 200 else desc

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
            "system_dependencies": self._extract_system_dependencies(content)
        }

        # Try each installation method
        for method, patterns in self._installation_patterns.items():
            for pattern in patterns:
                match = pattern.search(content)
                if match:
                    package = match.group(1).strip()
                    # Clean up package name
                    package = package.strip('"\'`')
                    if package and not package.startswith('http') and len(package) < 100:
                        installation_info["method"] = method
                        installation_info["package"] = package
                        return installation_info

        return installation_info

    def _extract_system_dependencies(self, content: str) -> List[str]:
        """Extract system dependencies from content.

        Args:
            content: Content to parse

        Returns:
            List of system dependencies
        """
        dependencies = []

        # Look for common system dependencies
        dep_patterns = [
            r'node(?:js)?(?:\s+v?\d+)?',
            r'python(?:\s*3)?(?:\.\d+)?',
            r'git',
            r'npm',
            r'pip',
        ]

        for pattern in dep_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                dep_name = pattern.replace(r'(?:.*?)', '').replace(r'(?:\.*?)', '').replace('\\', '')
                if dep_name not in dependencies:
                    dependencies.append(dep_name)

        return dependencies

    def _extract_repository(self, content: str, source_url: str) -> Optional[str]:
        """Extract repository URL from content.

        Args:
            content: Content to parse
            source_url: Source URL for reference

        Returns:
            Repository URL or None
        """
        # Try to find GitHub/GitLab URLs
        repo_patterns = [
            r'https://github\.com/[\w\.-]+/[\w\.-]+',
            r'https://gitlab\.com/[\w\.-]+/[\w\.-]+',
        ]

        for pattern in repo_patterns:
            match = re.search(pattern, content)
            if match:
                repo_url = match.group(0)
                # Clean up URL (remove .git suffix if present)
                repo_url = re.sub(r'\.git$', '', repo_url)
                return repo_url

        # If source URL is from GitHub, use that
        if 'github.com' in source_url:
            parsed = urlparse(source_url)
            path_parts = parsed.path.strip('/').split('/')
            if len(path_parts) >= 2:
                return f"https://github.com/{path_parts[0]}/{path_parts[1]}"

        return None

    def _extract_author(self, content: str, source_url: str) -> str:
        """Extract author information from content.

        Args:
            content: Content to parse
            source_url: Source URL for reference

        Returns:
            Author name
        """
        # Try to extract from various patterns
        author_patterns = [
            r'(?:Author|By):\s*([^\n]+)',
            r'Created by\s+([^\n]+)',
            r'@([a-zA-Z0-9_-]+)',  # GitHub username
            r'author:\s*([^\n]+)',
        ]

        for pattern in author_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                author = match.group(1).strip()
                if author:
                    return author

        # Try to extract from GitHub URL
        if 'github.com' in source_url:
            parsed = urlparse(source_url)
            path_parts = parsed.path.strip('/').split('/')
            if len(path_parts) >= 1:
                return path_parts[0]

        return "Unknown"

    def _extract_license(self, content: str) -> str:
        """Extract license information from content.

        Args:
            content: Content to parse

        Returns:
            License name
        """
        license_patterns = [
            r'License:\s*([^\n]+)',
            r'Licensed under\s+([^\n]+)',
            r'\b(MIT|Apache|GPL|BSD|ISC)\b',
        ]

        for pattern in license_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                license_name = match.group(1).strip()
                if license_name:
                    return license_name

        return "Unknown"

    def _extract_capabilities(self, content: str) -> List[str]:
        """Extract capabilities from content.

        Args:
            content: Content to parse

        Returns:
            List of capabilities
        """
        capabilities = []

        # Define capability keywords and their mappings
        capability_keywords = {
            'file': ['filesystem', 'files', 'directory'],
            'database': ['sqlite', 'postgres', 'mysql', 'db'],
            'web': ['http', 'api', 'rest', 'fetch'],
            'shell': ['bash', 'command', 'exec', 'shell'],
            'memory': ['memory', 'knowledge', 'context'],
            'search': ['search', 'query', 'find'],
            'git': ['git', 'version control', 'repository'],
            'screenshot': ['screenshot', 'capture', 'image'],
        }

        content_lower = content.lower()

        for capability, keywords in capability_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                capabilities.append(capability)

        return capabilities if capabilities else ["general"]

    def _infer_categories(self, content: str) -> List[str]:
        """Infer categories from content.

        Args:
            content: Content to parse

        Returns:
            List of categories
        """
        categories = []

        category_keywords = {
            'development': ['dev', 'development', 'coding', 'programming'],
            'productivity': ['productivity', 'workflow', 'automation'],
            'database': ['database', 'sql', 'data'],
            'web': ['web', 'browser', 'http'],
            'file-management': ['file', 'filesystem', 'directory'],
            'utilities': ['utility', 'tool', 'helper'],
            'screenshot': ['screenshot', 'capture', 'image'],
        }

        content_lower = content.lower()

        for category, keywords in category_keywords.items():
            if any(keyword in content_lower for keyword in keywords):
                categories.append(category)

        return categories if categories else ["utilities"]

    def _generate_server_id(self, server_info: Dict[str, Any]) -> str:
        """Generate server ID from server information.

        Args:
            server_info: Server information dictionary

        Returns:
            Generated server ID
        """
        # If this is from mcpmarket.com, use the URL-based ID
        source_url = server_info.get("source_url", "")
        if "mcpmarket.com" in source_url:
            parsed_url = urlparse(source_url)
            if '/server/' in parsed_url.path:
                server_identifier = parsed_url.path.split('/server/')[-1]
                return f"mcpmarket.com/{server_identifier}"
        
        # Try to use package name first
        installation = server_info.get("installation", {})
        package = installation.get("package")

        if package and package != "unknown":
            # Clean up package name to create ID
            server_id = package.lower()
            server_id = re.sub(r'^@[\w-]+/', '', server_id)  # Remove npm scope
            server_id = re.sub(r'[^a-z0-9-]', '-', server_id)
            server_id = re.sub(r'-+', '-', server_id).strip('-')
            if server_id:
                return server_id

        # Fall back to name
        name = server_info.get("name", "")
        if name and name != "Unknown Server":
            server_id = name.lower()
            server_id = re.sub(r'[^a-z0-9-]', '-', server_id)
            server_id = re.sub(r'-+', '-', server_id).strip('-')
            if server_id:
                return server_id

        # Last resort - use URL
        if source_url:
            parsed = urlparse(source_url)
            path_parts = parsed.path.strip('/').split('/')
            if path_parts and path_parts[-1]:
                server_id = path_parts[-1].lower()
                server_id = re.sub(r'[^a-z0-9-]', '-', server_id)
                server_id = re.sub(r'-+', '-', server_id).strip('-')
                if server_id:
                    return server_id

        return "unknown-server"

    def _set_defaults(self, server_info: Dict[str, Any]) -> None:
        """Set default values for missing fields.

        Args:
            server_info: Server information to modify
        """
        defaults = {
            "name": "Unknown Server",
            "description": "MCP server for enhanced functionality",
            "author": "Unknown",
            "license": "Unknown",
            "capabilities": ["general"],
            "category": ["utilities"],
            "platforms": ["linux", "darwin", "windows"],
            "versions": {
                "latest": "1.0.0",
                "supported": ["1.0.0"]
            }
        }

        for key, value in defaults.items():
            if not server_info.get(key):
                server_info[key] = value

        # Ensure installation has required structure
        installation = server_info.get("installation", {})
        if not installation.get("method"):
            installation["method"] = "unknown"
        if not installation.get("package"):
            installation["package"] = server_info.get("id", "unknown")
        if "system_dependencies" not in installation:
            installation["system_dependencies"] = []
        server_info["installation"] = installation

        # Ensure configuration structure exists
        if "configuration" not in server_info:
            server_info["configuration"] = {
                "required_params": [],
                "optional_params": []
            }

    def _validate_extracted_info(self, server_info: Dict[str, Any]) -> bool:
        """Validate extracted server information.

        Args:
            server_info: Server information to validate

        Returns:
            True if valid, False otherwise
        """
        # Check required fields
        required_fields = ["id", "name", "description", "installation"]
        for field in required_fields:
            value = server_info.get(field)
            if not value or (isinstance(value, str) and not value.strip()):
                return False

        # Validate server ID format
        server_id = server_info.get("id", "")
        if not re.match(r'^[a-z0-9][a-z0-9.-]*[a-z0-9]$|^[a-z0-9]$', server_id):
            return False

        # Validate installation info
        installation = server_info.get("installation", {})
        if not installation.get("method") or not installation.get("package"):
            return False

        return True

    def validate_server_info(self, server_info: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate server information and return detailed errors.

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
        if installation.get("method") not in ["npm", "pip", "git", "unknown"]:
            errors.append("Installation method must be npm, pip, git, or unknown")

        package = installation.get("package")
        method = installation.get("method")
        if package and method and method != "unknown" and not validate_package_name(package, method):
            errors.append(f"Invalid package name for {method}: {package}")

        return len(errors) == 0, errors