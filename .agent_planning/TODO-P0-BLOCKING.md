# P0 Blocking Issues - Implementation Tracker

**Started**: 2025-10-28
**Source**: PLAN-2025-10-28-063509.md

## P0-1: Fix Broken Test Import Errors (28 files)

**Status**: IN PROGRESS

### Analysis Complete
- [x] Count test files: 84 total test files
- [x] Count import errors: 28 files (33% of test suite)
- [x] Identify patterns of failures

### Import Error Patterns Found

#### Pattern 1: Deleted modules (no longer exist)
- `mcpi.registry.manager` - Module deleted, no replacement
- `mcpi.registry.doc_parser` - Module deleted, no replacement

#### Pattern 2: Missing classes (never existed or renamed)
- `ServerInstallation` from `mcpi.registry.catalog` - Does NOT exist
- `ClaudeCodeInstaller` from `mcpi.installer.claude_code` - Need to check if exists
- `get_method_string` from `mcpi.cli` - Does NOT exist

#### Pattern 3: Missing functions
- `get_method_string()` - Does NOT exist in current codebase

### Current Reality (from source inspection)
- `mcpi.registry.catalog` has: MCPServer, ServerCatalog, InstallationMethod, ServerRegistry
- `mcpi.installer.base` has: InstallationStatus, InstallationResult, BaseInstaller
- `mcpi.registry/` has: catalog.py, discovery.py, validation.py, cue_validator.py (NO manager.py, NO doc_parser.py)

### Test Files with Import Errors (28 files)

#### Delete - Obsolete functionality (no replacement)
- [ ] tests/test_registry_doc_parser.py - tests deleted doc_parser module
- [ ] tests/test_registry_manager.py - tests deleted manager module
- [ ] tests/test_config_manager_comprehensive.py - tests deleted config.manager
- [ ] tests/test_config_profiles_comprehensive.py - tests profile system (replaced by scopes)
- [ ] tests/test_config_profiles_refactored.py - tests profile system (replaced by scopes)
- [ ] tests/test_config_templates_comprehensive.py - tests template system (not implemented)
- [ ] tests/test_config_templates_missing_lines.py - tests template system (not implemented)
- [ ] tests/test_performance_optimizations.py - performance tests for deleted modules

#### Investigate - May have replacements
- [ ] tests/functional/test_end_to_end_workflows.py - imports ServerInstallation
- [ ] tests/functional/test_installation_workflows.py - imports ServerInstallation
- [ ] tests/functional/test_real_installation_workflows.py - imports ServerInstallation
- [ ] tests/test_cli_comprehensive.py - imports get_method_string, ClaudeCodeInstaller
- [ ] tests/test_cli_comprehensive_fixed.py - imports get_method_string
- [ ] tests/test_cli_refactored.py - imports get_method_string
- [ ] tests/test_client_manager.py - needs investigation
- [ ] tests/test_config.py - needs investigation
- [ ] tests/test_installer_claude_code.py - imports ClaudeCodeInstaller
- [ ] tests/test_installer_claude_code_missing_line.py - imports ClaudeCodeInstaller
- [ ] tests/test_installer_git.py - needs investigation
- [ ] tests/test_installer_python.py - needs investigation
- [ ] tests/test_integration_core.py - needs investigation
- [ ] tests/test_registry.py - needs investigation
- [ ] tests/test_registry_catalog_comprehensive.py - needs investigation
- [ ] tests/test_registry_catalog_comprehensive_fixed.py - needs investigation
- [ ] tests/test_registry_discovery.py - needs investigation
- [ ] tests/test_registry_validation.py - needs investigation
- [ ] tests/test_server_state.py - needs investigation
- [ ] tests/test_stateful_installer.py - needs investigation

### Actions Taken
- None yet

### Next Steps
1. Check if ClaudeCodeInstaller exists in installer/claude_code.py
2. For each test file, determine: DELETE vs UPDATE vs FLAG_AS_GAP
3. Delete obsolete tests
4. Update tests with corrected imports
5. Run pytest --collect-only to verify 0 import errors

---

## P0-2: Remove Dead Code Files

**Status**: NOT STARTED

### Dead Code Files Identified
- [ ] src/mcpi/cli_old.py (41KB)
- [ ] src/mcpi/cli_optimized.py (8.6KB)
- [ ] src/mcpi/cli_original.py (25KB)

### Actions Required
- [ ] Search for any imports: `git grep "cli_old\|cli_optimized\|cli_original"`
- [ ] Delete all three files
- [ ] Verify mcpi command still works
- [ ] Run test suite

---

## P0-3: Verify Core Functionality

**Status**: NOT STARTED

### Commands to Test Manually
- [ ] `mcpi list` - Should show servers
- [ ] `mcpi search <term>` - Should find servers
- [ ] `mcpi info <server>` - Should show server details
- [ ] `mcpi add <server> --scope <scope>` - Install server
- [ ] `mcpi remove <server> --scope <scope>` - Remove server
- [ ] `mcpi status` - Show installed servers
- [ ] `mcpi rescope <server> --from <scope> --to <scope>` - Move server
- [ ] `mcpi completion install bash` - Install completion

### Document Results
- Document what works
- Document what's broken
- Determine if tests are wrong or implementation is wrong

---

## Success Criteria
- [ ] All 84 test files can import (0 import errors)
- [ ] Dead code files removed
- [ ] Core commands verified and documented
- [ ] Test suite runs to completion (may have failures, but no import errors)
- [ ] Git commits with clear messages

## Current Status Summary
- Test files with import errors: 28/84 (33%)
- Dead code files: 3 files (75KB)
- Core functionality: Unknown (needs manual testing)
