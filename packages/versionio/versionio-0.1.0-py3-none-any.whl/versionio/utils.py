"""Utility functions for versionIO."""

import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Tuple
from contextlib import contextmanager


def get_timestamp_string() -> Tuple[str, str]:
    """
    Get timestamp strings for versioning.

    Returns:
        Tuple of (date_string, time_string) in format (YYYYMMDD, HHMMSS)
    """
    # Use timezone-aware datetime to avoid deprecation warning
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y%m%d")
    time_str = now.strftime("%H%M%S")
    return date_str, time_str


def get_next_version_path(versions_dir: Path, base_name: str, extension: str) -> Path:
    """
    Get the next available version path with timestamp and increment.

    Args:
        versions_dir: Directory containing versions
        base_name: Base filename without extension
        extension: File extension (including dot)

    Returns:
        Path to next version file
    """
    date_str, time_str = get_timestamp_string()

    # Find next increment for this timestamp
    increment = 1
    while True:
        version_name = f"{date_str}_{time_str}_{increment:03d}{extension}"
        version_path = versions_dir / version_name
        if not version_path.exists():
            return version_path
        increment += 1
        if increment > 999:
            # Wait a second to get a new timestamp
            import time

            time.sleep(1)
            date_str, time_str = get_timestamp_string()
            increment = 1


@contextmanager
def file_lock(file_path: Path, timeout: float = 5.0):
    """
    Cross-platform file locking (best-effort).

    Args:
        file_path: Path to lock
        timeout: Lock timeout in seconds

    Yields:
        None if successful, raises LockError on timeout
    """
    lock_path = Path(str(file_path) + ".lock")

    if sys.platform == "win32":
        # Windows implementation using msvcrt
        try:
            import msvcrt
            import time

            start_time = time.time()
            lock_file = None

            while time.time() - start_time < timeout:
                try:
                    lock_file = open(lock_path, "wb")
                    msvcrt.locking(lock_file.fileno(), msvcrt.LK_NBLCK, 1)
                    break
                except (OSError, IOError):
                    if lock_file:
                        lock_file.close()
                    time.sleep(0.1)
            else:
                warnings.warn(
                    f"Could not acquire lock for {file_path}, continuing anyway"
                )
                yield
                return

            try:
                yield
            finally:
                if lock_file:
                    try:
                        msvcrt.locking(lock_file.fileno(), msvcrt.LK_UNLCK, 1)
                    except:
                        pass
                    lock_file.close()
                    try:
                        lock_path.unlink()
                    except:
                        pass
        except ImportError:
            # msvcrt not available, skip locking
            warnings.warn("File locking not available on this platform")
            yield
    else:
        # Unix implementation using fcntl
        try:
            import fcntl
            import time

            start_time = time.time()
            lock_file = None

            while time.time() - start_time < timeout:
                try:
                    lock_file = open(lock_path, "wb")
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except (OSError, IOError):
                    if lock_file:
                        lock_file.close()
                    time.sleep(0.1)
            else:
                warnings.warn(
                    f"Could not acquire lock for {file_path}, continuing anyway"
                )
                yield
                return

            try:
                yield
            finally:
                if lock_file:
                    try:
                        fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                    except:
                        pass
                    lock_file.close()
                    try:
                        lock_path.unlink()
                    except:
                        pass
        except ImportError:
            # fcntl not available, skip locking
            warnings.warn("File locking not available on this platform")
            yield


def is_write_mode(mode: str) -> bool:
    """
    Check if file mode implies writing.

    Args:
        mode: File open mode

    Returns:
        True if mode will write to file
    """
    # Remove 'b' and 't' modifiers to check base mode
    base_mode = mode.replace("b", "").replace("t", "")
    return any(m in base_mode for m in ["w", "a", "x", "+"])


def should_create_backup(mode: str, file_path: Path) -> bool:
    """
    Determine if a backup should be created.

    Args:
        mode: File open mode
        file_path: Path to file

    Returns:
        True if backup should be created
    """
    if not is_write_mode(mode):
        return False

    # Don't backup if file doesn't exist
    if not file_path.exists():
        return False

    # Don't backup for exclusive creation (file shouldn't exist)
    if "x" in mode:
        return False

    # Don't backup for 'w' mode (handled in core.py before truncation)
    if "w" in mode and "+" not in mode:
        return False

    return True
