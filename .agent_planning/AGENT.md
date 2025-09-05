# AGENT.md

## Setup Detection
**PRIORITY CHECK**: If `setup/project-setup.md` exists, IMMEDIATELY run the project setup wizard. Do not proceed until complete.

## Autonomous Main Loop
Repeat until `projects/<active-project>/TODO.md` is empty:

1. **Plan** → `/project-plan-next-step` selects highest-priority backlog task
2. **Implement** → `/project-implement-item` implements selected task  
3. **Test** → `/project-retest` runs tests, identifies and fixes regressions
4. **Refactor** → `/project-refactor` simplifies code, improves tests, reduces complexity
5. **Validate UX** → `/project-validate-ux` ensures intuitive documented user flows
6. **Track** → `/project-status` updates project STATUS.md and repository-level milestones

**Stabilization Mode**: If stability KPI falls below threshold, prioritize regression fixes, test failures, and complexity reduction.

## Requirements Analysis Protocol
**CRITICAL**: Before implementing any feature request, ALWAYS check for conflict patterns:

### Conflict Detection Patterns
- **Existing vs. Specified**: User says "implement [feature]" but component already exists with different architecture
- **General vs. Specific**: Requirements mix vague language ("make functional") with detailed technical specs  
- **Technology Stack Mismatches**: Existing code uses different tech stack than specifications require

### Mandatory Clarification Process
When conflicts detected, MUST ask:
```
I see [specific conflict]. Before implementing, I need to clarify:

Option A: Enhance existing [component] with [current approach]
Option B: Replace with [specified requirements approach]

Which approach should I take?

Also, should I use existing [current tech] OR specified [required tech]?
```

### Implementation Rules
1. **Specifications are AUTHORITATIVE** - implement exactly as written
2. **Don't rationalize alternatives** - follow specs even if existing seems "better"  
3. **Don't add enhancements** during initial implementation
4. **Match ALL specified technologies** - don't substitute

### Implementation Sequence
1. **Minimal Viable Specification**: Build exactly what's specified, nothing more
2. **Validation**: Confirm with user that basic spec is met
3. **Enhancement**: Only add features if explicitly requested

## File Management Protocol

Definitions:
- project: the entire big picture work product you want out of the code in this repo
- initiative: a smaller, lower level project that could be thought of as a feature or chunk of work with a definite outcome

### Repository-Level Files (`.agent_planning/<files>`)
- `PROJECT.md`: High-level architecture, goals, dependencies for the repo-wide project
- `BACKLOG.md`: Project roadmap (names/descriptions only)
- `TODO.md`: Active TODO list  
- `PROGRESS.md`: Cross-project milestones, stability metrics, architectural health
- `DEPRECATED.md`: Auto-updated list of deprecated components

### Initiative-Level Files (`.agent_planning/initiatives/<initiative name>`)
- `PROJECT.md`: Goals, features, requirements for single project
- `BACKLOG.md`: Story backlog
- `TODO.md`: Task backlog
- `STATUS.md`: Completion log, notes, test results, complexity metrics
- `RFCs.md`: Architectural designs for future reference (updated when work completed)

**File Access Rules**:
- Read `PROJECT.md` when understanding project requirements
- Read `PROGRESS.md` when determining what's implemented
- Read `BACKLOG.md` when planning or when TODO is empty
- Read `TODO.md` when finding next task
- Update files only as described or when explicitly asked
- Create missing files as needed

## Priority Escalation & Monitoring

### Automated Signal Collection
- **Test & Stability**: Run pytest suite, log failures, flag recurring issues
- **Dead-Code Detection**: Detect unused/deprecated code, update DEPRECATED.md
- **Documentation Drift**: Detect doc/implementation mismatches
- **UX Monitoring**: Analyze usage/error logs, flag underused/confusing features
- **Architectural Integrity**: Verify defined architectural boundaries

### Escalation Rules  
- Tasks failing ≥3 cycles escalate to high priority
- Stabilization Mode triggered by KPI thresholds:
  - Test pass rate < 95%
  - UX violations detected  
  - Complexity trends negatively

## Quality Standards

### Testing Requirements
- All code thoroughly tested with meaningful, non-trivial tests
- Mocks must not make tests tautologically true - test real behavior
- Use pytest with parameterization and fixtures
- Integration tests test real component interactions
- Unit tests test individual components with minimal mocking
- Tests required for all new functionality before completion
- See `TESTING.md` for execution instructions

### Code Quality Rules
- Fix all compiler warnings before completing tasks
- Use testability to guide abstractions and implementation design
- Prioritize simplicity, logical abstractions, code reuse, best practices
- Ensure modularity and robust error handling
- Follow `templates/conventions.md` for coding standards

### Simulated Functionality Rule
- Placeholder functionality permitted for scaffolding only
- Work NOT complete until ALL simulated functionality replaced with actual implementations
- Comments like "Simulated", "Placeholder", "TODO: implement" indicate incomplete work
- Production-ready means NO simulated functionality

### Fake Demo Data Prohibition
**NEVER create fake demo data for production features:**
- ❌ Prohibited: Fake sample logs, mock API responses, dummy data arrays, setTimeout fake data
- ✅ Required: Use actual application data sources, integrate with existing APIs, show proper empty states

**Implementation Process:**
1. Identify real data source first
2. If data source doesn't exist, create it properly  
3. Connect to actual backend APIs or application state
4. Show appropriate loading/empty states for real scenarios

## Environment Management

### Python Environment
- Always use `uv` for virtual environments and dependency management
- Always activate venv

### Post-Completion Cleanup
- Clean up low-level details after work completion
- Save important info in RFCs.md and summary in STATUS.md  
- Update DEPRECATED.md with unused components
- Ensure all documentation reflects current implementation

## User Communication Guidelines

### When User Says "Make X Functional"
```
I see X exists but isn't working as expected. To help me understand:
- Should I enhance the existing X approach?
- Or do you have specific requirements for how X should work?
- Are there any technical constraints (positioning, technologies, etc.)?
```

### When User Provides Detailed Specs
```
I see detailed technical specifications. To confirm:
- These specifications should be followed exactly?
- Should I replace any existing similar functionality?
- Are the specified technologies (CSS framework, libraries) required?
```

### Red Flags for User Intent Mismatches
- User says "make functional" but existing code is partially functional
- User provides detailed specs but doesn't explicitly say "replace existing"
- User asks for "refinement" but specs describe completely different architecture
- User doesn't mention existing code when requesting features

**Response**: Explicitly surface the potential mismatch rather than making assumptions.

### Debugging Communication Failures
When user says implementation is wrong, immediately check:
1. Did I follow specifications exactly? (Most common failure)
2. Did I ask clarifying questions when conflicts were detected?
3. Did I assume enhancements were wanted?
4. Did I substitute technologies without permission?
5. Did I prioritize existing code over specifications?

**Recovery Process**: Acknowledge mismatch, explain wrong choice, offer correct solution, update AGENT.md with lessons learned.

**Reinforcement**: When ever a user says I did something very well, analyze what they mean to understand what behavior resulted in the positive outcome. Confirm with them to make sure it is correct, then update AGENT.md with the positive behavior. 
