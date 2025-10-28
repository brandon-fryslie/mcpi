"""CUE schema validation for registry data."""

import json
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional


class CUEValidator:
    """Validate registry data against CUE schema."""

    def __init__(self, schema_path: Optional[Path] = None):
        """Initialize with CUE schema path."""
        if schema_path is None:
            # Default to package data directory
            package_dir = Path(__file__).parent.parent.parent.parent
            schema_path = package_dir / "data" / "registry.cue"

        self.schema_path = schema_path

        # Check if cue is available
        self._check_cue_available()

    def _check_cue_available(self) -> None:
        """Check if cue command is available."""
        try:
            result = subprocess.run(["cue", "version"], capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError(
                    "CUE command not found. Please install CUE from https://cuelang.org/docs/install/"
                )
        except FileNotFoundError:
            raise RuntimeError(
                "CUE command not found. Please install CUE from https://cuelang.org/docs/install/"
            )

    def validate(self, data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate data against CUE schema.

        Args:
            data: Registry data to validate

        Returns:
            (is_valid, error_message) tuple
        """
        try:
            # Create temporary file with data
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            ) as f:
                json.dump(data, f, indent=2)
                data_path = f.name

            try:
                # Run cue vet to validate
                result = subprocess.run(
                    ["cue", "vet", str(self.schema_path), data_path],
                    capture_output=True,
                    text=True,
                )

                if result.returncode == 0:
                    return True, None
                else:
                    return False, result.stderr.strip()
            finally:
                # Clean up temp file
                Path(data_path).unlink(missing_ok=True)

        except Exception as e:
            return False, f"Validation error: {str(e)}"

    def validate_file(self, file_path: Path) -> tuple[bool, Optional[str]]:
        """Validate a JSON file against CUE schema.

        Args:
            file_path: Path to JSON file to validate

        Returns:
            (is_valid, error_message) tuple
        """
        try:
            # Run cue vet directly on the file
            result = subprocess.run(
                ["cue", "vet", str(self.schema_path), str(file_path)],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                return True, None
            else:
                return False, result.stderr.strip()

        except Exception as e:
            return False, f"Validation error: {str(e)}"
