# Post-v0.5.0 Feature Proposals: Building on Configuration Templates

**Generated**: 2025-11-17
**Context**: v0.5.0 Configuration Templates SHIPPED (12 templates, 87% time savings, 100% test pass rate)
**Approach**: Product Visionary - Steve Jobs meets Alan Kay meets pragmatic engineering
**Status**: PROPOSAL - Ready for evaluation

---

## Executive Summary

MCPI v0.5.0 just shipped Configuration Templates, achieving an 87% reduction in server setup time and proving that guided interaction transforms user experience. This breakthrough creates the perfect foundation for three NEW high-impact features that compound this success.

**What v0.5.0 Proved**:
- Users LOVE guided setup (12 templates already, more requested)
- Interactive prompts eliminate documentation hunting
- Validation prevents configuration errors
- Templates are easy to author and extend

**The Opportunity**:
Now that we've solved "how do I configure ONE server easily," we can tackle the next tier of problems:
1. How do I discover the RIGHT templates for my needs?
2. How do I test my configuration BEFORE I commit to it?
3. How do I share my perfect setup with my team?

**Core Philosophy Applied**:
- Build on proven success (templates work, double down)
- Solve problems users can't articulate yet
- Make the complex feel effortless
- Each feature enables the next

---

## Deep Analysis: What Did v0.5.0 Teach Us?

### User Behavior Insights

**From the template work, we learned**:
1. Users don't want to read documentation - they want to DO
2. Validation feedback loops create confidence
3. Smart defaults eliminate decisions
4. Success on first try creates delight
5. Templates serve as living documentation

### Architectural Strengths to Leverage

**What worked brilliantly**:
- YAML template format (human-readable, git-friendly, easy to author)
- Prompt types (string, secret, path, port, url) cover 95% of use cases
- Priority system organizes choices without overwhelming
- Factory pattern makes testing trivial
- DIP compliance enables confident refactoring

### Gaps That Became Visible

**What users STILL struggle with**:
1. **Discovery**: "Which template should I use?" (12 templates, growing to 50+)
2. **Confidence**: "Will this actually work before I install it?"
3. **Iteration**: "I want to try different configs without breaking what works"
4. **Sharing**: "How do I give this exact setup to my teammate?"
5. **Learning**: "Why did you suggest THIS template for MY project?"

---

## Brainstorming: 10 Ideas Explored

### Category: Enhance Template Discovery
1. **Template Recommendation Engine** - Smart suggestions based on project context
2. **Template Search with Fuzzy Matching** - "postgre" finds "postgres-local-development"
3. **Template Comparison Tool** - Show differences between similar templates side-by-side

### Category: Build Confidence Before Installation
4. **Template Test Drive** - Dry-run with validation but no installation
5. **Template Preview** - See exactly what will be configured before committing
6. **Template Validation** - Check if your inputs would work (test DB connection, API key, etc.)

### Category: Enable Iteration and Experimentation
7. **Template Variants** - Start from template, save customization as new template
8. **Configuration Rollback** - "Undo last template installation"
9. **Template Diff** - Compare current config vs template's expected config

### Category: Team Collaboration
10. **Template Packages** - Bundle multiple templates together ("full-stack-dev" = postgres + github + filesystem)

---

## Filtering: Rigorous Evaluation

### Why Most Ideas Were Rejected

**Rejected for Overlap with Existing Proposals**:
- **Template Search**: Basic search already exists, fuzzy matching is incremental
- **Template Comparison**: Niche use case, premature optimization
- **Configuration Rollback**: Subset of snapshot functionality (from v0.4.0 proposals)
- **Template Diff**: Implementation complexity high, value medium

**Rejected for Insufficient User Pain**:
- **Template Variants**: Users can already copy YAML files
- **Template Validation**: Overlap with Test Drive feature

**Rejected for Architectural Concerns**:
- None! All ideas fit the architecture, but some don't justify the effort

### Advanced to Detailed Analysis

Three features survived rigorous filtering:

1. **Template Recommendation Engine** ✓ - Solves "which template?" problem at scale
2. **Template Test Drive** ✓ - De-risks experimentation, enables learning
3. **Template Packages (Reimagined as "Workflows")** ✓ - Teams + discovery + best practices

---

## FEATURE 1: Template Discovery Agent

### One-Liner
Stop asking "which template should I use?" - MCPI analyzes your project and suggests the perfect template with explanation.

### The Problem Users Feel But Don't Articulate

**Current state** (12 templates, soon to be 50+):
```bash
$ mcpi add postgres --list-templates

Available templates for postgres:
1. local-development - PostgreSQL on localhost
2. docker - PostgreSQL in Docker container
3. production - Production-ready configuration

Which template? [1]:
```

**User's internal monologue**:
- "I don't know the difference between these..."
- "What do other people use?"
- "Is docker better than local?"
- "What if I pick wrong and waste time?"
- Picks randomly or defaults to #1
- May not be optimal for their actual setup

**The deeper problem**: Templates work great IF you know which one to pick. As we add more templates (redis, mysql, s3, etc.), choice paralysis grows exponentially.

### The Solution That Feels Obvious in Retrospect

Add `--recommend` flag that analyzes project context and suggests the best template:

```bash
$ mcpi add postgres --recommend

Analyzing your project...
  ✓ Detected Docker Compose in project root
  ✓ Found docker-compose.yml with postgres service
  ✓ Project type: Node.js application
  ✓ Environment: Development (not production)

Recommended Template: postgres/docker
───────────────────────────────────────

Why this template?
  • Your project already uses Docker Compose
  • The 'docker' template will connect to your existing postgres service
  • Easier than running postgres locally (matches your workflow)

What you'll configure:
  • Container name (default: postgres)
  • Database name (detected: myapp_dev from docker-compose.yml)
  • Port (default: 5432)

Alternative: postgres/local-development
  If you prefer postgres outside Docker

Continue with 'docker' template? [Y/n]:
```

**Even smarter** - auto-recommend without flag:
```bash
$ mcpi add postgres --template

🧠 Smart suggestion: postgres/docker
   (your project uses Docker Compose)

   1. docker - PostgreSQL in Docker container (recommended)
   2. local-development - PostgreSQL on localhost
   3. production - Production-ready configuration

Which template? [1]:
```

### Why This Creates User Delight

**The transformation**:
- **Before**: "Which template?" → Anxiety → Guess → Maybe wrong choice
- **After**: "Which template?" → "Here's what fits YOUR project and why"

**Key delight moments**:
1. **Project awareness**: "It knew I use Docker!"
2. **Explanatory power**: Not just recommendation, but WHY
3. **Confidence**: "This makes sense for my setup"
4. **Learning**: "I understand the tradeoffs now"
5. **Zero effort**: Works automatically, no setup needed

### Implementation Approach

**Week 1: Detection Heuristics (3-4 days)**
- Implement project analyzers:
  - Docker detector (docker-compose.yml, Dockerfile)
  - Language detector (package.json, requirements.txt, go.mod)
  - Database detector (existing configs, connection strings)
  - Environment detector (production indicators, .env files)
- Create scoring system for template matching
- Unit tests for each detector

**Week 2: Recommendation Engine (4-5 days)**
- Create `TemplateRecommender` class
- Implement template metadata enrichment (add "best_for" field to templates)
- Scoring algorithm: detector confidence × template fit score
- Explanation generator (why this template fits)
- Integration with existing `TemplateManager`

**Week 3: CLI Integration & Polish (3-4 days)**
- Add `--recommend` flag to `mcpi add`
- Update interactive template selection to show recommendations first
- Rich formatting for recommendations
- Tests (unit, integration, E2E)
- Documentation

**Architectural Integration**:
```python
# Minimal changes, extends existing template system

class TemplateMetadata(BaseModel):
    # Existing fields...
    best_for: List[str] = []  # ["docker", "development", "nodejs"]
    keywords: List[str] = []  # For fuzzy matching

class ProjectContext(BaseModel):
    """Detected project characteristics."""
    has_docker: bool = False
    has_docker_compose: bool = False
    language: Optional[str] = None
    databases: List[str] = []
    environment: str = "development"

class TemplateRecommender:
    """Recommends templates based on project context."""

    def detect_context(self, project_path: Path) -> ProjectContext:
        """Analyze project to determine context."""

    def recommend(
        self,
        server_id: str,
        context: ProjectContext
    ) -> List[Tuple[Template, float, str]]:
        """Returns (template, confidence_score, explanation)."""
```

**Data enhancement** (add to templates):
```yaml
# data/templates/postgres/docker.yaml
metadata:
  best_for:
    - docker
    - docker-compose
    - containers
  keywords:
    - docker
    - containerized
    - compose
```

**Implementation Complexity**: 2-3 weeks, LOW RISK

### Success Metrics

**Quantitative**:
- 70%+ of users with Docker projects pick docker template (vs 33% random)
- 40%+ users enable `--recommend` explicitly
- 85%+ users stick with recommended template (don't switch)
- Template selection time: 45 sec → 10 sec

**Qualitative**:
- "It knew my project uses Docker!"
- "The explanation helped me understand tradeoffs"
- "I trust MCPI's recommendations"

### What NOT to Do (Anti-Patterns)

- Don't require telemetry or external services (100% local detection)
- Don't make recommendations opaque ("trust me" vs "here's why")
- Don't recommend without explanation
- Don't force recommendations (always show all templates)
- Don't detect sensitive information (secrets, passwords)

---

## FEATURE 2: Template Test Drive

### One-Liner
Try before you buy - preview and validate template configurations without actually installing anything.

### The Problem Hiding in Plain Sight

**Current experience**:
```bash
$ mcpi add slack --template bot-token

Enter Slack Bot Token: xoxb-...
Enter Channel IDs (comma-separated): #general,#dev

✓ Installing slack to project-mcp scope
✓ Configuration saved to .mcp.json
✓ Server ready to use

# User reloads Claude Code
# Server fails to connect
# "Invalid channel ID" error
# Now have to remove and reinstall
```

**User frustration points**:
1. **No preview**: Can't see what will be configured before committing
2. **No validation**: Typos/mistakes only caught after installation
3. **Destructive**: Installation is all-or-nothing, can't test safely
4. **Learning curve**: Beginners afraid to experiment ("what if I break something?")
5. **Iteration friction**: Try config → install → test → remove → try again

**The invisible cost**: Users under-experiment, stick with defaults, never optimize their setup.

### The Solution That Opens Doors

Add `--dry-run` mode that validates and previews without installing:

```bash
$ mcpi add slack --template bot-token --dry-run

Slack MCP Server - Bot Token Template
═════════════════════════════════════

Configuration Preview (not installed yet)
──────────────────────────────────────

This will configure:
  Scope: project-mcp (.mcp.json)
  Command: npx -y @modelcontextprotocol/server-slack
  Environment variables:
    SLACK_BOT_TOKEN: xoxb-1234... (hidden)
    SLACK_CHANNEL_IDS: C123ABC,C456DEF

Validation
──────────
✓ Bot token format valid
✓ Testing Slack API connection...
✓ Connected as bot "MyApp Bot"
✓ Channel access verified:
  • #general (C123ABC) - ✓ readable/writable
  • #dev-team (C456DEF) - ✓ readable/writable
⚠ Warning: Bot lacks access to #private-channel
  Add bot to channel or remove from list

Setup Notes
───────────
• Bot needs 'chat:write' and 'channels:history' scopes
• Test with: @MyApp Bot help
• Update permissions: https://api.slack.com/apps/A123/oauth

───────────────────────────────────────────────────

Looks good? Install for real:
  mcpi add slack --template bot-token

Want to try different values:
  mcpi add slack --template bot-token --dry-run
```

**Even better** - make dry-run interactive:
```bash
$ mcpi add slack --template bot-token --interactive --dry-run

# Goes through full template prompts
# Validates each input in real-time
# Shows preview at end
# Offers to save for later OR install immediately

Preview looks good!

What would you like to do?
  1. Install now (saves to .mcp.json)
  2. Save as custom template (reuse later)
  3. Try different values (start over)
  4. Cancel

Choice [1]:
```

### Why This Changes Everything

**Current state**: Users fear experimentation (irreversible installations)
**Future state**: Users explore confidently (safe sandbox)

**The transformation**:
- **Beginners**: "I'm afraid to mess up" → "Let me try this and see what happens"
- **Experts**: "I'll just install and debug" → "Let me validate before committing"
- **Teams**: "Hope this works" → "Verified before sharing with team"

**Unexpected benefits**:
1. **Onboarding**: New users learn by experimenting safely
2. **Template authoring**: Test new templates without installation
3. **Troubleshooting**: "Does my config look right?"
4. **Documentation**: Dry-run output shows exactly what happens

### Implementation Approach

**Week 1: Validation Framework (4-5 days)**
- Create `TemplateValidator` class
- Implement validators for each prompt type:
  - `URLValidator` - actually fetch URL, check HTTP status
  - `PortValidator` - check if port is available/in use
  - `PathValidator` - check if path exists, is readable/writable
  - `SecretValidator` - format validation (API key patterns)
- Add optional `validate()` method to prompt types
- Unit tests for each validator

**Week 2: Preview System (3-4 days)**
- Create `ConfigurationPreview` class
- Generate preview from template + user inputs
- Show what will be written where
- Integration with validation results
- Rich formatting for preview output

**Week 3: CLI Integration (3-4 days)**
- Add `--dry-run` flag to `mcpi add`
- Interactive mode with dry-run
- Save preview as custom template feature
- Tests and documentation

**Architectural Integration**:
```python
# Extends existing prompt handler

class PromptValidator(Protocol):
    """Protocol for validating prompt values."""

    def validate(self, value: str) -> ValidationResult:
        """Returns (is_valid, message, details)."""

class URLValidator:
    def validate(self, value: str) -> ValidationResult:
        """Fetch URL, check 200 response."""
        try:
            response = requests.head(value, timeout=5)
            if response.status_code == 200:
                return ValidationResult(True, "URL accessible", None)
            else:
                return ValidationResult(
                    False,
                    f"URL returned {response.status_code}",
                    "Check URL or network connection"
                )
        except Exception as e:
            return ValidationResult(False, f"Cannot reach URL: {e}", None)

class ConfigurationPreview:
    """Shows what will be configured without installing."""

    def __init__(self, server_config: ServerConfig, scope: str):
        self.config = server_config
        self.scope = scope

    def generate(self) -> str:
        """Generate Rich-formatted preview."""

    def validate(self) -> List[ValidationResult]:
        """Run all validators on configuration."""
```

**Template enhancement**:
```yaml
# data/templates/slack/bot-token.yaml
prompts:
  - name: SLACK_BOT_TOKEN
    type: secret
    description: Slack Bot Token (starts with xoxb-)
    required: true
    validation:
      pattern: "^xoxb-[0-9]+-[0-9]+-[a-zA-Z0-9]+$"
      validator: slack_token  # Optional real API validation

  - name: SLACK_CHANNEL_IDS
    type: string
    description: Channel IDs (comma-separated)
    required: true
    validation:
      pattern: "^[A-Z0-9]+(,[A-Z0-9]+)*$"
      validator: slack_channels  # Check channel access
```

**Implementation Complexity**: 2-3 weeks, MEDIUM RISK (network validation can be fragile)

### Success Metrics

**Quantitative**:
- 50%+ of template installations use `--dry-run` first
- 80%+ reduction in "server won't start" issues
- 40%+ of dry-runs reveal problems before installation
- Template iteration time: 10 min → 2 min

**Qualitative**:
- "I tested 3 configurations before picking the right one"
- "Dry-run caught my typo before it broke anything"
- "I feel confident experimenting now"

### What NOT to Do (Anti-Patterns)

- Don't make every validation network-based (fallback to syntax checking)
- Don't fail dry-run on warnings (show warnings, allow proceed)
- Don't require external services for basic validation
- Don't make dry-run slow (timeout aggressively)
- Don't store validation results permanently (privacy)

---

## FEATURE 3: Template Workflows

### One-Liner
Bundle proven template combinations into one-command setups that install and configure entire workflows.

### The Problem Users Don't Know They Have

**Current reality** (v0.5.0):
```bash
# New team member joins
$ mcpi add postgres --template docker
# ... fill out postgres config ...

$ mcpi add github --template personal-full-access
# ... fill out github config ...

$ mcpi add filesystem --template project-files
# ... fill out filesystem config ...

$ mcpi add brave-search --template api-key
# ... fill out brave-search config ...

# 15-20 minutes total
# Easy to forget a server
# No guidance on which templates to combine
```

**Team lead's pain**:
- "Here's our standard setup" → Slack message with 10 steps
- New developer takes 30 min to set up
- Someone always forgets a server or picks wrong template
- Configuration drift (everyone's setup slightly different)

**The deeper problem**: Templates solved single-server setup, but real workflows need MULTIPLE servers configured correctly together.

### The Solution That Feels Like Magic

One command installs entire proven workflow:

```bash
$ mcpi workflow install full-stack-web-dev

Full-Stack Web Development Workflow
═══════════════════════════════════

This workflow installs 5 servers with recommended templates:

  1. PostgreSQL (docker template)
     → Database for your application

  2. GitHub (personal-full-access template)
     → Access repository code and history

  3. Filesystem (project-files template)
     → Read/write project files safely

  4. Brave Search (api-key template)
     → Search web for documentation/solutions

  5. Slack (bot-token template) - Optional
     → Send notifications to team channels

Setup will take ~5 minutes.
Continue? [Y/n]:

──────────────────────────────────────

Step 1 of 5: PostgreSQL
───────────────────────

Using 'docker' template (detected Docker Compose in project)

Database name: myapp_dev
Port [5432]: 5433

✓ Installed postgres to project-mcp

Step 2 of 5: GitHub
───────────────────

Using 'personal-full-access' template

GitHub Personal Access Token: ghp_...

✓ Validated token (expires 2026-06-15)
✓ Installed github to user-global

# ... continues through all 5 servers ...

──────────────────────────────────────

🎉 Workflow Complete!

Installed 5 servers:
  ✓ postgres (project-mcp)
  ✓ github (user-global)
  ✓ filesystem (project-mcp)
  ✓ brave-search (user-global)
  ✓ slack (project-mcp)

Next steps:
  1. Reload Claude Code to activate servers
  2. Try: "Show me recent commits to this repository"
  3. Try: "Query the users table from my database"

Save this workflow for teammates:
  mcpi workflow export full-stack-web-dev
```

**For teams** - share workflow configs:
```bash
# Team lead creates and shares
$ mcpi workflow export full-stack-web-dev > team-setup.yaml
# Send team-setup.yaml to team via Slack/email

# New developer uses it
$ mcpi workflow install team-setup.yaml
# Fills in their own secrets/paths
# Gets identical setup in 5 minutes
```

### Why This Is The Feature Users Tell Friends About

**The magic**:
- **One command** → Entire workflow configured
- **Proven combinations** → No guessing which servers work together
- **Smart ordering** → Dependencies installed first
- **Shareable** → Team standardization trivial
- **Customizable** → Each person uses their own secrets/paths
- **Discoverable** → `mcpi workflow list` shows curated workflows

**The use cases nobody explicitly asks for but desperately need**:
1. **Team onboarding**: New developer ready in 5 minutes
2. **Project types**: "I'm starting a Python data science project" → Perfect setup
3. **Learning**: "What do experienced developers use for web dev?"
4. **Standardization**: Entire team has identical setup
5. **Evolution**: Update workflow, team re-runs to sync

### Implementation Approach

**Week 1: Workflow Format & Engine (4-5 days)**
- Design workflow YAML schema
- Create `Workflow` Pydantic model
- Implement `WorkflowManager` class
- Built-in workflows: full-stack-web-dev, data-science, devops, api-development
- Template selection logic (per-server template overrides)

**Week 2: Installation Orchestration (4-5 days)**
- Sequential template installation
- Progress tracking and user feedback
- Error handling (partial success, rollback option)
- Scope resolution for each server
- Integration with existing template system

**Week 3: Sharing & CLI (4-5 days)**
- `mcpi workflow list/info/install` commands
- `mcpi workflow export` (shareable YAML)
- Variable substitution (team shares, individuals customize)
- Tests and documentation
- Create 4 curated workflows

**Architectural Integration**:
```yaml
# data/workflows/full-stack-web-dev.yaml
metadata:
  name: full-stack-web-dev
  description: Full-stack web application development
  author: MCPI Team
  tags: [web, database, git, search]

servers:
  - id: postgres
    template: docker  # Which template to use
    scope: project-mcp  # Where to install
    required: true
    description: Database for your application

  - id: github
    template: personal-full-access
    scope: user-global
    required: true
    description: Access repository code and history

  - id: filesystem
    template: project-files
    scope: project-mcp
    required: true
    description: Read/write project files

  - id: brave-search
    template: api-key
    scope: user-global
    required: true
    description: Search web for documentation

  - id: slack
    template: bot-token
    scope: project-mcp
    required: false  # Optional
    description: Send notifications to team

setup_notes: |
  This workflow gives you everything for modern web development:
  - Database access (postgres)
  - Code repository access (github)
  - File operations (filesystem)
  - Web search (brave-search)
  - Team notifications (slack, optional)

next_steps:
  - Reload Claude Code
  - Try: "Show me the database schema"
  - Try: "List recent commits to this repo"
```

**For team sharing** (variables):
```yaml
# team-setup.yaml (exported workflow)
metadata:
  name: acme-corp-web-dev
  description: Acme Corp standard web dev setup
  created_by: alice@acme.com
  created_at: 2025-11-17

# Same structure as built-in workflow
servers:
  - id: postgres
    template: docker
    scope: project-mcp
    # Template prompts will ask for values

variables:
  # Shared values (same for everyone)
  POSTGRES_PORT: "5432"

secrets:
  # Each person provides their own
  - GITHUB_TOKEN
  - SLACK_BOT_TOKEN
```

**Implementation Complexity**: 2-3 weeks, LOW-MEDIUM RISK

### Success Metrics

**Quantitative**:
- 30%+ of users install at least one workflow
- 80%+ of workflow installs complete successfully
- Average setup time for 5 servers: 25 min → 5 min
- 60%+ of teams share custom workflows

**Qualitative**:
- "This made onboarding our new developer trivial"
- "I use workflows to quickly set up new projects"
- "Everyone on the team has the same setup now"

### What NOT to Do (Anti-Patterns)

- Don't make workflows too opinionated (allow customization)
- Don't fail entire workflow if one server fails (offer partial + retry)
- Don't hardcode values in workflows (use variables/prompts)
- Don't create too many workflows (4-6 curated is enough)
- Don't make workflows immutable (allow editing before install)

---

## Feature Comparison & Prioritization

### Impact vs Effort Matrix

```
High Impact │
           │                  ┌─────────────┐
           │                  │ Workflows   │
           │  ┌──────────┐    │ (Feature 3) │
           │  │ Template │    └─────────────┘
           │  │ Discovery│
Medium     │  │(Feature1)│    ┌─────────────┐
Impact     │  └──────────┘    │ Test Drive  │
           │                  │ (Feature 2) │
           │                  └─────────────┘
           │
Low Impact │
           └────────────────────────────────────
              2 weeks    2.5 weeks   3 weeks
                      Effort
```

### Recommended Implementation Order

**Option A: Sequential (9 weeks total)**

**Phase 1 (Weeks 1-3): Template Discovery**
- **Why first**: Immediate value, leverages existing templates
- **Risk**: Low (pure recommendation, no writes)
- **Dependencies**: None
- **Value**: Makes growing template library navigable

**Phase 2 (Weeks 4-6): Template Test Drive**
- **Why second**: Complements discovery, enables experimentation
- **Risk**: Medium (network validation)
- **Dependencies**: None (but enhanced by discovery)
- **Value**: De-risks configuration, builds confidence

**Phase 3 (Weeks 7-9): Template Workflows**
- **Why third**: Builds on both previous features
- **Risk**: Low-Medium (orchestration complexity)
- **Dependencies**: Benefits from discovery + test drive
- **Value**: Team collaboration, complete solution

**Option B: Parallel (6 weeks total if 2 developers)**

**Track 1: Developer A**
- Weeks 1-3: Template Discovery
- Weeks 4-6: Template Workflows

**Track 2: Developer B**
- Weeks 1-3: Template Test Drive
- Weeks 4-6: Help with Workflows or polish

**Option C: MVP First (4-5 weeks)**

Pick the single highest-value feature:
- **If solo developer experience matters most**: Template Discovery
- **If team collaboration matters most**: Template Workflows
- **If confidence/learning matters most**: Template Test Drive

### Combined User Journey

**Week 1** (new MCPI user):
```bash
$ mcpi workflow install full-stack-web-dev
# Installs 5 servers in 5 minutes
# Each server uses recommended template (via discovery)
```

**Week 2** (adding more servers):
```bash
$ mcpi add redis --recommend
# Suggests redis/docker (detected Docker in project)
$ mcpi add redis --template docker --dry-run
# Previews and validates config
$ mcpi add redis --template docker
# Installs confidently
```

**Week 3** (sharing with team):
```bash
$ mcpi workflow export my-setup
# Creates shareable workflow
# Team members install identical setup
```

---

## Technical Implementation Details

### Feature 1: Template Discovery - Architecture

```python
# src/mcpi/templates/discovery.py

@dataclass
class ProjectContext:
    """Detected project characteristics."""
    root_path: Path
    has_docker: bool = False
    has_docker_compose: bool = False
    docker_services: List[str] = field(default_factory=list)
    language: Optional[str] = None  # python, nodejs, go, etc.
    frameworks: List[str] = field(default_factory=list)  # django, express, react
    databases: List[str] = field(default_factory=list)  # postgres, mysql, redis
    package_managers: List[str] = field(default_factory=list)  # npm, pip, go mod
    environment: str = "development"  # development, staging, production

class ProjectDetector:
    """Detects project characteristics."""

    def detect(self, project_path: Path) -> ProjectContext:
        """Analyze project to build context."""
        context = ProjectContext(root_path=project_path)

        # Docker detection
        if (project_path / "docker-compose.yml").exists():
            context.has_docker_compose = True
            context.docker_services = self._parse_docker_compose(project_path)

        if (project_path / "Dockerfile").exists():
            context.has_docker = True

        # Language detection
        if (project_path / "package.json").exists():
            context.language = "nodejs"
        elif (project_path / "requirements.txt").exists():
            context.language = "python"
        elif (project_path / "go.mod").exists():
            context.language = "go"

        # ... more detectors

        return context

@dataclass
class TemplateRecommendation:
    """A template recommendation with explanation."""
    template: Template
    confidence: float  # 0.0 to 1.0
    reasons: List[str]
    match_details: Dict[str, Any]

class TemplateRecommender:
    """Recommends templates based on project context."""

    def __init__(self, template_manager: TemplateManager):
        self.template_manager = template_manager
        self.detector = ProjectDetector()

    def recommend(
        self,
        server_id: str,
        project_path: Optional[Path] = None
    ) -> List[TemplateRecommendation]:
        """Returns ranked template recommendations."""

        # Detect project context
        context = self.detector.detect(project_path or Path.cwd())

        # Get all templates for server
        templates = self.template_manager.get_templates(server_id)

        # Score each template
        recommendations = []
        for template in templates:
            score, reasons = self._score_template(template, context)
            if score > 0.3:  # Minimum confidence threshold
                recommendations.append(
                    TemplateRecommendation(
                        template=template,
                        confidence=score,
                        reasons=reasons,
                        match_details=self._get_match_details(template, context)
                    )
                )

        # Sort by confidence (descending)
        recommendations.sort(key=lambda r: r.confidence, reverse=True)

        return recommendations

    def _score_template(
        self,
        template: Template,
        context: ProjectContext
    ) -> Tuple[float, List[str]]:
        """Score how well template matches context."""
        score = 0.0
        reasons = []

        # Check best_for tags
        if context.has_docker and "docker" in template.metadata.best_for:
            score += 0.4
            reasons.append("Project uses Docker")

        if context.language and context.language in template.metadata.best_for:
            score += 0.3
            reasons.append(f"Optimized for {context.language}")

        if context.environment in template.metadata.best_for:
            score += 0.2
            reasons.append(f"Designed for {context.environment}")

        # Bonus for docker-compose service match
        if context.has_docker_compose:
            service_match = self._check_docker_service_match(
                template, context.docker_services
            )
            if service_match:
                score += 0.5
                reasons.append(f"Matches docker-compose service: {service_match}")

        return min(score, 1.0), reasons
```

**Template metadata enhancement**:
```yaml
# data/templates/postgres/docker.yaml
metadata:
  name: docker
  description: PostgreSQL in Docker container
  priority: high
  best_for:
    - docker
    - docker-compose
    - containers
    - development
  keywords:
    - docker
    - containerized
    - compose

  # NEW: Recommendation hints
  recommendations:
    requires:
      - docker  # Only recommend if Docker detected
    bonus_for:
      - docker-compose  # Extra score if docker-compose present
    docker_service_match: postgres  # Match docker-compose service name
```

---

### Feature 2: Test Drive - Architecture

```python
# src/mcpi/templates/validation.py

@dataclass
class ValidationResult:
    """Result of validating a configuration value."""
    is_valid: bool
    message: str
    details: Optional[str] = None
    warnings: List[str] = field(default_factory=list)

class PromptValidator(Protocol):
    """Protocol for validating prompt values."""

    def validate(self, value: str, context: Dict[str, Any]) -> ValidationResult:
        """Validate a value and return result."""

class URLValidator:
    """Validates URLs by attempting to fetch them."""

    def validate(self, value: str, context: Dict[str, Any]) -> ValidationResult:
        if not value.startswith(("http://", "https://")):
            return ValidationResult(
                is_valid=False,
                message="URL must start with http:// or https://",
                details="Example: https://api.example.com"
            )

        try:
            response = requests.head(value, timeout=5, allow_redirects=True)
            if response.status_code < 400:
                return ValidationResult(
                    is_valid=True,
                    message=f"URL accessible (HTTP {response.status_code})"
                )
            else:
                return ValidationResult(
                    is_valid=False,
                    message=f"URL returned HTTP {response.status_code}",
                    details="Check URL or network connection"
                )
        except requests.Timeout:
            return ValidationResult(
                is_valid=False,
                message="URL request timed out",
                details="Check URL or network connection",
                warnings=["Network may be slow"]
            )
        except Exception as e:
            return ValidationResult(
                is_valid=False,
                message=f"Cannot reach URL: {str(e)}",
                details="Check URL format and network connection"
            )

class PortValidator:
    """Validates ports and checks availability."""

    def validate(self, value: str, context: Dict[str, Any]) -> ValidationResult:
        try:
            port = int(value)
        except ValueError:
            return ValidationResult(
                is_valid=False,
                message="Port must be a number",
                details="Valid range: 1-65535"
            )

        if not (1 <= port <= 65535):
            return ValidationResult(
                is_valid=False,
                message=f"Port {port} out of range",
                details="Valid range: 1-65535"
            )

        # Check if port is available
        import socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(('localhost', port))
                if result == 0:
                    return ValidationResult(
                        is_valid=True,
                        message=f"Port {port} is in use",
                        warnings=["Port already in use - make sure service is running"]
                    )
                else:
                    return ValidationResult(
                        is_valid=True,
                        message=f"Port {port} is available"
                    )
        except Exception:
            return ValidationResult(
                is_valid=True,
                message=f"Port {port} (availability check skipped)",
                warnings=["Could not check if port is in use"]
            )

class ConfigurationPreview:
    """Previews configuration before installation."""

    def __init__(
        self,
        server_id: str,
        template: Template,
        values: Dict[str, str],
        scope: str
    ):
        self.server_id = server_id
        self.template = template
        self.values = values
        self.scope = scope

    def generate(self) -> str:
        """Generate Rich-formatted preview."""
        from rich.console import Console
        from rich.panel import Panel
        from rich.table import Table

        console = Console()

        # Build server configuration
        config = self._build_config()

        # Create preview output
        output = []
        output.append(f"\n[bold]{self.server_id.title()} - {self.template.metadata.name} Template[/bold]")
        output.append("\n[bold cyan]Configuration Preview[/bold cyan]")
        output.append(f"\nScope: {self.scope}")
        output.append(f"Command: {config.command}")

        if config.args:
            output.append(f"Arguments: {' '.join(config.args)}")

        if config.env:
            output.append("\n[bold]Environment Variables:[/bold]")
            for key, value in config.env.items():
                if any(secret in key.lower() for secret in ['password', 'token', 'key', 'secret']):
                    display_value = "********"
                else:
                    display_value = value
                output.append(f"  {key}: {display_value}")

        return "\n".join(output)

    def validate(self) -> List[ValidationResult]:
        """Run validators on configuration."""
        results = []

        for prompt in self.template.prompts:
            value = self.values.get(prompt.name)
            if not value:
                continue

            # Get validator for prompt type
            validator = self._get_validator(prompt)
            if validator:
                result = validator.validate(value, self.values)
                results.append(result)

        return results
```

---

### Feature 3: Workflows - Architecture

```python
# src/mcpi/workflows/models.py

class WorkflowServer(BaseModel):
    """Server configuration within a workflow."""
    id: str  # Server ID (postgres, github, etc.)
    template: str  # Template name to use
    scope: str  # Installation scope
    required: bool = True  # Can user skip this?
    description: Optional[str] = None

    # Optional: Override template prompts
    prompt_overrides: Dict[str, str] = {}

class Workflow(BaseModel):
    """A workflow bundles multiple servers together."""
    metadata: WorkflowMetadata
    servers: List[WorkflowServer]
    setup_notes: Optional[str] = None
    next_steps: Optional[List[str]] = None

class WorkflowMetadata(BaseModel):
    """Workflow metadata."""
    name: str
    description: str
    author: str = "MCPI Team"
    tags: List[str] = []
    created_at: Optional[datetime] = None

# src/mcpi/workflows/manager.py

class WorkflowManager:
    """Manages workflow loading and installation."""

    def __init__(
        self,
        workflows_dir: Path,
        template_manager: TemplateManager,
        mcp_manager: MCPManager
    ):
        self.workflows_dir = workflows_dir
        self.template_manager = template_manager
        self.mcp_manager = mcp_manager

    def list_workflows(self) -> List[Workflow]:
        """List all available workflows."""
        workflows = []

        # Built-in workflows
        for yaml_file in self.workflows_dir.glob("*.yaml"):
            workflow = self._load_workflow(yaml_file)
            workflows.append(workflow)

        return workflows

    def install_workflow(
        self,
        workflow: Workflow,
        interactive: bool = True,
        dry_run: bool = False
    ) -> WorkflowInstallResult:
        """Install all servers in a workflow."""

        console = Console()

        # Show workflow overview
        console.print(f"\n[bold]{workflow.metadata.name}[/bold]")
        console.print(workflow.metadata.description)
        console.print(f"\nThis workflow installs {len(workflow.servers)} servers:\n")

        for i, server in enumerate(workflow.servers, 1):
            required = "" if server.required else " (Optional)"
            console.print(f"  {i}. {server.id} ({server.template} template){required}")
            if server.description:
                console.print(f"     → {server.description}")

        if interactive and not Confirm.ask("\nContinue?", default=True):
            return WorkflowInstallResult(cancelled=True)

        # Install each server
        results = []
        for i, server in enumerate(workflow.servers, 1):
            console.print(f"\n[bold cyan]Step {i} of {len(workflow.servers)}: {server.id}[/bold cyan]")

            # Skip if optional and user declines
            if not server.required and interactive:
                if not Confirm.ask(f"Install {server.id}?", default=True):
                    results.append(ServerInstallResult(server_id=server.id, skipped=True))
                    continue

            # Get template
            template = self.template_manager.get_template(server.id, server.template)

            # Install with template
            try:
                # Use existing template installation flow
                result = self._install_server_with_template(
                    server_id=server.id,
                    template=template,
                    scope=server.scope,
                    interactive=interactive,
                    dry_run=dry_run
                )
                results.append(result)
            except Exception as e:
                console.print(f"[red]Error installing {server.id}: {e}[/red]")

                if interactive:
                    if Confirm.ask("Continue with remaining servers?", default=True):
                        results.append(ServerInstallResult(
                            server_id=server.id,
                            error=str(e)
                        ))
                        continue
                    else:
                        break

        return WorkflowInstallResult(
            workflow=workflow,
            server_results=results
        )

    def export_workflow(
        self,
        workflow_name: str,
        output_path: Optional[Path] = None
    ) -> Path:
        """Export workflow to shareable YAML file."""
        # Get current server configurations
        servers = self.mcp_manager.list_servers()

        # Build workflow from current state
        workflow = self._build_workflow_from_state(workflow_name, servers)

        # Write to file
        if not output_path:
            output_path = Path.cwd() / f"{workflow_name}.yaml"

        with open(output_path, 'w') as f:
            yaml.dump(workflow.model_dump(), f, default_flow_style=False)

        return output_path
```

---

## Strategic Analysis

### How These Features Compound

**Individual value** is high, but **combined value** is exponential:

1. **Discovery** makes templates navigable at scale (50+ templates manageable)
2. **Test Drive** makes experimentation safe (try templates confidently)
3. **Workflows** package proven combinations (no need to guess what works together)

**Compound effect**:
- New user runs workflow (Feature 3)
- Each server uses recommended template via discovery (Feature 1)
- User test-drives before installing (Feature 2)
- Entire team uses shared workflow (Feature 3)
- 30-minute setup → 5-minute setup with 100% confidence

### Competitive Differentiation

**What competitors offer**:
- Manual server installation (Claude Desktop, Cursor)
- Basic documentation (GitHub READMEs)
- No guided setup

**What MCPI offers after these features**:
- Intelligent recommendations (knows your project)
- Safe experimentation (test before commit)
- Team-ready workflows (instant standardization)
- Living documentation (templates + workflows)

**Category creation**: MCPI becomes "Infrastructure as Guided Experience"

### Long-Term Vision

These features set up future capabilities:

**v0.6.0+**:
- **Template marketplace**: Community-contributed templates
- **Workflow analytics**: "90% of teams using postgres also use redis"
- **Auto-sync workflows**: Team workflow updates push to members
- **Template versioning**: Track template changes, migrations

**v1.0+**:
- **Cloud workflow sharing**: Public workflow registry
- **Template testing framework**: Validate templates against real servers
- **AI-powered recommendations**: "Based on your code, you might need..."

---

## Risk Assessment

### Feature 1: Template Discovery

**Technical Risks**:
- False positives in detection (LOW) - Conservative scoring prevents
- Missing project types (MEDIUM) - Add detectors incrementally
- Recommendation quality degrades over time (LOW) - Curated rules, not ML

**Mitigation**:
- Start with 5 detectors (Docker, language, database, framework, environment)
- Conservative confidence thresholds (> 0.3)
- Always show all templates (recommendations just re-order)
- Collect feedback, iterate on rules

**Overall Risk**: LOW

### Feature 2: Template Test Drive

**Technical Risks**:
- Network validators unreliable (MEDIUM) - Timeouts, firewalls
- Validation false negatives (MEDIUM) - Pass validation but still fail
- Slow preview generation (LOW) - Async validation

**Mitigation**:
- Make network validation optional (syntax validation always)
- Graceful degradation (skip validator if network unavailable)
- Clear warnings vs errors
- Aggressive timeouts (5 seconds max)

**Overall Risk**: MEDIUM (but mitigated well)

### Feature 3: Template Workflows

**Technical Risks**:
- Partial installation failures (MEDIUM) - Some servers succeed, some fail
- Workflow version drift (LOW) - User modifies after install
- Complex orchestration bugs (MEDIUM) - Edge cases in multi-server install

**Mitigation**:
- Clear progress tracking (Step X of Y)
- Rollback option on failure
- Save workflow state (resume if interrupted)
- Extensive integration testing

**Overall Risk**: LOW-MEDIUM

---

## Success Criteria Summary

### Quantitative Goals

| Metric | Feature 1 | Feature 2 | Feature 3 |
|--------|-----------|-----------|-----------|
| **Adoption Rate** | 40%+ use recommendations | 50%+ use dry-run | 30%+ install workflows |
| **Success Rate** | 85%+ accept top recommendation | 80%+ validations catch errors | 90%+ complete successfully |
| **Time Savings** | Template selection 75% faster | Config iteration 80% faster | Multi-server setup 80% faster |
| **User Satisfaction** | 80%+ "helpful" | 85%+ "gave confidence" | 90%+ "essential for teams" |

### Qualitative Goals

**Feature 1 (Discovery)**:
- "It knew my project uses Docker!"
- "The explanation helped me understand"
- "I trust MCPI's recommendations"

**Feature 2 (Test Drive)**:
- "Caught my typo before it broke anything"
- "I experimented without fear"
- "The preview showed exactly what would happen"

**Feature 3 (Workflows)**:
- "Onboarded new developer in 5 minutes"
- "Entire team has identical setup"
- "This is why I use MCPI over manual config"

---

## Implementation Roadmap

### Option A: Sequential - Maximum Quality (9 weeks)

**Weeks 1-3: Template Discovery**
- Complete implementation
- 20+ unit tests
- Integration with existing CLI
- Documentation
- **Deliverable**: `--recommend` flag working perfectly

**Weeks 4-6: Template Test Drive**
- Complete implementation
- Network validators
- Preview system
- 25+ tests
- **Deliverable**: `--dry-run` flag with validation

**Weeks 7-9: Template Workflows**
- Complete implementation
- 4 curated workflows
- Export/import
- 30+ tests
- **Deliverable**: `mcpi workflow` commands

**Total**: 9 weeks, very high quality, sequential dependencies

### Option B: Parallel - Faster Delivery (6 weeks with 2 devs)

**Developer 1**:
- Weeks 1-3: Template Discovery
- Weeks 4-6: Template Workflows (builds on discovery)

**Developer 2**:
- Weeks 1-3: Template Test Drive (independent)
- Weeks 4-6: Help with Workflows + polish

**Total**: 6 weeks, high quality, requires coordination

### Option C: MVP - Quick Win (2-3 weeks)

**Pick ONE feature for maximum impact**:

**If solo developer experience is priority**: Template Discovery
- Fastest to implement (2 weeks)
- Immediate value
- Grows with template library

**If team collaboration is priority**: Template Workflows
- Highest strategic value (3 weeks)
- Solves onboarding problem
- Demonstrates MCPI's enterprise readiness

**If learning/confidence is priority**: Template Test Drive
- Medium complexity (2.5 weeks)
- Enables experimentation
- Reduces support burden

### Recommendation

**For solo maintainer**: Option C (MVP) → Pick Template Discovery
- 2 weeks to ship
- Immediate value with existing 12 templates
- Sets up workflows later
- Low risk, high confidence

**For team of 2**: Option B (Parallel)
- 6 weeks to ship all three
- Maximum value delivery
- Good division of labor

**For maximum quality**: Option A (Sequential)
- 9 weeks total
- Each feature polished before next
- Lower risk, higher confidence
- Best for production readiness

---

## Appendix: Ideas Deferred to v0.6.0+

These didn't make the cut for post-v0.5.0 but could be valuable later:

### Template Marketplace
- Community-contributed templates
- Voting/rating system
- Template submission workflow
- **Complexity**: HIGH (moderation, quality control)

### Template Versioning
- Track template changes over time
- Migrations when templates evolve
- Rollback to previous template versions
- **Complexity**: MEDIUM (versioning logic)

### Advanced Validation
- Actual server health checks (start server, test connection)
- Integration testing for configurations
- Automated troubleshooting suggestions
- **Complexity**: HIGH (daemon required)

### Workflow Analytics
- Track which workflows are popular
- Suggest workflows based on anonymous usage
- Community workflow sharing
- **Complexity**: MEDIUM (telemetry concerns)

### Auto-Configuration
- Scan project, auto-generate workflow
- No prompts needed (all auto-detected)
- One-click setup
- **Complexity**: HIGH (fragile, lots of edge cases)

---

## Conclusion

These 3 features represent the **natural evolution of Configuration Templates**:

**v0.5.0 solved**: "How do I configure ONE server easily?"

**Post-v0.5.0 solves**:
1. **Discovery** - "Which template is right for me?"
2. **Confidence** - "Will this work before I commit?"
3. **Scale** - "How do I set up MULTIPLE servers?"

**Combined impact**:
- Template library stays navigable at 50+ templates (Discovery)
- Users experiment fearlessly (Test Drive)
- Teams achieve setup parity in minutes (Workflows)
- MCPI becomes indispensable for MCP server management

**Timeline**:
- **Sequential**: 9 weeks for all three (highest quality)
- **Parallel**: 6 weeks for all three (2 developers)
- **MVP**: 2-3 weeks for one feature (quick win)

**Recommended first feature**: Template Discovery
- 2 weeks to implement
- Leverages existing templates immediately
- Sets foundation for workflows
- Low risk, high user delight

**Risk level**: LOW-MEDIUM overall
- Discovery: LOW risk
- Test Drive: MEDIUM risk (network validation)
- Workflows: LOW-MEDIUM risk (orchestration)

**Strategic value**: VERY HIGH
- Differentiates from all competitors
- Makes MCPI essential for teams
- Creates network effects (shared workflows)
- Sets up template marketplace (v0.6.0+)

---

**Status**: Ready for evaluation and prioritization
**Next Step**: Choose implementation approach (Option A/B/C)
**Recommendation**: Start with Template Discovery (2 weeks, low risk, high value)
**Author**: Product Visionary Agent
**Date**: 2025-11-17

---

## Exact Text to Add to PROJECT_SPEC.md

### New Section: "Post-v0.5.0 Planned Features"

Add after line 363 (Future Enhancements section):

```markdown
## Post-v0.5.0 Feature Roadmap

### Configuration Templates Evolution

v0.5.0 introduced Configuration Templates with 12 templates across 5 servers, achieving 87% reduction in setup time. The next phase builds on this success with three high-impact features:

#### 1. Template Discovery Engine (v0.6.0)

**Problem**: As template library grows (50+ templates), users face choice paralysis.

**Solution**: Intelligent template recommendations based on project context:
- Analyzes project (Docker, language, databases, frameworks)
- Recommends templates with explanations ("Your project uses Docker Compose")
- Works automatically with `--recommend` flag or interactively
- Local detection only (no telemetry, no external services)

**Impact**: 75% faster template selection, 85%+ users accept top recommendation

**Example**:
```bash
$ mcpi add postgres --recommend

🧠 Detected: Docker Compose in project root
   Recommended: postgres/docker template

   Why: Your docker-compose.yml has postgres service
   Alternative: postgres/local-development
```

**Implementation**: 2-3 weeks, LOW risk
- Project detectors (Docker, language, database, environment)
- Template metadata enrichment (best_for, keywords)
- Scoring algorithm (detector confidence × template fit)
- Integration with existing template system

#### 2. Template Test Drive (v0.6.0)

**Problem**: Users can't preview or validate configurations before installation.

**Solution**: Dry-run mode with validation and preview:
- Shows exactly what will be configured without installing
- Validates inputs (URL reachable? Port available? Path exists?)
- Tests connections where possible (database, API)
- Safe experimentation without breaking existing setup

**Impact**: 80% reduction in config errors, 50%+ use before installation

**Example**:
```bash
$ mcpi add slack --template bot-token --dry-run

Configuration Preview
─────────────────────
Scope: project-mcp
Environment: SLACK_BOT_TOKEN=xoxb-***

Validation
──────────
✓ Bot token format valid
✓ Testing Slack API... Connected as "MyApp Bot"
✓ Channel access verified: #general, #dev-team
⚠ Warning: Bot lacks access to #private

Looks good? Install: mcpi add slack --template bot-token
```

**Implementation**: 2-3 weeks, MEDIUM risk
- Validation framework (URL, port, path, secret validators)
- Preview generation (Rich formatted)
- Network validation (with graceful fallback)
- Integration with template prompts

#### 3. Template Workflows (v0.7.0)

**Problem**: Real projects need MULTIPLE servers configured correctly together.

**Solution**: Bundle proven template combinations into one-command workflows:
- Curated workflows (full-stack-web-dev, data-science, devops)
- Sequential installation with progress tracking
- Shareable team configurations
- Custom workflow creation

**Impact**: 80% faster multi-server setup (30 min → 5 min), 90%+ team adoption

**Example**:
```bash
$ mcpi workflow install full-stack-web-dev

Full-Stack Web Development Workflow
────────────────────────────────────
Installs: postgres, github, filesystem, brave-search, slack

Step 1 of 5: PostgreSQL (docker template)
Database name: myapp_dev
...
✓ Installed postgres to project-mcp

# ... continues through all servers ...

🎉 Complete! 5 servers ready to use.
```

**Implementation**: 2-3 weeks, LOW-MEDIUM risk
- Workflow YAML format (metadata, servers list)
- Sequential installation orchestration
- Export/import for team sharing
- 4 built-in curated workflows

### Implementation Timeline

**Sequential** (9 weeks total):
- Weeks 1-3: Template Discovery
- Weeks 4-6: Template Test Drive
- Weeks 7-9: Template Workflows

**Parallel with 2 developers** (6 weeks total):
- Developer 1: Discovery (weeks 1-3), Workflows (weeks 4-6)
- Developer 2: Test Drive (weeks 1-3), Polish (weeks 4-6)

**MVP - Quick Win** (2-3 weeks):
- Start with Template Discovery only (highest value, lowest risk)

### Design Principles

All three features follow established MCPI patterns:
- Build on existing architecture (zero breaking changes)
- DIP compliant (fully testable via dependency injection)
- Local-first (no external services or telemetry)
- CLI-focused with beautiful Rich output
- Backward compatible (new flags, no required changes)

### Success Metrics

- Template Discovery: 40%+ adoption, 85%+ accept recommendations
- Test Drive: 50%+ use dry-run, 80%+ catch errors
- Workflows: 30%+ install workflows, 90%+ team adoption

### Strategic Value

These features transform MCPI from "good CLI tool" to "essential team infrastructure":
- Discovery: Makes growing template library navigable
- Test Drive: De-risks experimentation, builds confidence
- Workflows: Enables team standardization and onboarding

Combined impact: Entire team setup (5+ servers) in 5 minutes with 100% confidence.
```
