"""Shared utilities for code review tools."""

from pathlib import Path

# Global variables
_working_directory = Path(".")
_tools_header_printed = False


def get_working_directory() -> Path:
    """Get the current working directory for tools."""
    return _working_directory


def print_tools_header() -> None:
    """Print the tools activity header once."""
    global _tools_header_printed
    if not _tools_header_printed:
        print("\n============================", flush=True)
        print("🔧 Tool Activity", flush=True)
        print("============================", flush=True)
        _tools_header_printed = True


def initialize_tools(working_directory: str = ".") -> None:
    """Initialize tools with working directory.
    
    Args:
        working_directory: Base directory for file operations
    """
    global _working_directory, _tools_header_printed
    _working_directory = Path(working_directory).resolve()
    # Reset header for each run
    _tools_header_printed = False
    print(f"🛠️ init_tools: working_directory='{_working_directory}'", flush=True)

