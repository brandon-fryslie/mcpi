# claudew - Claude Code Autonomous Agent System

An autonomous and self-correcting agentic loop system for Claude Code, implemented through structured markdown files and shell scripts that enable Claude to operate with minimal human intervention.

## Objective

Transform Claude Code from a reactive assistant into a proactive, autonomous development agent capable of planning, implementing, testing, refactoring, and self-correcting through structured workflows. The system uses markdown files as "programs" that define agent behavior patterns and decision-making processes.

## Target Audience

- Solo developers seeking autonomous AI development assistance
- Development teams wanting consistent AI-driven workflows
- Coworkers and GitHub community interested in AI agent orchestration

## Core Functionality

### Autonomous Loop Cycle
1. **Plan** → Select highest-priority tasks from backlog
2. **Implement** → Execute selected tasks with minimal supervision  
3. **Test** → Run tests, identify and fix regressions automatically
4. **Refactor** → Simplify code, improve tests, reduce complexity
5. **Validate UX** → Ensure intuitive user flows and documentation
6. **Track** → Update project status and repository milestones

### Self-Correction Mechanisms
- **Test & Stability Monitoring** → Automatic failure detection and resolution
- **Dead-Code Detection** → Identify and remove deprecated components
- **Documentation Drift Detection** → Keep docs synchronized with implementation
- **Architectural Integrity Tests** → Maintain defined system boundaries
- **Priority Escalation** → Automatically elevate stuck tasks

### Agent Behavior Programming
- Markdown files define agent decision trees and workflows
- Structured project management with TODO/BACKLOG/STATUS tracking
- Requirements analysis protocols to prevent misalignment
- Quality gates and completion criteria

## Implementation

### Architecture
- **Shell Scripts** → Setup, execution, and integration helpers
- **Markdown Programs** → Agent behavior definitions and workflows
- **Project Templates** → Structured directories for multi-project management
- **Configuration System** → Adaptive settings and preferences

### Core Components
- `CLAUDE.md` → Primary agent instruction set and workflow definitions
- `PROJECT_SETUP.md` → Interactive wizard for new project initialization  
- `.agent_projects/` → Multi-project workspace management
- Agent command files → Specialized behaviors for different phases
- Setup scripts → Easy installation and configuration

### Project Management Structure
- Repository-level coordination (PROJECT.md, BACKLOG.md, PROGRESS.md)
- Feature-level organization (individual project directories)
- Cross-project milestone tracking and stability metrics
- Automated task generation from signals (test failures, code analysis)

## Distribution

**Primary**: GitHub repository with setup scripts
**Secondary**: Word-of-mouth introduction to coworkers and development community

### Installation Process
1. Clone repository to local development environment
2. Run setup script to configure Claude Code integration
3. Initialize project wizard for repository-specific setup
4. Begin autonomous development cycles

## Development Approach

### Philosophy
- Markdown as executable agent programs
- Self-modifying workflows based on project feedback
- Minimal human intervention after initial setup
- Quality-first automation with built-in safety nets

### Success Metrics
- Reduction in manual task management overhead
- Improved code quality through systematic refactoring
- Faster development cycles with maintained stability
- Effective cross-project knowledge transfer
