"""Search files tool for code review agent."""

from langchain_core.tools import tool

from ._shared import get_working_directory, print_tools_header


@tool
def search_files(pattern: str, path: str = ".") -> list[str]:
    """Search for files by FILENAME pattern (glob). This searches filenames ONLY, NOT file contents.

    Use this to find files when you know part of the filename but not the exact path.
    This does NOT search inside files - use read_file for that.

    Args:
        pattern: Glob pattern to match FILENAMES (e.g., "*.py", "**/*test*.py", "*config*")
                 Use * as wildcard. Examples:
                 - "*.py" = all Python files in current dir
                 - "**/*.test.py" = all test files recursively
                 - "*repository*" = files with "repository" in filename
        path: Starting directory path (default: ".")

    Returns:
        List of matching file paths

    Example: To find test files, use pattern="**/*test*.py", NOT pattern="test" or pattern="TestClass"
    """
    print_tools_header()
    working_dir = get_working_directory()
    full_path = working_dir / path

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
            relative_matches.append(str(match.relative_to(working_dir)))

    matches_sorted = sorted(relative_matches)

    print(
        f"🛠️ search_files: '{path}' pattern='{pattern}' matches={len(matches_sorted)}",
        flush=True,
    )
    return matches_sorted

