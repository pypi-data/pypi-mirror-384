"""Version management functionality."""

import re
from datetime import datetime
from pathlib import Path
from typing import List


class Version:
    """Represents a single file version."""

    def __init__(self, path: Path):
        """
        Initialize Version from backup file path.

        Args:
            path: Path to version file
        """
        self._path = path
        self._parse_filename()

    def _parse_filename(self):
        """Parse timestamp from filename."""
        # Format: YYYYMMDD_HHMMSS_NNN.ext
        match = re.match(r"(\d{8})_(\d{6})_(\d{3})(\..*)?$", self._path.name)
        if match:
            date_str, time_str, increment, ext = match.groups()
            dt_str = f"{date_str}{time_str}"
            self._timestamp = datetime.strptime(dt_str, "%Y%m%d%H%M%S")
            self._increment = int(increment)
        else:
            # Fallback for non-standard names
            if self._path.exists():
                self._timestamp = datetime.fromtimestamp(self._path.stat().st_mtime)
            else:
                self._timestamp = datetime.now()
            self._increment = 0

    @property
    def timestamp(self) -> datetime:
        """When version was created."""
        return self._timestamp

    @property
    def size(self) -> int:
        """Size in bytes."""
        if self._path.exists():
            return self._path.stat().st_size
        return 0

    @property
    def path(self) -> Path:
        """Path to version file."""
        return self._path

    @property
    def checksum(self) -> str:
        """SHA256 hash of content (not implemented yet)."""
        return ""

    def __repr__(self) -> str:
        return f"Version({self._path.name}, {self.timestamp.isoformat()})"


def list_versions(versions_dir: Path) -> List[Version]:
    """
    List all versions in a directory, sorted newest first.

    Args:
        versions_dir: Directory containing version files

    Returns:
        List of Version objects, newest first
    """
    if not versions_dir.exists():
        return []

    versions = []
    for file_path in versions_dir.iterdir():
        if file_path.is_file() and not file_path.name.endswith(".meta"):
            try:
                versions.append(Version(file_path))
            except Exception:
                # Skip files that don't match version pattern
                continue

    # Sort by filename in reverse (which will sort by date, time, then increment)
    # This ensures proper ordering even when timestamps are identical
    versions.sort(key=lambda v: v.path.name, reverse=True)
    return versions
