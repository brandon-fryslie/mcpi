# MCPI Post-v2.0 Planning Summary

**Generated**: 2025-11-16 07:36:37
**Source**: STATUS-2025-11-16-184500.md (v2.0 SHIP-READY)
**Planning Horizon**: 3 months
**Confidence**: HIGH

---

## Quick Reference

### Planning Documents Created

1. **ROADMAP-POST-V2.0-2025-11-16-073637.md** - Complete 3-month roadmap
2. **SPRINT-V2.0.1-2025-11-16-073637.md** - Detailed 1-week sprint plan
3. **This Summary** - Quick reference and action items

### Release Timeline

```
TODAY ──► v2.0 SHIP (93% tests, all features working)
  │
  │ 1 week
  ▼
v2.0.1 SHIP (98% tests, documentation complete)
  │
  │ 1 month
  ▼
v2.1 SHIP (DIP Phase 2, improved testability)
  │
  │ 2+ months
  ▼
v2.2+ SHIP (DIP Phases 3-4, new features)
```

---

## Immediate Next Steps (After v2.0 Ships)

### Week 1: v2.0.1 Sprint

**Goal**: Fix 33 test failures, achieve 98%+ pass rate

**Day 1**: Fix 15 safety check violations in CLI tests
**Day 2**: Fix 10 safety check violations in functional/TUI tests
**Day 3**: Fix 7 CLI output assertions + 1 schema test
**Day 4**: Add enable/disable documentation + final testing
**Day 5**: Release v2.0.1

**Deliverables**:
- ✅ 98% test pass rate (677/692 tests passing)
- ✅ Enable/disable mechanisms documented
- ✅ v2.0.1 tagged and released

---

## v2.0.1 - Test Quality Improvements (1 Week)

### Scope
Fix all 33 failing tests from v2.0 (test quality issues, not production bugs).

### Work Breakdown

**Category 1: Safety Check Violations** (25 tests, 3 hours)
- Tests not using `mcp_harness` fixture properly
- Fix: Add fixture and path_overrides
- Files: test_cli_*.py, test_functional_*.py, test_tui_*.py

**Category 2: CLI Output Mismatches** (7 tests, 30 minutes)
- Tests expecting old CLI output format
- Fix: Update assertions to match Rich console output
- Files: test_cli_*.py

**Category 3: Test Data Schema** (1 test, 10 minutes)
- Test data missing required `command` field
- Fix: Add field to MCPServer test data
- File: test_installer.py

**Documentation** (30 minutes)
- Add enable/disable mechanisms section to CLAUDE.md
- Document ArrayBased and FileTracked handlers
- Include examples and troubleshooting

### Success Criteria
- [ ] Test pass rate ≥ 98%
- [ ] All safety checks working
- [ ] Enable/disable documented
- [ ] v2.0.1 released

---

## v2.1 - DIP Phase 2 Architecture (1 Month)

### Scope
Implement dependency injection for 5 key components to improve testability.

### Work Breakdown

**Component 1: ClaudeCodePlugin** (1-2 weeks)
- Inject readers, writers, validators
- Update FileBasedScope
- Create factory functions
- Update all tests

**Component 2: ClientRegistry** (3-5 days)
- Support plugin injection
- Maintain auto-discovery
- Create factory functions
- Update tests

**Component 3: CLI Factory Pattern** (1-2 days)
- Inject manager/catalog factories
- Update CLI commands
- Create test fixtures
- Update tests

**Component 4: Registry Abstraction** (3-5 days)
- Create RegistryDataSource protocol
- Implement FileRegistryDataSource
- Implement InMemoryRegistryDataSource
- Update ServerCatalog

**Component 5: TUI Factory** (1 day)
- Inject adapter factory
- Create MockTUIAdapter
- Update tests

### Success Criteria
- [ ] DIP Phase 2 complete (5 components)
- [ ] Test coverage >80% for refactored components
- [ ] Unit tests run without file I/O
- [ ] v2.1 released

---

## v2.2+ - Future Enhancements (2+ Months)

### Scope
Complete DIP implementation and add new features as needed.

### Work Breakdown

**DIP Phases 3-4** (2-3 weeks)
- PluginDiscovery abstraction
- SchemaValidator injection
- EnableDisableHandler refactoring
- PathResolver abstraction
- Factory pattern consistency
- Code organization cleanup

**Planning Cleanup** (30 minutes)
- Archive completed work
- Move superseded docs
- Keep only 4 recent STATUS files
- Organize `.agent_planning/`

**New Features** (TBD)
- Based on user feedback
- Additional client support
- Enhanced catalog features
- Performance optimizations

### Success Criteria
- [ ] 100% DIP compliance
- [ ] Planning documents organized
- [ ] New features prioritized
- [ ] v2.2+ released

---

## Effort Summary

### v2.0.1 (1 Week)
- Safety check fixes: 3 hours
- CLI output updates: 30 minutes
- Schema fix: 10 minutes
- Documentation: 30 minutes
- Testing/release: 2 hours
- **Total: 4-5 hours**

### v2.1 (1 Month)
- ClaudeCodePlugin: 10 days
- ClientRegistry: 3-5 days
- CLI Factory: 1-2 days
- Registry Abstraction: 3-5 days
- TUI Factory: 1 day
- **Total: 2-3 weeks**

### v2.2+ (Flexible)
- DIP Phases 3-4: 2-3 weeks
- Planning cleanup: 30 minutes
- New features: TBD
- **Total: 2-3+ weeks**

---

## Key Milestones

### Milestone 1: v2.0 Ships (TODAY)
- All features working
- 93% test pass rate
- Zero production bugs
- Ready for production use

### Milestone 2: v2.0.1 Ships (Week 1)
- 98% test pass rate
- 33 test failures resolved
- Enable/disable documented
- Quality improvements complete

### Milestone 3: v2.1 Ships (Month 1)
- DIP Phase 2 complete
- Improved testability
- Better SOLID compliance
- Unit tests without file I/O

### Milestone 4: v2.2+ Ships (Month 2+)
- 100% DIP compliance
- Planning organized
- New features added
- Long-term improvements

---

## Risk Assessment

### Overall Risk: LOW
All work is well-defined with clear patterns and acceptance criteria.

### By Release

**v2.0.1**: MINIMAL RISK
- Test fixes only
- No production code changes
- 1 week timeline

**v2.1**: LOW-MEDIUM RISK
- Well-documented patterns
- Incremental refactoring
- Comprehensive test coverage
- 1 month timeline

**v2.2+**: LOW RISK
- Non-critical enhancements
- Flexible timeline
- Can be deferred

---

## Success Metrics

### v2.0.1 Metrics
| Metric | Target | Status |
|--------|--------|--------|
| Test Pass Rate | ≥98% | 🎯 |
| Test Failures | 0 | 🎯 |
| Documentation | Complete | 🎯 |
| Release | Tagged | 🎯 |

### v2.1 Metrics
| Metric | Target | Status |
|--------|--------|--------|
| DIP Phase 2 | 5 components | 🎯 |
| Test Coverage | >80% | 🎯 |
| Unit Tests | No file I/O | 🎯 |
| Release | Tagged | 🎯 |

### v2.2+ Metrics
| Metric | Target | Status |
|--------|--------|--------|
| DIP Complete | 100% | 🎯 |
| Planning | Organized | 🎯 |
| New Features | As needed | 🎯 |
| Release | Tagged | 🎯 |

---

## Action Items

### Immediate (After v2.0 Ships)
- [ ] Start v2.0.1 sprint (Day 1)
- [ ] Fix first 15 safety check violations
- [ ] Continue with sprint plan

### Week 1
- [ ] Complete v2.0.1 sprint
- [ ] Release v2.0.1
- [ ] Announce release

### Week 2-5
- [ ] Start v2.1 development
- [ ] Implement DIP Phase 2
- [ ] Update documentation

### Month 2+
- [ ] Start v2.2+ planning
- [ ] Implement DIP Phases 3-4
- [ ] Add new features as needed

---

## Questions and Decisions

### Decisions Made
✅ Ship v2.0 now (all features working, 93% tests)
✅ Fix test quality in v2.0.1 (1 week sprint)
✅ DIP Phase 2 in v2.1 (1 month timeline)
✅ DIP Phases 3-4 in v2.2+ (flexible timeline)

### Open Questions
❓ Should we prioritize new features over DIP Phases 3-4?
❓ What new features do users want most?
❓ Should we support additional MCP clients?

**Decision Strategy**: Gather user feedback after v2.0 ships, prioritize based on impact.

---

## Dependencies

### v2.0.1 Dependencies
- None (can start immediately after v2.0 ships)

### v2.1 Dependencies
- v2.0.1 complete (avoid merge conflicts)

### v2.2+ Dependencies
- v2.1 complete (DIP Phase 2 foundation)

---

## Conclusion

MCPI has a clear post-ship roadmap with three releases planned:

1. **v2.0.1** (1 week) - Quick wins for test quality
2. **v2.1** (1 month) - Architecture improvements via DIP Phase 2
3. **v2.2+** (2+ months) - Complete DIP + new features

All work is **low-risk, well-defined, and actionable**.

**Recommendation**: Ship v2.0 now, execute this roadmap iteratively.

---

## References

- **Detailed Roadmap**: `ROADMAP-POST-V2.0-2025-11-16-073637.md`
- **Sprint Plan**: `SPRINT-V2.0.1-2025-11-16-073637.md`
- **Current Status**: `STATUS-2025-11-16-184500.md`
- **DIP Audit**: `DIP_AUDIT-2025-11-07-010149.md`
- **Original Plan**: `PLAN-2025-11-16-070237.md`

---

**Planning Date**: 2025-11-16 07:36:37
**Planner**: Claude Code (Project Planner)
**Confidence**: HIGH - All work is well-defined and actionable
**Next Review**: After v2.0.1 ships
