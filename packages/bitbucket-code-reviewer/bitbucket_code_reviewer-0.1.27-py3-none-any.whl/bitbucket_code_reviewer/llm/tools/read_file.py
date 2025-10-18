"""Read file tool for code review agent."""

from langchain_core.tools import tool

from ...core.models import FileContent
from ._shared import get_working_directory, print_tools_header


@tool
def read_file(file_path: str) -> FileContent:
    """Read the complete contents of a file.

    WARNING: Do not attempt to read large files like poetry.lock, package-lock.json,
    or other lock files. They will exceed context limits. Focus on source code files.

    Args:
        file_path: Path to the file to read (relative to working directory)

    Returns:
        FileContent object with the full file contents
    """
    print_tools_header()
    working_dir = get_working_directory()
    full_path = working_dir / file_path

    if not full_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if not full_path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")

    # Check file size before reading (max 100KB for text files)
    file_size = full_path.stat().st_size
    if file_size > 100_000:
        raise ValueError(
            f"File '{file_path}' is too large ({file_size:,} bytes). "
            f"Skip large files like lock files (poetry.lock, package-lock.json, etc). "
            f"Focus on source code files only."
        )

    try:
        with open(full_path, encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError as err:
        raise ValueError(f"Cannot read binary file: {file_path}") from err

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

