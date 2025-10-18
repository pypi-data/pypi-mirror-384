"""LangChain tools for the code review agent."""

from ._shared import initialize_tools
from .get_file_info import get_file_info
from .list_directory import list_directory
from .read_file import read_file
from .search_files import search_files

__all__ = [
    "read_file",
    "list_directory",
    "get_file_info",
    "search_files",
    "create_code_review_tools",
]


def create_code_review_tools(working_directory: str = ".") -> list:
    """Create a list of code review tools.

    Args:
        working_directory: Base directory for file operations

    Returns:
        List of LangChain tools
    """
    initialize_tools(working_directory)

    return [
        read_file,
        list_directory,
        get_file_info,
        search_files,
    ]

