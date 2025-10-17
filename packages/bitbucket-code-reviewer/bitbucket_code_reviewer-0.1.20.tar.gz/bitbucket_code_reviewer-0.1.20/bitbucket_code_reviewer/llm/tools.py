"""LangChain tools for the code review agent."""

from pathlib import Path
from typing import Optional

from langchain_core.tools import tool

from ..core.models import DirectoryListing, FileContent


# Global variables
_working_directory = Path(".")
_tools_header_printed = False


def _print_tools_header() -> None:
    global _tools_header_printed
    if not _tools_header_printed:
        print("\n============================", flush=True)
        print("🔧 Tool Activity", flush=True)
        print("============================", flush=True)
        _tools_header_printed = True


def _initialize_tools(working_directory: str = ".") -> None:
    """Initialize tools with working directory."""
    global _working_directory
    _working_directory = Path(working_directory).resolve()
    # Reset header for each run
    global _tools_header_printed
    _tools_header_printed = False
    print(f"🛠️ init_tools: working_directory='{_working_directory}'", flush=True)


@tool
def read_file(
    file_path: str,
    start_line: Optional[int] = None,
    end_line: Optional[int] = None,
) -> FileContent:
    """Read the contents of a file and return the full contents.

    Note: `start_line` and `end_line` parameters are accepted for backward
    compatibility but are ignored. The entire file is always returned.

    Args:
        file_path: Path to the file to read (relative to working directory)
        start_line: Ignored (kept for backward compatibility)
        end_line: Ignored (kept for backward compatibility)

    Returns:
        FileContent object with the full file contents
    """
    _print_tools_header()
    full_path = _working_directory / file_path

    if not full_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if not full_path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")

    try:
        with open(full_path, encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError as err:
        raise ValueError(f"Cannot read binary file: {file_path}") from err

    # Always return full file contents; ignore any range parameters

    result = FileContent(
        file_path=file_path,
        content=content,
        start_line=None,
        end_line=None,
    )

    # Single-line summary per file (timing handled by callback)
    print(
        f"🛠️ read_file: '{file_path}' chars={len(result.content)}",
        flush=True,
    )
    return result


@tool
def list_directory(path: str = ".") -> DirectoryListing:
    """List the contents of a directory.

    Args:
        path: Directory path to list (relative to working directory)

    Returns:
        DirectoryListing object with files and subdirectories
    """
    _print_tools_header()
    full_path = _working_directory / path

    if not full_path.exists():
        raise FileNotFoundError(f"Directory not found: {path}")

    if not full_path.is_dir():
        raise ValueError(f"Path is not a directory: {path}")

    try:
        entries = list(full_path.iterdir())
    except PermissionError as err:
        raise ValueError(f"Permission denied accessing directory: {path}") from err

    files = []
    directories = []

    for entry in sorted(entries):
        if entry.is_file():
            files.append(entry.name)
        elif entry.is_dir() and not entry.name.startswith("."):  # Skip hidden dirs
            directories.append(entry.name)

    result = DirectoryListing(
        path=path,
        files=files,
        directories=directories,
    )

    print(
        f"🛠️ list_directory: '{path}' files={len(result.files)} dirs={len(result.directories)}",
        flush=True,
    )
    return result


@tool
def get_file_info(file_path: str) -> dict:
    """Get basic information about a file.

    Args:
        file_path: Path to the file

    Returns:
        Dictionary with file information
    """
    _print_tools_header()
    full_path = _working_directory / file_path

    if not full_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    stat = full_path.stat()

    info = {
        "file_path": file_path,
        "size": stat.st_size,
        "modified": stat.st_mtime,
        "is_file": full_path.is_file(),
        "extension": full_path.suffix,
    }

    print(
        f"🛠️ get_file_info: '{file_path}' size={info['size']} modified={info['modified']}",
        flush=True,
    )
    return info


@tool
def search_files(pattern: str, path: str = ".") -> list[str]:
    """Search for files matching a pattern in a directory tree.

    Args:
        pattern: Glob pattern (e.g., "*.py", "**/*.md")
        path: Starting directory path

    Returns:
        List of matching file paths
    """
    _print_tools_header()
    full_path = _working_directory / path

    if not full_path.exists():
        raise FileNotFoundError(f"Directory not found: {path}")

    try:
        matches = list(full_path.glob(pattern))
    except ValueError as err:
        raise ValueError(f"Invalid glob pattern: {pattern}") from err

    # Convert to relative paths
    relative_matches = []
    for match in matches:
        if match.is_file():
            relative_matches.append(str(match.relative_to(_working_directory)))

    matches_sorted = sorted(relative_matches)

    print(
        f"🛠️ search_files: '{path}' pattern='{pattern}' matches={len(matches_sorted)}",
        flush=True,
    )
    return matches_sorted


# Factory function to create tools with working directory
def create_code_review_tools(working_directory: str = ".") -> list:
    """Create a list of code review tools.

    Args:
        working_directory: Base directory for file operations

    Returns:
        List of LangChain tools
    """
    _initialize_tools(working_directory)

    return [
        read_file,
        list_directory,
        get_file_info,
        search_files,
    ]
