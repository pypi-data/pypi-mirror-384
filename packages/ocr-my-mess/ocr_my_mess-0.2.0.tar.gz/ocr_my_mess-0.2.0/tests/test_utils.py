"""Unit tests for the utility functions in utils.py."""

import tempfile
from pathlib import Path

import pytest

from pdf_pipeline.utils import find_files, check_command_exists


@pytest.fixture
def temp_dir_with_files() -> Path:
    """Create a temporary directory with a nested structure and various files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "file1.txt").touch()
        (root / "image.jpg").touch()
        subfolder = root / "sub"
        subfolder.mkdir()
        (subfolder / "document.pdf").touch()
        (subfolder / "file2.txt").touch()
        yield root


def test_find_files_single_extension(temp_dir_with_files: Path):
    """Test finding files with a single extension."""
    files = list(find_files(temp_dir_with_files, [".txt"]))
    assert len(files) == 2
    assert temp_dir_with_files / "file1.txt" in files
    assert temp_dir_with_files / "sub" / "file2.txt" in files


def test_find_files_multiple_extensions(temp_dir_with_files: Path):
    """Test finding files with multiple extensions."""
    files = list(find_files(temp_dir_with_files, [".jpg", ".pdf"]))
    assert len(files) == 2
    assert temp_dir_with_files / "image.jpg" in files
    assert temp_dir_with_files / "sub" / "document.pdf" in files


def test_find_files_no_matches(temp_dir_with_files: Path):
    """Test that an empty list is returned when no files match."""
    files = list(find_files(temp_dir_with_files, [".png", ".docx"]))
    assert len(files) == 0


def test_check_command_exists():
    """Test the command existence check."""
    # A command that should exist on most Unix-like systems
    assert check_command_exists("ls") is True
    # A command that should definitely not exist
    assert check_command_exists("non_existent_command_12345") is False
