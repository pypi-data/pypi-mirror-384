"""
Core versionIO functionality.

Example usage:

    # Example 1: Simple file write with automatic versioning
    from versionio import open
    
    with open('config.json', 'w') as f:
        f.write('{"setting": "value1"}')
    
    # Later, update the file (previous version is automatically backed up)
    with open('config.json', 'w') as f:
        f.write('{"setting": "value2"}')
    
    # Example 2: Custom retention policy
    from versionio import open, VersionPolicy
    
    # Keep only last 3 versions
    policy = VersionPolicy(max_versions=3)
    
    for i in range(10):
        with open('data.txt', 'w', policy=policy) as f:
            f.write(f'Version {i}')
    # Only the last 3 backups are kept
"""

import builtins
import warnings
from pathlib import Path
from typing import Any, Optional, Union, IO

from versionio.wrapper import VersionedIOWrapper
from versionio.policy import VersionPolicy
from versionio.version import Version, list_versions
from versionio.exceptions import VersionNotFound
from versionio.utils import file_lock, get_next_version_path


def _create_pre_write_backup(file_path: Path, policy: Optional[VersionPolicy] = None):
    """Create a backup before opening file in write mode."""
    if not file_path.exists():
        return

    policy = policy or VersionPolicy()

    try:
        with file_lock(file_path):
            # Create versions directory
            versions_base = file_path.parent / ".versions"
            versions_dir = versions_base / file_path.name
            versions_dir.mkdir(parents=True, exist_ok=True)

            # Determine backup file path
            backup_path = get_next_version_path(
                versions_dir, file_path.stem, file_path.suffix
            )

            # Copy file to backup location
            backup_path.write_bytes(file_path.read_bytes())

            # Apply retention policy
            if policy.max_versions is not None:
                versions = list_versions(versions_dir)
                if len(versions) > policy.max_versions:
                    # Remove oldest versions
                    for version in versions[policy.max_versions :]:
                        try:
                            version.path.unlink()
                            # Also remove metadata file if it exists
                            meta_path = version.path.with_suffix(
                                version.path.suffix + ".meta"
                            )
                            if meta_path.exists():
                                meta_path.unlink()
                        except Exception:
                            pass
    except Exception as e:
        warnings.warn(f"Failed to create backup: {e}")


def open(
    file: Union[str, Path],
    mode: str = "r",
    buffering: int = -1,
    encoding: Optional[str] = None,
    errors: Optional[str] = None,
    newline: Optional[str] = None,
    closefd: bool = True,
    opener: Optional[Any] = None,
    *,
    versioning: bool = True,
    policy: Optional[VersionPolicy] = None,
) -> IO:
    """
    Drop-in replacement for built-in open() with automatic versioning.

    This function wraps Python's built-in open() and adds automatic
    file versioning. Before any write operation, it creates a backup
    of the existing file in a .versions directory.

    Args:
        file: Path to file (str, Path, or file descriptor)
        mode: File mode (same as built-in open)
        buffering: Buffer size (same as built-in open)
        encoding: Text encoding (same as built-in open)
        errors: Error handling (same as built-in open)
        newline: Newline handling (same as built-in open)
        closefd: Close file descriptor (same as built-in open)
        opener: Custom opener (same as built-in open)
        versioning: Enable/disable versioning (default: True)
        policy: VersionPolicy instance or None for defaults

    Returns:
        VersionedIOWrapper wrapping the file object

    Example:
        >>> from versionio import open
        >>> with open('test.txt', 'w') as f:
        ...     f.write('Hello, World!')
    """
    # Convert to Path object
    if isinstance(file, str):
        file_path = Path(file)
    elif isinstance(file, Path):
        file_path = file
    else:
        # File descriptor or other type - pass through without versioning
        return builtins.open(
            file, mode, buffering, encoding, errors, newline, closefd, opener
        )

    # Create backup BEFORE opening in write mode (since 'w' truncates immediately)
    if versioning and "w" in mode and "x" not in mode and file_path.exists():
        _create_pre_write_backup(file_path, policy)

    # Open the actual file
    file_obj = builtins.open(
        file_path, mode, buffering, encoding, errors, newline, closefd, opener
    )

    # Wrap with versioning support
    wrapper = VersionedIOWrapper(
        file_obj, file_path, mode, versioning=versioning, policy=policy
    )

    # Mark backup as already created for 'w' mode
    if "w" in mode and versioning:
        wrapper._backup_created = True

    return wrapper


class VersionedFile:
    """
    High-level interface for versioned file operations.

    This class provides a more object-oriented interface for
    working with versioned files.
    """

    def __init__(
        self, filepath: Union[str, Path], policy: Optional[VersionPolicy] = None
    ):
        """
        Initialize with file path and optional policy.

        Args:
            filepath: Path to the file
            policy: Versioning policy
        """
        self.filepath = Path(filepath)
        self.policy = policy or VersionPolicy()

    def read(self, version: Optional[Version] = None) -> Union[str, bytes]:
        """
        Read file content (current or specific version).

        Args:
            version: Specific version to read, or None for current

        Returns:
            File content as string (text mode) or bytes (binary mode)
        """
        if version is None:
            # Read current file
            if not self.filepath.exists():
                raise FileNotFoundError(f"File not found: {self.filepath}")
            return self.filepath.read_text()
        else:
            # Read specific version
            if not version.path.exists():
                raise VersionNotFound(f"Version not found: {version.path}")
            return version.path.read_text()

    def write(self, content: Union[str, bytes], mode: str = "w"):
        """
        Write content with automatic versioning.

        Args:
            content: Content to write
            mode: Write mode ('w' or 'wb')
        """
        with open(self.filepath, mode, policy=self.policy) as f:
            f.write(content)

    def append(self, content: Union[str, bytes]):
        """
        Append content with versioning.

        Args:
            content: Content to append
        """
        mode = "ab" if isinstance(content, bytes) else "a"
        with open(self.filepath, mode, policy=self.policy) as f:
            f.write(content)

    def versions(self) -> list[Version]:
        """
        List all available versions (newest first).

        Returns:
            List of Version objects

        Raises:
            VersioningDisabled: If versioning is not enabled
        """
        versions_base = self.filepath.parent / ".versions"
        versions_dir = versions_base / self.filepath.name

        return list_versions(versions_dir)

    def restore(self, version: Version):
        """
        Restore file to specific version.

        Args:
            version: Version to restore

        Raises:
            VersionNotFound: If version doesn't exist
        """
        if not version.path.exists():
            raise VersionNotFound(f"Version not found: {version.path}")

        # Create backup of current version first (if file exists)
        if self.filepath.exists():
            _create_pre_write_backup(self.filepath, self.policy)

        # Copy version to current file
        self.filepath.write_bytes(version.path.read_bytes())

    def diff(
        self, version1: Optional[Version] = None, version2: Optional[Version] = None
    ):
        """
        Show differences between versions (not implemented yet).

        Args:
            version1: First version (None for current)
            version2: Second version (None for current)
        """
        raise NotImplementedError("diff() will be implemented in a future version")

    def cleanup(self, keep_last: Optional[int] = None):
        """
        Manual cleanup of old versions.

        Args:
            keep_last: Number of versions to keep (None uses policy)
        """
        versions_base = self.filepath.parent / ".versions"
        versions_dir = versions_base / self.filepath.name

        if not versions_dir.exists():
            return

        keep = keep_last or self.policy.max_versions
        if keep is None:
            return

        versions = list_versions(versions_dir)
        if len(versions) > keep:
            for version in versions[keep:]:
                try:
                    version.path.unlink()
                except Exception:
                    pass  # Best effort cleanup
