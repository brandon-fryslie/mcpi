# iCloud-Compatible Solution for .pth Hidden Flag Issue

**Date**: 2025-10-30
**Constraint**: Must keep source code in iCloud Drive
**Goal**: Make `.venv` local-only to avoid iCloud hidden flag issues

## Recommended Solution: Use .nosync Suffix

macOS iCloud has a built-in feature: directories with `.nosync` suffix are **excluded from iCloud sync**.

### Implementation

```bash
cd ~/icode/mcpi

# 1. Remove current broken venv
rm -rf .venv

# 2. Create .venv.nosync (iCloud will ignore it)
uv sync --python-preference managed --python 3.12

# Wait, uv creates .venv not .venv.nosync, so we need to configure it

# Actually, better approach:
# Create .venv.nosync and symlink
python -m venv .venv.nosync
ln -sf .venv.nosync .venv

# Or even better - tell uv to use .venv.nosync directly
UV_PROJECT_ENVIRONMENT=.venv.nosync uv sync

# But simplest: rename after creation
uv sync
mv .venv .venv.nosync
ln -s .venv.nosync .venv
```

**Problem**: Tools expect `.venv`, not `.venv.nosync`.

### Better Solution: Configure UV to Use Custom Location

Set `UV_PROJECT_ENVIRONMENT` to use `.venv.nosync`:

```bash
cd ~/icode/mcpi

# Add to .envrc (if using direnv) or .env
echo 'export UV_PROJECT_ENVIRONMENT=.venv.nosync' > .envrc

# Or set in your shell profile
echo 'export UV_PROJECT_ENVIRONMENT=.venv.nosync' >> ~/.zshrc

# Then recreate venv
rm -rf .venv .venv.nosync
uv sync
```

**Problem**: This affects ALL projects, not just mcpi.

## Alternative Solutions

### Option A: Post-Install Hook (Automated Fix)

Create a hook that automatically removes hidden flags after each install.

**Implementation**:

1. Create a post-install script:

```bash
#!/bin/bash
# scripts/fix-pth-flags.sh
set -e

VENV_PATH="${1:-.venv}"
PTH_DIR="${VENV_PATH}/lib/python3.*/site-packages"

echo "Fixing .pth file flags in ${VENV_PATH}..."

# Find and fix all .pth files
find "${VENV_PATH}" -name "*.pth" -type f 2>/dev/null | while read pth_file; do
    # Check if file has hidden flag
    if ls -lO "$pth_file" 2>/dev/null | grep -q "hidden"; then
        chflags nohidden "$pth_file"
        echo "  Fixed: $pth_file"
    fi
done

echo "Done!"
```

2. Make it executable:

```bash
chmod +x scripts/fix-pth-flags.sh
```

3. Run after every `uv sync`:

```bash
# Manual
uv sync && ./scripts/fix-pth-flags.sh

# Or create an alias
alias uvsync='uv sync && ./scripts/fix-pth-flags.sh'
```

**Pros**:
- Automated
- Source stays in iCloud
- Works with standard tools

**Cons**:
- Must remember to run script
- iCloud can reset flags again
- Requires manual intervention

### Option B: Watch Script (Continuous Fix)

Create a background process that continuously monitors and fixes flags.

```bash
#!/bin/bash
# scripts/watch-pth-flags.sh

VENV_PATH=".venv"
INTERVAL=60  # Check every 60 seconds

echo "Watching .pth files in ${VENV_PATH} for hidden flags..."
echo "Press Ctrl+C to stop"

while true; do
    find "${VENV_PATH}" -name "*.pth" -type f 2>/dev/null | while read pth_file; do
        if ls -lO "$pth_file" 2>/dev/null | grep -q "hidden"; then
            chflags nohidden "$pth_file"
            echo "$(date): Fixed hidden flag on $pth_file"
        fi
    done
    sleep "$INTERVAL"
done
```

Run in background:
```bash
./scripts/watch-pth-flags.sh &
```

**Pros**:
- Automatic and continuous
- No manual intervention needed

**Cons**:
- Must keep script running
- Resource overhead
- Hack-ish solution

### Option C: LaunchAgent (macOS Service)

Create a LaunchAgent that runs the fix script periodically.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.user.mcpi.fix-pth-flags</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/bmf/icode/mcpi/scripts/fix-pth-flags.sh</string>
    </array>
    <key>StartInterval</key>
    <integer>300</integer> <!-- Run every 5 minutes -->
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
```

Install:
```bash
cp scripts/com.user.mcpi.fix-pth-flags.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.user.mcpi.fix-pth-flags.plist
```

**Pros**:
- Fully automated
- Runs at startup
- No manual intervention

**Cons**:
- Complex setup
- Project-specific service
- Still a workaround

### Option D: Only Use UV Tool Install (Recommended!)

The simplest solution that actually works reliably:

**Reality Check**:
- UV tool install at `~/.local/share/uv/tools/mcpi/` works perfectly ✓
- It's NOT in iCloud Drive ✓
- No hidden flag issues ✓
- Always reliable ✓

**For development**:
```bash
# Use UV tool for CLI
uv tool install --editable ~/icode/mcpi
mcpi --help  # Always works

# Use pytest directly for testing (doesn't need venv)
cd ~/icode/mcpi
pytest  # Uses pythonpath from pyproject.toml

# No need for dev venv activation!
```

**Why this works**:
- UV tool environment is local-only (not in iCloud)
- Source code stays in iCloud (backed up)
- Tests work via `pythonpath = ["src"]` in pyproject.toml
- No hidden flag issues ever

**What you lose**:
- Can't do `source .venv/bin/activate` for development
- But you don't actually need it!

**What you gain**:
- 100% reliable
- No workarounds
- No maintenance
- Clean separation

## Recommended Approach

**Use Option D: UV Tool Install Only**

### Setup

```bash
cd ~/icode/mcpi

# 1. Remove problematic dev venv (optional - can keep for other tools)
# rm -rf .venv

# 2. Install as UV tool (already done, but ensure it's up to date)
uv tool install --editable ~/icode/mcpi

# 3. For development, just edit code and test
# - Edit files: use your editor normally
# - Run CLI: mcpi <command>
# - Run tests: pytest (no activation needed)
# - Type checking: mypy src/
# - Formatting: black src/ tests/

# 4. When you make changes to CLI
#    UV tool automatically picks them up (it's --editable)
mcpi --help  # Shows latest changes
```

### Development Workflow

```bash
# Edit code
vim src/mcpi/cli.py

# Test immediately
mcpi --version  # UV tool picks up changes

# Run test suite
pytest

# No venv activation needed!
```

### Why This Is Actually Better

1. **Single source of truth**: One installation, not two
2. **Always available**: Works from any directory
3. **iCloud safe**: UV tool is in `~/.local/`, not iCloud
4. **Zero maintenance**: No scripts, no workarounds
5. **Matches production**: How users will actually run mcpi

### When You DO Need a Venv

If you need a venv for other tools (IDE integration, etc.):

```bash
# Create .venv.nosync (excluded from iCloud)
mkdir .venv.nosync
ln -s .venv.nosync .venv

# Use UV with explicit path
UV_PROJECT_ENVIRONMENT=.venv.nosync uv sync

# Or manually create and populate
python -m venv .venv.nosync
source .venv.nosync/bin/activate
pip install -e .
```

Then in your IDE, point to `.venv.nosync/bin/python`.

## Implementation Plan

### Immediate Fix (Right Now)

```bash
cd ~/icode/mcpi

# Fix current venv (temporary until iCloud resets)
chflags nohidden .venv/lib/python3.12/site-packages/*.pth

# Verify it works
source .venv/bin/activate
mcpi --help
```

### Permanent Fix (Recommended)

```bash
# 1. Create and use .venv.nosync
cd ~/icode/mcpi
rm -rf .venv

# 2. Create venv with .nosync suffix
python -m venv .venv.nosync

# 3. Activate and install
source .venv.nosync/bin/activate
pip install -e .

# 4. Create symlink for tool compatibility
ln -s .venv.nosync .venv

# 5. Test
python -c "import mcpi; print(mcpi.__file__)"
mcpi --help

# 6. Verify .nosync is working
ls -lO .venv.nosync/lib/python3.12/site-packages/*.pth
# Should NOT have "hidden" flag
```

### Even Better: Just Use UV Tool

```bash
# Ensure UV tool is installed and current
uv tool install --editable ~/icode/mcpi --force

# Remove dev venv (optional)
rm -rf .venv .venv.nosync

# Development workflow
mcpi --help    # Run CLI
pytest         # Run tests
black src/     # Format code

# No activation needed!
```

## Testing the Solution

After implementing `.venv.nosync`:

```bash
# 1. Check the flag is not set
ls -lO .venv.nosync/lib/python3.12/site-packages/*.pth | grep hidden
# Should return nothing

# 2. Wait for iCloud sync (or force it)
# Let iCloud sync run for 10-15 minutes

# 3. Re-check flags
ls -lO .venv.nosync/lib/python3.12/site-packages/*.pth | grep hidden
# Should still return nothing (.nosync means iCloud doesn't touch it)

# 4. Verify import still works
source .venv/bin/activate
python -c "import mcpi"
# Should succeed

# 5. Test over multiple days
# Verify it stays working
```

## Documentation Updates

### Add to README.md

```markdown
## macOS iCloud Drive Considerations

If developing in iCloud Drive, use one of these approaches:

### Option 1: UV Tool Install (Recommended)
\`\`\`bash
uv tool install --editable .
mcpi --help  # Always works, no venv activation needed
pytest       # Run tests without activation
\`\`\`

### Option 2: Use .venv.nosync
\`\`\`bash
python -m venv .venv.nosync
ln -s .venv.nosync .venv
source .venv/bin/activate
pip install -e .
\`\`\`

The `.nosync` suffix tells iCloud to exclude the directory from sync,
preventing the "hidden flag" issue that breaks .pth file processing.
```

### Add to CLAUDE.md

```markdown
## Development with iCloud Drive

This project can be developed in iCloud Drive with the following considerations:

1. **Recommended**: Use `uv tool install --editable .` for CLI development
2. **Alternative**: Create virtual environment as `.venv.nosync` to exclude from iCloud sync
3. **Avoid**: Regular `.venv` in iCloud (causes intermittent .pth file issues)

See `.agent_planning/ICLOUD-COMPATIBLE-FIX-2025-10-30.md` for details.
```

## Summary

| Solution | Reliability | Complexity | Recommendation |
|----------|-------------|------------|----------------|
| UV Tool Only | ★★★★★ | ★☆☆☆☆ | **BEST** |
| .venv.nosync | ★★★★☆ | ★★☆☆☆ | Good |
| Post-install Hook | ★★☆☆☆ | ★★★☆☆ | Workaround |
| Watch Script | ★★★☆☆ | ★★★★☆ | Over-engineered |
| LaunchAgent | ★★★☆☆ | ★★★★★ | Over-engineered |

**Recommended**: Use UV tool install for CLI + pytest for testing (no venv needed).

**Alternative**: Use `.venv.nosync` if you need IDE integration or other venv-dependent tools.

## Next Steps

1. Choose approach (UV tool or .venv.nosync)
2. Implement solution
3. Test reliability
4. Update documentation
5. Never think about this again!
