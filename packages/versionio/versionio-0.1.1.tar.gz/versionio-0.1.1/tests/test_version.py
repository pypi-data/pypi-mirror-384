"""Tests for Version class and version management."""

import time
from datetime import datetime

from versionio import open
from versionio.version import Version, list_versions


class TestVersion:
    """Test the Version class."""

    def test_version_properties(self, tmp_path):
        """Version should expose correct properties."""
        # Create a versioned file
        file_path = tmp_path / "test.txt"
        file_path.write_text("Original")

        with open(file_path, "w") as f:
            f.write("Updated")

        # Get the version
        versions_dir = tmp_path / ".versions" / "test.txt"
        version_files = list(versions_dir.glob("*.txt"))
        assert len(version_files) == 1

        version = Version(version_files[0])

        # Test properties
        assert isinstance(version.timestamp, datetime)
        assert version.size == len("Original")
        assert version.path == version_files[0]
        assert version.checksum == ""  # Not implemented yet

        # Test string representation
        repr_str = repr(version)
        assert "Version" in repr_str
        assert version_files[0].name in repr_str

    def test_version_filename_parsing(self, tmp_path):
        """Version should correctly parse timestamp from filename."""
        # Create a file with specific naming pattern
        versions_dir = tmp_path / ".versions" / "test.txt"
        versions_dir.mkdir(parents=True)

        # Create version file with known timestamp
        version_file = versions_dir / "20240115_143022_001.txt"
        version_file.write_text("Content")

        version = Version(version_file)

        # Check parsed timestamp
        assert version.timestamp.year == 2024
        assert version.timestamp.month == 1
        assert version.timestamp.day == 15
        assert version.timestamp.hour == 14
        assert version.timestamp.minute == 30
        assert version.timestamp.second == 22
        assert version._increment == 1

    def test_list_versions_empty(self, tmp_path):
        """list_versions should return empty list for non-existent directory."""
        versions_dir = tmp_path / ".versions" / "nonexistent.txt"
        versions = list_versions(versions_dir)
        assert versions == []

    def test_list_versions_sorted(self, tmp_path):
        """list_versions should return versions sorted newest first."""
        file_path = tmp_path / "test.txt"

        # Create multiple versions with delays
        for i in range(3):
            with open(file_path, "w") as f:
                f.write(f"Version {i}")
            time.sleep(0.1)  # Ensure different timestamps

        versions_dir = tmp_path / ".versions" / "test.txt"
        versions = list_versions(versions_dir)

        assert len(versions) == 2  # 3 - 1 (current)

        # Check sorting (newest first)
        timestamps = [v.timestamp for v in versions]
        assert timestamps == sorted(timestamps, reverse=True)

    def test_list_versions_ignores_metadata(self, tmp_path):
        """list_versions should ignore .meta files."""
        versions_dir = tmp_path / ".versions" / "test.txt"
        versions_dir.mkdir(parents=True)

        # Create version files
        (versions_dir / "20240115_100000_001.txt").write_text("v1")
        (versions_dir / "20240115_100000_001.txt.meta").write_text("{}")
        (versions_dir / "20240115_110000_001.txt").write_text("v2")
        (versions_dir / "20240115_110000_001.txt.meta").write_text("{}")

        versions = list_versions(versions_dir)

        # Should only return actual version files, not .meta files
        assert len(versions) == 2
        for v in versions:
            assert not v.path.name.endswith(".meta")

    def test_list_versions_multiple_increments(self, tmp_path):
        """Versions with same timestamp but different increments should be handled."""
        versions_dir = tmp_path / ".versions" / "test.txt"
        versions_dir.mkdir(parents=True)

        # Create files with same timestamp but different increments
        base = "20240115_120000"
        for i in range(1, 4):
            (versions_dir / f"{base}_{i:03d}.txt").write_text(f"v{i}")

        versions = list_versions(versions_dir)

        assert len(versions) == 3
        # Should be sorted by increment (highest first for same timestamp)
        increments = [v._increment for v in versions]
        assert increments == [3, 2, 1]

    def test_version_with_binary_file(self, tmp_path):
        """Version should work with binary files."""
        file_path = tmp_path / "data.bin"
        data = b"\x00\x01\x02\x03\x04"
        file_path.write_bytes(data)

        with open(file_path, "wb") as f:
            f.write(b"\x05\x06\x07\x08\x09")

        versions_dir = tmp_path / ".versions" / "data.bin"
        versions = list_versions(versions_dir)

        assert len(versions) == 1
        assert versions[0].size == len(data)
        assert versions[0].path.read_bytes() == data


class TestVersionNaming:
    """Test version file naming conventions."""

    def test_rapid_version_creation(self, tmp_path):
        """Rapid version creation should use incremental numbers."""
        file_path = tmp_path / "test.txt"

        # Create versions very quickly
        for i in range(5):
            with open(file_path, "w") as f:
                f.write(f"Version {i}")

        versions_dir = tmp_path / ".versions" / "test.txt"
        version_files = sorted(versions_dir.glob("*.txt"))

        # Check that increments are used when timestamps collide
        names = [f.name for f in version_files]

        # Extract increments from filenames
        increments = []
        for name in names:
            # Format: YYYYMMDD_HHMMSS_NNN.txt
            parts = name.split("_")
            if len(parts) == 3:
                inc = int(parts[2].split(".")[0])
                increments.append(inc)

        # Increments should be unique
        assert len(increments) == len(set(increments))
