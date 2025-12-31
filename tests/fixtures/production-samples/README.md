# Production File Format Samples

This directory contains sanitized samples of real production file formats used by MCP clients.

**Purpose**: Ensure test fixtures match actual production formats to prevent bugs like the installed_plugins.json array format issue.

## Directory Structure

```
production-samples/
├── claude-code/
│   ├── installed_plugins_v1_dict.json    # Legacy dict format
│   ├── installed_plugins_v2_array.json   # Current array format
│   ├── settings_user_global.json         # User-level settings
│   └── enabled_plugins.json              # Plugin enable state
├── mcp-json/
│   ├── minimal.json                      # Minimal valid config
│   ├── with_env_vars.json                # Environment variable usage
│   └── multi_server.json                 # Multiple servers
└── README.md
```

## Maintenance

1. When a format-related bug is discovered, add a sample that would have caught it
2. Include version markers in filenames when formats change over time
3. Keep samples sanitized (no real paths, secrets, or identifying info)
4. Reference samples in `test_production_formats.py`

## Source of Truth

These samples are derived from:
- Bug reports that revealed format mismatches
- Actual file inspection on development machines
- Claude Code documentation when available
