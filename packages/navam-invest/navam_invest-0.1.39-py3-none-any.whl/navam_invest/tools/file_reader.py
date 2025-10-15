"""File reading tools for local portfolio and investment data analysis."""

import os
from pathlib import Path
from typing import List, Optional

from langchain_core.tools import tool


def _get_safe_working_directory() -> Path:
    """Get the current working directory where navam was invoked.

    Returns:
        Path object representing the current working directory
    """
    return Path.cwd()


def _is_safe_path(file_path: str, base_dir: Path) -> bool:
    """Check if the file path is safe to read (within working directory).

    Args:
        file_path: Path to validate
        base_dir: Base directory to restrict access to

    Returns:
        True if path is safe, False otherwise
    """
    try:
        # Resolve both paths to absolute paths
        resolved_base = base_dir.resolve()
        resolved_path = (base_dir / file_path).resolve()

        # Check if resolved path is within base directory
        # Use string comparison for compatibility
        try:
            resolved_path.relative_to(resolved_base)
            return True
        except ValueError:
            return False
    except (ValueError, RuntimeError):
        return False


def _get_safe_file_extensions() -> List[str]:
    """Get list of safe file extensions that can be read.

    Returns:
        List of safe file extensions
    """
    return [
        # Data formats
        ".csv",
        ".json",
        ".xml",
        ".yaml",
        ".yml",
        # Text formats
        ".txt",
        ".md",
        ".markdown",
        # Spreadsheets
        ".xlsx",
        ".xls",
        # Investment-specific
        ".ofx",
        ".qfx",  # Financial data formats
    ]


@tool
async def read_local_file(file_path: str) -> str:
    """Read a file from the current working directory.

    This tool allows reading local files that contain portfolio data,
    transaction history, or other investment-related information.
    Only files within the current working directory can be read.

    Supported file formats:
    - CSV (.csv) - Portfolio holdings, transaction history
    - JSON (.json) - Structured investment data
    - Excel (.xlsx, .xls) - Spreadsheet data
    - Text (.txt, .md) - Notes, analysis documents
    - OFX/QFX (.ofx, .qfx) - Financial data exports

    Args:
        file_path: Relative path to the file from current working directory.
                   Example: "portfolio.csv" or "data/holdings.json"

    Returns:
        File contents as a string, or error message if file cannot be read

    Examples:
        read_local_file("portfolio.csv")
        read_local_file("data/transactions.json")
    """
    base_dir = _get_safe_working_directory()

    # Security check: ensure path is within working directory
    if not _is_safe_path(file_path, base_dir):
        return f"Error: Access denied. File must be within the current working directory: {base_dir}"

    # Resolve full path
    full_path = (base_dir / file_path).resolve()

    # Check if file exists
    if not full_path.exists():
        return f"Error: File not found: {file_path}"

    # Check if it's a file (not a directory)
    if not full_path.is_file():
        return f"Error: Path is not a file: {file_path}"

    # Check file extension
    safe_extensions = _get_safe_file_extensions()
    if full_path.suffix.lower() not in safe_extensions:
        return (
            f"Error: Unsupported file type '{full_path.suffix}'. "
            f"Supported types: {', '.join(safe_extensions)}"
        )

    # Check file size (limit to 10MB)
    max_size = 10 * 1024 * 1024  # 10MB
    file_size = full_path.stat().st_size
    if file_size > max_size:
        return f"Error: File too large ({file_size / 1024 / 1024:.1f}MB). Maximum size is 10MB"

    try:
        # Read file contents
        with open(full_path, "r", encoding="utf-8") as f:
            content = f.read()

        return f"File: {file_path}\nSize: {file_size} bytes\n\n{content}"

    except UnicodeDecodeError:
        return f"Error: File appears to be binary or uses unsupported encoding: {file_path}"
    except PermissionError:
        return f"Error: Permission denied reading file: {file_path}"
    except Exception as e:
        return f"Error reading file: {str(e)}"


@tool
async def list_local_files(directory: str = ".", pattern: Optional[str] = None) -> str:
    """List files in the current working directory or subdirectory.

    This tool helps discover what files are available for analysis.
    Only directories within the current working directory can be listed.

    Args:
        directory: Relative path to directory (default: current directory ".")
        pattern: Optional glob pattern to filter files (e.g., "*.csv", "data/*.json")

    Returns:
        List of files found, or error message

    Examples:
        list_local_files() - List all files in current directory
        list_local_files("data") - List files in data subdirectory
        list_local_files(".", "*.csv") - List all CSV files
    """
    base_dir = _get_safe_working_directory()

    # Security check: ensure path is within working directory
    if not _is_safe_path(directory, base_dir):
        return f"Error: Access denied. Directory must be within: {base_dir}"

    target_dir = (base_dir / directory).resolve()

    # Check if directory exists
    if not target_dir.exists():
        return f"Error: Directory not found: {directory}"

    # Check if it's a directory
    if not target_dir.is_dir():
        return f"Error: Path is not a directory: {directory}"

    try:
        # List files
        if pattern:
            files = list(target_dir.glob(pattern))
        else:
            files = list(target_dir.iterdir())

        # Filter only files (not directories) and get safe extensions
        safe_extensions = _get_safe_file_extensions()
        readable_files = [
            f for f in files if f.is_file() and f.suffix.lower() in safe_extensions
        ]

        if not readable_files:
            return f"No readable files found in: {directory}"

        # Format output
        file_list = []
        for file in sorted(readable_files):
            relative_path = file.relative_to(base_dir)
            size = file.stat().st_size
            file_list.append(f"  - {relative_path} ({size:,} bytes)")

        header = f"Readable files in {directory}:"
        return header + "\n" + "\n".join(file_list)

    except Exception as e:
        return f"Error listing directory: {str(e)}"
