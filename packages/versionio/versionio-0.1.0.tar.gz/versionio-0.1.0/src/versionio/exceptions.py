"""Custom exceptions for versionIO."""


class VersionIOError(Exception):
    """Base exception for all versionIO errors."""

    pass


class VersionNotFound(VersionIOError):
    """Requested version doesn't exist."""

    pass


class VersioningDisabled(VersionIOError):
    """Operation requires versioning but it's disabled."""

    pass


class StorageError(VersionIOError):
    """Storage backend operation failed."""

    pass


class PolicyError(VersionIOError):
    """Invalid policy configuration."""

    pass


class LockError(VersionIOError):
    """File locking operation failed."""

    pass
