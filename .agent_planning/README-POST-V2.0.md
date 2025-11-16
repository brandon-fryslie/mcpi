# MCPI Post-v2.0 Planning - Quick Reference

**Generated**: 2025-11-16 07:36:37
**Status**: v2.0 READY TO SHIP

---

## 📄 Planning Documents

### Primary Documents (Read These First)
1. **ROADMAP-POST-V2.0-2025-11-16-073637.md** - Complete 3-month roadmap with all releases
2. **SPRINT-V2.0.1-2025-11-16-073637.md** - Detailed 1-week sprint plan for v2.0.1
3. **PLANNING-SUMMARY-POST-V2.0-2025-11-16-073637.md** - Quick reference and action items

### Supporting Documents
- **STATUS-2025-11-16-184500.md** - Current project status (v2.0 ship-ready)
- **PLAN-2025-11-16-070237.md** - Original implementation plan with deferred work
- **DIP_AUDIT-2025-11-07-010149.md** - DIP audit for architecture improvements

---

## 🗓️ Release Timeline

```
TODAY ──────► v2.0 SHIP (93% tests, all features working)
              │
              │ 1 week
              ▼
              v2.0.1 (98% tests, documentation)
              │
              │ 1 month
              ▼
              v2.1 (DIP Phase 2 architecture)
              │
              │ 2+ months
              ▼
              v2.2+ (DIP Phases 3-4 + features)
```

---

## 🎯 Next Steps (After v2.0 Ships)

### Week 1: v2.0.1 Sprint
- **Day 1**: Fix 15 safety check violations (CLI tests)
- **Day 2**: Fix 10 safety check violations (functional/TUI tests)
- **Day 3**: Fix 7 CLI output assertions + 1 schema test
- **Day 4**: Add enable/disable documentation
- **Day 5**: Release v2.0.1

**Deliverable**: 98% test pass rate (677/692 tests)

### Month 1: v2.1 Development
- **Week 1-2**: ClaudeCodePlugin refactoring (DIP)
- **Week 3**: ClientRegistry + CLI factory pattern (DIP)
- **Week 4**: Registry abstraction + TUI factory (DIP)

**Deliverable**: DIP Phase 2 complete, improved testability

### Month 2+: v2.2+ Planning
- Gather user feedback from v2.0 and v2.0.1
- Prioritize DIP Phases 3-4 vs new features
- Plan additional enhancements

**Deliverable**: Feature roadmap based on user needs

---

## 📊 Work Breakdown

### v2.0.1 (1 Week)
| Category | Tests | Effort |
|----------|-------|--------|
| Safety check violations | 25 | 3 hours |
| CLI output mismatches | 7 | 30 min |
| Test data schema | 1 | 10 min |
| Documentation | - | 30 min |
| **Total** | **33** | **~5 hours** |

### v2.1 (1 Month)
| Component | Effort |
|-----------|--------|
| ClaudeCodePlugin | 1-2 weeks |
| ClientRegistry | 3-5 days |
| CLI Factory | 1-2 days |
| Registry Abstraction | 3-5 days |
| TUI Factory | 1 day |
| **Total** | **2-3 weeks** |

### v2.2+ (Flexible)
| Component | Effort |
|-----------|--------|
| DIP Phases 3-4 | 2-3 weeks |
| Planning cleanup | 30 min |
| New features | TBD |
| **Total** | **2-3+ weeks** |

---

## ✅ Success Metrics

### v2.0 (Current)
- ✅ All features working
- ✅ 93% test pass rate
- ✅ Zero production bugs
- ✅ Ready to ship

### v2.0.1 (Week 1)
- 🎯 98% test pass rate
- 🎯 All safety checks working
- 🎯 Enable/disable documented
- 🎯 Released and tagged

### v2.1 (Month 1)
- 🎯 DIP Phase 2 complete
- 🎯 >80% test coverage
- 🎯 Unit tests without file I/O
- 🎯 Released and tagged

### v2.2+ (Month 2+)
- 🎯 100% DIP compliance
- 🎯 Planning organized
- 🎯 New features added
- 🎯 Released and tagged

---

## 🔧 Test Failures to Fix (v2.0.1)

### Category 1: Safety Check Violations (25 tests)
**Error**: `SAFETY VIOLATION: ClaudeCodePlugin instantiated in test mode without path_overrides!`

**Fix**: Add `mcp_harness` fixture to tests

**Files**:
- test_cli_integration.py (3)
- test_cli_missing_coverage.py (5)
- test_cli_scope_features.py (2)
- test_cli_targeted_coverage.py (4)
- test_functional_*.py (7)
- test_installer_workflows_integration.py (1)
- test_rescope_aggressive.py (1)
- test_tui_reload.py (4)

### Category 2: CLI Output Mismatches (7 tests)
**Error**: Assertions expect old CLI output format

**Fix**: Update assertions to match Rich console format

**Files**:
- test_cli_integration.py
- test_cli_missing_coverage.py
- test_cli_targeted_coverage.py
- test_cli_smoke.py

### Category 3: Test Data Schema (1 test)
**Error**: Missing required `command` field

**Fix**: Add `command` field to test data

**File**: test_installer.py

---

## 🏗️ DIP Phase 2 Components (v2.1)

### 1. ClaudeCodePlugin (1-2 weeks)
- Inject readers, writers, validators
- Update FileBasedScope
- Create factory functions

### 2. ClientRegistry (3-5 days)
- Support plugin injection
- Maintain auto-discovery
- Create factory functions

### 3. CLI Factory Pattern (1-2 days)
- Inject manager/catalog factories
- Update CLI commands
- Create test fixtures

### 4. Registry Abstraction (3-5 days)
- Create RegistryDataSource protocol
- Implement FileRegistryDataSource
- Implement InMemoryRegistryDataSource

### 5. TUI Factory (1 day)
- Inject adapter factory
- Create MockTUIAdapter
- Update tests

---

## 📚 References

### Planning Documents
- **ROADMAP-POST-V2.0-2025-11-16-073637.md** - Full roadmap
- **SPRINT-V2.0.1-2025-11-16-073637.md** - Sprint plan
- **PLANNING-SUMMARY-POST-V2.0-2025-11-16-073637.md** - Summary

### Status and Analysis
- **STATUS-2025-11-16-184500.md** - Current status
- **PLAN-2025-11-16-070237.md** - Original plan
- **DIP_AUDIT-2025-11-07-010149.md** - Architecture audit

### Historical
- **completed/** - Completed work archives
- **archive/2025-11/** - Superseded planning documents

---

## 🎯 Key Decisions

### ✅ Decisions Made
1. Ship v2.0 now (all features working)
2. Fix test quality in v2.0.1 (1 week)
3. DIP Phase 2 in v2.1 (1 month)
4. DIP Phases 3-4 in v2.2+ (flexible)

### ❓ Open Questions
1. Prioritize new features vs DIP Phases 3-4?
2. What features do users want most?
3. Support additional MCP clients?

**Strategy**: Gather user feedback after v2.0 ships

---

## 🚀 Quick Commands

### Start v2.0.1 Sprint
```bash
# Day 1: Fix first batch of tests
cd /Users/bmf/icode/mcpi
pytest tests/test_cli_integration.py -v
# Fix tests using mcp_harness fixture
# Continue with sprint plan...
```

### Check Test Status
```bash
# Run full suite
pytest --override-ini="addopts=" --tb=short -q

# Current: 644 passing, 33 failing
# Target: 677 passing, 0 failing
```

### View Planning Docs
```bash
cd /Users/bmf/icode/mcpi/.agent_planning

# Read roadmap
cat ROADMAP-POST-V2.0-2025-11-16-073637.md

# Read sprint plan
cat SPRINT-V2.0.1-2025-11-16-073637.md

# Read summary
cat PLANNING-SUMMARY-POST-V2.0-2025-11-16-073637.md
```

---

## 📈 Progress Tracking

### v2.0.1 Progress (Week 1)
- [ ] Day 1: Fix 15 safety checks
- [ ] Day 2: Fix 10 safety checks
- [ ] Day 3: Fix 7 CLI + 1 schema
- [ ] Day 4: Add documentation
- [ ] Day 5: Release v2.0.1

### v2.1 Progress (Month 1)
- [ ] ClaudeCodePlugin refactored
- [ ] ClientRegistry refactored
- [ ] CLI Factory implemented
- [ ] Registry Abstraction implemented
- [ ] TUI Factory refactored
- [ ] Release v2.1

### v2.2+ Progress (Month 2+)
- [ ] DIP Phase 3 complete
- [ ] DIP Phase 4 complete
- [ ] Planning cleanup done
- [ ] New features added
- [ ] Release v2.2+

---

## 🎉 Celebration Milestones

- 🚢 **v2.0 Ships** - All features working!
- 🎯 **v2.0.1 Ships** - 98% test quality!
- 🏗️ **v2.1 Ships** - Better architecture!
- 🌟 **v2.2+ Ships** - Complete DIP + features!

---

**Last Updated**: 2025-11-16 07:36:37
**Status**: v2.0 READY TO SHIP
**Next Action**: Ship v2.0, start v2.0.1 sprint
