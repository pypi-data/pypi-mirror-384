"""Shared pytest fixtures and configuration."""

import pytest
from pathlib import Path
import shutil


@pytest.fixture
def sample_files_dir():
    """Return path to sample files directory."""
    return Path(__file__).parent / "fixtures" / "sample_files"


@pytest.fixture
def temp_file(tmp_path):
    """Create a temporary file with initial content."""
    file_path = tmp_path / "test.txt"
    file_path.write_text("Initial content")
    return file_path


@pytest.fixture
def clean_versions_dir(tmp_path):
    """Ensure no .versions directory exists."""
    versions_dir = tmp_path / ".versions"
    if versions_dir.exists():
        shutil.rmtree(versions_dir)
    return tmp_path


@pytest.fixture(autouse=True)
def isolate_tests(tmp_path, monkeypatch):
    """Isolate each test by changing to temp directory."""
    monkeypatch.chdir(tmp_path)
    return tmp_path
