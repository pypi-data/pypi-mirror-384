"""Simple logger for CLI output - git-style, CI-friendly."""

from typing import Optional

from colorama import Fore, Style, init

# Initialize colorama for cross-platform color support
init(autoreset=True)


class Logger:
    """Simple logger with git-style output and minimal coloring."""

    def __init__(self, enable_colors: bool = True):
        """Initialize logger.

        Args:
            enable_colors: Whether to use colors in output
        """
        self.enable_colors = enable_colors

    def _colorize(self, text: str, color: str) -> str:
        """Apply color to text if colors are enabled."""
        if not self.enable_colors:
            return text

        color_map = {
            "blue": Fore.BLUE,
            "green": Fore.GREEN,
            "red": Fore.RED,
            "yellow": Fore.YELLOW,
            "cyan": Fore.CYAN,
            "magenta": Fore.MAGENTA,
        }

        return f"{color_map.get(color, '')}{text}{Style.RESET_ALL}"

    def info(self, message: str, prefix: str = "ℹ️") -> None:
        """Print info message."""
        print(f"{prefix} {message}")

    def success(self, message: str, prefix: str = "✅") -> None:
        """Print success message."""
        colored_msg = self._colorize(message, "green")
        print(f"{prefix} {colored_msg}")

    def error(self, message: str, prefix: str = "❌") -> None:
        """Print error message."""
        colored_msg = self._colorize(message, "red")
        print(f"{prefix} {colored_msg}")

    def warning(self, message: str, prefix: str = "⚠️") -> None:
        """Print warning message."""
        colored_msg = self._colorize(message, "yellow")
        print(f"{prefix} {colored_msg}")

    def step(self, message: str, prefix: str = "🔧") -> None:
        """Print step/action message."""
        colored_msg = self._colorize(message, "blue")
        print(f"{prefix} {colored_msg}")

    def header(self, message: str) -> None:
        """Print header message."""
        print(f"\n{message}")
        print("=" * len(message))

    def subheader(self, message: str) -> None:
        """Print subheader message."""
        print(f"\n{message}")
        print("-" * len(message))

    def progress_start(self, message: str) -> None:
        """Start a progress operation."""
        print(f"⏳ {message}...")

    def progress_end(self, message: str = "Done") -> None:
        """End a progress operation."""
        self.success(message)

    def key_value(self, key: str, value: str, indent: int = 0) -> None:
        """Print key-value pair."""
        indent_str = " " * indent
        colored_key = self._colorize(f"{key}:", "cyan")
        print(f"{indent_str}{colored_key} {value}")

    def list_item(self, item: str, indent: int = 2) -> None:
        """Print list item."""
        indent_str = " " * indent
        print(f"{indent_str}• {item}")

    def blank_line(self) -> None:
        """Print blank line."""
        print()

    def table_row(self, *columns: str, widths: Optional[list[int]] = None) -> None:
        """Print table row (simple space-separated)."""
        if widths:
            formatted = []
            for i, col in enumerate(columns):
                width = widths[i] if i < len(widths) else 20
                formatted.append(f"{col:<{width}}")
            print(" ".join(formatted))
        else:
            print("  ".join(columns))


# Global logger instance
logger = Logger()


def create_logger(enable_colors: bool = True) -> Logger:
    """Create a logger instance.

    Args:
        enable_colors: Whether to enable colors

    Returns:
        Logger instance
    """
    return Logger(enable_colors=enable_colors)


def detect_ci_environment() -> bool:
    """Detect if running in CI environment."""
    import os

    ci_indicators = [
        "CI",  # General CI
        "CONTINUOUS_INTEGRATION",  # Travis CI
        "BITBUCKET_BUILD_NUMBER",  # Bitbucket Pipelines
        "GITHUB_ACTIONS",  # GitHub Actions
        "GITLAB_CI",  # GitLab CI
        "JENKINS_HOME",  # Jenkins
    ]

    return any(os.getenv(indicator) for indicator in ci_indicators)


# Auto-detect CI and create appropriate logger
is_ci = detect_ci_environment()
logger = create_logger(enable_colors=not is_ci)
