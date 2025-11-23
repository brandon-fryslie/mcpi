# Sprint Plan - CLI Integration for Template Discovery v0.6.0

**Generated**: 2025-11-18-145319
**Source**: PLAN-CLI-INTEGRATION-v0.6.0-2025-11-18-145319.md
**Sprint Duration**: 2-3 days (10 hours)
**Sprint Goal**: Ship v0.6.0 with complete CLI integration for template recommendations

---

## Sprint Overview

**Context**: Template Discovery Engine library is production-ready (19/19 tests passing, 91% coverage). This sprint delivers the final piece: CLI integration to make intelligent template recommendations accessible to end users.

**Objective**: Enable users to run `mcpi add <server> --recommend` and get AI-powered template suggestions based on their project context.

**Success Criteria**:
- All 3 CLI tasks complete (P1-1, P1-2, P1-3)
- All 5 manual verification scenarios pass
- Documentation updated
- v0.6.0 ready to ship

---

## Sprint Backlog

### Day 1: Detection Integration (4 hours)

#### Task P1-1: Add --recommend Flag and Wire Up Discovery Engine
**Priority**: P1 (Critical)
**Effort**: 3-4 hours
**Status**: Not Started

**Subtasks**:
1. [ ] Add `--recommend` boolean flag to `mcpi add` command
   - Update @click.option decorators in cli.py
   - Add flag to function signature
   - Estimated: 15 minutes

2. [ ] Implement project detection logic
   - Get current working directory as project_path
   - Import ProjectDetector from mcpi.templates.discovery
   - Call detector.detect(project_path)
   - Store ProjectContext result
   - Estimated: 30 minutes

3. [ ] Implement template recommendation logic
   - Import TemplateRecommender from mcpi.templates.recommender
   - Create recommender with TemplateManager
   - Call recommender.recommend(server_id, project_path, top_n=3)
   - Store recommendations list
   - Estimated: 30 minutes

4. [ ] Add error handling and fallback logic
   - Wrap detection in try/except (handle file I/O errors)
   - Wrap recommendation in try/except (handle model errors)
   - Log warnings on errors
   - Fall back to manual config if errors occur
   - Estimated: 30 minutes

5. [ ] Add empty recommendations handling
   - Check if recommendations list is empty
   - Show helpful message if no recommendations
   - Continue to manual config or list-templates
   - Estimated: 15 minutes

6. [ ] Manual testing
   - Test with docker project (postgres service)
   - Test with empty project
   - Test error scenarios
   - Fix any issues found
   - Estimated: 1 hour

**Exit Criteria**:
- --recommend flag works without crashing
- Detection returns ProjectContext
- Recommendations returns list of TemplateRecommendation objects
- Errors handled gracefully
- Ready for display logic (P1-2)

**Blockers**: NONE

---

### Day 2: Rich Display Implementation (4 hours)

#### Task P1-2: Implement Rich Display for Recommendations
**Priority**: P1 (Critical)
**Effort**: 3-4 hours
**Status**: Not Started
**Dependencies**: P1-1 (needs recommendations data)

**Subtasks**:
1. [ ] Create display function
   - Function signature: `display_template_recommendations(context, recommendations, server_id)`
   - Location: src/mcpi/cli.py or new src/mcpi/cli_display.py
   - Estimated: 15 minutes

2. [ ] Implement context summary display
   - Show "Analyzing project context..." header
   - Display detected features with checkmarks:
     - "✓ Detected: Docker Compose project"
     - "✓ Found service: postgres"
     - "✓ Language: Node.js"
     - "✓ Database: postgres"
   - Use Rich Text with colors
   - Estimated: 45 minutes

3. [ ] Implement recommendations table
   - Create Rich Table with columns:
     - Template name (cyan)
     - Confidence (green/yellow/white based on %)
     - Explanation (bulleted reasons)
   - Format confidence as percentage (0.95 → "95%")
   - Add color coding: ≥80% green, ≥60% yellow, <60% white
   - Show top 3 recommendations
   - Estimated: 1.5 hours

4. [ ] Add visual enhancements
   - Mark top recommendation with "★" or bold
   - Format explanation bullets (• prefix, one per line)
   - Truncate long explanations to fit table
   - Add table title: "Recommended templates for 'postgres'"
   - Estimated: 30 minutes

5. [ ] Add empty state handling
   - Display message if no recommendations
   - Suggest --list-templates as alternative
   - Estimated: 15 minutes

6. [ ] Manual testing and refinement
   - Test with real terminal (check colors, alignment)
   - Test with different terminal widths
   - Refine table layout for readability
   - Fix any formatting issues
   - Estimated: 45 minutes

**Exit Criteria**:
- Context summary displays clearly
- Recommendations table renders correctly
- Colors and formatting professional
- Empty state handled gracefully
- Ready for interactive selection (P1-3)

**Blockers**: NONE (P1-1 must be complete)

---

### Day 3: Interactive Selection + Ship (3 hours)

#### Task P1-3: Add Interactive Template Selection Flow
**Priority**: P1 (Critical)
**Effort**: 2-3 hours
**Status**: Not Started
**Dependencies**: P1-2 (needs display)

**Subtasks**:
1. [ ] Implement selection prompt
   - Use Rich Prompt.ask() or input()
   - Show numbered options:
     - 1) template1 (recommended)
     - 2) template2
     - 3) template3
     - 4) Skip recommendation, configure manually
   - Set default to "1" (top recommendation)
   - Estimated: 30 minutes

2. [ ] Add input validation
   - Validate numeric choice (1 to N+1)
   - Accept empty input (use default)
   - Reject invalid input (show error, re-prompt)
   - Handle Ctrl+C gracefully
   - Estimated: 30 minutes

3. [ ] Wire up template selection flow
   - Map choice number to TemplateRecommendation object
   - Extract template from recommendation
   - REUSE existing --template flow:
     - Call collect_template_values(template_obj)
     - Call apply_template(template_obj, user_values)
     - Add server with configuration
   - Use template's scope if --scope not provided
   - Estimated: 45 minutes

4. [ ] Wire up skip flow
   - If user selects "Skip" option
   - Continue to manual config (existing add flow)
   - Add server without template
   - Estimated: 15 minutes

5. [ ] End-to-end testing (all 5 scenarios)
   - Scenario 1: Docker Compose + postgres
   - Scenario 2: Node.js project (no Docker)
   - Scenario 3: Empty project
   - Scenario 4: Server with no templates
   - Scenario 5: User skips recommendation
   - Document results, fix issues
   - Estimated: 1 hour

**Exit Criteria**:
- Selection prompt works correctly
- Selected template applies successfully
- Skip option works (manual config)
- All 5 scenarios pass
- No crashes or errors

**Blockers**: NONE (P1-2 must be complete)

---

### Day 3: Documentation + Ship (1 hour)

#### Task: Update Documentation and Ship v0.6.0
**Priority**: P1 (Critical)
**Effort**: 1 hour
**Status**: Not Started
**Dependencies**: All P1 tasks complete

**Subtasks**:
1. [ ] Update CLAUDE.md
   - Add "Template Discovery Engine (v0.6.0+)" subsection
   - Document detection algorithm
   - Document scoring algorithm
   - Add CLI usage examples
   - Add template metadata explanation
   - Estimated: 30 minutes

2. [ ] Final smoke test
   - Run all 5 scenarios one more time
   - Verify no regressions in existing tests
   - Check for uncommitted changes
   - Estimated: 15 minutes

3. [ ] Ship preparation
   - Commit all changes
   - Tag v0.6.0
   - Push to remote
   - Estimated: 15 minutes

**Exit Criteria**:
- Documentation complete and accurate
- All code committed
- v0.6.0 tagged
- Ready to announce

**Blockers**: NONE (all tasks must be complete)

---

## Daily Goals

### Day 1 End State
- [ ] --recommend flag functional
- [ ] Detection and recommendation working
- [ ] Error handling in place
- [ ] Ready for display work

### Day 2 End State
- [ ] Beautiful Rich display working
- [ ] Context summary clear
- [ ] Recommendations table formatted well
- [ ] Ready for interactive selection

### Day 3 End State
- [ ] Interactive selection working
- [ ] All 5 scenarios passing
- [ ] Documentation updated
- [ ] v0.6.0 shipped

---

## Testing Plan

### Manual Verification (Required)

**Test Environment Setup**:
```bash
# Create test projects
mkdir -p ~/test-mcpi-v060/{docker-app,node-app,empty-app}

# Docker project with postgres
cd ~/test-mcpi-v060/docker-app
cat > docker-compose.yml <<EOF
services:
  postgres:
    image: postgres:15
EOF

# Node.js project
cd ~/test-mcpi-v060/node-app
echo '{"name": "test-app"}' > package.json

# Empty project
cd ~/test-mcpi-v060/empty-app
# (leave empty)
```

**Scenario 1: Docker + Postgres** (Must Pass)
```bash
cd ~/test-mcpi-v060/docker-app
mcpi add postgres --recommend

# Expected:
# - Shows "Analyzing project context..."
# - Shows "✓ Detected: Docker Compose"
# - Shows "✓ Found service: postgres"
# - Table shows "docker" template with 90%+ confidence
# - Interactive prompt appears
# - Selecting template works
# - Server added successfully
```

**Scenario 2: Node.js Project** (Must Pass)
```bash
cd ~/test-mcpi-v060/node-app
mcpi add postgres --recommend

# Expected:
# - Shows "✓ Detected: Node.js"
# - Table shows "local-development" template recommended
# - Docker template shown with lower confidence (penalty)
# - Interactive prompt appears
# - Selecting template works
```

**Scenario 3: Empty Project** (Must Pass)
```bash
cd ~/test-mcpi-v060/empty-app
mcpi add postgres --recommend

# Expected:
# - Shows no strong detections OR baseline detections only
# - Shows message about low confidence OR all templates equal weight
# - Provides fallback option (list templates or manual config)
```

**Scenario 4: No Templates Available** (Must Pass)
```bash
cd ~/test-mcpi-v060/docker-app
mcpi add some-server-without-templates --recommend

# Expected:
# - Shows message: "No templates available for 'some-server-without-templates'"
# - Falls back to normal add flow (manual config)
# - No crash or error
```

**Scenario 5: User Skips** (Must Pass)
```bash
cd ~/test-mcpi-v060/docker-app
mcpi add postgres --recommend
# Select: 4 (Skip recommendation, configure manually)

# Expected:
# - Proceeds to manual configuration prompts
# - No template applied
# - Server added with default config
```

### Automated Testing (Optional)

If time permits, add CLI integration tests:
- Test file: `tests/test_cli_recommend_integration.py`
- Mock ProjectDetector and TemplateRecommender
- Mock user input for selection prompt
- Verify display function called
- Priority: LOW (manual testing sufficient)

---

## Definition of Done

### Code Complete Checklist
- [ ] P1-1: --recommend flag implemented and working
- [ ] P1-2: Rich display rendering correctly
- [ ] P1-3: Interactive selection functional
- [ ] Error handling robust (no crashes)
- [ ] Code formatted (black, ruff)
- [ ] No debug print statements

### Testing Complete Checklist
- [ ] All 5 manual scenarios pass
- [ ] No regressions in existing CLI tests
- [ ] Library tests still passing (19/19)
- [ ] Overall test pass rate ≥92%

### Documentation Complete Checklist
- [ ] CLAUDE.md updated with v0.6.0 section
- [ ] Usage examples included
- [ ] Architecture documented
- [ ] All changes committed

### Ship Checklist
- [ ] All of the above complete
- [ ] Clean git state
- [ ] Version bumped to v0.6.0 (if needed)
- [ ] Tagged v0.6.0
- [ ] Pushed to remote

---

## Risk Management

### High Priority Risks

**Risk 1: Rich Display Formatting Issues**
- **Probability**: MEDIUM
- **Impact**: LOW (cosmetic)
- **Mitigation**: Test in real terminal early, iterate on layout
- **Owner**: Developer
- **Status**: Monitoring

**Risk 2: Integration with Existing Template Flow**
- **Probability**: LOW
- **Impact**: MEDIUM (could break existing functionality)
- **Mitigation**: Reuse existing code as-is, add minimal new logic, run full test suite
- **Owner**: Developer
- **Status**: Monitoring

### Medium Priority Risks

**Risk 3: User Input Validation Edge Cases**
- **Probability**: LOW
- **Impact**: MEDIUM (poor UX)
- **Mitigation**: Comprehensive validation, clear error messages, test edge cases
- **Owner**: Developer
- **Status**: Monitoring

**Risk 4: Performance Degradation**
- **Probability**: LOW
- **Impact**: LOW (detection already fast)
- **Mitigation**: Detection already <100ms, CLI overhead minimal
- **Owner**: Developer
- **Status**: Monitoring

---

## Communication Plan

### Daily Updates
- End of Day 1: Share status (P1-1 complete or issues)
- End of Day 2: Share display screenshots/demo
- End of Day 3: Share ship notification

### Blockers Escalation
- If any task takes >2x estimated time → escalate immediately
- If test scenarios fail repeatedly → escalate for help
- If integration issues with existing code → escalate to architect

---

## Success Metrics

### Sprint Success
- [ ] All 3 P1 tasks complete
- [ ] All 5 scenarios pass
- [ ] v0.6.0 shipped on time (by 2025-11-21)

### Feature Success (Post-Ship)
- User adoption: Track % using --recommend flag (target 40%+)
- Acceptance rate: Track % accepting top recommendation (target 85%+)
- User feedback: Monitor GitHub issues for bugs/improvements
- Time savings: Measure template selection time (target <10s vs ~45s)

---

## References

### Planning Documents
- **Implementation Plan**: PLAN-CLI-INTEGRATION-v0.6.0-2025-11-18-145319.md
- **Source STATUS**: STATUS-TEMPLATE-DISCOVERY-IMPLEMENTATION-EVALUATION-2025-11-18.md

### Code References
- **CLI Code**: src/mcpi/cli.py (add command, line 1157+)
- **Library Code**: src/mcpi/templates/discovery.py, recommender.py
- **Existing Template Flow**: src/mcpi/cli.py (lines 1226-1256)

### Test References
- **Library Tests**: tests/test_template_discovery_functional.py (19 tests passing)
- **Manual Test Projects**: ~/test-mcpi-v060/

---

**Sprint Start**: 2025-11-18
**Sprint End**: 2025-11-20 or 2025-11-21
**Sprint Goal**: Ship v0.6.0 with CLI integration
**First Task**: P1-1 (Add --recommend flag)
**Status**: Ready to Start
