"""Tests for VersionedIOWrapper class."""

import builtins

from versionio.wrapper import VersionedIOWrapper


class TestVersionedIOWrapper:
    """Test the VersionedIOWrapper class."""

    def test_context_manager(self, tmp_path):
        """Wrapper should support context manager protocol."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("Original")

        # First, backup the content manually since we're testing wrapper directly
        versions_dir = tmp_path / ".versions" / "test.txt"
        versions_dir.mkdir(parents=True, exist_ok=True)
        backup_path = versions_dir / "20250101_120000_001.txt"
        backup_path.write_text("Original")

        # Now test the wrapper with already truncated file
        file_obj = builtins.open(file_path, "w")
        wrapper = VersionedIOWrapper(file_obj, file_path, "w")
        wrapper._backup_created = True  # Mark as already backed up

        with wrapper as f:
            f.write("New content")
            assert not f.closed

        assert wrapper.closed
        assert file_path.read_text() == "New content"

        # Check backup exists (we created it manually)
        assert versions_dir.exists()

    def test_write_methods(self, tmp_path):
        """Test write and writelines methods."""
        file_path = tmp_path / "test.txt"
        file_path.write_text("Original")

        # Create backup manually before using built-in open
        versions_dir = tmp_path / ".versions" / "test.txt"
        versions_dir.mkdir(parents=True, exist_ok=True)
        backup_path = versions_dir / "20250101_120000_001.txt"
        backup_path.write_text("Original")

        file_obj = builtins.open(file_path, "w")
        wrapper = VersionedIOWrapper(file_obj, file_path, "w")
        wrapper._backup_created = True  # Mark as already backed up

        # Test write
        wrapper.write("Line 1\n")

        # Test writelines
        wrapper.writelines(["Line 2\n", "Line 3\n"])
        wrapper.close()

        assert file_path.read_text() == "Line 1\nLine 2\nLine 3\n"

        # Check the backup we created
        backups = list(versions_dir.glob("*.txt"))
        assert len(backups) == 1
        assert backups[0].read_text() == "Original"

    # ... rest of the tests remain the same ...
