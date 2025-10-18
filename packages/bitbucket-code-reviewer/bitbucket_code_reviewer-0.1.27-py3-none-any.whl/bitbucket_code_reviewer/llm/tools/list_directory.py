"""List directory tool for code review agent."""

from langchain_core.tools import tool

from ...core.models import DirectoryListing
from ._shared import get_working_directory, print_tools_header


@tool
def list_directory(path: str = ".") -> DirectoryListing:
    """List the contents of a directory.

    Args:
        path: Directory path to list (relative to working directory)

    Returns:
        DirectoryListing object with files and subdirectories
    """
    print_tools_header()
    working_dir = get_working_directory()
    full_path = working_dir / path

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

