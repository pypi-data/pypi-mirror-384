"""Tests for file reading tools."""

import os
import tempfile
from pathlib import Path

import pytest

from navam_invest.tools.file_reader import (
    _get_safe_file_extensions,
    _get_safe_working_directory,
    _is_safe_path,
    list_local_files,
    read_local_file,
)


def test_get_safe_working_directory() -> None:
    """Test getting safe working directory."""
    cwd = _get_safe_working_directory()
    assert isinstance(cwd, Path)
    assert cwd.exists()
    assert cwd.is_dir()


def test_get_safe_file_extensions() -> None:
    """Test safe file extensions list."""
    extensions = _get_safe_file_extensions()
    assert ".csv" in extensions
    assert ".json" in extensions
    assert ".txt" in extensions
    assert ".md" in extensions
    assert ".xlsx" in extensions


def test_is_safe_path() -> None:
    """Test path safety validation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)

        # Create test files and directories
        (base_dir / "test.txt").write_text("test")
        (base_dir / "data").mkdir()
        (base_dir / "data" / "test.csv").write_text("test")

        # Safe path within base directory
        assert _is_safe_path("test.txt", base_dir)
        assert _is_safe_path("data/test.csv", base_dir)

        # Unsafe paths (outside base directory)
        assert not _is_safe_path("../test.txt", base_dir)
        assert not _is_safe_path("/etc/passwd", base_dir)
        assert not _is_safe_path("../../etc/passwd", base_dir)


@pytest.mark.asyncio
async def test_read_local_file_success() -> None:
    """Test successful file reading."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Change to temp directory
        original_cwd = os.getcwd()
        os.chdir(tmpdir)

        try:
            # Create test file
            test_file = Path("test.csv")
            test_content = "symbol,shares,price\nAAPL,100,150.00\nMSFT,50,350.00"
            test_file.write_text(test_content)

            # Read file using ainvoke for async tool
            result = await read_local_file.ainvoke({"file_path": "test.csv"})

            # Verify
            assert "File: test.csv" in result
            assert test_content in result
            assert "AAPL" in result
            assert "MSFT" in result

        finally:
            os.chdir(original_cwd)


@pytest.mark.asyncio
async def test_read_local_file_not_found() -> None:
    """Test reading non-existent file."""
    result = await read_local_file.ainvoke({"file_path": "nonexistent.csv"})
    assert "Error: File not found" in result


@pytest.mark.asyncio
async def test_read_local_file_unsafe_path() -> None:
    """Test reading file outside working directory."""
    result = await read_local_file.ainvoke({"file_path": "../etc/passwd"})
    assert "Error: Access denied" in result


@pytest.mark.asyncio
async def test_read_local_file_unsupported_extension() -> None:
    """Test reading file with unsupported extension."""
    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = os.getcwd()
        os.chdir(tmpdir)

        try:
            # Create file with unsupported extension
            test_file = Path("test.exe")
            test_file.write_text("test")

            result = await read_local_file.ainvoke({"file_path": "test.exe"})
            assert "Error: Unsupported file type" in result

        finally:
            os.chdir(original_cwd)


@pytest.mark.asyncio
async def test_read_local_file_size_limit() -> None:
    """Test file size limit enforcement."""
    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = os.getcwd()
        os.chdir(tmpdir)

        try:
            # Create large file (over 10MB)
            test_file = Path("large.txt")
            # Write 11MB of data
            test_file.write_text("x" * (11 * 1024 * 1024))

            result = await read_local_file.ainvoke({"file_path": "large.txt"})
            assert "Error: File too large" in result

        finally:
            os.chdir(original_cwd)


@pytest.mark.asyncio
async def test_list_local_files_success() -> None:
    """Test successful file listing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = os.getcwd()
        os.chdir(tmpdir)

        try:
            # Create test files
            Path("portfolio.csv").write_text("test")
            Path("data.json").write_text("{}")
            Path("notes.md").write_text("# Notes")

            # List files
            result = await list_local_files.ainvoke({"directory": "."})

            # Verify
            assert "portfolio.csv" in result
            assert "data.json" in result
            assert "notes.md" in result

        finally:
            os.chdir(original_cwd)


@pytest.mark.asyncio
async def test_list_local_files_with_pattern() -> None:
    """Test file listing with glob pattern."""
    with tempfile.TemporaryDirectory() as tmpdir:
        original_cwd = os.getcwd()
        os.chdir(tmpdir)

        try:
            # Create test files
            Path("portfolio.csv").write_text("test")
            Path("data.json").write_text("{}")
            Path("notes.md").write_text("# Notes")

            # List only CSV files
            result = await list_local_files.ainvoke(
                {"directory": ".", "pattern": "*.csv"}
            )

            # Verify
            assert "portfolio.csv" in result
            assert "data.json" not in result
            assert "notes.md" not in result

        finally:
            os.chdir(original_cwd)


@pytest.mark.asyncio
async def test_list_local_files_unsafe_path() -> None:
    """Test listing directory outside working directory."""
    result = await list_local_files.ainvoke({"directory": "../etc"})
    assert "Error: Access denied" in result


@pytest.mark.asyncio
async def test_list_local_files_not_found() -> None:
    """Test listing non-existent directory."""
    result = await list_local_files.ainvoke({"directory": "nonexistent_dir"})
    assert "Error: Directory not found" in result
