"""Bitbucket Code Reviewer CLI Tool."""

try:
    # Try to get version from package metadata (works when installed)
    from importlib.metadata import version
    __version__ = version("bitbucket-code-reviewer")
except Exception:
    # Fallback for development
    import re
    from pathlib import Path

    pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
    try:
        with open(pyproject_path) as f:
            content = f.read()
        match = re.search(r'version = "([^"]+)"', content)
        if match:
            __version__ = match.group(1)
        else:
            __version__ = "0.1.0"
    except Exception:
        __version__ = "0.1.0"
