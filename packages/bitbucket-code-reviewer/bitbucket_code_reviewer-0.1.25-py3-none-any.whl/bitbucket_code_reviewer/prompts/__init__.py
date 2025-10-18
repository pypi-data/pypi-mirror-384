"""Prompt loading utilities for the Bitbucket Code Reviewer."""

from pathlib import Path
from typing import Optional


def load_prompt(name: str, language: Optional[str] = None) -> str:
    """Load a prompt file by name.

    Args:
        name: Name of the prompt file (without .md extension)
        language: Optional language-specific prompt to load

    Returns:
        The content of the prompt file as a string

    Raises:
        FileNotFoundError: If the prompt file doesn't exist
    """
    prompts_dir = Path(__file__).parent

    if language:
        prompt_path = prompts_dir / "language_specific" / f"{language}.md"
    else:
        prompt_path = prompts_dir / f"{name}.md"

    if not prompt_path.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_path}")

    return prompt_path.read_text(encoding="utf-8")


def get_system_prompt(language: Optional[str] = None) -> str:
    """Get the complete system prompt by combining all components.

    Args:
        language: Optional language for language-specific guidelines

    Returns:
        The complete system prompt as a string
    """
    system = load_prompt("system")
    guidelines = load_prompt("review_guidelines")
    tools = load_prompt("tool_instructions")

    # Combine base components (format instructions now in human message)
    prompt_parts = [system, guidelines, tools]

    # Add language-specific guidelines if provided
    if language:
        try:
            language_guidelines = load_prompt("python", language=language)
            prompt_parts.append(language_guidelines)
        except FileNotFoundError:
            # Language-specific file doesn't exist, continue without it
            pass

    return "\n\n".join(prompt_parts)


def list_available_languages() -> list[str]:
    """List all available language-specific prompt files.

    Returns:
        List of language names (without .md extension)
    """
    prompts_dir = Path(__file__).parent
    language_dir = prompts_dir / "language_specific"

    if not language_dir.exists():
        return []

    return [f.stem for f in language_dir.glob("*.md")]


def get_all_prompts() -> dict[str, str]:
    """Get all available prompt files as a dictionary.

    Returns:
        Dictionary mapping prompt names to their content
    """
    prompts = {}
    prompts_dir = Path(__file__).parent

    # Load main prompts
    for prompt_file in prompts_dir.glob("*.md"):
        name = prompt_file.stem
        prompts[name] = prompt_file.read_text(encoding="utf-8")

    # Load language-specific prompts
    language_dir = prompts_dir / "language_specific"
    if language_dir.exists():
        for prompt_file in language_dir.glob("*.md"):
            name = f"{prompt_file.stem}_language"
            prompts[name] = prompt_file.read_text(encoding="utf-8")

    return prompts
