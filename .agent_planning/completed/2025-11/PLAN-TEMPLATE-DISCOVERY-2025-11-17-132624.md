# Template Discovery Engine - Implementation Plan v0.6.0

**Generated**: 2025-11-17 13:26:24
**Source STATUS**: `STATUS-2025-11-17-132221.md` (Zero-Optimism Protocol)
**Source Evaluation**: `STATUS-TEMPLATE-DISCOVERY-EVALUATION-2025-11-17-080057.md`
**Foundation**: v0.5.0 Configuration Templates (100% complete, shipped)
**Target Version**: v0.6.0
**Implementation Status**: 0% (NOT STARTED - This is Day 0)
**Readiness Score**: 85/100 (READY TO IMPLEMENT NOW)

---

## Executive Summary

This plan details the implementation of the Template Discovery Engine, a feature that analyzes project context (Docker, language, databases) and recommends the best configuration templates with confidence scores and explanations.

**CRITICAL REALITY CHECK**:
- v0.5.0 Templates: 100% COMPLETE ✅ (solid foundation)
- v0.6.0 Discovery: 0% IMPLEMENTED 🔴 (all work ahead)
- Planning: 100% COMPLETE ✅ (this plan consolidates 2680 lines of planning)
- Code Written: 0 lines / ~2220 lines planned

**Timeline**: 2-3 weeks (realistic, based on past velocity)
**Risk Level**: LOW (no breaking changes, conservative approach)
**Test Coverage Target**: 95%+ on new code
**Expected Impact**: 75% faster template selection, 85%+ recommendation acceptance

---

## 1. Foundation Assessment

### 1.1 What We Have (v0.5.0 - Rock Solid)

**Template Infrastructure** (100% Complete):
- ✅ `src/mcpi/templates/models.py` (161 lines) - Pydantic models with validation
- ✅ `src/mcpi/templates/template_manager.py` (5388 bytes) - Load/list/apply templates
- ✅ `src/mcpi/templates/prompt_handler.py` (3727 bytes) - Interactive Rich prompts
- ✅ 12 production templates across 5 servers (postgres, github, filesystem, slack, brave-search)
- ✅ CLI integration (`--template`, `--list-templates` flags)
- ✅ 94 tests, 95%+ coverage, 100% pass rate on template tests
- ✅ Factory functions following DIP pattern

**Runtime Verification**:
```bash
$ mcpi --version
mcpi, version 0.5.0

$ mcpi add postgres --list-templates
# Works perfectly - shows 3 templates in rich table

$ pytest tests/test_template*.py -q
94 passed in 0.55s
```

**Dependencies Already Installed**:
- PyYAML ^6.0 (for docker-compose parsing)
- Pydantic ^2.9.2 (for models)
- Rich ^13.9.4 (for console output)
- Click ^8.1.7 (for CLI)

### 1.2 What We Need to Build (v0.6.0 - All New)

**New Components**:
1. `src/mcpi/templates/discovery.py` (~300 lines) - Project detection
2. `src/mcpi/templates/recommender.py` (~250 lines) - Recommendation engine
3. Extend `models.py` (+20 lines) - Add metadata fields
4. Update 12 template YAML files (+100 lines) - Add metadata
5. Extend `cli.py` (+50 lines) - Add `--recommend` flag
6. Create 4 new test files (+~1500 lines) - Comprehensive test coverage

**Total New Code**: ~2220 lines

---

## 2. Implementation Roadmap

### Phase 1: Detection Infrastructure (Week 1, Days 1-5)

#### P0-1: ProjectContext Data Model
**Effort**: 2 hours | **Dependencies**: None | **Status**: NOT STARTED

**Description**:
Create the `ProjectContext` dataclass to hold detected project characteristics. This is the data foundation for all detection logic.

**Files to Create**:
- `src/mcpi/templates/discovery.py` (new file)

**Implementation**:
```python
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

@dataclass
class ProjectContext:
    """Detected project characteristics for template recommendation."""
    root_path: Path
    has_docker: bool = False
    has_docker_compose: bool = False
    docker_services: List[str] = field(default_factory=list)
    language: Optional[str] = None
    databases: List[str] = field(default_factory=list)
    environment: str = "development"

    def __str__(self) -> str:
        """Human-readable representation for debugging."""
        parts = [f"Project at {self.root_path}"]
        if self.has_docker_compose:
            parts.append(f"Docker Compose with services: {', '.join(self.docker_services)}")
        if self.language:
            parts.append(f"Language: {self.language}")
        return " | ".join(parts)
```

**Acceptance Criteria**:
- [ ] `ProjectContext` dataclass defined with all fields
- [ ] Type hints for all fields
- [ ] Sensible defaults (empty lists, False booleans)
- [ ] `__str__` method for debugging
- [ ] Can instantiate with minimal args: `ProjectContext(root_path=Path("."))`

**Tests to Write** (in `tests/test_project_detector.py`):
```python
def test_project_context_creation():
    """Test ProjectContext can be instantiated."""
    context = ProjectContext(root_path=Path("."))
    assert context.root_path == Path(".")
    assert context.has_docker is False
    assert context.docker_services == []
```

---

#### P0-2: Docker Detection
**Effort**: 4 hours | **Dependencies**: P0-1 | **Status**: NOT STARTED

**Description**:
Implement Docker detection logic to identify projects using Docker and Docker Compose. Parse docker-compose.yml to extract service names for smart matching.

**Implementation**:
```python
import yaml

class ProjectDetector:
    """Detects project characteristics from file system."""

    def __init__(self):
        """Initialize detector."""
        pass

    def detect(self, project_path: Path) -> ProjectContext:
        """Analyze project to determine context."""
        context = ProjectContext(root_path=project_path)
        self._detect_docker(context, project_path)
        return context

    def _detect_docker(self, context: ProjectContext, path: Path) -> None:
        """Detect Docker usage."""
        # Check for docker-compose.yml (highest value signal)
        compose_file = path / "docker-compose.yml"
        if compose_file.exists():
            context.has_docker_compose = True
            context.docker_services = self._parse_docker_compose(compose_file)

        # Check for Dockerfile
        if (path / "Dockerfile").exists():
            context.has_docker = True

    def _parse_docker_compose(self, compose_file: Path) -> List[str]:
        """Parse docker-compose.yml to extract service names.

        Returns empty list on any error (graceful degradation).
        """
        try:
            with open(compose_file) as f:
                data = yaml.safe_load(f)
            services = data.get("services", {})
            return list(services.keys())
        except Exception:
            # Graceful failure - any parsing error returns empty list
            return []
```

**Acceptance Criteria**:
- [ ] `ProjectDetector` class created
- [ ] `_detect_docker()` method detects docker-compose.yml
- [ ] `_detect_docker()` method detects Dockerfile
- [ ] `_parse_docker_compose()` extracts service names
- [ ] Graceful failure on corrupted YAML (returns empty list)
- [ ] Only checks project root (not subdirectories)

**Tests to Write** (15-20 tests):
```python
def test_detect_docker_compose_file(tmp_path):
    """Detects docker-compose.yml presence."""
    (tmp_path / "docker-compose.yml").write_text("services:\n  postgres:")
    detector = ProjectDetector()
    context = detector.detect(tmp_path)
    assert context.has_docker_compose is True

def test_detect_docker_services(tmp_path):
    """Parses service names from docker-compose.yml."""
    (tmp_path / "docker-compose.yml").write_text(
        "services:\n  postgres:\n  redis:\n  nginx:"
    )
    detector = ProjectDetector()
    context = detector.detect(tmp_path)
    assert "postgres" in context.docker_services
    assert "redis" in context.docker_services
    assert "nginx" in context.docker_services

def test_detect_dockerfile_only(tmp_path):
    """Detects Dockerfile without compose."""
    (tmp_path / "Dockerfile").write_text("FROM node:18")
    detector = ProjectDetector()
    context = detector.detect(tmp_path)
    assert context.has_docker is True
    assert context.has_docker_compose is False

def test_docker_compose_parse_error_graceful(tmp_path):
    """Handles corrupted docker-compose.yml gracefully."""
    (tmp_path / "docker-compose.yml").write_text("invalid: yaml: {{{")
    detector = ProjectDetector()
    context = detector.detect(tmp_path)
    assert context.docker_services == []  # Empty list, not crash
```

**Manual Verification**:
```bash
# Create test project
mkdir -p /tmp/test-docker-detection
cd /tmp/test-docker-detection
cat > docker-compose.yml <<EOF
services:
  postgres:
    image: postgres:15
  redis:
    image: redis:7
EOF

# Test detection
python -c "
from pathlib import Path
from mcpi.templates.discovery import ProjectDetector

detector = ProjectDetector()
context = detector.detect(Path('/tmp/test-docker-detection'))
print(f'Has Docker Compose: {context.has_docker_compose}')
print(f'Services: {context.docker_services}')
"
# Expected output:
# Has Docker Compose: True
# Services: ['postgres', 'redis']
```

---

#### P0-3: Language Detection
**Effort**: 3 hours | **Dependencies**: P0-1 | **Status**: NOT STARTED

**Description**:
Detect programming language by checking for package manager files. Supports Node.js, Python, Go, with easy extension for more languages.

**Implementation**:
```python
def _detect_language(self, context: ProjectContext, path: Path) -> None:
    """Detect programming language from package manager files."""
    # Node.js detection
    if (path / "package.json").exists():
        context.language = "nodejs"
        return

    # Python detection (prefer pyproject.toml as more modern)
    if (path / "pyproject.toml").exists():
        context.language = "python"
        return
    if (path / "requirements.txt").exists():
        context.language = "python"
        return

    # Go detection
    if (path / "go.mod").exists():
        context.language = "go"
        return

    # Rust detection (bonus)
    if (path / "Cargo.toml").exists():
        context.language = "rust"
        return
```

**Acceptance Criteria**:
- [ ] Detects Node.js from package.json
- [ ] Detects Python from requirements.txt or pyproject.toml
- [ ] Detects Go from go.mod
- [ ] Handles polyglot projects (sets first found language)
- [ ] Returns None if no language detected

**Tests to Write** (10-12 tests):
```python
def test_detect_nodejs_from_package_json(tmp_path):
    """Detects Node.js from package.json."""
    (tmp_path / "package.json").write_text('{"name": "test"}')
    detector = ProjectDetector()
    context = detector.detect(tmp_path)
    assert context.language == "nodejs"

def test_detect_python_from_requirements(tmp_path):
    """Detects Python from requirements.txt."""
    (tmp_path / "requirements.txt").write_text("django==4.2.0")
    detector = ProjectDetector()
    context = detector.detect(tmp_path)
    assert context.language == "python"

def test_detect_python_from_pyproject(tmp_path):
    """Detects Python from pyproject.toml."""
    (tmp_path / "pyproject.toml").write_text("[tool.poetry]")
    detector = ProjectDetector()
    context = detector.detect(tmp_path)
    assert context.language == "python"

def test_polyglot_project_first_wins(tmp_path):
    """In polyglot projects, first detected language wins."""
    (tmp_path / "package.json").write_text('{"name": "test"}')
    (tmp_path / "requirements.txt").write_text("django==4.2.0")
    detector = ProjectDetector()
    context = detector.detect(tmp_path)
    # Node.js checked first
    assert context.language == "nodejs"

def test_no_language_detected(tmp_path):
    """Returns None when no language detected."""
    detector = ProjectDetector()
    context = detector.detect(tmp_path)
    assert context.language is None
```

---

#### P0-4: Database Detection
**Effort**: 3 hours | **Dependencies**: P0-2 | **Status**: NOT STARTED

**Description**:
Detect database usage by examining docker-compose services. Future: check .env files for DATABASE_URL patterns.

**Implementation**:
```python
def _detect_database(self, context: ProjectContext, path: Path) -> None:
    """Detect database usage from docker-compose services."""
    # Common database service names
    db_keywords = {
        "postgres": "postgres",
        "postgresql": "postgres",
        "mysql": "mysql",
        "mariadb": "mysql",
        "redis": "redis",
        "mongodb": "mongodb",
        "mongo": "mongodb",
    }

    # Check docker-compose services
    for service in context.docker_services:
        service_lower = service.lower()
        for keyword, db_name in db_keywords.items():
            if keyword in service_lower:
                if db_name not in context.databases:
                    context.databases.append(db_name)
```

**Acceptance Criteria**:
- [ ] Detects postgres/postgresql from docker-compose services
- [ ] Detects mysql/mariadb from docker-compose services
- [ ] Detects redis from docker-compose services
- [ ] Detects mongodb/mongo from docker-compose services
- [ ] Handles multiple databases in one project
- [ ] Case-insensitive matching

**Tests to Write** (8-10 tests):
```python
def test_detect_postgres_from_compose(tmp_path):
    """Detects PostgreSQL from docker-compose."""
    (tmp_path / "docker-compose.yml").write_text(
        "services:\n  postgres:\n    image: postgres:15"
    )
    detector = ProjectDetector()
    context = detector.detect(tmp_path)
    assert "postgres" in context.databases

def test_detect_multiple_databases(tmp_path):
    """Detects multiple databases in same project."""
    (tmp_path / "docker-compose.yml").write_text(
        "services:\n  postgres:\n  redis:\n  mongodb:"
    )
    detector = ProjectDetector()
    context = detector.detect(tmp_path)
    assert "postgres" in context.databases
    assert "redis" in context.databases
    assert "mongodb" in context.databases

def test_database_aliases_recognized(tmp_path):
    """Recognizes common database name aliases."""
    (tmp_path / "docker-compose.yml").write_text(
        "services:\n  my-postgresql-db:\n  cache-redis:"
    )
    detector = ProjectDetector()
    context = detector.detect(tmp_path)
    assert "postgres" in context.databases
    assert "redis" in context.databases
```

---

#### P0-5: ProjectDetector Integration
**Effort**: 2 hours | **Dependencies**: P0-2, P0-3, P0-4 | **Status**: NOT STARTED

**Description**:
Wire up all detection methods into the main `detect()` method. Add integration tests with realistic project structures.

**Implementation**:
```python
def detect(self, project_path: Path) -> ProjectContext:
    """Analyze project to determine context.

    Runs all detection heuristics and returns a complete context.
    Fast (< 100ms target) and safe (no external calls).
    """
    context = ProjectContext(root_path=project_path)

    # Run all detectors (order doesn't matter)
    self._detect_docker(context, project_path)
    self._detect_language(context, project_path)
    self._detect_database(context, project_path)

    return context
```

**Acceptance Criteria**:
- [ ] `detect()` method calls all detection methods
- [ ] Returns fully populated `ProjectContext`
- [ ] Performance < 100ms for typical project
- [ ] Integration tests with realistic project structures
- [ ] Manual verification with real projects

**Integration Tests** (5-8 tests):
```python
def test_detect_nodejs_docker_postgres_project(tmp_path):
    """Realistic Node.js + Docker + PostgreSQL project."""
    # Set up project structure
    (tmp_path / "package.json").write_text('{"name": "api"}')
    (tmp_path / "docker-compose.yml").write_text(
        "services:\n  postgres:\n    image: postgres:15"
    )
    (tmp_path / "Dockerfile").write_text("FROM node:18")

    # Detect
    detector = ProjectDetector()
    context = detector.detect(tmp_path)

    # Verify all characteristics detected
    assert context.language == "nodejs"
    assert context.has_docker is True
    assert context.has_docker_compose is True
    assert "postgres" in context.docker_services
    assert "postgres" in context.databases

def test_detect_python_local_project(tmp_path):
    """Python project without Docker."""
    (tmp_path / "requirements.txt").write_text("django==4.2.0")

    detector = ProjectDetector()
    context = detector.detect(tmp_path)

    assert context.language == "python"
    assert context.has_docker is False
    assert context.has_docker_compose is False

def test_detect_performance(tmp_path, benchmark):
    """Detection completes in < 100ms."""
    # Create realistic project
    (tmp_path / "package.json").write_text('{"name": "test"}')
    (tmp_path / "docker-compose.yml").write_text("services:\n  postgres:")

    detector = ProjectDetector()

    # Benchmark detection
    result = benchmark(detector.detect, tmp_path)
    assert result.has_docker_compose is True
    # Benchmark will report timing
```

**Manual Verification**:
```bash
# Test with real MCPI project
cd ~/icode/mcpi
python -c "
from pathlib import Path
from mcpi.templates.discovery import ProjectDetector

detector = ProjectDetector()
context = detector.detect(Path.cwd())
print(f'Language: {context.language}')
print(f'Has Docker: {context.has_docker}')
print(f'Services: {context.docker_services}')
"
# Expected: Language: python, Has Docker: False (or True if you have docker-compose)
```

**Week 1 Checkpoint**: Detection infrastructure works programmatically ✅

---

### Phase 2: Template Metadata & Recommendation Engine (Week 1-2, Days 3-10)

#### P0-6: Extend ServerTemplate Model
**Effort**: 3 hours | **Dependencies**: None | **Status**: NOT STARTED

**Description**:
Add three optional fields to `ServerTemplate` for recommendation metadata. Maintain backward compatibility (old templates work without new fields).

**Files to Modify**:
- `src/mcpi/templates/models.py` (add fields to ServerTemplate class)

**Implementation**:
```python
# In src/mcpi/templates/models.py, update ServerTemplate:

class ServerTemplate(BaseModel):
    """Template for server configuration with interactive prompts."""
    name: str
    description: str
    server_id: str
    scope: str
    priority: Literal["high", "medium", "low"]
    config: dict[str, Any]
    prompts: list[PromptDefinition] = Field(default_factory=list)
    notes: str = Field(default="")

    # NEW FIELDS FOR RECOMMENDATIONS (v0.6.0)
    best_for: list[str] = Field(
        default_factory=list,
        description="Tags describing what this template is optimized for (e.g., 'docker', 'local', 'production')"
    )
    keywords: list[str] = Field(
        default_factory=list,
        description="Keywords for fuzzy search and matching"
    )
    recommendations: Optional[dict[str, Any]] = Field(
        default=None,
        description="Hints for the recommendation engine (e.g., required tools, bonus matches)"
    )
```

**Acceptance Criteria**:
- [ ] Three new fields added: `best_for`, `keywords`, `recommendations`
- [ ] All fields are optional (default to empty list or None)
- [ ] Pydantic validation accepts templates with and without new fields
- [ ] Existing templates load without modification
- [ ] Unit tests verify backward compatibility

**Tests to Write**:
```python
def test_server_template_with_metadata():
    """Template with recommendation metadata validates."""
    template_data = {
        "name": "docker",
        "description": "Docker setup",
        "server_id": "postgres",
        "scope": "project-mcp",
        "priority": "high",
        "config": {},
        "best_for": ["docker", "development"],
        "keywords": ["container", "compose"],
        "recommendations": {"requires": ["docker"]}
    }
    template = ServerTemplate(**template_data)
    assert template.best_for == ["docker", "development"]
    assert template.keywords == ["container", "compose"]
    assert template.recommendations["requires"] == ["docker"]

def test_server_template_without_metadata():
    """Old template without metadata still works."""
    template_data = {
        "name": "docker",
        "description": "Docker setup",
        "server_id": "postgres",
        "scope": "project-mcp",
        "priority": "high",
        "config": {}
    }
    template = ServerTemplate(**template_data)
    assert template.best_for == []
    assert template.keywords == []
    assert template.recommendations is None

def test_existing_templates_still_load(template_manager):
    """All existing templates load successfully."""
    templates = template_manager.list_templates("postgres")
    assert len(templates) == 3
    for template in templates:
        # New fields exist but may be empty
        assert hasattr(template, 'best_for')
        assert hasattr(template, 'keywords')
```

---

#### P0-7: Update Template YAML Files with Metadata
**Effort**: 3 hours | **Dependencies**: P0-6 | **Status**: NOT STARTED

**Description**:
Add recommendation metadata to all 12 existing templates. This is the data foundation that makes recommendations smart.

**Files to Modify** (12 templates):
- `data/templates/postgres/docker.yaml`
- `data/templates/postgres/local-development.yaml`
- `data/templates/postgres/production.yaml`
- `data/templates/github/personal-full-access.yaml`
- `data/templates/github/read-only.yaml`
- `data/templates/github/public-repos.yaml`
- `data/templates/filesystem/project-files.yaml`
- `data/templates/filesystem/user-documents.yaml`
- `data/templates/filesystem/custom-directories.yaml`
- `data/templates/slack/bot-token.yaml`
- `data/templates/slack/limited-channels.yaml`
- `data/templates/brave-search/api-key.yaml`

**Example Metadata** (postgres/docker.yaml):
```yaml
name: docker
description: "PostgreSQL running in Docker container"
server_id: postgres
scope: user-global
priority: high

# NEW: Recommendation metadata
best_for:
  - docker
  - docker-compose
  - containers
  - development
keywords:
  - docker
  - containerized
  - compose
  - dev
recommendations:
  requires:
    - docker
  bonus_for:
    - docker-compose
  docker_service_match: postgres

config:
  command: npx
  args: ["-y", "@modelcontextprotocol/server-postgres"]
  env: {}

prompts:
  - name: POSTGRES_CONTAINER
    description: "Name of your Docker container running PostgreSQL"
    type: string
    required: true
    default: "postgres"
# ... rest of template
```

**Metadata Guidelines**:
1. **best_for**: 3-5 tags describing ideal use cases
   - Common tags: docker, local, production, development, cloud, team
2. **keywords**: 3-6 search terms for fuzzy matching
   - Include variations, abbreviations, related terms
3. **recommendations**: Optional hints for scoring algorithm
   - `requires`: Tools that must be present (e.g., docker, git)
   - `bonus_for`: Tools that increase confidence (e.g., docker-compose)
   - `docker_service_match`: Service name to look for in docker-compose.yml

**Acceptance Criteria**:
- [ ] All 12 templates updated with metadata
- [ ] Metadata follows guidelines (3-5 best_for tags, 3-6 keywords)
- [ ] YAML syntax valid (tests pass after changes)
- [ ] Templates load successfully in TemplateManager
- [ ] No functional regressions (existing template flow still works)

**Tests to Write**:
```python
def test_all_templates_have_metadata():
    """All templates include recommendation metadata."""
    manager = create_default_template_manager()

    servers = ["postgres", "github", "filesystem", "slack", "brave-search"]
    for server_id in servers:
        templates = manager.list_templates(server_id)
        for template in templates:
            # All templates should have at least some metadata
            assert len(template.best_for) > 0, f"{template.name} missing best_for"
            assert len(template.keywords) > 0, f"{template.name} missing keywords"

def test_docker_template_metadata():
    """Docker template has appropriate metadata."""
    manager = create_default_template_manager()
    template = manager.get_template("postgres", "docker")

    assert "docker" in template.best_for
    assert "docker-compose" in template.best_for
    assert "docker" in template.keywords
    assert template.recommendations is not None
    assert "docker" in template.recommendations.get("requires", [])
```

**Manual Verification**:
```bash
# Verify YAML syntax
pytest tests/test_template_validation.py -v

# Verify templates load
mcpi add postgres --list-templates
# Should show 3 templates without errors
```

---

#### P0-8: Scoring Algorithm
**Effort**: 5 hours | **Dependencies**: P0-5, P0-7 | **Status**: NOT STARTED

**Description**:
Implement the confidence scoring algorithm that matches project context against template metadata. Returns score (0.0-1.0) and human-readable explanations.

**Files to Create/Modify**:
- `src/mcpi/templates/recommender.py` (new file, add scoring method)

**Implementation**:
```python
from typing import Tuple, List

class TemplateRecommender:
    """Recommends templates based on project context."""

    # Scoring weights (tunable based on feedback)
    WEIGHTS = {
        "docker_match": 0.4,
        "language_match": 0.3,
        "environment_match": 0.2,
        "docker_service_match": 0.5,  # Bonus, can exceed 1.0
    }

    def _score_template(
        self,
        template: ServerTemplate,
        context: ProjectContext
    ) -> Tuple[float, List[str]]:
        """Score how well template matches project context.

        Returns:
            (confidence_score, reasons) where:
            - confidence_score: 0.0 to 1.0 (capped)
            - reasons: List of human-readable explanations
        """
        score = 0.0
        reasons = []

        # Docker match
        if context.has_docker or context.has_docker_compose:
            if "docker" in template.best_for or "docker-compose" in template.best_for:
                score += self.WEIGHTS["docker_match"]
                if context.has_docker_compose:
                    reasons.append("Your project uses Docker Compose")
                else:
                    reasons.append("Your project uses Docker")

        # Language match
        if context.language:
            if context.language in template.best_for:
                score += self.WEIGHTS["language_match"]
                reasons.append(f"Optimized for {context.language} projects")

        # Docker service match (BONUS - high value signal)
        if context.has_docker_compose and template.recommendations:
            service_match = template.recommendations.get("docker_service_match")
            if service_match and service_match in context.docker_services:
                score += self.WEIGHTS["docker_service_match"]
                reasons.append(f"Matches your docker-compose service: {service_match}")

        # Environment match (future enhancement)
        # if context.environment in template.best_for:
        #     score += self.WEIGHTS["environment_match"]
        #     reasons.append(f"Designed for {context.environment} environments")

        # Cap score at 1.0
        score = min(score, 1.0)

        return score, reasons
```

**Acceptance Criteria**:
- [ ] `_score_template()` method implemented
- [ ] Scoring weights defined and tunable
- [ ] Returns (score: float, reasons: List[str]) tuple
- [ ] Score capped at 1.0
- [ ] Reasons are human-readable and actionable
- [ ] Unit tests cover all scoring scenarios

**Tests to Write** (10-15 tests):
```python
def test_score_docker_template_with_docker_project():
    """Docker template scores high for Docker project."""
    template = ServerTemplate(
        name="docker",
        server_id="postgres",
        best_for=["docker", "docker-compose"],
        # ... other required fields
    )
    context = ProjectContext(
        root_path=Path("."),
        has_docker_compose=True,
        docker_services=["postgres"]
    )

    recommender = TemplateRecommender(template_manager=mock_manager)
    score, reasons = recommender._score_template(template, context)

    assert score >= 0.4  # At least docker_match weight
    assert any("Docker" in reason for reason in reasons)

def test_score_service_match_bonus():
    """Service match provides significant bonus."""
    template = ServerTemplate(
        name="docker",
        server_id="postgres",
        best_for=["docker"],
        recommendations={"docker_service_match": "postgres"}
    )
    context = ProjectContext(
        root_path=Path("."),
        has_docker_compose=True,
        docker_services=["postgres", "redis"]
    )

    recommender = TemplateRecommender(template_manager=mock_manager)
    score, reasons = recommender._score_template(template, context)

    assert score >= 0.9  # docker_match + service_match bonus
    assert any("docker-compose service" in reason for reason in reasons)

def test_score_capped_at_one():
    """Score never exceeds 1.0."""
    # Set up template and context that would score > 1.0
    template = ServerTemplate(
        name="perfect",
        server_id="test",
        best_for=["docker", "nodejs", "production"],
        recommendations={"docker_service_match": "test"}
    )
    context = ProjectContext(
        root_path=Path("."),
        has_docker_compose=True,
        docker_services=["test"],
        language="nodejs",
        environment="production"
    )

    recommender = TemplateRecommender(template_manager=mock_manager)
    score, reasons = recommender._score_template(template, context)

    assert score == 1.0  # Capped
    assert len(reasons) >= 2  # Multiple matches

def test_score_no_match():
    """Template with no matches scores 0.0."""
    template = ServerTemplate(
        name="production",
        server_id="postgres",
        best_for=["production", "cloud"]
    )
    context = ProjectContext(
        root_path=Path("."),
        has_docker=False,
        language="python"  # Doesn't match template
    )

    recommender = TemplateRecommender(template_manager=mock_manager)
    score, reasons = recommender._score_template(template, context)

    assert score == 0.0
    assert len(reasons) == 0
```

---

#### P0-9: TemplateRecommendation Data Model
**Effort**: 1 hour | **Dependencies**: None | **Status**: NOT STARTED

**Description**:
Create dataclass to represent a single template recommendation with metadata (confidence, reasons, match details).

**Implementation**:
```python
@dataclass
class TemplateRecommendation:
    """A template recommendation with confidence score and explanation."""
    template: ServerTemplate
    confidence: float  # 0.0 to 1.0
    reasons: List[str]  # Human-readable explanations

    def __lt__(self, other: 'TemplateRecommendation') -> bool:
        """Enable sorting by confidence (descending)."""
        return self.confidence > other.confidence  # Note: reversed for descending sort
```

**Acceptance Criteria**:
- [ ] `TemplateRecommendation` dataclass defined
- [ ] Fields: template, confidence, reasons
- [ ] Can be sorted by confidence (descending)
- [ ] Type hints for all fields

**Tests to Write**:
```python
def test_template_recommendation_creation():
    """TemplateRecommendation can be instantiated."""
    template = ServerTemplate(name="test", server_id="test", ...)
    rec = TemplateRecommendation(
        template=template,
        confidence=0.85,
        reasons=["Matches Docker", "Optimized for Node.js"]
    )
    assert rec.confidence == 0.85
    assert len(rec.reasons) == 2

def test_template_recommendation_sorting():
    """Recommendations sort by confidence descending."""
    rec1 = TemplateRecommendation(template=mock_template, confidence=0.5, reasons=[])
    rec2 = TemplateRecommendation(template=mock_template, confidence=0.9, reasons=[])
    rec3 = TemplateRecommendation(template=mock_template, confidence=0.7, reasons=[])

    recommendations = [rec1, rec2, rec3]
    recommendations.sort()

    assert recommendations[0].confidence == 0.9
    assert recommendations[1].confidence == 0.7
    assert recommendations[2].confidence == 0.5
```

---

#### P0-10: TemplateRecommender Class
**Effort**: 6 hours | **Dependencies**: P0-5, P0-8, P0-9 | **Status**: NOT STARTED

**Description**:
Implement main `TemplateRecommender` class that orchestrates detection, scoring, filtering, and ranking. This is the public API for the recommendation engine.

**Implementation**:
```python
class TemplateRecommender:
    """Recommends templates based on project context."""

    # Minimum confidence threshold for recommendations
    CONFIDENCE_THRESHOLD = 0.3

    def __init__(self, template_manager: TemplateManager):
        """Initialize recommender with template manager."""
        self.template_manager = template_manager
        self.detector = ProjectDetector()

    def recommend(
        self,
        server_id: str,
        project_path: Optional[Path] = None
    ) -> List[TemplateRecommendation]:
        """Returns ranked template recommendations for a server.

        Args:
            server_id: Server to get recommendations for (e.g., "postgres")
            project_path: Path to analyze (defaults to current directory)

        Returns:
            List of TemplateRecommendation, sorted by confidence (descending).
            Empty list if no recommendations pass threshold.
        """
        # Detect project context
        path = project_path or Path.cwd()
        context = self.detector.detect(path)

        # Get all templates for server
        try:
            templates = self.template_manager.list_templates(server_id)
        except Exception:
            # Server not found or no templates
            return []

        # Score each template
        recommendations = []
        for template in templates:
            score, reasons = self._score_template(template, context)

            # Filter by confidence threshold
            if score >= self.CONFIDENCE_THRESHOLD:
                recommendations.append(
                    TemplateRecommendation(
                        template=template,
                        confidence=score,
                        reasons=reasons
                    )
                )

        # Sort by confidence (descending)
        recommendations.sort()

        return recommendations
```

**Acceptance Criteria**:
- [ ] `TemplateRecommender` class defined
- [ ] Constructor takes `template_manager: TemplateManager`
- [ ] `recommend(server_id, project_path)` method returns ranked list
- [ ] Detects project context using ProjectDetector
- [ ] Scores all templates for server
- [ ] Filters by confidence threshold (0.3)
- [ ] Sorts by confidence descending
- [ ] Returns empty list if no recommendations
- [ ] Handles server not found gracefully

**Tests to Write** (10-15 tests):
```python
def test_recommend_returns_ranked_list(mock_template_manager):
    """recommend() returns templates ranked by confidence."""
    recommender = TemplateRecommender(template_manager=mock_template_manager)

    recommendations = recommender.recommend("postgres", tmp_path_with_docker)

    assert len(recommendations) > 0
    # Verify descending order
    for i in range(len(recommendations) - 1):
        assert recommendations[i].confidence >= recommendations[i+1].confidence

def test_recommend_filters_low_confidence(mock_template_manager):
    """Templates below threshold are excluded."""
    recommender = TemplateRecommender(template_manager=mock_template_manager)

    # Set up context that won't match any templates well
    recommendations = recommender.recommend("postgres", tmp_path_empty)

    # All recommendations should have confidence >= 0.3
    for rec in recommendations:
        assert rec.confidence >= recommender.CONFIDENCE_THRESHOLD

def test_recommend_with_no_matches(mock_template_manager):
    """Returns empty list when no templates match."""
    recommender = TemplateRecommender(template_manager=mock_template_manager)

    # Project with no detectable characteristics
    recommendations = recommender.recommend("postgres", tmp_path_empty)

    # Either empty or all have reasons
    assert all(len(rec.reasons) > 0 for rec in recommendations)

def test_recommend_server_not_found(mock_template_manager):
    """Handles server not found gracefully."""
    mock_template_manager.list_templates.side_effect = Exception("Server not found")

    recommender = TemplateRecommender(template_manager=mock_template_manager)
    recommendations = recommender.recommend("nonexistent", tmp_path)

    assert recommendations == []  # Empty list, not error

def test_recommend_uses_current_dir_by_default():
    """Uses current directory when project_path not specified."""
    recommender = TemplateRecommender(template_manager=mock_manager)

    with unittest.mock.patch.object(ProjectDetector, 'detect') as mock_detect:
        recommender.recommend("postgres")

        # Verify detect was called with cwd
        called_path = mock_detect.call_args[0][0]
        assert called_path == Path.cwd()
```

---

#### P0-11: Factory Functions for DIP
**Effort**: 2 hours | **Dependencies**: P0-10 | **Status**: NOT STARTED

**Description**:
Create factory functions following DIP pattern for creating recommender instances in production and test scenarios.

**Implementation**:
```python
# In src/mcpi/templates/recommender.py:

def create_default_template_recommender() -> TemplateRecommender:
    """Create recommender with default dependencies.

    Use this in production code.
    """
    from mcpi.templates.template_manager import create_default_template_manager
    template_manager = create_default_template_manager()
    return TemplateRecommender(template_manager=template_manager)


def create_test_template_recommender(
    template_manager: TemplateManager
) -> TemplateRecommender:
    """Create recommender for testing with injected dependencies.

    Use this in tests to inject mock template manager.
    """
    return TemplateRecommender(template_manager=template_manager)


# In src/mcpi/templates/__init__.py:
from mcpi.templates.recommender import (
    TemplateRecommender,
    TemplateRecommendation,
    create_default_template_recommender,
    create_test_template_recommender,
)
```

**Acceptance Criteria**:
- [ ] `create_default_template_recommender()` defined
- [ ] `create_test_template_recommender(template_manager)` defined
- [ ] Default factory uses `create_default_template_manager()`
- [ ] Test factory accepts injected template manager
- [ ] Both factories exported from `__init__.py`
- [ ] Unit tests verify factories work

**Tests to Write**:
```python
def test_default_factory_creates_recommender():
    """Default factory creates working recommender."""
    recommender = create_default_template_recommender()
    assert isinstance(recommender, TemplateRecommender)
    assert recommender.template_manager is not None
    assert recommender.detector is not None

def test_test_factory_accepts_injected_manager():
    """Test factory accepts mock template manager."""
    mock_manager = MagicMock(spec=TemplateManager)
    recommender = create_test_template_recommender(mock_manager)

    assert isinstance(recommender, TemplateRecommender)
    assert recommender.template_manager is mock_manager

def test_factories_create_independent_instances():
    """Each factory call creates new instance."""
    rec1 = create_default_template_recommender()
    rec2 = create_default_template_recommender()

    assert rec1 is not rec2  # Different objects
```

**Week 2 Checkpoint**: Recommendation engine works end-to-end ✅

---

### Phase 3: CLI Integration & Ship (Week 2-3, Days 11-15)

#### P1-12: Add --recommend Flag to CLI
**Effort**: 4 hours | **Dependencies**: P0-11 | **Status**: NOT STARTED

**Description**:
Add `--recommend` flag to `mcpi add` command. Flag triggers recommendation flow before template selection.

**Files to Modify**:
- `src/mcpi/cli.py` (add option and logic to add command)

**Implementation**:
```python
# In src/mcpi/cli.py, update add command:

@click.option(
    "--recommend",
    is_flag=True,
    help="Automatically recommend best template based on your project"
)
def add(
    ctx: click.Context,
    server_id: str,
    client: Optional[str],
    scope: Optional[str],
    template: Optional[str],
    list_templates: bool,
    recommend: bool,
    ...
):
    """Add an MCP server from the registry."""

    # ... existing code ...

    # NEW: Handle --recommend flag
    if recommend:
        from mcpi.templates.recommender import create_default_template_recommender

        try:
            recommender = create_default_template_recommender()
            recommendations = recommender.recommend(server_id)

            if recommendations:
                # Show recommendations (implemented in P1-13)
                template = _handle_recommendations(recommendations, console)
            else:
                console.print("[yellow]No clear recommendation - showing all templates[/yellow]\n")
                list_templates = True  # Fall back to showing all
        except Exception as e:
            console.print(f"[yellow]Recommendation error: {e}[/yellow]")
            console.print("[yellow]Showing all templates instead[/yellow]\n")
            list_templates = True

    # ... rest of existing code ...
```

**Acceptance Criteria**:
- [ ] `--recommend` flag added to add command
- [ ] Flag triggers recommendation before template selection
- [ ] Falls back to template list if no recommendations
- [ ] Falls back gracefully on errors
- [ ] Can be used with --client and --scope flags
- [ ] Mutually exclusive with --template flag (--template wins)

**Tests to Write** (5-8 CLI tests):
```python
def test_cli_recommend_flag_exists():
    """--recommend flag is recognized."""
    result = runner.invoke(cli, ["add", "postgres", "--help"])
    assert "--recommend" in result.output

def test_cli_recommend_triggers_recommendations(monkeypatch):
    """--recommend flag triggers recommendation engine."""
    # Mock the recommender
    mock_recommender = MagicMock()
    mock_recommender.recommend.return_value = []

    def mock_create_recommender():
        return mock_recommender

    monkeypatch.setattr(
        "mcpi.cli.create_default_template_recommender",
        mock_create_recommender
    )

    result = runner.invoke(cli, ["add", "postgres", "--recommend"])

    # Verify recommender was called
    mock_recommender.recommend.assert_called_once_with("postgres")

def test_cli_recommend_template_flag_wins():
    """--template flag takes precedence over --recommend."""
    # --template and --recommend both specified
    # Should use specified template, not recommend
    result = runner.invoke(cli, [
        "add", "postgres",
        "--template", "docker",
        "--recommend"
    ])

    # Should use docker template directly, not run recommendations
    # (verify by checking output or mock calls)
```

---

#### P1-13: Rich Console Output for Recommendations
**Effort**: 3 hours | **Dependencies**: P1-12 | **Status**: NOT STARTED

**Description**:
Implement beautiful Rich-formatted console output for displaying recommendations with confidence scores and explanations.

**Implementation**:
```python
def _handle_recommendations(
    recommendations: List[TemplateRecommendation],
    console: Console
) -> Optional[str]:
    """Display recommendations and get user choice.

    Returns:
        Template name if user accepts, None otherwise.
    """
    top = recommendations[0]

    # Show top recommendation
    console.print(f"\n[bold cyan]🧠 Recommended Template:[/bold cyan] {top.template.name}")
    console.print(f"[dim]Confidence: {top.confidence*100:.0f}%[/dim]\n")

    # Show reasons
    console.print("[bold]Why this template?[/bold]")
    for reason in top.reasons:
        console.print(f"  • {reason}")

    # Show alternatives if available
    if len(recommendations) > 1:
        console.print(f"\n[bold]Alternatives:[/bold]")
        for rec in recommendations[1:3]:  # Top 3 total
            console.print(f"  • {rec.template.name} ({rec.confidence*100:.0f}% match)")

    console.print()

    # Ask user to confirm
    from rich.prompt import Confirm
    if Confirm.ask(f"Continue with '{top.template.name}' template?", default=True):
        return top.template.name
    else:
        return None  # User declined
```

**Acceptance Criteria**:
- [ ] Recommendation header with template name
- [ ] Confidence percentage displayed
- [ ] "Why this template?" section with bullet points
- [ ] Alternative templates shown (top 3 total)
- [ ] Color coding (cyan for recommended, dim for confidence)
- [ ] Confirmation prompt to use recommended template
- [ ] Matches proposal examples

**Manual Verification**:
```bash
# Test in real terminal
cd ~/icode/mcpi
mcpi add postgres --recommend

# Expected output:
# 🧠 Recommended Template: docker
#    Confidence: 90%
#
# Why this template?
#   • Your project uses Docker Compose
#   • Matches your docker-compose service: postgres
#   • Optimized for nodejs projects
#
# Alternatives:
#   • local-development (40% match)
#   • production (30% match)
#
# Continue with 'docker' template? [Y/n]:
```

---

#### P1-14: Integrate with Template Selection Flow
**Effort**: 3 hours | **Dependencies**: P1-13 | **Status**: NOT STARTED

**Description**:
Seamlessly integrate recommendations into existing template selection workflow. No breaking changes to current behavior.

**Implementation**:
```python
# In src/mcpi/cli.py, refactor add command logic:

def add(...):
    """Add an MCP server from the registry."""

    # ... setup code ...

    selected_template = None

    # Path 1: --template flag (highest priority)
    if template:
        selected_template = template

    # Path 2: --recommend flag
    elif recommend:
        recommendations = _get_recommendations(server_id, console)
        if recommendations:
            selected_template = _handle_recommendations(recommendations, console)
        # If no recommendations or user declined, fall through to Path 3

    # Path 3: --list-templates or no flags
    if not selected_template:
        if list_templates or not template:
            # Show all templates and let user choose
            selected_template = _show_template_selection(server_id, console)

    if not selected_template:
        console.print("[yellow]No template selected[/yellow]")
        return

    # Continue with template installation...
```

**Acceptance Criteria**:
- [ ] Recommendations shown BEFORE template list
- [ ] User can accept recommendation (skip template list)
- [ ] User can decline recommendation (see template list)
- [ ] No recommendations = show template list automatically
- [ ] --template flag bypasses recommendations
- [ ] --recommend and --list-templates can coexist
- [ ] No breaking changes to existing flows

**Tests to Write** (8-10 integration tests):
```python
def test_recommend_then_accept():
    """User accepts top recommendation."""
    # Mock recommender to return recommendations
    # Mock user input to accept (Y)
    # Verify template is used without showing list

def test_recommend_then_decline():
    """User declines recommendation, sees template list."""
    # Mock recommender to return recommendations
    # Mock user input to decline (n)
    # Verify template list is shown

def test_recommend_no_results_shows_list():
    """No recommendations automatically shows template list."""
    # Mock recommender to return empty list
    # Verify template list is shown automatically

def test_template_flag_bypasses_recommend():
    """--template flag takes precedence."""
    # Use both --template and --recommend
    # Verify --template is used directly

def test_recommend_error_shows_list():
    """Recommendation error falls back to template list."""
    # Mock recommender to raise exception
    # Verify graceful fallback to template list
```

---

#### P1-15, P1-16, P1-17, P2-18: Comprehensive Testing
**Combined Effort**: 20 hours | **Dependencies**: All implementation tasks | **Status**: NOT STARTED

**Description**:
Write comprehensive test suite covering all new code. Target: 95%+ coverage, 100% pass rate.

**Test Files to Create**:
1. `tests/test_project_detector.py` (15-20 tests)
2. `tests/test_template_scoring.py` (10-15 tests)
3. `tests/test_template_recommender.py` (10-15 tests)
4. `tests/test_template_discovery_e2e.py` (8-10 tests)

**Coverage Target**:
- `discovery.py`: 95%+
- `recommender.py`: 95%+
- CLI integration: 90%+
- Template metadata: 100% (validation tests)

**Acceptance Criteria**:
- [ ] All unit tests written and passing
- [ ] All integration tests written and passing
- [ ] All edge cases covered
- [ ] Coverage >= 95% on new code
- [ ] No test failures in CI/CD

---

#### P2-19: Documentation Updates
**Effort**: 4 hours | **Dependencies**: P1-17 | **Status**: NOT STARTED

**Description**:
Update all documentation to reflect Template Discovery feature.

**Files to Update**:
- README.md (add --recommend examples)
- CLAUDE.md (usage guide, architecture section)
- Create: docs/TEMPLATE_METADATA_GUIDE.md (for template authors)
- CHANGELOG.md (v0.6.0 entry)

**Acceptance Criteria**:
- [ ] README has --recommend usage examples
- [ ] CLAUDE.md updated with architecture changes
- [ ] Template metadata guide created
- [ ] CHANGELOG.md has v0.6.0 entry
- [ ] CLI help text accurate

---

#### P2-20: Performance Testing
**Effort**: 2 hours | **Dependencies**: P1-17 | **Status**: NOT STARTED

**Description**:
Verify performance meets targets.

**Performance Targets**:
- Detection: < 100ms for typical project
- Recommendation: < 50ms for 10 templates
- Total: < 500ms end-to-end

**Acceptance Criteria**:
- [ ] Performance benchmarks written
- [ ] All targets met
- [ ] No regression in existing features

---

#### P3-21: Final Integration & Polish
**Effort**: 4 hours | **Dependencies**: All tasks | **Status**: NOT STARTED

**Description**:
Final polish, bug fixes, and pre-ship verification.

**Pre-Ship Checklist**:
- [ ] All tests passing (100%)
- [ ] Coverage >= 95% on new code
- [ ] No regressions
- [ ] Documentation complete
- [ ] CLI output polished
- [ ] Git history clean
- [ ] CHANGELOG updated

**Week 3 Checkpoint**: v0.6.0 ready to ship ✅

---

## 3. Implementation Schedule

### Week 1: Detection & Metadata (Days 1-5)
- **Day 1**: P0-1, P0-2 (ProjectContext, Docker detection)
- **Day 2**: P0-3, P0-4 (Language, Database detection)
- **Day 3**: P0-5, P0-6 (Integration, Model extension)
- **Day 4**: P0-7, P0-8 (Template metadata, Scoring)
- **Day 5**: P0-9, P1-15 (Data model, Unit tests)

**Deliverable**: Detection works, templates have metadata

### Week 2: Recommendation Engine (Days 6-10)
- **Day 6**: P0-10 (TemplateRecommender class)
- **Day 7**: P0-11, P1-16 (Factories, Scoring tests)
- **Day 8**: P1-17 (Integration tests)
- **Day 9**: P2-18 (Edge case tests)
- **Day 10**: P2-20 (Performance testing)

**Deliverable**: Recommendations work end-to-end

### Week 3: CLI & Ship (Days 11-15)
- **Day 11**: P1-12, P1-13 (CLI flag, Rich output)
- **Day 12**: P1-14, P2-19 (Integration, Documentation)
- **Day 13**: Bug fixing, testing marathon
- **Day 14**: P3-21 (Polish, pre-ship checklist)
- **Day 15**: PR, review, ship v0.6.0

**Deliverable**: v0.6.0 shipped to users

---

## 4. Success Metrics

### Quantitative Goals
- **Adoption Rate**: 40%+ users use --recommend flag
- **Acceptance Rate**: 85%+ accept top recommendation
- **Time Savings**: 75% faster (45 sec → 10 sec)
- **Test Coverage**: 95%+ on new code

### Qualitative Goals
- "It knew my project uses Docker!"
- "The explanation helped me understand"
- "I trust MCPI's recommendations"

---

## 5. Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| False positive detection | MEDIUM | LOW | Conservative scoring, show all templates |
| Missing project types | HIGH | MEDIUM | Start with 5 detectors, incremental |
| Performance issues | LOW | LOW | Cache results, fast file checks |
| Scoring quality poor | MEDIUM | MEDIUM | Extensive testing, tunable weights |

**Overall Risk**: LOW

---

## 6. Ship Criteria for v0.6.0

- [ ] All P0 tasks completed (21 tasks)
- [ ] Test coverage >= 95% on new code
- [ ] All tests passing (100%)
- [ ] No regressions in existing features
- [ ] Documentation updated (4 files)
- [ ] All 12 templates have metadata
- [ ] Manual E2E verification passes (8 scenarios)

---

## 7. Post-Implementation (v0.6.1+)

**Future Enhancements**:
- Framework detection (Django, Express, React)
- Environment detection (production vs development)
- Cloud provider detection (AWS, GCP, Azure)
- Performance caching
- User feedback mechanism (thumbs up/down)

---

**Generated by**: Implementation Planner Agent
**Date**: 2025-11-17 13:26:24
**Status**: Ready to execute - BEGIN P0-1 (ProjectContext dataclass)
**Next Review**: End of Week 1 (Day 5)
