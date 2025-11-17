# MCPI Post-v0.3.0 Roadmap

**Generated**: 2025-11-16 16:37:57
**Source STATUS**: STATUS-2025-11-16-FINAL-100-PERCENT-EVALUATION.md
**Current State**: v0.3.0 PRODUCTION READY (100% test pass rate, zero bugs)
**Planning Horizon**: 6 months (November 2025 - May 2026)

---

## Executive Summary

MCPI v0.3.0 is **production ready and shipping immediately**. This roadmap outlines future development in three major releases:

- **v0.3.1** (Optional, 1-2 weeks): Minor fixes and improvements if needed
- **v0.4.0** (1-2 months): DIP Phase 2 architecture + Cursor client plugin
- **v0.5.0** (3-4 months): Additional features and client plugins

### Current Achievement (v0.3.0)

**Quality Metrics**:
- 100% test pass rate (681/681)
- Zero production bugs
- 2.16:1 test-to-code ratio
- Complete feature set

**Capabilities**:
- Custom disable mechanism (user-global, user-internal)
- JSON output (info, search)
- TUI with fzf integration
- 6 configuration scopes
- 5 installation methods
- 50+ servers in catalog

### Post-Ship Strategy

1. **Monitor v0.3.0** - Gather user feedback, watch for issues
2. **Quick fixes in v0.3.1** - Address any critical bugs or usability issues
3. **Architecture improvements in v0.4.0** - Complete DIP Phase 2
4. **Feature expansion in v0.5.0** - Add Cursor/VS Code plugins, new commands

---

## Version 0.3.1 - Maintenance Release (Optional)

**Timeline**: 1-2 weeks post-v0.3.0 ship (if needed)
**Effort**: 1-2 days
**Priority**: P2 (only if critical issues found)
**Status**: CONDITIONAL (only create if issues arise)

### Trigger Conditions

Create v0.3.1 if any of these occur:

1. **Critical Bug**: Production bug with workaround but needs proper fix
2. **Usability Issue**: User confusion requiring documentation or code changes
3. **Platform Issue**: CI fails on specific platform (Windows, macOS, Linux)
4. **Dependency Issue**: Incompatibility with dependency version

### Potential Work Items

**If Critical Bugs Found**:
- Fix bug with comprehensive tests
- Update documentation if needed
- Verify fix across all platforms

**If Usability Issues Found**:
- Improve error messages
- Add help text or examples
- Update documentation
- Add validation for common mistakes

**If Platform Issues Found**:
- Add platform-specific handling
- Update tests with platform markers
- Document platform limitations

**If Dependency Issues Found**:
- Update pinned versions
- Test compatibility
- Update CI matrix if needed

### Release Criteria

**Ship v0.3.1 if**:
- At least 1 P0 or P1 bug fixed
- All tests still passing (100% pass rate)
- No new bugs introduced
- Documentation updated

**Skip v0.3.1 if**:
- No critical bugs found
- All issues can wait for v0.4.0
- User feedback is positive

---

## Version 0.4.0 - Architecture and Cursor Plugin

**Timeline**: 1-2 months (December 2025 - January 2026)
**Effort**: 3-4 weeks
**Priority**: P1
**Status**: PLANNED

### Goals

1. **Complete DIP Phase 2** - Improve testability of 5 P1 components
2. **Add Cursor Client Plugin** - Extend to second MCP client
3. **Enhance Testing Infrastructure** - Test harness improvements
4. **Performance Optimization** - Reduce startup time, improve caching

### Work Items

#### [P1] Complete DIP Phase 2 Architecture

**Status**: Not Started
**Effort**: Large (2-3 weeks)
**Dependencies**: None (DIP Phase 1 complete)
**Reference**: `.agent_planning/DIP_AUDIT-2025-11-07-010149.md`

**Components** (5 total):
1. `ClaudeCodePlugin` - Inject file handlers, scope factories
2. `FileBasedScope` - Inject config reader/writer
3. `FileMoveEnableDisableHandler` - Inject file operations
4. `JSONFileReader` / `JSONFileWriter` - Inject file system access
5. `SchemaValidator` - Inject schema loader

**Acceptance Criteria**:
- [ ] All 5 components accept dependencies via constructor
- [ ] Factory functions created for production use
- [ ] Test factories created for testing
- [ ] All tests updated to use dependency injection
- [ ] 100% test pass rate maintained
- [ ] Documentation updated in CLAUDE.md
- [ ] Migration guide for any breaking changes

**Technical Notes**:

Each component should follow this pattern:

```python
# Before (v0.3.0)
class FileBasedScope:
    def __init__(self, scope_name: str, config_path: Path):
        self.reader = JSONFileReader()  # Hidden dependency
        self.writer = JSONFileWriter()  # Hidden dependency

# After (v0.4.0)
class FileBasedScope:
    def __init__(
        self,
        scope_name: str,
        config_path: Path,
        reader: ConfigReader,
        writer: ConfigWriter
    ):
        self.reader = reader
        self.writer = writer

# Factory function
def create_default_file_based_scope(scope_name: str, config_path: Path) -> FileBasedScope:
    return FileBasedScope(
        scope_name=scope_name,
        config_path=config_path,
        reader=JSONFileReader(),
        writer=JSONFileWriter()
    )
```

**Testing Strategy**:
- Unit tests with mocked dependencies (no file I/O)
- Integration tests with real file operations
- Verify all existing tests still pass
- Add new tests for factory functions

**Benefits**:
- True unit testing without file system
- Easier mocking in tests
- Better separation of concerns
- Consistent with DIP Phase 1 pattern

---

#### [P1] Implement Cursor Client Plugin

**Status**: Not Started
**Effort**: Medium (1 week)
**Dependencies**: Cursor client investigation

**Description**:

Add support for Cursor MCP client as second client plugin, demonstrating plugin architecture extensibility.

**Scope**:
1. **Research Cursor MCP Configuration**:
   - Investigate Cursor's MCP configuration format
   - Identify configuration file locations
   - Understand scope hierarchy
   - Document enable/disable mechanism

2. **Implement CursorPlugin**:
   - Create `mcpi/clients/cursor.py`
   - Implement `MCPClientPlugin` protocol
   - Define scope handlers for Cursor scopes
   - Add Cursor-specific logic

3. **Register Plugin**:
   - Add Cursor to `ClientRegistry`
   - Update client detection logic
   - Add to CLI `--client` options

4. **Testing**:
   - Unit tests for CursorPlugin
   - Integration tests for Cursor operations
   - E2E tests with real Cursor config (skipped in CI)

**Acceptance Criteria**:
- [ ] Cursor plugin implements `MCPClientPlugin` protocol
- [ ] All Cursor scopes defined and working
- [ ] Enable/disable works for Cursor servers
- [ ] Add/remove/rescope operations work
- [ ] Client detection prefers Claude Code, falls back to Cursor
- [ ] 100% test coverage for Cursor plugin
- [ ] All tests passing (including existing tests)
- [ ] Documentation updated in CLAUDE.md

**Technical Notes**:

Expected Cursor configuration structure (to be verified):
```json
// Cursor config location (hypothetical)
~/.cursor/mcp-settings.json
{
  "mcpServers": {
    "server-id": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem"],
      "env": {}
    }
  }
}
```

**Investigation Tasks**:
- [ ] Install Cursor IDE
- [ ] Find MCP configuration files
- [ ] Test manual MCP server configuration
- [ ] Document configuration format
- [ ] Identify scope hierarchy

**Plugin Implementation**:
```python
class CursorPlugin(MCPClientPlugin):
    """Cursor MCP client plugin."""

    def __init__(self, path_overrides: Optional[Dict[str, Path]] = None):
        self.scopes = {
            "user-global": CursorGlobalScope(...),
            # Additional scopes as discovered
        }

    def detect_client(self) -> bool:
        """Detect if Cursor is installed."""
        # Check for Cursor installation
        # Check for config directory
        return cursor_detected
```

---

#### [P2] Add `mcpi doctor` Command

**Status**: Not Started
**Effort**: Medium (3-5 days)
**Dependencies**: None

**Description**:

Add diagnostic command to help users troubleshoot MCPI and MCP server issues.

**Features**:
1. **System Check**:
   - Python version check
   - MCP client detection (Claude Code, Cursor)
   - Configuration file locations and permissions
   - Catalog validation

2. **Server Health Check**:
   - Verify server executables exist
   - Check command paths (npx, npm, pip, uv)
   - Test server connectivity
   - Validate server configurations

3. **Common Issues Detection**:
   - Missing dependencies (node, python)
   - Invalid JSON in config files
   - Duplicate server IDs
   - Circular dependencies
   - File permission issues

4. **Repair Actions**:
   - Fix invalid JSON syntax
   - Remove duplicate servers
   - Reset corrupted configs (with backup)
   - Suggest fixes for common issues

**CLI Usage**:
```bash
# Run all checks
mcpi doctor

# Check specific component
mcpi doctor --check config
mcpi doctor --check servers
mcpi doctor --check catalog

# Output as JSON
mcpi doctor --json

# Fix issues automatically
mcpi doctor --fix
```

**Acceptance Criteria**:
- [ ] All checks implemented and working
- [ ] Clear, actionable output
- [ ] JSON output support
- [ ] Repair actions safe (create backups)
- [ ] Comprehensive test coverage
- [ ] All tests passing
- [ ] Documentation updated

**Technical Notes**:

Output format:
```
MCPI Doctor Report
==================

✅ Python Version: 3.12.0 (OK)
✅ Claude Code: Detected at ~/.config/claude
⚠️  Cursor: Not detected
✅ Configuration Files: Valid JSON
✅ Catalog: 50 servers, all valid
⚠️  Server 'broken-server': Command not found
❌ Server 'invalid-json': Configuration syntax error

Issues Found: 2
Warnings: 2

Run 'mcpi doctor --fix' to repair issues automatically.
```

---

#### [P2] Performance Optimization

**Status**: Not Started
**Effort**: Small (2-3 days)
**Dependencies**: None

**Description**:

Optimize MCPI performance for faster startup and operations.

**Optimizations**:

1. **Lazy Loading**:
   - Defer catalog loading until needed
   - Cache catalog in memory
   - Load client plugins on demand

2. **Caching**:
   - Cache parsed configuration files
   - Cache server states
   - Invalidate cache on file modification

3. **Parallel Operations**:
   - Load multiple scopes in parallel
   - Validate servers concurrently
   - Search catalog with parallel matching

4. **Startup Time**:
   - Profile import times
   - Defer expensive imports
   - Reduce initialization overhead

**Acceptance Criteria**:
- [ ] CLI startup time < 500ms (currently ~1s)
- [ ] List operation < 200ms for 100 servers (currently ~500ms)
- [ ] Search operation < 100ms (currently ~200ms)
- [ ] No performance regressions in tests
- [ ] All tests still passing
- [ ] Memory usage acceptable (< 50MB for normal operations)

**Technical Notes**:

Profile current performance:
```bash
# Startup time
time mcpi --help

# List operation time
time mcpi list

# Search operation time
time mcpi search filesystem
```

**Optimization Techniques**:
- Use `importlib.util.LazyLoader` for deferred imports
- Implement LRU cache for parsed configs
- Use `concurrent.futures` for parallel operations
- Profile with `cProfile` to find bottlenecks

---

### Release Criteria for v0.4.0

**Must Have** (Blocking):
- [ ] DIP Phase 2 complete (5 components)
- [ ] Cursor plugin implemented and tested
- [ ] All tests passing (100% pass rate)
- [ ] Zero production bugs
- [ ] Documentation updated

**Should Have** (Important):
- [ ] `mcpi doctor` command implemented
- [ ] Performance optimizations complete
- [ ] Test coverage maintained or improved
- [ ] CI/CD passing on all platforms

**Nice to Have** (Optional):
- [ ] Additional Cursor scopes beyond basic support
- [ ] Enhanced TUI features
- [ ] Improved error messages

---

## Version 0.5.0 - Feature Expansion

**Timeline**: 3-4 months (February - March 2026)
**Effort**: 4-6 weeks
**Priority**: P2
**Status**: PLANNED

### Goals

1. **Add VS Code Client Plugin** - Support third MCP client
2. **Complete DIP Phases 3-4** - Finish dependency injection refactoring
3. **Remote Server Installation** - Install servers from URLs
4. **Enhanced Search** - Fuzzy search, categories, tags

### Work Items

#### [P2] Implement VS Code Client Plugin

**Status**: Not Started
**Effort**: Medium (1 week)
**Dependencies**: VS Code MCP support (may not exist yet)

**Description**:

Add support for VS Code MCP client (if/when VS Code adds MCP support).

**Note**: VS Code does not currently have official MCP support. This item is **conditional** on VS Code releasing MCP integration.

**Investigation**:
- Monitor VS Code for MCP announcements
- Check VS Code extension marketplace for MCP extensions
- Research community efforts for VS Code MCP integration

**If VS Code adds MCP support**:
- Follow same pattern as Cursor plugin
- Implement VSCodePlugin
- Add to ClientRegistry
- Test with VS Code config

---

#### [P2] Complete DIP Phases 3-4

**Status**: Not Started
**Effort**: Medium (2 weeks)
**Dependencies**: DIP Phase 2 complete
**Reference**: `.agent_planning/DIP_AUDIT-2025-11-07-010149.md`

**Phase 3 Components** (4 medium priority):
1. `CUEValidator` - Inject CUE binary executor
2. `SchemaLoader` - Inject file system access
3. `ServerDiscovery` - Inject catalog dependency
4. `CommandExecutor` - Inject subprocess executor

**Phase 4 Components** (2 low priority):
1. `ConfigMerger` - Inject merge strategy
2. `StateDetector` - Inject file reader

**Acceptance Criteria**:
- [ ] All 6 components use dependency injection
- [ ] Factory functions for production and testing
- [ ] All tests updated and passing
- [ ] Documentation complete
- [ ] Migration guide if breaking changes

---

#### [P2] Remote Server Installation

**Status**: Not Started
**Effort**: Medium (1 week)
**Dependencies**: None

**Description**:

Support installing MCP servers from remote URLs, not just package managers.

**Features**:
1. **Git Repositories**:
   - Clone from GitHub, GitLab, etc.
   - Support specific branches/tags
   - Handle submodules

2. **HTTP/HTTPS URLs**:
   - Download tarballs or zip files
   - Extract and install
   - Verify checksums

3. **Docker Images**:
   - Pull docker images
   - Run as MCP servers
   - Manage container lifecycle

**CLI Usage**:
```bash
# Install from git
mcpi add my-server --git https://github.com/user/mcp-server.git

# Install from URL
mcpi add my-server --url https://example.com/server.tar.gz

# Install from docker
mcpi add my-server --docker user/mcp-server:latest
```

**Acceptance Criteria**:
- [ ] Git installation working
- [ ] URL installation working
- [ ] Docker installation working (optional)
- [ ] Comprehensive tests
- [ ] All tests passing
- [ ] Documentation updated

---

#### [P3] Enhanced Search Features

**Status**: Not Started
**Effort**: Small (2-3 days)
**Dependencies**: None

**Description**:

Improve server search with fuzzy matching, categories, and tags.

**Features**:
1. **Fuzzy Search**:
   - Typo-tolerant search
   - Similarity scoring
   - Ranked results

2. **Categories**:
   - Group servers by category (filesystem, web, database, etc.)
   - Filter by category
   - Browse by category

3. **Tags**:
   - Add tags to servers in catalog
   - Search by tags
   - Filter by multiple tags

4. **Advanced Filters**:
   - Filter by install method
   - Filter by language (Python, Node.js)
   - Filter by license
   - Filter by author

**CLI Usage**:
```bash
# Fuzzy search
mcpi search filesytem  # Finds "filesystem" despite typo

# Search by category
mcpi search --category filesystem

# Search by tags
mcpi search --tag python --tag database

# Advanced filters
mcpi search --install-method pip --language python
```

**Acceptance Criteria**:
- [ ] Fuzzy search implemented
- [ ] Categories added to catalog
- [ ] Tags added to catalog
- [ ] Advanced filters working
- [ ] All tests passing
- [ ] Documentation updated

---

### Release Criteria for v0.5.0

**Must Have** (Blocking):
- [ ] At least 1 additional client plugin (VS Code or other)
- [ ] DIP Phases 3-4 complete
- [ ] All tests passing (100% pass rate)
- [ ] Zero production bugs
- [ ] Documentation updated

**Should Have** (Important):
- [ ] Remote server installation working
- [ ] Enhanced search features implemented
- [ ] Test coverage maintained or improved
- [ ] CI/CD passing on all platforms

**Nice to Have** (Optional):
- [ ] Docker installation support
- [ ] Server health monitoring
- [ ] Usage analytics

---

## Future Versions (v0.6.0+)

### Potential Features (Not Committed)

**Server Management**:
- Server version management and updates
- Server dependencies and prerequisites
- Server health monitoring
- Automatic server updates

**Configuration Management**:
- Configuration templates
- Configuration validation
- Configuration migration tools
- Configuration backup/restore

**TUI Enhancements**:
- Full-screen TUI with multiple panes
- Interactive configuration editor
- Server logs viewer
- Real-time server status

**Integration**:
- Editor plugins (VS Code extension, etc.)
- CI/CD integration (GitHub Actions)
- Webhook support for server events
- API server for remote management

**Community**:
- User-contributed server catalog
- Server ratings and reviews
- Community server repository
- Plugin marketplace

---

## Technical Debt Roadmap

### DIP Implementation Status

**Phase 1** (Complete in v0.3.0):
- ✅ `ServerCatalog`
- ✅ `MCPManager`

**Phase 2** (Target: v0.4.0):
- ⏳ `ClaudeCodePlugin`
- ⏳ `FileBasedScope`
- ⏳ `FileMoveEnableDisableHandler`
- ⏳ `JSONFileReader` / `JSONFileWriter`
- ⏳ `SchemaValidator`

**Phase 3** (Target: v0.5.0):
- ⏳ `CUEValidator`
- ⏳ `SchemaLoader`
- ⏳ `ServerDiscovery`
- ⏳ `CommandExecutor`

**Phase 4** (Target: v0.5.0):
- ⏳ `ConfigMerger`
- ⏳ `StateDetector`

**Total Progress**: 2/13 components (15%)
**Estimated Completion**: v0.5.0 (March 2026)

---

### Planning Document Cleanup

**Status**: Needs attention (69 files in `.agent_planning/`)
**Priority**: P2 (not blocking releases)
**Target**: v0.4.0 timeframe

**Recommended Actions**:

1. **Move to `completed/`** (10-15 files):
   - Ship checklists for completed features
   - Old STATUS reports (keep 4 most recent)
   - Old PLAN files (keep 4 most recent)
   - Day-complete summaries

2. **Move to `archive/`** (15-20 files):
   - Old release plans (superseded by current)
   - Deprecated analysis documents
   - Outdated planning files
   - Historical evaluation documents

3. **Keep Active** (15-20 files):
   - Recent STATUS reports (4 most recent)
   - Recent PLAN files (4 most recent)
   - Current ROADMAP
   - DIP audit
   - CLAUDE.md
   - Backlog

**Retention Policy**:
- STATUS files: Keep 4 most recent
- PLAN files: Keep 4 most recent
- ROADMAP files: Keep current + 1 previous
- Ship checklists: Move to completed after ship
- Evaluation docs: Keep if referenced by recent work

---

## Success Metrics

### Version Success Criteria

**v0.3.1** (if created):
- No regressions from v0.3.0
- All critical bugs fixed
- User satisfaction maintained

**v0.4.0**:
- 100% test pass rate maintained
- DIP Phase 2 complete
- Cursor plugin working
- Performance improvements measurable

**v0.5.0**:
- 100% test pass rate maintained
- DIP Phases 3-4 complete
- At least 2 client plugins working
- Enhanced features well-received

### Quality Gates

**Every Release**:
- 100% test pass rate (all active tests passing)
- Zero production bugs at ship time
- Test-to-code ratio ≥ 2:1
- Code quality: No TODO/FIXME in src/
- Documentation: Complete and current
- CI/CD: Passing on all platforms

**Non-Negotiable**:
- Backward compatibility (or documented migration)
- No data loss or corruption
- Clear error messages
- Comprehensive test coverage

---

## Risk Assessment

### Technical Risks

**DIP Implementation**:
- **Risk**: Breaking changes affect users
- **Mitigation**: Factory functions maintain backward compatibility
- **Probability**: LOW (careful design prevents breaks)

**New Client Plugins**:
- **Risk**: Client format changes break plugin
- **Mitigation**: Version detection, graceful degradation
- **Probability**: MEDIUM (clients may update formats)

**Performance Optimization**:
- **Risk**: Optimization introduces bugs
- **Mitigation**: Comprehensive tests, benchmark suite
- **Probability**: LOW (tests catch regressions)

### Schedule Risks

**Feature Creep**:
- **Risk**: Scope expands, delays releases
- **Mitigation**: Strict prioritization, MVP mindset
- **Probability**: MEDIUM (common in open source)

**Dependency on External Clients**:
- **Risk**: VS Code never adds MCP support
- **Mitigation**: Focus on Claude Code and Cursor first
- **Probability**: HIGH (VS Code MCP is uncertain)

**Maintainer Availability**:
- **Risk**: Solo maintainer has limited time
- **Mitigation**: Prioritize ruthlessly, defer low-priority work
- **Probability**: MEDIUM (single maintainer)

---

## Community and Ecosystem

### Potential Integrations

**Editor Extensions**:
- VS Code extension for MCPI management
- JetBrains plugin
- Emacs package
- Vim plugin

**CI/CD Tools**:
- GitHub Actions for MCP server testing
- Pre-commit hooks for config validation
- Docker images for reproducible environments

**Ecosystem Tools**:
- MCP server template generator
- MCP server testing framework
- MCP server documentation generator

### Community Growth

**Outreach**:
- Blog posts about MCPI features
- Tutorials and guides
- Conference talks or demos
- Social media presence

**Contribution**:
- Contributor guidelines
- Good first issues for newcomers
- Code review process
- Community discussions (GitHub Discussions)

**Sustainability**:
- Consider sponsorship or funding
- Build co-maintainer team
- Establish governance model
- Long-term roadmap transparency

---

## Conclusion

MCPI v0.3.0 represents a **major quality milestone** with 100% test pass rate and comprehensive features. The roadmap for v0.4.0 and v0.5.0 focuses on:

1. **Architecture excellence** - Complete DIP implementation
2. **Client extensibility** - Add Cursor and potentially VS Code
3. **Enhanced capabilities** - Doctor command, remote installation, better search
4. **Community growth** - Build ecosystem and contributor base

**Key Principles for Future Development**:
- Ship working software frequently
- Maintain 100% test pass rate
- Preserve backward compatibility
- Document everything
- Prioritize ruthlessly
- Listen to users

**Next Immediate Steps**:
1. Ship v0.3.0 NOW
2. Monitor for issues (Week 1)
3. Gather user feedback (Week 1-2)
4. Plan v0.4.0 work (Week 2-3)
5. Begin DIP Phase 2 implementation (Week 3+)

---

**Status**: READY TO SHIP v0.3.0
**Confidence**: 99.25% (VERY HIGH)
**Next Milestone**: v0.4.0 (December 2025 - January 2026)

---

*Generated by: Project Planning Agent*
*Date: 2025-11-16 16:37:57*
*Source: STATUS-2025-11-16-FINAL-100-PERCENT-EVALUATION.md*
*Recommendation: SHIP v0.3.0 NOW, begin v0.4.0 planning*
