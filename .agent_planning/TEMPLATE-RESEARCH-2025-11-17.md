# Configuration Templates Research - Day 3

**Date**: 2025-11-17
**Task**: TMPL-007 - Research Server Parameters
**Goal**: Document configuration requirements for 5 target servers
**Status**: COMPLETE

---

## Research Summary

All 5 servers have been researched by examining official documentation and source code. Key findings:

1. **PostgreSQL**: Takes a single PostgreSQL URL as command-line argument (not env vars)
2. **GitHub**: Requires only `GITHUB_PERSONAL_ACCESS_TOKEN` environment variable
3. **Filesystem**: Takes allowed directories as command-line arguments (not env vars)
4. **Slack**: Requires `SLACK_BOT_TOKEN` and `SLACK_TEAM_ID`, optional `SLACK_CHANNEL_IDS`
5. **Brave Search**: Requires only `BRAVE_API_KEY` environment variable

---

## 1. PostgreSQL Server

### Basic Information
- **Server ID**: `postgres`
- **Repository**: https://github.com/modelcontextprotocol/servers-archived/tree/main/src/postgres
- **Install Command**: `npx -y @modelcontextprotocol/server-postgres`
- **Description**: Read-only access to PostgreSQL databases with schema inspection

### Configuration Method

**IMPORTANT**: PostgreSQL server uses a **PostgreSQL connection URL** passed as a command-line argument, NOT environment variables.

**Format**: `postgresql://[user[:password]@][host][:port][/dbname][?param1=value1&...]`

**Examples**:
```
postgresql://localhost/mydb
postgresql://user:password@localhost:5432/mydb
postgresql://user:password@host.docker.internal:5432/mydb
postgresql://postgres@localhost/production_db?sslmode=require
```

### Required Parameters (embedded in URL)
1. **Host**: Database server hostname or IP (default: localhost)
2. **Port**: Database server port (default: 5432)
3. **Database Name**: Name of the database to connect to (REQUIRED)
4. **User**: PostgreSQL username (default: current OS user)
5. **Password**: PostgreSQL password (if required)

### Optional Parameters (URL query parameters)
- `sslmode`: SSL connection mode (disable, prefer, require, verify-ca, verify-full)
- `connect_timeout`: Connection timeout in seconds
- `application_name`: Application name for connection tracking

### Use Cases

**Use Case 1: Local Development**
- **Scenario**: Developer's local PostgreSQL instance
- **URL Pattern**: `postgresql://localhost/mydb`
- **Notes**: No password needed if using peer authentication
- **Template Name**: `development`

**Use Case 2: Docker Container**
- **Scenario**: PostgreSQL running in Docker, accessed from host
- **URL Pattern**: `postgresql://postgres:password@localhost:5432/mydb`
- **Notes**: Default PostgreSQL Docker username is 'postgres'
- **Template Name**: `docker`

**Use Case 3: Remote Production Database**
- **Scenario**: Connecting to production database with SSL
- **URL Pattern**: `postgresql://user:password@prod-db.example.com:5432/prod_db?sslmode=require`
- **Notes**: SSL should be required for production
- **Template Name**: `production`

### Template Proposals

1. **local-development.yaml**
   - Prompts: database name, optional username
   - Config: `postgresql://localhost/{database}`
   - Priority: high (most common)

2. **docker.yaml**
   - Prompts: database name, password
   - Config: `postgresql://postgres:{password}@localhost:5432/{database}`
   - Priority: high (common for dev)

3. **production.yaml**
   - Prompts: host, port, database, username, password
   - Config: `postgresql://{user}:{password}@{host}:{port}/{database}?sslmode=require`
   - Priority: medium (important but less common)

### Validation Rules
- **Host**: Valid hostname or IP address format
- **Port**: Integer between 1 and 65535
- **Database Name**: Non-empty, alphanumeric with underscores
- **URL**: Must start with `postgresql://`

---

## 2. GitHub Server

### Basic Information
- **Server ID**: `github`
- **Repository**: https://github.com/modelcontextprotocol/servers-archived/tree/main/src/github
- **Install Command**: `npx -y @modelcontextprotocol/server-github`
- **Description**: Interact with GitHub repositories, issues, and pull requests

### Configuration Method

**Environment Variables** (passed in `env` section of config)

### Required Parameters
1. **GITHUB_PERSONAL_ACCESS_TOKEN**
   - Type: Secret (Personal Access Token)
   - Format: `ghp_...` (classic) or `github_pat_...` (fine-grained)
   - Source: https://github.com/settings/tokens
   - Validation: Starts with `ghp_` or `github_pat_`

### Optional Parameters
- None explicitly required by the server
- The GitHub API URL is hardcoded to `https://api.github.com`
- Enterprise GitHub would require code modifications

### Token Scopes

**Full Access (repo scope)**:
- Private and public repository access
- Create/update/delete files
- Create issues and PRs
- Fork repositories
- Full repository management

**Read-Only (public_repo + read:org scopes)**:
- Public repository read access
- Cannot modify repositories
- Can view issues and PRs
- Cannot create or update

**Minimal (public_repo only)**:
- Public repositories only
- Limited operations
- Good for open source work

### Use Cases

**Use Case 1: Personal Development - Full Access**
- **Scenario**: Developer working on personal private repos
- **Token Scopes**: `repo` (full control)
- **Template Name**: `personal-full-access`

**Use Case 2: Read-Only Access**
- **Scenario**: Browsing code and issues without modification
- **Token Scopes**: `public_repo`, `read:org`
- **Template Name**: `read-only`

**Use Case 3: Organization Work**
- **Scenario**: Working with organization repositories
- **Token Scopes**: `repo`, `read:org`, `write:org` (if managing org)
- **Template Name**: `organization`

**Use Case 4: Open Source Contributor**
- **Scenario**: Contributing to public repositories only
- **Token Scopes**: `public_repo`
- **Template Name**: `public-repos`

### Template Proposals

1. **personal-full-access.yaml**
   - Prompts: Personal Access Token (secret)
   - Notes: Includes instructions to create token with `repo` scope
   - Priority: high (most common)

2. **read-only.yaml**
   - Prompts: Personal Access Token (secret)
   - Notes: Create token with `public_repo` and `read:org` scopes
   - Priority: medium

3. **public-repos.yaml**
   - Prompts: Personal Access Token (secret)
   - Notes: Create token with only `public_repo` scope
   - Priority: low (specific use case)

### Validation Rules
- **Token**: Must start with `ghp_` or `github_pat_`
- **Token**: Minimum length 40 characters

---

## 3. Filesystem Server

### Basic Information
- **Server ID**: `filesystem`
- **Repository**: https://github.com/modelcontextprotocol/servers/tree/main/src/filesystem
- **Install Command**: `npx -y @modelcontextprotocol/server-filesystem`
- **Description**: Secure file operations with configurable access controls

### Configuration Method

**Command-Line Arguments** (passed in `args` array after the package name)

### Required Parameters
1. **Allowed Directories**: One or more paths that the server can access
   - Format: Absolute paths (e.g., `/Users/username/Documents`)
   - Multiple paths: Each path is a separate argument

**Example**:
```json
{
  "command": "npx",
  "args": [
    "-y",
    "@modelcontextprotocol/server-filesystem",
    "/Users/username/Desktop",
    "/Users/username/Documents"
  ]
}
```

### Optional Features
- **Read-Only Mode**: Not supported via args (would require code changes)
- **MCP Roots Protocol**: Can dynamically update directories if client supports it

### Use Cases

**Use Case 1: Current Project Only**
- **Scenario**: AI assistant can only access current project directory
- **Paths**: `${workspaceFolder}` or specific project path
- **Safety**: High (limited scope)
- **Template Name**: `project-files`

**Use Case 2: User Documents**
- **Scenario**: Access to user's document directory
- **Paths**: `~/Documents` or `${HOME}/Documents`
- **Safety**: Medium (broader access)
- **Template Name**: `user-documents`

**Use Case 3: Multiple Specific Directories**
- **Scenario**: Access to several specific directories
- **Paths**: Multiple custom paths
- **Safety**: Medium (depends on paths)
- **Template Name**: `multi-directory`

**Use Case 4: Home Directory**
- **Scenario**: Full access to user's home directory
- **Paths**: `${HOME}` or `~`
- **Safety**: Low (very broad access)
- **Template Name**: `home-directory`

### Template Proposals

1. **project-files.yaml**
   - Prompts: Project directory path
   - Default: Current directory or `${workspaceFolder}`
   - Priority: high (safest, most common for project work)

2. **user-documents.yaml**
   - Prompts: None (uses standard Documents path)
   - Config: `~/Documents` or platform-specific
   - Priority: medium

3. **custom-directories.yaml**
   - Prompts: One or more directory paths
   - Validation: Paths must be absolute
   - Priority: low (advanced use case)

### Validation Rules
- **Paths**: Must be absolute paths (start with `/` on Unix, drive letter on Windows)
- **Paths**: Should exist (warn if they don't)
- **Paths**: No null bytes or invalid characters

---

## 4. Slack Server

### Basic Information
- **Server ID**: `slack`
- **Repository**: https://github.com/modelcontextprotocol/servers-archived/tree/main/src/slack
- **Install Command**: `npx -y @modelcontextprotocol/server-slack`
- **Description**: Send and receive messages in Slack workspaces

### Configuration Method

**Environment Variables** (passed in `env` section of config)

### Required Parameters

1. **SLACK_BOT_TOKEN**
   - Type: Secret (Bot User OAuth Token)
   - Format: Starts with `xoxb-`
   - Source: Slack App OAuth & Permissions page
   - Used For: Bot identity and permissions

2. **SLACK_TEAM_ID**
   - Type: String (Workspace ID)
   - Format: Starts with `T`
   - Source: Workspace settings
   - Used For: Workspace identification

### Optional Parameters

3. **SLACK_CHANNEL_IDS**
   - Type: String (comma-separated channel IDs)
   - Format: `C01234567,C76543210` (channels start with `C`)
   - Used For: Limit which channels the bot can access
   - Default: If not set, all public channels are accessible

### Token Types

**Bot Token (`xoxb-...`)**:
- Used for automated actions
- Messages appear as bot
- Can be invited to channels
- Requires bot scopes

**User Token (`xoxp-...`)**:
- Used for user context
- Messages appear as user
- User's permissions
- Requires user scopes
- NOT recommended for MCP server (security risk)

### Required Bot Scopes
- `channels:history` - View messages in channels
- `channels:read` - View basic channel info
- `chat:write` - Send messages
- `reactions:write` - Add emoji reactions
- `users:read` - View users
- `users.profile:read` - View user profiles

### Use Cases

**Use Case 1: Bot Integration**
- **Scenario**: Automated bot for notifications and responses
- **Token**: Bot token with standard scopes
- **Template Name**: `bot-token`

**Use Case 2: Specific Channels Only**
- **Scenario**: Limit bot to specific channels
- **Token**: Bot token
- **Additional**: SLACK_CHANNEL_IDS configured
- **Template Name**: `limited-channels`

**Use Case 3: Read-Only Monitoring**
- **Scenario**: Monitor channels without posting
- **Token**: Bot token with minimal scopes (no chat:write)
- **Template Name**: Would require custom scopes (not templating)

### Template Proposals

1. **bot-token.yaml**
   - Prompts: Bot token (secret), Team ID
   - Notes: Instructions for creating Slack app and getting token
   - Priority: high (primary use case)

2. **limited-channels.yaml**
   - Prompts: Bot token (secret), Team ID, Channel IDs
   - Notes: Explains how to find channel IDs
   - Priority: medium (for restricted access)

### Validation Rules
- **Bot Token**: Must start with `xoxb-`
- **Team ID**: Must start with `T`
- **Channel IDs**: If provided, comma-separated values starting with `C`

---

## 5. Brave Search Server

### Basic Information
- **Server ID**: `brave-search`
- **Repository**: https://github.com/modelcontextprotocol/servers-archived/tree/main/src/brave-search
- **Note**: Now maintained at https://github.com/brave/brave-search-mcp-server
- **Install Command**: `npx -y @anthropic/mcp-server-brave-search` (old archived version)
- **Description**: Search the web using Brave Search API

### Configuration Method

**Environment Variables** (passed in `env` section of config)

### Required Parameters

1. **BRAVE_API_KEY**
   - Type: Secret (API Key)
   - Format: Long alphanumeric string
   - Source: https://api-dashboard.search.brave.com/app/keys
   - Free Tier: 2,000 queries/month
   - Paid Tiers: Higher limits

### Optional Parameters
- None exposed by the server
- API endpoint is hardcoded

### API Tiers

**Free Tier**:
- 2,000 queries per month
- Rate limited
- All features included
- Good for testing and light usage

**Paid Tiers**:
- Higher query limits
- Same features
- Better rate limits
- Production usage

### Use Cases

**Use Case 1: Standard API Key**
- **Scenario**: User with Brave Search API key
- **Template Name**: `api-key`

**Use Case 2: Free Tier**
- **Scenario**: Testing with free tier
- **Template Name**: Not needed (same as api-key)

### Template Proposals

1. **api-key.yaml**
   - Prompts: API key (secret)
   - Notes: Instructions for getting API key from Brave
   - Link: https://api-dashboard.search.brave.com/app/keys
   - Priority: high (only configuration needed)

### Validation Rules
- **API Key**: Non-empty string
- **API Key**: Alphanumeric format

---

## Template Priority Matrix

| Server | Template Name | Priority | Complexity | Common |
|--------|--------------|----------|------------|--------|
| PostgreSQL | local-development | HIGH | Low | Very High |
| PostgreSQL | docker | HIGH | Medium | High |
| PostgreSQL | production | MEDIUM | High | Medium |
| GitHub | personal-full-access | HIGH | Low | Very High |
| GitHub | read-only | MEDIUM | Low | Medium |
| GitHub | public-repos | LOW | Low | Low |
| Filesystem | project-files | HIGH | Low | Very High |
| Filesystem | user-documents | MEDIUM | Low | Medium |
| Filesystem | custom-directories | LOW | Medium | Low |
| Slack | bot-token | HIGH | Medium | High |
| Slack | limited-channels | MEDIUM | Medium | Medium |
| Brave Search | api-key | HIGH | Low | High |

**Total Templates to Create**: 12

**Minimum Goal**: 6 templates (2 per major server)
**Target Goal**: 12 templates (all listed above)

---

## Template Creation Checklist

### Phase 1: High Priority (Minimum 6)
- [ ] postgres/local-development.yaml
- [ ] postgres/docker.yaml
- [ ] github/personal-full-access.yaml
- [ ] filesystem/project-files.yaml
- [ ] slack/bot-token.yaml
- [ ] brave-search/api-key.yaml

### Phase 2: Medium Priority (Target 10)
- [ ] postgres/production.yaml
- [ ] github/read-only.yaml
- [ ] filesystem/user-documents.yaml
- [ ] slack/limited-channels.yaml

### Phase 3: Low Priority (Stretch 12)
- [ ] github/public-repos.yaml
- [ ] filesystem/custom-directories.yaml

---

## Key Findings

### Configuration Patterns

1. **Command-Line Arguments** (PostgreSQL, Filesystem)
   - Arguments go in `args` array AFTER package name
   - No environment variables
   - Example: `["npx", "-y", "@package/name", "arg1", "arg2"]`

2. **Environment Variables** (GitHub, Slack, Brave Search)
   - Variables go in `env` object
   - Keys are uppercase with underscores
   - Example: `{"env": {"KEY_NAME": "value"}}`

3. **Mixed Pattern** (PostgreSQL with URL)
   - Connection string contains all parameters
   - Format: `protocol://user:pass@host:port/db?params`

### Security Considerations

1. **Secrets Should Be Marked**
   - GitHub token: GITHUB_PERSONAL_ACCESS_TOKEN
   - Slack token: SLACK_BOT_TOKEN
   - Brave API key: BRAVE_API_KEY
   - PostgreSQL password: In URL format

2. **Validation Is Critical**
   - URL format validation for PostgreSQL
   - Token prefix validation (xoxb-, ghp_)
   - Path validation for filesystem
   - Channel ID format for Slack

### Template Design Principles

1. **Prompt Clarity**
   - Clear descriptions of what each parameter is
   - Examples in description text
   - Links to documentation for getting tokens

2. **Sensible Defaults**
   - localhost for development scenarios
   - Standard ports (5432 for PostgreSQL)
   - Common paths (~/Documents)

3. **Safety Notes**
   - Warn about security implications
   - Explain scope requirements
   - Guide users to minimal necessary permissions

---

## Next Steps

1. **Create Template Directory Structure**
   ```bash
   mkdir -p data/templates/{postgres,github,filesystem,slack,brave-search}
   ```

2. **Create Template Files**
   - Start with Phase 1 (high priority)
   - Follow YAML format from models.py
   - Test each template validates

3. **Validation Testing**
   - Load templates with TemplateManager
   - Verify Pydantic validation passes
   - Test prompt validation rules

4. **Documentation**
   - Create template authoring guide
   - Document common patterns
   - Provide examples for contributors

---

## Research Status: COMPLETE

All 5 servers researched and documented:

| Server | Docs Read | Code Read | Parameters Documented | Use Cases Identified | Ready for Templates |
|--------|-----------|-----------|----------------------|---------------------|---------------------|
| PostgreSQL | ✓ | ✓ | ✓ | ✓ | ✓ |
| GitHub | ✓ | ✓ | ✓ | ✓ | ✓ |
| Filesystem | ✓ | ✓ | ✓ | ✓ | ✓ |
| Slack | ✓ | ✓ | ✓ | ✓ | ✓ |
| Brave Search | ✓ | ✓ | ✓ | ✓ | ✓ |

**Ready to proceed to TMPL-008 (Template Creation)**

---

**Research Completed**: 2025-11-17
**Next Task**: TMPL-008 - Create Template Files
**Estimated Time for Templates**: 6-8 hours for all 12 templates
