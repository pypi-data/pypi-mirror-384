"""File wrapper with versioning support."""

import io
import warnings
from pathlib import Path
from typing import Optional

from versionio.policy import VersionPolicy
from versionio.utils import (
    file_lock,
    get_next_version_path,
    should_create_backup,
)
from versionio.exceptions import StorageError


class VersionedIOWrapper(io.IOBase):
    """
    Wrapper around file object that handles versioning.

    This class wraps a standard file object and ensures backups
    are created before any write operations.
    """

    def __init__(
        self,
        file_obj: io.IOBase,
        file_path: Path,
        mode: str,
        versioning: bool = True,
        policy: Optional[VersionPolicy] = None,
    ):
        """
        Initialize the wrapper.

        Args:
            file_obj: Underlying file object
            file_path: Path to the file
            mode: File open mode
            versioning: Whether to enable versioning
            policy: Versioning policy
        """
        self._file = file_obj
        self._path = file_path
        self._mode = mode
        self._versioning = versioning
        self._policy = policy or VersionPolicy()
        self._backup_created = False

    def _create_backup(self):
        """Create a backup of the current file if needed."""
        if self._backup_created or not self._versioning:
            return

        if not should_create_backup(self._mode, self._path):
            self._backup_created = True
            return

        try:
            with file_lock(self._path):
                self._perform_backup()
        except Exception as e:
            warnings.warn(f"Failed to create backup: {e}")
            # Continue without backup rather than failing the operation

        self._backup_created = True

    def _perform_backup(self):
        """Perform the actual backup operation."""
        # Create versions directory
        versions_base = self._path.parent / ".versions"
        versions_dir = versions_base / self._path.name
        versions_dir.mkdir(parents=True, exist_ok=True)

        # Determine backup file path
        backup_path = get_next_version_path(
            versions_dir, self._path.stem, self._path.suffix
        )

        # Copy file to backup location
        try:
            backup_path.write_bytes(self._path.read_bytes())
        except Exception as e:
            raise StorageError(f"Failed to create backup: {e}")

        # Apply retention policy
        self._apply_retention_policy(versions_dir)

    def _apply_retention_policy(self, versions_dir: Path):
        """Apply retention policy to remove old versions."""
        if self._policy.max_versions is None:
            return

        # Import here to avoid circular import
        from versionio.version import list_versions

        versions = list_versions(versions_dir)

        if len(versions) > self._policy.max_versions:
            # Remove oldest versions
            for version in versions[self._policy.max_versions :]:
                try:
                    version.path.unlink()
                    # Also remove metadata file if it exists
                    meta_path = version.path.with_suffix(version.path.suffix + ".meta")
                    if meta_path.exists():
                        meta_path.unlink()
                except Exception as e:
                    warnings.warn(f"Failed to remove old version {version.path}: {e}")

    # Delegate all file operations to underlying file object
    def read(self, *args, **kwargs):
        return self._file.read(*args, **kwargs)

    def write(self, *args, **kwargs):
        self._create_backup()
        return self._file.write(*args, **kwargs)

    def writelines(self, *args, **kwargs):
        self._create_backup()
        return self._file.writelines(*args, **kwargs)

    def truncate(self, *args, **kwargs):
        self._create_backup()
        return self._file.truncate(*args, **kwargs)

    def seek(self, *args, **kwargs):
        return self._file.seek(*args, **kwargs)

    def tell(self, *args, **kwargs):
        return self._file.tell(*args, **kwargs)

    def flush(self, *args, **kwargs):
        return self._file.flush(*args, **kwargs)

    def close(self):
        return self._file.close()

    def fileno(self):
        return self._file.fileno()

    def isatty(self):
        return self._file.isatty()

    def readable(self):
        return self._file.readable()

    def writable(self):
        return self._file.writable()

    def seekable(self):
        return self._file.seekable()

    @property
    def closed(self):
        return self._file.closed

    @property
    def mode(self):
        return self._file.mode

    @property
    def name(self):
        return self._file.name

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._file.__exit__(exc_type, exc_val, exc_tb)

    def __iter__(self):
        return self._file.__iter__()

    def __next__(self):
        return self._file.__next__()

    def readline(self, *args, **kwargs):
        return self._file.readline(*args, **kwargs)

    def readlines(self, *args, **kwargs):
        return self._file.readlines(*args, **kwargs)
