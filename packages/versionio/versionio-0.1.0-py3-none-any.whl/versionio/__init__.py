"""
versionIO - File I/O with Automatic Versioning

A drop-in replacement for Python's built-in open() with automatic file versioning.
"""

from versionio.core import open, VersionedFile
from versionio.policy import VersionPolicy
from versionio.version import Version
from versionio.exceptions import (
    VersionIOError,
    VersionNotFound,
    VersioningDisabled,
    StorageError,
    PolicyError,
    LockError,
)

__version__ = "0.1.0"
__all__ = [
    "open",
    "VersionedFile",
    "VersionPolicy",
    "Version",
    "VersionIOError",
    "VersionNotFound",
    "VersioningDisabled",
    "StorageError",
    "PolicyError",
    "LockError",
]
