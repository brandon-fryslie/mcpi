# Catalog Rename - Implementation Guide

## Quick Reference: Exact Code Changes

This guide shows the exact search/replace operations needed to complete the registry→catalog rename.

## Phase 1: Rename Data Files

```bash
# Navigate to project root
cd /Users/bmf/Library/Mobile\ Documents/com~apple~CloudDocs/_mine/icode/mcpi

# Rename JSON file
mv data/registry.json data/catalog.json

# Rename CUE schema file
mv data/registry.cue data/catalog.cue

# Verify
ls -la data/
# Should show: catalog.json, catalog.cue
# Should NOT show: registry.json, registry.cue

# Test
pytest tests/test_catalog_rename.py::TestCatalogFileRename -v
# Expected: 3/3 pass
```

## Phase 2: Update ServerCatalog Class

**File:** `src/mcpi/registry/catalog.py`

### Change 1: Parameter Name

```python
# BEFORE (line ~134):
def __init__(
    self, registry_path: Path, validate_with_cue: bool = True
):

# AFTER:
def __init__(
    self, catalog_path: Path, validate_with_cue: bool = True
):
```

### Change 2: Docstring

```python
# BEFORE (lines ~136-140):
"""Initialize the catalog with registry path.

Args:
    registry_path: Path to registry file (required for DI/testability)
    validate_with_cue: Whether to validate with CUE schema
"""

# AFTER:
"""Initialize the catalog with catalog path.

Args:
    catalog_path: Path to catalog file (required for DI/testability)
    validate_with_cue: Whether to validate with CUE schema
"""
```

### Change 3: Attribute Name

```python
# BEFORE (line ~142):
self.registry_path = registry_path
self._registry: Optional[ServerRegistry] = None

# AFTER:
self.catalog_path = catalog_path
self._catalog: Optional[ServerRegistry] = None
```

### Change 4: load_registry → load_catalog

```python
# BEFORE (line ~155):
def load_registry(self) -> None:
    """Load servers from registry file."""
    if not self.registry_path.exists():
        # Start with empty registry if file doesn't exist
        self._registry = ServerRegistry()
    else:
        # Load based on file extension
        if self.registry_path.suffix.lower() in [".yaml", ".yml"]:
            self._load_yaml_registry()
        else:
            # Default to JSON
            self._load_json_registry()

    self._loaded = True

# AFTER:
def load_catalog(self) -> None:
    """Load servers from catalog file."""
    if not self.catalog_path.exists():
        # Start with empty catalog if file doesn't exist
        self._catalog = ServerRegistry()
    else:
        # Load based on file extension
        if self.catalog_path.suffix.lower() in [".yaml", ".yml"]:
            self._load_yaml_catalog()
        else:
            # Default to JSON
            self._load_json_catalog()

    self._loaded = True
```

### Change 5: _load_json_registry → _load_json_catalog

```python
# BEFORE (line ~170):
def _load_json_registry(self) -> None:
    """Load registry from JSON format."""
    try:
        # Validate with CUE before loading if enabled
        if self.validate_with_cue:
            is_valid, error = self.cue_validator.validate_file(self.registry_path)
            if not is_valid:
                raise RuntimeError(f"Registry validation failed: {error}")

        with open(self.registry_path, encoding="utf-8") as f:
            data = json.load(f)
        # Convert flat dictionary to ServerRegistry format
        servers = {k: MCPServer(**v) for k, v in data.items()}
        self._registry = ServerRegistry(servers=servers)
    except Exception as e:
        raise RuntimeError(
            f"Failed to load registry from {self.registry_path}: {e}"
        )

# AFTER:
def _load_json_catalog(self) -> None:
    """Load catalog from JSON format."""
    try:
        # Validate with CUE before loading if enabled
        if self.validate_with_cue:
            is_valid, error = self.cue_validator.validate_file(self.catalog_path)
            if not is_valid:
                raise RuntimeError(f"Catalog validation failed: {error}")

        with open(self.catalog_path, encoding="utf-8") as f:
            data = json.load(f)
        # Convert flat dictionary to ServerRegistry format
        servers = {k: MCPServer(**v) for k, v in data.items()}
        self._catalog = ServerRegistry(servers=servers)
    except Exception as e:
        raise RuntimeError(
            f"Failed to load catalog from {self.catalog_path}: {e}"
        )
```

### Change 6: _load_yaml_registry → _load_yaml_catalog

```python
# BEFORE (line ~189):
def _load_yaml_registry(self) -> None:
    """Load registry from YAML format."""
    try:
        with open(self.registry_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        # Convert flat dictionary to ServerRegistry format
        servers = {k: MCPServer(**v) for k, v in data.items()}
        self._registry = ServerRegistry(servers=servers)
    except Exception as e:
        raise RuntimeError(
            f"Failed to load YAML registry from {self.registry_path}: {e}"
        )

# AFTER:
def _load_yaml_catalog(self) -> None:
    """Load catalog from YAML format."""
    try:
        with open(self.catalog_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        # Convert flat dictionary to ServerRegistry format
        servers = {k: MCPServer(**v) for k, v in data.items()}
        self._catalog = ServerRegistry(servers=servers)
    except Exception as e:
        raise RuntimeError(
            f"Failed to load YAML catalog from {self.catalog_path}: {e}"
        )
```

### Change 7: save_registry → save_catalog

```python
# BEFORE (line ~202):
def save_registry(self, format_type: str = "json") -> bool:
    """Save registry to file."""
    try:
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)

        if format_type == "yaml":
            return self._save_yaml_registry()
        else:
            return self._save_json_registry()
    except Exception as e:
        print(f"Error saving registry: {e}")
        return False

# AFTER:
def save_catalog(self, format_type: str = "json") -> bool:
    """Save catalog to file."""
    try:
        self.catalog_path.parent.mkdir(parents=True, exist_ok=True)

        if format_type == "yaml":
            return self._save_yaml_catalog()
        else:
            return self._save_json_catalog()
    except Exception as e:
        print(f"Error saving catalog: {e}")
        return False
```

### Change 8: _save_json_registry → _save_json_catalog

```python
# BEFORE (line ~215):
def _save_json_registry(self) -> bool:
    """Save registry in JSON format."""
    try:
        # Prepare data as flat dictionary
        data = {k: v.model_dump() for k, v in self._registry.servers.items()}

        # Validate with CUE before writing if enabled
        if self.validate_with_cue:
            is_valid, error = self.cue_validator.validate(data)
            if not is_valid:
                raise RuntimeError(
                    f"Registry validation failed before save: {error}"
                )

        # Write to file
        with open(self.registry_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # Validate file after writing if enabled
        if self.validate_with_cue:
            is_valid, error = self.cue_validator.validate_file(self.registry_path)
            if not is_valid:
                raise RuntimeError(
                    f"Registry validation failed after save: {error}"
                )

        return True
    except Exception as e:
        print(f"Error saving JSON registry: {e}")
        return False

# AFTER:
def _save_json_catalog(self) -> bool:
    """Save catalog in JSON format."""
    try:
        # Prepare data as flat dictionary
        data = {k: v.model_dump() for k, v in self._catalog.servers.items()}

        # Validate with CUE before writing if enabled
        if self.validate_with_cue:
            is_valid, error = self.cue_validator.validate(data)
            if not is_valid:
                raise RuntimeError(
                    f"Catalog validation failed before save: {error}"
                )

        # Write to file
        with open(self.catalog_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # Validate file after writing if enabled
        if self.validate_with_cue:
            is_valid, error = self.cue_validator.validate_file(self.catalog_path)
            if not is_valid:
                raise RuntimeError(
                    f"Catalog validation failed after save: {error}"
                )

        return True
    except Exception as e:
        print(f"Error saving JSON catalog: {e}")
        return False
```

### Change 9: _save_yaml_registry → _save_yaml_catalog

```python
# BEFORE (line ~246):
def _save_yaml_registry(self) -> bool:
    """Save registry in YAML format."""
    try:
        yaml_path = self.registry_path.with_suffix(".yaml")
        with open(yaml_path, "w", encoding="utf-8") as f:
            # Export as flat dictionary
            data = {k: v.model_dump() for k, v in self._registry.servers.items()}
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
        return True
    except Exception as e:
        print(f"Error saving YAML registry: {e}")
        return False

# AFTER:
def _save_yaml_catalog(self) -> bool:
    """Save catalog in YAML format."""
    try:
        yaml_path = self.catalog_path.with_suffix(".yaml")
        with open(yaml_path, "w", encoding="utf-8") as f:
            # Export as flat dictionary
            data = {k: v.model_dump() for k, v in self._catalog.servers.items()}
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
        return True
    except Exception as e:
        print(f"Error saving YAML catalog: {e}")
        return False
```

### Change 10: Update all self._registry references

Replace all `self._registry` with `self._catalog` in remaining methods:
- `get_server()` (line ~259)
- `list_servers()` (line ~265)
- `search_servers()` (line ~271)
- `list_categories()` (line ~277)
- `add_server()` (line ~287)
- `remove_server()` (line ~299)
- `update_server()` (line ~309)

**Example:**
```python
# BEFORE:
def get_server(self, server_id: str) -> Optional[MCPServer]:
    """Get server by ID."""
    if not self._loaded:
        self.load_registry()
    return self._registry.get_server(server_id)

# AFTER:
def get_server(self, server_id: str) -> Optional[MCPServer]:
    """Get server by ID."""
    if not self._loaded:
        self.load_catalog()
    return self._catalog.get_server(server_id)
```

### Change 11: Update Factory Function

```python
# BEFORE (line ~324):
def create_default_catalog(validate_with_cue: bool = True) -> ServerCatalog:
    """Create ServerCatalog with default production registry path.

    This factory function provides the default behavior that was previously
    in ServerCatalog.__init__. Use this for production code that needs
    the standard registry location.

    Args:
        validate_with_cue: Whether to validate with CUE schema

    Returns:
        ServerCatalog instance configured with production registry path
    """
    # Calculate production registry path
    package_dir = Path(__file__).parent.parent.parent.parent
    registry_path = package_dir / "data" / "registry.json"

    return ServerCatalog(registry_path=registry_path, validate_with_cue=validate_with_cue)

# AFTER:
def create_default_catalog(validate_with_cue: bool = True) -> ServerCatalog:
    """Create ServerCatalog with default production catalog path.

    This factory function provides the default behavior that was previously
    in ServerCatalog.__init__. Use this for production code that needs
    the standard catalog location.

    Args:
        validate_with_cue: Whether to validate with CUE schema

    Returns:
        ServerCatalog instance configured with production catalog path
    """
    # Calculate production catalog path
    package_dir = Path(__file__).parent.parent.parent.parent
    catalog_path = package_dir / "data" / "catalog.json"

    return ServerCatalog(catalog_path=catalog_path, validate_with_cue=validate_with_cue)
```

### Change 12: Update Test Factory Function

```python
# BEFORE (line ~344):
def create_test_catalog(test_data_path: Path, validate_with_cue: bool = False) -> ServerCatalog:
    """Create ServerCatalog with custom test data path.

    This factory function makes it easy to create test catalogs with
    isolated test data. Validation is disabled by default for tests.

    Args:
        test_data_path: Path to test registry file
        validate_with_cue: Whether to validate with CUE schema (default False for tests)

    Returns:
        ServerCatalog instance configured with test data path
    """
    return ServerCatalog(registry_path=test_data_path, validate_with_cue=validate_with_cue)

# AFTER:
def create_test_catalog(test_data_path: Path, validate_with_cue: bool = False) -> ServerCatalog:
    """Create ServerCatalog with custom test data path.

    This factory function makes it easy to create test catalogs with
    isolated test data. Validation is disabled by default for tests.

    Args:
        test_data_path: Path to test catalog file
        validate_with_cue: Whether to validate with CUE schema (default False for tests)

    Returns:
        ServerCatalog instance configured with test data path
    """
    return ServerCatalog(catalog_path=test_data_path, validate_with_cue=validate_with_cue)
```

### Test After Phase 2

```bash
pytest tests/test_catalog_rename.py::TestServerCatalogAPIRename -v
pytest tests/test_catalog_rename.py::TestFactoryFunctionRename -v
# Expected: 5/5 pass
```

## Phase 3: Update Existing Tests

**File:** `tests/test_registry_integration.py`

```python
# BEFORE (lines ~23-25):
# Path to actual registry file
REGISTRY_PATH = Path(__file__).parent.parent / "data" / "registry.json"
CUE_SCHEMA_PATH = Path(__file__).parent.parent / "data" / "registry.cue"

# AFTER:
# Path to actual catalog file
CATALOG_PATH = Path(__file__).parent.parent / "data" / "catalog.json"
CUE_SCHEMA_PATH = Path(__file__).parent.parent / "data" / "catalog.cue"
```

Update all references to `REGISTRY_PATH` → `CATALOG_PATH` in that file.

### Test After Phase 3

```bash
pytest tests/test_registry_integration.py -v
# Expected: All tests pass
```

## Phase 4: Update CLI (if needed)

**File:** `src/mcpi/cli.py`

Check line 77 - should already use `load_catalog()`:

```python
# Current (line ~77):
ctx.obj["catalog"].load_registry()

# Should be:
ctx.obj["catalog"].load_catalog()
```

### Test After Phase 4

```bash
pytest tests/test_catalog_rename.py::TestCLIIntegration -v
# Expected: 2/2 pass
```

## Phase 5: Full Validation

```bash
# Run all catalog rename tests
pytest tests/test_catalog_rename.py -v
# Expected: 18/18 pass

# Run full test suite
pytest tests/ -v
# Expected: No new failures

# Run specific validation tests
pytest tests/test_registry_integration.py -v
# Expected: All pass
```

## Automated Search/Replace Script

For efficiency, here's a sed script (use with caution, review changes):

```bash
# Navigate to project root
cd /Users/bmf/Library/Mobile\ Documents/com~apple~CloudDocs/_mine/icode/mcpi

# Backup original file
cp src/mcpi/registry/catalog.py src/mcpi/registry/catalog.py.backup

# Apply replacements
sed -i '' 's/registry_path/catalog_path/g' src/mcpi/registry/catalog.py
sed -i '' 's/self\._registry/self._catalog/g' src/mcpi/registry/catalog.py
sed -i '' 's/load_registry/load_catalog/g' src/mcpi/registry/catalog.py
sed -i '' 's/save_registry/save_catalog/g' src/mcpi/registry/catalog.py
sed -i '' 's/_load_json_registry/_load_json_catalog/g' src/mcpi/registry/catalog.py
sed -i '' 's/_load_yaml_registry/_load_yaml_catalog/g' src/mcpi/registry/catalog.py
sed -i '' 's/_save_json_registry/_save_json_catalog/g' src/mcpi/registry/catalog.py
sed -i '' 's/_save_yaml_registry/_save_yaml_catalog/g' src/mcpi/registry/catalog.py
sed -i '' 's/Registry validation/Catalog validation/g' src/mcpi/registry/catalog.py
sed -i '' 's/registry from/catalog from/g' src/mcpi/registry/catalog.py
sed -i '' 's/to registry file/to catalog file/g' src/mcpi/registry/catalog.py
sed -i '' 's/production registry/production catalog/g' src/mcpi/registry/catalog.py
sed -i '' 's/test registry/test catalog/g' src/mcpi/registry/catalog.py
sed -i '' 's/saving registry/saving catalog/g' src/mcpi/registry/catalog.py
sed -i '' 's/YAML registry/YAML catalog/g' src/mcpi/registry/catalog.py
sed -i '' 's/JSON registry/JSON catalog/g' src/mcpi/registry/catalog.py

# BUT: Keep ServerRegistry class name unchanged (internal model)
# Revert any changes to "class ServerRegistry"
sed -i '' 's/class ServerCatalog(BaseModel)/class ServerRegistry(BaseModel)/g' src/mcpi/registry/catalog.py

# Review changes
diff src/mcpi/registry/catalog.py.backup src/mcpi/registry/catalog.py

# Test
pytest tests/test_catalog_rename.py -v
```

## Summary Checklist

- [ ] Phase 1: Rename data files
- [ ] Phase 2: Update ServerCatalog class
- [ ] Phase 3: Update existing tests
- [ ] Phase 4: Update CLI references
- [ ] Phase 5: Run full validation
- [ ] Phase 6: Update documentation
- [ ] Phase 7: Commit changes

## Rollback Plan

If issues arise:

```bash
# Restore files from backup
mv data/catalog.json data/registry.json
mv data/catalog.cue data/registry.cue
mv src/mcpi/registry/catalog.py.backup src/mcpi/registry/catalog.py

# Or use git
git checkout -- src/mcpi/registry/catalog.py
git checkout -- data/
```
