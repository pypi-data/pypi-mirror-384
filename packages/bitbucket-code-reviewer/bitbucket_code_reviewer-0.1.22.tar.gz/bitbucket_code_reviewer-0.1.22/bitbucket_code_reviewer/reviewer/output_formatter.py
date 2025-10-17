"""Format code review results for Bitbucket PR comments."""

from typing import Any

from ..core.models import CodeReviewResult, Severity


def format_review_output(review_result: CodeReviewResult) -> list[dict[str, Any]]:
    """Format a code review result into Bitbucket PR comments.

    Creates ONE inline comment per issue (change):
    - First line: brief description of the issue (plain text)
    - Then: "Proposed fix:" followed by either a short suggestion (text) or a fenced
      code snippet with the proposed change when available.
    """
    comments: list[dict[str, Any]] = []

    for change in review_result.changes:
        change_comment = _format_change_comment(change)
        comments.append(change_comment)

    return comments


def _format_summary_comment(review_result: CodeReviewResult) -> dict[str, Any]:
    """Format the summary as a general PR comment.

    Args:
        review_result: The review result

    Returns:
        Comment dictionary for Bitbucket API
    """
    severity_summary = _get_severity_summary(review_result)

    content_lines = [
        "## 🤖 Automated Code Review Summary",
        "",
        review_result.summary,
        "",
        "### 📊 Issue Summary",
        severity_summary,
        "",
        "_This review was generated automatically using AI-powered code analysis._",
    ]

    return {
        "content": "\n".join(content_lines),
        "file_path": None,
        "line": None,
    }


def _looks_like_code(text: str) -> bool:
    """Heuristic to decide if a string is code-like for fencing."""
    if not text:
        return False
    indicators = [
        "\n",
        "def ",
        "class ",
        "import ",
        "from ",
        "return ",
        "=",
        "{",
        "}",
        "(",
        ")",
        ":",
        ";",
    ]
    lowered = text.strip().lower()
    return any(tok in text for tok in indicators) or lowered.startswith(("#", "//"))


def _format_change_comment(change) -> dict[str, Any]:
    """Format a code change as a single inline suggested-change comment."""
    description_text = (
        change.description.strip() if hasattr(change, "description") else "Issue"
    )
    suggestion_text = (getattr(change, "suggestion", "") or "").strip()
    proposed_code = (getattr(change, "suggested_code", "") or "").strip()

    lines: list[str] = [description_text, "", "Proposed fix:"]
    if proposed_code and _looks_like_code(proposed_code):
        # Prefer a code block only if it looks like code
        lines += ["```", proposed_code, "```"]
    elif suggestion_text:
        lines.append(suggestion_text)
    else:
        lines.append("(see diff)")

    # Prefer single-line anchoring; rely on orchestrator to snap to diff
    anchor_line = getattr(change, "line", None)
    if anchor_line is None:
        anchor_line = getattr(change, "start_line", None)

    # Provide an anchor snippet derived from the first line of code_snippet
    anchor_snippet = None
    if proposed_code:
        # If proposed_code provided, it often reflects the desired change, not current line
        pass
    code_snip = (getattr(change, "code_snippet", "") or "").strip()
    if code_snip:
        first_line = code_snip.splitlines()[0].strip()
        if first_line:
            anchor_snippet = first_line[:160]
    return {
        "content": "\n".join(lines),
        "file_path": change.file_path,
        "line": anchor_line,
        "anchor_snippet": anchor_snippet,
    }


def _format_positives_comment(positives) -> dict[str, Any]:
    """Format positive aspects as a general comment.

    Args:
        positives: List of positive aspects

    Returns:
        Comment dictionary for Bitbucket API
    """
    content_lines = [
        "## ✅ Positive Aspects",
        "",
        "Great work on these areas:",
        "",
    ]

    for positive in positives:
        content_lines.append(f"✓ {positive.description}")

    return {
        "content": "\n".join(content_lines),
        "file_path": None,
        "line": None,
    }


def _format_recommendations_comment(recommendations) -> dict[str, Any]:
    """Format recommendations as a general comment.

    Args:
        recommendations: List of recommendations

    Returns:
        Comment dictionary for Bitbucket API
    """
    content_lines = [
        "## 🚀 Future Recommendations",
        "",
        "Consider these suggestions for future improvements:",
        "",
    ]

    for recommendation in recommendations:
        content_lines.append(f"• {recommendation}")

    return {
        "content": "\n".join(content_lines),
        "file_path": None,
        "line": None,
    }


def _get_severity_summary(review_result: CodeReviewResult) -> str:
    """Generate a summary of issues by severity.

    Args:
        review_result: The review result

    Returns:
        Formatted severity summary string
    """
    counts = review_result.severity_counts

    summary_parts = []
    if counts[Severity.CRITICAL] > 0:
        summary_parts.append(f"🚨 **{counts[Severity.CRITICAL]}** critical")
    if counts[Severity.MAJOR] > 0:
        summary_parts.append(f"⚠️ **{counts[Severity.MAJOR]}** major")
    if counts[Severity.MINOR] > 0:
        summary_parts.append(f"ℹ️ **{counts[Severity.MINOR]}** minor")
    if counts[Severity.INFO] > 0:
        summary_parts.append(f"💡 **{counts[Severity.INFO]}** informational")

    if not summary_parts:
        return "✅ **No issues found** - Great job!"

    return " | ".join(summary_parts)


def print_review_summary(review_result: CodeReviewResult) -> None:
    """Print a human-readable summary of the review result.

    Args:
        review_result: The review result to print
    """
    print("\n" + "=" * 60)
    print("🤖 CODE REVIEW SUMMARY")
    print("=" * 60)

    print(f"\n📝 Summary: {review_result.summary}")

    print("\n📊 Issue Breakdown:")
    counts = review_result.severity_counts
    for severity in [Severity.CRITICAL, Severity.MAJOR, Severity.MINOR, Severity.INFO]:
        if counts[severity] > 0:
            print(f"  {severity.value.title()}: {counts[severity]}")

    if review_result.changes:
        print("\n🔧 Key Changes:")
        for i, change in enumerate(review_result.changes[:5], 1):  # Show first 5
            print(f"  {i}. {change.title} ({change.file_path}:{change.start_line})")

        if len(review_result.changes) > 5:
            print(f"  ... and {len(review_result.changes) - 5} more")

    if review_result.positives:
        print("\n✅ Positives:")
        for positive in review_result.positives:
            print(f"  ✓ {positive.description}")

    if review_result.recommendations:
        print("\n🚀 Recommendations:")
        for rec in review_result.recommendations:
            print(f"  • {rec}")

    print("\n" + "=" * 60)


def print_inline_comments_preview(review_result: CodeReviewResult) -> None:
    """Print one suggested-change preview per issue, for console output.

    Format:
    <description>
    ```
    <current code>
    ```

    Proposed fix:
    ```
    <new code>
    ```
    """
    if not review_result.changes:
        return

    print("\n" + "=" * 60)
    print("🔎 INLINE COMMENT PREVIEWS")
    print("=" * 60)

    for idx, change in enumerate(review_result.changes, start=1):
        header = f"{idx}. {change.file_path}:{change.start_line}"
        print(f"\n{header}")

        description = (change.description or "").strip()
        suggestion_text = (getattr(change, "suggestion", "") or "").strip()
        proposed_code = (getattr(change, "suggested_code", "") or "").strip()

        if description:
            print(description)

        print("\nProposed fix:")
        if proposed_code and _looks_like_code(proposed_code):
            print("```")
            print(proposed_code)
            print("```")
        elif suggestion_text:
            print(suggestion_text)
        else:
            print("(see diff)")
