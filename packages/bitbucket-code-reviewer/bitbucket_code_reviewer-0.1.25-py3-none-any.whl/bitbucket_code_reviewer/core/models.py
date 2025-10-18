"""Pydantic models for the code review system."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Severity(str, Enum):
    """Severity levels for code review issues."""

    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    INFO = "info"


class Category(str, Enum):
    """Categories for code review issues."""

    SECURITY = "security"
    PERFORMANCE = "performance"
    MAINTAINABILITY = "maintainability"
    ARCHITECTURE = "architecture"
    STYLE = "style"


class CodeChange(BaseModel):
    """A single code change/issue found during review."""

    file_path: str = Field(..., description="Path to the file containing the issue")
    start_line: int = Field(..., description="Starting line number of the issue")
    end_line: int = Field(..., description="Ending line number of the issue")
    severity: Severity = Field(..., description="Severity level of the issue")
    category: Category = Field(..., description="Category of the issue")
    title: str = Field(
        ..., max_length=80, description="Brief title describing the issue"
    )
    description: str = Field(..., description="Detailed explanation of the problem")
    suggestion: str = Field(
        ..., description="Specific recommendation for how to fix it"
    )
    code_snippet: str = Field(..., description="The problematic code snippet")
    suggested_code: str = Field(..., description="The improved code suggestion")
    rationale: str = Field(..., description="Why this change improves the code")


class PositiveAspect(BaseModel):
    """A positive aspect found during code review."""

    description: str = Field(..., description="Description of the positive aspect")


class CodeReviewResult(BaseModel):
    """Complete code review result."""

    summary: str = Field(..., description="Brief overview of the overall code quality")
    severity_counts: dict[Severity, int] = Field(
        default_factory=lambda: dict.fromkeys(Severity, 0),
        description="Count of issues by severity level",
    )
    changes: list[CodeChange] = Field(
        default_factory=list, description="List of code changes/issues found"
    )
    positives: list[PositiveAspect] = Field(
        default_factory=list, description="Positive aspects found"
    )
    recommendations: list[str] = Field(
        default_factory=list, description="High-level recommendations"
    )


class PullRequestInfo(BaseModel):
    """Information about a pull request."""

    id: int = Field(..., description="Pull request ID")
    title: str = Field(..., description="Pull request title")
    description: Optional[str] = Field(None, description="Pull request description")
    source_branch: str = Field(..., description="Source branch name")
    target_branch: str = Field(..., description="Target branch name")
    author: str = Field(..., description="Pull request author")
    state: str = Field(..., description="Pull request state")


class FileChange(BaseModel):
    """A file change in a pull request."""

    filename: str = Field(..., description="Name of the changed file")
    status: str = Field(..., description="Change status (added, modified, removed)")
    additions: int = Field(..., description="Number of lines added")
    deletions: int = Field(..., description="Number of lines deleted")


class PullRequestDiff(BaseModel):
    """Complete diff information for a pull request."""

    pull_request: PullRequestInfo = Field(..., description="Pull request information")
    files: list[FileChange] = Field(..., description="List of changed files")
    diff_content: str = Field(..., description="Full diff content")


class FileContent(BaseModel):
    """Content of a file with optional line range."""

    file_path: str = Field(..., description="Path to the file")
    content: str = Field(..., description="File content")
    start_line: Optional[int] = Field(
        None, description="Starting line number if range specified"
    )
    end_line: Optional[int] = Field(
        None, description="Ending line number if range specified"
    )

    def __str__(self) -> str:
        """Return raw file content without line numbers."""
        return self.content


class DirectoryListing(BaseModel):
    """Contents of a directory."""

    path: str = Field(..., description="Directory path")
    files: list[str] = Field(..., description="List of files in the directory")
    directories: list[str] = Field(..., description="List of subdirectories")


class LLMProvider(str, Enum):
    """Supported LLM providers."""

    OPENAI = "openai"
    XAI = "xai"


class ReviewConfig(BaseModel):
    """Configuration for the code review process."""

    llm_provider: LLMProvider = Field(..., description="LLM provider to use")
    model_name: str = Field(..., description="Specific model name to use")
    temperature: float = Field(..., description="Temperature for LLM generation")
    max_tokens: Optional[int] = Field(
        default=None, description="Maximum tokens for LLM response"
    )
    language: Optional[str] = Field(
        default=None, description="Programming language for specific guidelines"
    )
    max_tool_iterations: int = Field(
        default=10, description="Maximum number of tool iterations"
    )
    working_directory: str = Field(
        default=".", description="Working directory for local repo operations"
    )
