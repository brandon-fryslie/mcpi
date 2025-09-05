# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2025-01-01

### Added
- Initial release of mcpi (MCP Manager)
- Comprehensive MCP server registry with core and community servers
- Command-line interface with full feature set:
  - `mcpi list` - List available MCP servers
  - `mcpi search` - Search servers by name, description, or capabilities
  - `mcpi info` - Show detailed server information
  - `mcpi install` - Install MCP servers with configuration
  - `mcpi uninstall` - Remove installed servers
  - `mcpi status` - Show installation status
  - `mcpi categories` - List server categories
  - `mcpi config` - Configuration management commands
  - `mcpi doctor` - System diagnostics
  - `mcpi sync` - Update server registry
- Installation support for multiple methods:
  - NPM packages (`npm install`)
  - Python packages (`pip install` and `uv add`)
  - Git repositories (`git clone`)
- Native Claude Code integration:
  - Automatic detection of Claude Code configuration
  - Direct updates to `mcp_servers.json`
  - Platform-specific configuration paths
- Configuration management:
  - Profile-based configurations for different environments
  - TOML-based configuration files
  - Template system for server configurations
- Server registry features:
  - JSON-based server catalog
  - Server validation and integrity checking
  - Category-based organization
  - Platform compatibility detection
  - Version management
- Comprehensive test coverage
- Rich CLI output with tables, colors, and progress indicators
- Dry-run mode for testing operations
- Cross-platform support (Linux, macOS, Windows)

### Server Registry
- **Core Servers** (Anthropic):
  - filesystem - Local filesystem operations
  - sqlite - SQLite database operations
  - git - Git repository management
  - brave-search - Web search via Brave Search API
  - slack - Slack workspace integration
- **Community Servers**:
  - github - GitHub API integration
  - postgres - PostgreSQL database operations
  - redis - Redis data structure operations
  - docker - Docker container management
  - aws-s3 - Amazon S3 bucket operations

### Technical Features
- Type-safe implementation with Pydantic models
- Async support for network operations
- Robust error handling and validation
- Comprehensive logging system
- Configuration backup and restore
- Installation rollback capability
- System dependency checking
- Platform compatibility validation

[Unreleased]: https://github.com/user/mcpi/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/user/mcpi/releases/tag/v0.1.0