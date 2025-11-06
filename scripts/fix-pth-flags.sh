#\!/bin/bash
# scripts/fix-pth-flags.sh
# Removes macOS hidden flags from .pth files (iCloud workaround)
set -e

VENV_PATH="${1:-.venv}"

echo "Fixing .pth file flags in ${VENV_PATH}..."

# Find and fix all .pth files
find "${VENV_PATH}" -name "*.pth" -type f 2>/dev/null | while read pth_file; do
    if ls -lO "$pth_file" 2>/dev/null | grep -q "hidden"; then
        chflags nohidden "$pth_file"
        echo "  Fixed: $(basename $pth_file)"
    fi
done

echo "Done\! All .pth files are now visible to Python."

