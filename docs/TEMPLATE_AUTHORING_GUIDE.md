# Template Authoring Guide

This guide explains how to create configuration templates for MCP servers in MCPI.

## What Are Templates?

Configuration templates provide guided, interactive setup for MCP servers. Instead of users manually configuring servers (which can take 15-30 minutes), templates reduce this to 2-3 minutes with interactive prompts.

**Benefits:**
- **Faster Setup**: Reduce configuration time by 80-90%
- **Fewer Errors**: Validation prevents common mistakes
- **Better UX**: Clear prompts guide users through setup
- **Reusable**: Templates can be shared and version-controlled

## Template Structure

Templates are YAML files stored in `data/templates/<server-id>/<template-name>.yaml`.

### Basic Template Format

```yaml
name: template-name
description: "Brief description of this template"
server_id: postgres
scope: user-global
priority: high

config:
  command: npx
  args:
    - "-y"
    - "@modelcontextprotocol/server-postgres"
  env: {}

prompts:
  - name: PARAMETER_NAME
    description: "Help text shown to user"
    type: string
    required: true
    default: "default-value"
    validation_pattern: "^[a-zA-Z0-9_]+$"

notes: |
  Multi-line setup instructions and examples.

  This text is displayed before prompts begin.
```

### Required Fields

**Top-level fields:**
- `name`: Template name (lowercase with hyphens, e.g., "local-development")
- `description`: Brief description shown in template lists
- `server_id`: Server this template is for (must match catalog entry)
- `scope`: Recommended scope (e.g., "user-global", "project-mcp")
- `priority`: Template priority for sorting ("high", "medium", "low")
- `config`: Server configuration (command, args, env)
- `prompts`: List of interactive prompts (can be empty)
- `notes`: Setup instructions and examples (can be empty)

**Config fields:**
- `command`: Command to run the server (e.g., "npx", "python", "docker")
- `args`: List of command-line arguments
- `env`: Dictionary of environment variables (can be empty `{}`)

**Prompt fields:**
- `name`: Parameter name (uppercase with underscores, e.g., "DATABASE_URL")
- `description`: Help text shown to user
- `type`: Prompt type ("string", "secret", "path", "port", "url")
- `required`: Whether this parameter is required (true/false)
- `default`: Default value if user provides nothing (optional)
- `validation_pattern`: Regex pattern for validation (optional)

## Prompt Types

### 1. String
General text input for any string value.

```yaml
- name: DATABASE_NAME
  description: "Name of the database to connect to"
  type: string
  required: true
  default: "postgres"
  validation_pattern: "^[a-zA-Z0-9_]+$"
```

**Validation:**
- Custom regex pattern (optional)
- No null bytes

### 2. Secret
Masked input for passwords, API keys, and tokens.

```yaml
- name: API_KEY
  description: "Your Brave Search API key"
  type: secret
  required: true
  validation_pattern: "^BSA[a-zA-Z0-9_-]{32,}$"
```

**Features:**
- Input displayed as `••••••••` during entry
- Custom regex pattern (optional)

**Use for:**
- Passwords
- API keys
- Access tokens
- Any sensitive data

### 3. Path
File system path validation.

```yaml
- name: PROJECT_ROOT
  description: "Project root directory"
  type: path
  required: true
  default: "/Users/alice/projects/myapp"
```

**Validation:**
- No null bytes
- Basic path format checking
- Does NOT check if path exists (may be created later)

**Use for:**
- Directory paths
- File paths
- Mount points

### 4. Port
Port number with range validation.

```yaml
- name: DATABASE_PORT
  description: "PostgreSQL port number"
  type: port
  required: false
  default: "5432"
  validation_pattern: "^[1-9][0-9]{3,4}$"
```

**Validation:**
- Must be a number
- Range: 1-65535
- Custom regex pattern (optional)

**Use for:**
- Database ports
- API ports
- Service ports

### 5. URL
URL format validation.

```yaml
- name: API_ENDPOINT
  description: "API endpoint URL"
  type: url
  required: true
  default: "https://api.example.com"
```

**Validation:**
- Must start with `http://`, `https://`, `ws://`, or `wss://`
- Custom regex pattern (optional)

**Use for:**
- API endpoints
- Database URLs
- Webhook URLs

## Validation Patterns

Use regex patterns to validate user input more strictly.

### Common Patterns

**Alphanumeric with underscores:**
```yaml
validation_pattern: "^[a-zA-Z0-9_]+$"
```

**Hostname:**
```yaml
validation_pattern: "^[a-zA-Z0-9.-]+$"
```

**PostgreSQL connection string:**
```yaml
validation_pattern: "^postgres(ql)?://.*"
```

**GitHub Personal Access Token:**
```yaml
validation_pattern: "^ghp_[a-zA-Z0-9]{36}$"
```

**Port number (1000-9999):**
```yaml
validation_pattern: "^[1-9][0-9]{3}$"
```

**Email:**
```yaml
validation_pattern: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
```

### Validation Tips

1. **Test your regex**: Use a regex tester to verify patterns work
2. **Keep it simple**: Complex patterns confuse users
3. **Provide examples**: Show valid input in description or notes
4. **Be lenient**: Only validate what's truly necessary

## Template Priority

Templates are sorted by priority in lists:

- `high`: Common, recommended templates (shown first)
- `medium`: Alternative configurations
- `low`: Advanced or rarely-used configurations

**Priority Guidelines:**
- Use `high` for the most common use case
- Use `medium` for alternative setups
- Use `low` for advanced or edge cases

**Example:**
```yaml
# PostgreSQL templates
local-development:
  priority: high      # Most common: local dev

docker:
  priority: high      # Also common: Docker

production:
  priority: medium    # Less common: production setup
```

## Writing Good Notes

The `notes` field provides setup instructions displayed before prompts.

### Good Notes Include:

1. **Context**: What this template sets up
2. **Requirements**: Prerequisites (e.g., "PostgreSQL must be running")
3. **Examples**: Example values or configurations
4. **Tips**: Helpful hints for success

### Example Notes

```yaml
notes: |
  This template creates a PostgreSQL connection for local development.

  Requirements:
  - PostgreSQL installed and running locally
  - Database already created (or use 'postgres' default)

  Connection URL format: postgresql://[user@]localhost/database

  If you leave the username empty, PostgreSQL will use peer authentication
  (your OS username). This is common for local development on macOS/Linux.

  Examples:
    - postgresql://localhost/myapp_dev (peer auth)
    - postgresql://myuser@localhost/myapp_dev (with username)
```

### Notes Best Practices

- Use clear, concise language
- Include practical examples
- Explain any non-obvious behavior
- Link to external docs if needed
- Keep it under 20 lines (if possible)

## Complete Example

Here's a complete template for PostgreSQL:

```yaml
name: local-development
description: "Local PostgreSQL database for development"
server_id: postgres
scope: user-global
priority: high

config:
  command: npx
  args:
    - "-y"
    - "@modelcontextprotocol/server-postgres"
  env: {}

prompts:
  - name: POSTGRES_DATABASE
    description: "Database name to connect to (e.g., 'myapp_dev')"
    type: string
    required: true
    default: "postgres"
    validation_pattern: "^[a-zA-Z0-9_]+$"

  - name: POSTGRES_USER
    description: "Database username (leave empty for peer authentication)"
    type: string
    required: false
    default: ""
    validation_pattern: "^[a-zA-Z0-9_]*$"

notes: |
  This template creates a PostgreSQL connection URL for local development.

  Connection URL format: postgresql://[user@]localhost/database

  If you leave the username empty, PostgreSQL will use peer authentication
  (your OS username). This is common for local development on macOS/Linux.

  Examples:
    - postgresql://localhost/myapp_dev (peer auth)
    - postgresql://myuser@localhost/myapp_dev (with username)
```

## Testing Your Template

### 1. Validate Template Structure

```bash
# Run template validation tests
pytest tests/test_template_validation.py -v
```

This checks:
- YAML syntax is valid
- All required fields present
- Regex patterns compile
- Template loads successfully

### 2. Test Interactively

```bash
# List templates for your server
mcpi add <server-id> --list-templates

# Test the template with real prompts
mcpi add <server-id> --template <template-name>
```

### 3. Test in Different Scopes

Test that the template works in various scopes:

```bash
# Project scope
mcpi add <server-id> --template <name> --scope project-mcp

# User scope
mcpi add <server-id> --template <name> --scope user-global
```

### 4. Test Validation

Try invalid inputs to verify validation works:
- Invalid port numbers (0, 70000, "abc")
- Invalid URLs (missing protocol)
- Invalid tokens (wrong format)
- Empty values for required fields

## Template Naming Conventions

**Template Names:**
- Lowercase with hyphens
- Descriptive of use case
- Brief (2-3 words max)

**Examples:**
- `local-development`
- `docker-compose`
- `production-tls`
- `read-only-access`
- `api-key-setup`

**Parameter Names:**
- Uppercase with underscores
- Follow environment variable conventions
- Match server's expected parameter names

**Examples:**
- `DATABASE_URL`
- `GITHUB_TOKEN`
- `API_KEY`
- `PROJECT_ROOT`

## Common Patterns

### PostgreSQL Server

```yaml
name: production
description: "Production database with TLS"
server_id: postgres
scope: user-global
priority: medium

config:
  command: npx
  args: ["-y", "@modelcontextprotocol/server-postgres"]
  env: {}

prompts:
  - name: POSTGRES_HOST
    description: "Database hostname"
    type: string
    required: true
    validation_pattern: "^[a-zA-Z0-9.-]+$"

  - name: POSTGRES_PORT
    description: "Database port"
    type: port
    required: false
    default: "5432"

  - name: POSTGRES_DATABASE
    description: "Database name"
    type: string
    required: true
    validation_pattern: "^[a-zA-Z0-9_]+$"

  - name: POSTGRES_USER
    description: "Database username"
    type: string
    required: true
    validation_pattern: "^[a-zA-Z0-9_]+$"

  - name: POSTGRES_PASSWORD
    description: "Database password"
    type: secret
    required: true

  - name: POSTGRES_SSL_MODE
    description: "SSL mode (require, verify-ca, verify-full)"
    type: string
    required: false
    default: "require"
    validation_pattern: "^(disable|allow|prefer|require|verify-ca|verify-full)$"
```

### GitHub Server

```yaml
name: personal-full-access
description: "Full access to private and public repositories"
server_id: github
scope: user-global
priority: high

config:
  command: npx
  args: ["-y", "@modelcontextprotocol/server-github"]
  env: {}

prompts:
  - name: GITHUB_TOKEN
    description: "GitHub Personal Access Token (with repo scope)"
    type: secret
    required: true
    validation_pattern: "^ghp_[a-zA-Z0-9]{36}$"

notes: |
  This template configures GitHub with full repository access.

  To create a Personal Access Token:
  1. Go to: https://github.com/settings/tokens
  2. Click "Generate new token (classic)"
  3. Select scopes: repo, read:org
  4. Generate token and copy it

  Token format: ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### Filesystem Server

```yaml
name: custom-directories
description: "Custom directory access with multiple paths"
server_id: filesystem
scope: project-mcp
priority: medium

config:
  command: npx
  args: ["-y", "@modelcontextprotocol/server-filesystem"]
  env: {}

prompts:
  - name: ALLOWED_PATHS
    description: "Comma-separated paths to allow access (e.g., /path1,/path2)"
    type: string
    required: true

  - name: READ_ONLY
    description: "Enable read-only mode? (true/false)"
    type: string
    required: false
    default: "false"
    validation_pattern: "^(true|false)$"

notes: |
  This template configures filesystem access to multiple directories.

  ALLOWED_PATHS:
  - Comma-separated list of absolute paths
  - Example: /Users/alice/projects,/Users/alice/Documents

  READ_ONLY:
  - Set to "true" to prevent write operations
  - Set to "false" to allow full read/write access
```

## Troubleshooting

### Common Issues

**Template not showing up:**
```bash
# Check template is in correct location
ls data/templates/<server-id>/<template-name>.yaml

# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('path/to/template.yaml'))"
```

**Validation not working:**
```bash
# Test regex pattern
python -c "import re; print(re.match(r'^your_pattern$', 'test_input'))"
```

**Prompts not appearing:**
- Check `prompts` is a list (not a dict)
- Verify YAML indentation is correct
- Check for typos in field names

## Contributing Templates

To contribute a template to MCPI:

1. **Create the template file**:
   ```bash
   # Create directory if needed
   mkdir -p data/templates/<server-id>

   # Create template
   vim data/templates/<server-id>/<template-name>.yaml
   ```

2. **Test the template**:
   ```bash
   # Validate
   pytest tests/test_template_validation.py -v

   # Test interactively
   mcpi add <server-id> --template <template-name>
   ```

3. **Document in README** (if adding new server):
   - Add to "Available Templates" section
   - Include brief description

4. **Submit pull request**:
   - Include template file
   - Include test results
   - Describe use case in PR description

## Best Practices Summary

1. **Start simple**: Begin with basic templates, add complexity as needed
2. **Test thoroughly**: Test with valid and invalid inputs
3. **Provide examples**: Show users what valid input looks like
4. **Use validation**: Catch errors early with good validation patterns
5. **Write clear notes**: Help users understand what they're configuring
6. **Follow conventions**: Use established naming patterns
7. **Keep it focused**: One template per use case

## Additional Resources

- **Pydantic validation**: Template models use Pydantic for validation
- **YAML syntax**: https://yaml.org/spec/1.2/spec.html
- **Regex patterns**: https://regex101.com/ (testing tool)
- **Rich prompts**: MCPI uses Rich library for beautiful CLI prompts

## Questions?

- **GitHub Issues**: https://github.com/user/mcpi/issues
- **Documentation**: See README.md and CLAUDE.md for more details
- **Examples**: Look at existing templates in `data/templates/` for inspiration
