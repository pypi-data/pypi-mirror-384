"""Version policy configuration."""

from typing import Optional


class VersionPolicy:
    """Configuration for versioning behavior."""

    def __init__(
        self,
        max_versions: Optional[int] = 10,
        compress: bool = False,
        diff_based: bool = False,
        min_interval_seconds: int = 0,
    ):
        """
        Initialize versioning policy.

        Args:
            max_versions: Keep last N versions (None = unlimited)
            compress: Compress backup files (not implemented yet)
            diff_based: Store diffs instead of full copies (not implemented yet)
            min_interval_seconds: Min time between versions (not implemented yet)
        """
        if max_versions is not None and max_versions < 1:
            raise ValueError("max_versions must be at least 1 or None")

        self.max_versions = max_versions
        self.compress = compress
        self.diff_based = diff_based
        self.min_interval_seconds = min_interval_seconds
