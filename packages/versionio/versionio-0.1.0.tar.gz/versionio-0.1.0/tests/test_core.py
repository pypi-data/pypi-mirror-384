"""Tests for core open() function and basic versioning."""

import time

from versionio import open, VersionPolicy


class TestOpenFunction:
    """Test the open() wrapper function."""

    def test_write_creates_backup(self, tmp_path):
        """Writing to existing file should create a backup."""
        file_path = tmp_path / "test.txt"

        # Create initial file
        with open(file_path, "w") as f:
            f.write("Version 1")

        # Write again - should create backup
        with open(file_path, "w") as f:
            f.write("Version 2")

        # Check backup was created
        versions_dir = tmp_path / ".versions" / "test.txt"
        assert versions_dir.exists()
        backups = list(versions_dir.glob("*.txt"))
        assert len(backups) == 1

        # Verify backup content
        assert backups[0].read_text() == "Version 1"
        # Current file should have new content
        assert file_path.read_text() == "Version 2"

    def test_read_mode_no_backup(self, tmp_path):
        """Reading a file should not create any backup."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("Read only content")

        with open(file_path, "r") as f:
            content = f.read()

        # No versions directory should be created
        versions_dir = tmp_path / ".versions"
        assert not versions_dir.exists()

    def test_append_mode_versioning(self, tmp_path):
        """Append mode should create one backup per session."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("Line 1\n")

        # First append session
        with open(file_path, "a") as f:
            f.write("Line 2\n")
            f.write("Line 3\n")  # Multiple writes in same session

        versions_dir = tmp_path / ".versions" / "test.txt"
        backups = list(versions_dir.glob("*.txt"))
        assert len(backups) == 1
        assert backups[0].read_text() == "Line 1\n"

        # Second append session
        with open(file_path, "a") as f:
            f.write("Line 4\n")

        backups = list(versions_dir.glob("*.txt"))
        assert len(backups) == 2

    def test_exclusive_create_no_backup(self, tmp_path):
        """Mode 'x' should not create backup (file doesn't exist)."""
        file_path = tmp_path / "new_file.txt"

        with open(file_path, "x") as f:
            f.write("New file content")

        versions_dir = tmp_path / ".versions"
        assert not versions_dir.exists()

    def test_binary_mode_support(self, tmp_path):
        """Binary files should be versioned correctly."""
        file_path = tmp_path / "data.bin"

        # Create binary file
        data1 = b"\x00\x01\x02\x03"
        with open(file_path, "wb") as f:
            f.write(data1)

        # Update binary file
        data2 = b"\x04\x05\x06\x07"
        with open(file_path, "wb") as f:
            f.write(data2)

        # Check backup
        versions_dir = tmp_path / ".versions" / "data.bin"
        backups = list(versions_dir.glob("*.bin"))
        assert len(backups) == 1
        assert backups[0].read_bytes() == data1
        assert file_path.read_bytes() == data2

    def test_versioning_disabled(self, tmp_path):
        """Versioning=False should skip all backups."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("Original")

        with open(file_path, "w", versioning=False) as f:
            f.write("Updated")

        versions_dir = tmp_path / ".versions"
        assert not versions_dir.exists()
        assert file_path.read_text() == "Updated"

    def test_custom_policy(self, tmp_path):
        """Custom policy should be applied."""
        file_path = tmp_path / "test.txt"
        policy = VersionPolicy(max_versions=2)

        # Create multiple versions
        for i in range(5):
            with open(file_path, "w", policy=policy) as f:
                f.write(f"Version {i}")
            time.sleep(0.01)  # Ensure different timestamps

        # Only 2 backups should remain
        versions_dir = tmp_path / ".versions" / "test.txt"
        backups = list(versions_dir.glob("*.txt"))
        assert len(backups) == 2

    def test_rplus_mode_backup_on_write(self, tmp_path):
        """Mode 'r+' should create backup on first write."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("Original content")

        with open(file_path, "r+") as f:
            content = f.read()  # Reading first
            f.seek(0)
            f.write("Modified content")
            f.truncate()

        # Backup should be created
        versions_dir = tmp_path / ".versions" / "test.txt"
        backups = list(versions_dir.glob("*.txt"))
        assert len(backups) == 1
        assert backups[0].read_text() == "Original content"

    def test_nonexistent_file_write(self, tmp_path):
        """Writing to non-existent file should not create backup."""
        file_path = tmp_path / "new.txt"

        with open(file_path, "w") as f:
            f.write("First write")

        # No backup for new files
        versions_dir = tmp_path / ".versions"
        assert not versions_dir.exists()

    def test_nested_directory_structure(self, tmp_path):
        """Versioning should work with nested directories."""
        nested_dir = tmp_path / "sub" / "dir"
        nested_dir.mkdir(parents=True)
        file_path = nested_dir / "test.txt"

        file_path.write_text("Version 1")

        with open(file_path, "w") as f:
            f.write("Version 2")

        versions_dir = nested_dir / ".versions" / "test.txt"
        assert versions_dir.exists()
        backups = list(versions_dir.glob("*.txt"))
        assert len(backups) == 1

    def test_file_with_multiple_extensions(self, tmp_path):
        """Files with multiple dots should be handled correctly."""
        file_path = tmp_path / "data.tar.gz"
        file_path.write_bytes(b"compressed data v1")

        with open(file_path, "wb") as f:
            f.write(b"compressed data v2")

        versions_dir = tmp_path / ".versions" / "data.tar.gz"
        backups = list(versions_dir.glob("*.gz"))
        assert len(backups) == 1


class TestConcurrentAccess:
    """Test concurrent file access handling."""

    def test_rapid_sequential_writes(self, tmp_path):
        """Rapid sequential writes should create unique backups."""
        file_path = tmp_path / "test.txt"

        # Write rapidly
        for i in range(3):
            with open(file_path, "w") as f:
                f.write(f"Version {i}")

        versions_dir = tmp_path / ".versions" / "test.txt"
        if versions_dir.exists():
            backups = list(versions_dir.glob("*.txt"))
            # All backups should have unique names
            backup_names = [b.name for b in backups]
            assert len(backup_names) == len(set(backup_names))
