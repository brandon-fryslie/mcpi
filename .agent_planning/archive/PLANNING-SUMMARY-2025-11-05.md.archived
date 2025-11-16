# Planning Summary: Rescope Auto-Detection Feature

**Date**: 2025-11-05
**Activity**: Feature planning based on project-evaluator assessment
**Outcome**: Comprehensive implementation backlog created

---

## Summary

Created a detailed implementation plan for adding automatic scope detection to the `mcpi rescope` command based on the evaluation in RESCOPE-AUTO-DETECT-EVALUATION.md.

### Deliverables Created

1. **BACKLOG-RESCOPE-AUTO-DETECT-2025-11-05.md** (NEW)
   - 8 prioritized work items (P0-1 through P0-8)
   - Each with clear acceptance criteria, dependencies, and time estimates
   - Total estimated effort: 3.5-5.5 hours
   - Conservative approach (OPTION B) recommended
   - Comprehensive testing strategy included
   - Risk assessment and mitigation strategies

2. **BACKLOG.md** (UPDATED)
   - Updated to reflect current project status
   - Added reference to new rescope auto-detect backlog
   - Removed obsolete emergency planning content
   - Current focus: feature enhancement

### Key Planning Decisions

**Approach Selected**: OPTION B (Conservative)
- Auto-detects source scope when server exists in exactly ONE scope (95% of cases)
- Errors with clear message when server exists in MULTIPLE scopes (5% edge case)
- Keeps `--from` parameter as optional override for power users
- Provides full backward compatibility

**Rationale**:
- Lowest risk implementation (2-3 hours vs. 4-6 hours for OPTION A)
- Prevents user surprises (explicit control for edge cases)
- Best UX for common case (auto-detect single scope)
- Safe fallback for rare multi-scope case

### Work Breakdown

**Implementation** (2-3 hours):
- P0-1: Add find_all_server_scopes() method to MCPManager (30-45 min)
- P0-2: Make --from parameter optional (15 min)
- P0-3: Implement auto-detection logic (1-1.5 hours)

**Testing** (1-2 hours):
- P0-4: Unit tests for find_all_server_scopes() (30 min)
- P0-5: Integration tests for auto-detection (1-1.5 hours)
- P0-6: Update existing tests (30 min)

**Finalization** (0.5-1 hour):
- P0-7: Update documentation (30 min)
- P0-8: Manual testing and verification (30 min)

### Quality Standards

**Acceptance Criteria**: 10+ criteria per work item totaling 70+ testable requirements

**Testing Strategy**:
- 6+ new tests (4 integration + 2+ unit)
- All 34 existing rescope tests must pass
- 100% coverage of new code paths
- Manual testing of all scenarios

**Documentation**:
- README.md updated with examples
- CLAUDE.md updated with usage patterns
- Inline help text updated
- All examples manually tested

### Risk Assessment

**Overall Risk**: LOW
- Conservative approach (no surprises)
- Backward compatible (additive change)
- Well-tested existing code to build on
- Clear error messages for edge cases

**Technical Risks**: Mitigated
- Multi-scope edge case: Clear error message
- Backward compatibility: Keep --from optional
- Transaction safety: Reuse proven rollback logic
- Performance: No new bottlenecks

**Quality Risks**: Addressed
- Test coverage: Comprehensive test plan
- Regression: Verify all existing tests pass
- Documentation: Update as part of implementation

### Dependencies

**Critical Path**: P0-1 → P0-3 → P0-5 → P0-8 (3.5 hours minimum)

**Parallelization Opportunities**:
- P0-2 can be done independently early
- P0-4 and P0-5 can be done in parallel after P0-1 and P0-3
- P0-7 can be written in parallel with P0-5/P0-6

**Blockers**: None (feature is self-contained)

### Files Modified

**Implementation** (2 files):
- `src/mcpi/clients/manager.py` - Add find_all_server_scopes() method
- `src/mcpi/cli.py` - Make --from optional, add auto-detection logic

**Testing** (1-2 files):
- `tests/test_cli_rescope.py` - Add integration tests, update existing
- `tests/test_manager.py` - Add unit tests for new method

**Documentation** (2 files):
- `CLAUDE.md` - Add command examples
- `README.md` - Update rescope examples

**Total**: 5-6 files modified, 140-240 lines changed

### Success Criteria

**Must Have** (Required for Completion):
- Auto-detects source scope when server in ONE scope
- Clear error when server not found
- Clear error when server in MULTIPLE scopes
- `--from` still works (backward compatibility)
- All existing tests pass (34 rescope tests)
- 6 new tests added and passing
- Documentation updated and verified
- Manual testing complete

**Should Have** (Strong Recommendations):
- Console output indicates auto-detection occurred
- Dry-run mode shows detected scope
- Help text accurate
- Error messages actionable

**Nice to Have** (Future):
- `--all-scopes` flag (P1-1)
- Interactive selection (P1-2)

### Next Steps

1. Review backlog with stakeholders
2. Confirm OPTION B approach (recommended)
3. Begin implementation with P0-1 (add find_all_server_scopes method)
4. Follow dependency order through P0-8
5. Don't skip manual testing (P0-8 is critical)

### Context and Provenance

**Source Documents**:
- STATUS-2025-10-30-062049.md - Current implementation state (CLI now functional)
- RESCOPE-AUTO-DETECT-EVALUATION.md - Evaluation recommending OPTION B
- CLAUDE.md - Project architecture and patterns
- Existing code: cli.py (rescope command), manager.py (helper methods)

**Evaluation Findings**:
- Current rescope requires explicit --from parameter
- Users must know which scope contains server (run `mcpi list` first)
- 95% of rescope operations involve single-scope servers
- 5% edge case: server exists in multiple scopes
- Existing helper methods return first match only (insufficient)
- New method needed: find_all_server_scopes() returning all matches

**Design Decisions**:
- Conservative over aggressive (OPTION B vs. OPTION A)
- Explicit control for edge cases (error on multi-scope)
- Backward compatibility (keep --from optional)
- Clear user guidance (actionable error messages)

### Alignment with Project Goals

**Current Project State**:
- CLI functional (emergency issues resolved)
- Core functionality operational
- Ready for feature enhancements
- Focus on UX improvements

**Feature Value**:
- HIGH value for users (simpler 95% case)
- LOW risk (conservative approach)
- MEDIUM effort (3.5-5.5 hours)
- NO breaking changes (backward compatible)

**Strategic Fit**:
- Improves user experience (less typing, fewer errors)
- Maintains safety (explicit control when needed)
- Demonstrates quality (comprehensive testing)
- Sets pattern for future enhancements

### Lessons Applied

Based on previous project experiences (per STATUS-2025-10-30):

**Avoid**:
- Assuming tests passing = feature working (mandate manual testing)
- Skipping documentation updates (include in feature work)
- Dismissing edge cases (handle multi-scope correctly)
- Leaving test gaps (comprehensive coverage required)

**Do**:
- Manual testing is critical (P0-8 is not optional)
- Comprehensive test coverage (unit + integration)
- Clear, actionable error messages
- Documentation accuracy (test examples)

**Quality Gates**:
- All existing tests must pass
- All new tests must pass
- Manual verification required
- Documentation examples tested

---

## Artifacts

### Created
- ✓ BACKLOG-RESCOPE-AUTO-DETECT-2025-11-05.md (complete implementation plan)
- ✓ BACKLOG.md (updated to reference new plan)
- ✓ PLANNING-SUMMARY-2025-11-05.md (this file)

### Referenced
- STATUS-2025-10-30-062049.md (current state)
- RESCOPE-AUTO-DETECT-EVALUATION.md (evaluation basis)
- CLAUDE.md (project patterns)

### To Archive
The following files are superseded by the new planning or relate to completed/resolved work:
- PLAN-2025-10-30-062544.md (emergency plan - issues resolved)
- BUG-FIX-PLAN-ENABLE-DISABLE.md (bugs fixed per commit history)
- PLANNING-SUMMARY-ENABLE-DISABLE-BUGS.md (related to fixed bugs)
- SUMMARY-ENABLE-DISABLE-PLANNING.md (related to fixed bugs)
- PLANNING-CLEANUP-2025-10-28.md (superseded by current planning)
- PLANNING-SUMMARY-2025-10-30.md (superseded by this summary)
- RELEASE-PLAN-1.0.md (old release plan)
- RELEASE-PLAN-1.0-UPDATED.md (old release plan)

**Note**: Per project guidelines, only keep the 4 most recent files per prefix (PLAN, BACKLOG, SPRINT). Currently have:
- BACKLOG.md (index, keep)
- BACKLOG-RESCOPE-AUTO-DETECT-2025-11-05.md (active feature plan, keep)

Older planning files should be moved to archive/ with .archived suffix to prevent confusion.

---

## Confidence Assessment

**Implementation Confidence**: 85%
- Well-understood problem (clear requirements)
- Existing code patterns to follow (rescope command, helper methods)
- Conservative approach (low risk)
- Comprehensive test strategy

**Timeline Confidence**: 80%
- 3.5-5.5 hour estimate is realistic
- Some unknowns in test updates (P0-6)
- Manual testing may reveal edge cases
- Buffer included in estimate range

**Quality Confidence**: 90%
- Comprehensive acceptance criteria (70+ testable requirements)
- Strong testing strategy (6+ new tests)
- Backward compatibility preserved
- Clear error handling

**Overall Project Health**: GOOD
- CLI functional and stable
- Team ready for feature work
- Clear requirements and evaluation
- Low-risk, high-value enhancement

---

**Planning Complete**: Ready to proceed with implementation
**Recommended Start**: P0-1 (add find_all_server_scopes method)
**Estimated Completion**: 3.5-5.5 hours from start
