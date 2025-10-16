"""Tests for VersionPolicy class."""

import pytest
import time

from versionio import VersionPolicy, open


class TestVersionPolicy:
    """Test the VersionPolicy class."""

    def test_default_policy(self):
        """Default policy should have sensible defaults."""
        policy = VersionPolicy()

        assert policy.max_versions == 10
        assert policy.compress is False
        assert policy.diff_based is False
        assert policy.min_interval_seconds == 0

    def test_custom_max_versions(self):
        """Custom max_versions should be respected."""
        policy = VersionPolicy(max_versions=5)
        assert policy.max_versions == 5

        # None means unlimited
        policy_unlimited = VersionPolicy(max_versions=None)
        assert policy_unlimited.max_versions is None

    def test_invalid_max_versions(self):
        """Invalid max_versions should raise ValueError."""
        with pytest.raises(ValueError, match="at least 1"):
            VersionPolicy(max_versions=0)

        with pytest.raises(ValueError, match="at least 1"):
            VersionPolicy(max_versions=-1)

    def test_max_versions_cleanup(self, tmp_path):
        """Old versions should be removed when exceeding max_versions."""
        file_path = tmp_path / "test.txt"
        policy = VersionPolicy(max_versions=3)

        # Create 5 versions
        for i in range(5):
            with open(file_path, "w", policy=policy) as f:
                f.write(f"Version {i}")
            time.sleep(0.02)  # Ensure different timestamps

        # Only 3 backups should remain
        versions_dir = tmp_path / ".versions" / "test.txt"
        backups = sorted(versions_dir.glob("*.txt"))
        assert len(backups) == 3

        # The current file has "Version 4"
        # So backups should have Version 1, 2, 3 (Version 0 should be deleted)
        backup_contents = [b.read_text() for b in backups]

        # Check that Version 0 was removed
        assert "Version 0" not in backup_contents

        # Check that we have the expected versions (1, 2, 3)
        # The exact versions depend on implementation, but we should NOT have Version 0
        assert all(
            content in ["Version 1", "Version 2", "Version 3"]
            for content in backup_contents
        )

    def test_unlimited_versions(self, tmp_path):
        """max_versions=None should keep all versions."""
        file_path = tmp_path / "test.txt"
        policy = VersionPolicy(max_versions=None)

        # Create multiple versions
        for i in range(10):
            with open(file_path, "w", policy=policy) as f:
                f.write(f"Version {i}")
            time.sleep(0.01)

        # All backups should be kept
        versions_dir = tmp_path / ".versions" / "test.txt"
        backups = list(versions_dir.glob("*.txt"))
        assert len(backups) == 9  # 10 - 1 (current)

    def test_policy_with_multiple_files(self, tmp_path):
        """Policy should work independently for different files."""
        policy = VersionPolicy(max_versions=2)

        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"

        # Create versions for file1
        for i in range(4):
            with open(file1, "w", policy=policy) as f:
                f.write(f"File1 v{i}")
            time.sleep(0.01)

        # Create versions for file2
        for i in range(3):
            with open(file2, "w", policy=policy) as f:
                f.write(f"File2 v{i}")
            time.sleep(0.01)

        # Each file should have max 2 backups
        versions1 = list((tmp_path / ".versions" / "file1.txt").glob("*.txt"))
        versions2 = list((tmp_path / ".versions" / "file2.txt").glob("*.txt"))

        assert len(versions1) == 2
        assert len(versions2) == 2

    def test_future_policy_attributes(self):
        """Future policy attributes should be configurable."""
        policy = VersionPolicy(
            max_versions=5, compress=True, diff_based=True, min_interval_seconds=60
        )

        assert policy.compress is True
        assert policy.diff_based is True
        assert policy.min_interval_seconds == 60
