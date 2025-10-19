# MCPI Project Action Plan - Test Infrastructure Recovery

## ⚠️ CRITICAL STATUS: TEST INFRASTRUCTURE BREAKDOWN ⚠️
**Reality Check**: Claims of "90% coverage" are false - actual coverage is 8%  
**Test Status**: 2.4% effective test rate (28 working tests out of 1,164)  
**Critical Issue**: ALL CLI tests fail due to architectural mismatch  

**Source**: STATUS-2025-10-16-045045.md evaluation results  
**Generated**: 2025-10-16 07:23:15

## 🚨 P0 CRITICAL TASKS - BROKEN TEST INFRASTRUCTURE

### P0-1: Fix CLI Test Architecture Mismatch **[BLOCKING ALL CLI TESTING]**
- **Issue**: All CLI tests fail with `AttributeError: does not have the attribute 'ClaudeCodeInstaller'`
- **Cause**: Tests mock `ClaudeCodeInstaller` but CLI actually uses `MCPManager`
- **Impact**: 447 lines of CLI code have 0% working test coverage
- **Action**: Update all CLI test mocks to use correct architecture from `mcpi.clients import MCPManager`

### P0-2: Fix Installer Module Testing **[827 LINES UNTESTED]**
- **Issue**: ALL installer modules have 0% test coverage despite being claimed "perfected"
- **Critical Modules**: npm.py (95 lines), python.py (142 lines), git.py (154 lines), claude_code.py (155 lines), base.py (78 lines)
- **Impact**: No verification that any installation method actually works
- **Action**: Create end-to-end tests for each installer with proper mocking

### P0-3: Fix Registry Management Testing **[249 LINES UNTESTED]**
- **Issue**: Registry manager.py has 0% coverage despite working manually
- **Critical Component**: doc_parser.py (438 lines, 0% coverage)
- **Impact**: Core server discovery and catalog management unvalidated
- **Action**: Create comprehensive tests for registry operations

## 📋 P1 HIGH PRIORITY TASKS - CORE VALIDATION

### P1-1: Configuration Management Validation
- **Current**: manager.py (19% coverage), profiles.py (11% coverage), server_state.py (0% coverage)
- **Target**: >90% coverage with cross-platform testing
- **Action**: Test profile switching, template application, path resolution

### P1-2: Client Plugin System Validation  
- **Current**: manager.py (12% coverage), registry.py (12% coverage)
- **Issue**: Plugin architecture is core system but poorly validated
- **Action**: Test MCPManager integration, ClientRegistry, ServerConfig management

### P1-3: Integration Testing
- **Current**: Integration tests claim to exist but test infrastructure is broken
- **Need**: End-to-end workflow testing from discovery → installation → configuration
- **Action**: Create working integration tests for complete user workflows

## 📝 P2 MEDIUM PRIORITY TASKS

### P2-1: Cross-Platform Compatibility
- **Current**: Only validated on Darwin
- **Need**: Windows and Linux path resolution testing
- **Action**: Create platform-specific test suites

### P2-2: Error Handling Validation
- **Current**: CLI has good error patterns but installation/config error scenarios untested
- **Need**: Test failure scenarios, rollback mechanisms, recovery
- **Action**: Create failure scenario test suite

## 🧹 P3 LOW PRIORITY TASKS

### P3-1: Documentation Cleanup
- **Issue**: Planning documents reference "claudew" instead of "MCPI"
- **Action**: Archive obsolete docs, clean up technical debt files

### P3-2: Performance Validation
- **Current**: Claims of optimization exist but unverified
- **Action**: Benchmark and validate performance improvements

## 🎯 REALITY CHECK: ACTUAL PROJECT STATUS

**Previous Claims vs. Reality**:
- ❌ Claimed: "90% total coverage" → **Reality**: 8% actual coverage
- ❌ Claimed: "912/992 tests passing" → **Reality**: CLI tests completely broken
- ❌ Claimed: "All installer modules perfected" → **Reality**: 0% coverage across all installers
- ❌ Claimed: "Comprehensive integration tests" → **Reality**: Test architecture mismatch

**What Actually Works**:
- ✅ CLI commands work manually (list, search, registry operations)
- ✅ Core plugin architecture implemented (MCPManager, ClientRegistry)
- ✅ Registry discovery functional (shows 3 servers)
- ✅ Basic server listing works (6 MCP servers configured)

**Next Steps**: Follow P0 priorities to fix test infrastructure before any new development

---

## 📊 COVERAGE REALITY BY MODULE

**Critical Modules with 0% Coverage**:
- CLI Interface: 447/447 lines missed
- Registry Manager: 249/249 lines missed  
- Registry Doc Parser: 438/438 lines missed
- ALL Installer Modules: 827/827 lines missed
- Config Server State: 153/153 lines missed

**Modules with Working Coverage**:
- Claude Code Plugin: 95% coverage (28/30 tests passing)
- Utility modules: Various coverage levels but functioning

**Total Project Reality**: 8% coverage with massive test infrastructure breakdown

---

## 🚀 IMMEDIATE NEXT STEPS

1. **Start with P0-1**: Fix CLI test mocks to use `MCPManager` instead of `ClaudeCodeInstaller`
2. **Validate Fix**: Ensure CLI tests pass and provide meaningful coverage
3. **Move to P0-2**: Begin installer module testing with end-to-end workflows
4. **Progress Tracking**: Update this TODO as each critical task is completed

**Remember**: The project has solid architecture but needs systematic validation. Focus on fixing what's broken before adding new features.
