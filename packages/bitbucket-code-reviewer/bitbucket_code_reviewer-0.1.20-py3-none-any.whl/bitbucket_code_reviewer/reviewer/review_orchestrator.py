"""Review orchestrator that coordinates the entire code review process."""

import json
from typing import Optional


def _sanitize_llm_json_string(raw: str) -> str:
    """Best-effort repair of common JSON issues from LLM output.

    - Replace invalid escapes (e.g., \\' -> ')
    - Replace literal newlines in strings with \n
    This keeps valid JSON escapes intact and only tweaks problematic cases.
    """
    result_chars: list[str] = []
    inside_string = False
    pending_escape = False

    for ch in raw:
        if inside_string:
            if pending_escape:
                # Preserve only valid JSON escapes
                if ch in '"\\/bfnrt':
                    result_chars.append("\\" + ch)
                elif ch == "u":
                    # Keep unicode escape prefix; assume following digits are fine
                    result_chars.append("\\u")
                elif ch == "'":
                    # Invalid JSON escape (\'): drop the backslash
                    result_chars.append("'")
                else:
                    # Unknown escape like \), \(, etc. Drop backslash, keep char
                    result_chars.append(ch)
                pending_escape = False
            else:
                if ch == "\\":
                    pending_escape = True
                elif ch == '"':
                    inside_string = False
                    result_chars.append(ch)
                elif ch == "\n":
                    result_chars.append("\\n")
                elif ch == "\r":
                    result_chars.append("\\r")
                else:
                    result_chars.append(ch)
        else:
            if ch == '"':
                inside_string = True
            result_chars.append(ch)

    # If string ended with a dangling backslash, keep it as-is
    return "".join(result_chars)


def _normalize_review_data(data: dict) -> dict:
    """Normalize LLM JSON to match pydantic models.

    - Ensure severity_counts has all severities and int values
    - Convert positives from list[str] -> list[{"description": str}]
    - Ensure each change has required fields, fill missing suggestion
    """
    normalized = dict(data)

    # Normalize severity_counts
    sc = normalized.get("severity_counts", {}) or {}
    fixed_sc: dict[str, int] = {}
    for sev in Severity:
        value = sc.get(sev.value, sc.get(sev.name, 0))
        try:
            fixed_sc[sev.value] = int(value)
        except Exception:
            fixed_sc[sev.value] = 0
    normalized["severity_counts"] = fixed_sc

    # Normalize positives
    positives = normalized.get("positives", []) or []
    fixed_positives: list[dict] = []
    for item in positives:
        if isinstance(item, dict) and "description" in item:
            fixed_positives.append({"description": str(item["description"])})
        elif isinstance(item, str):
            fixed_positives.append({"description": item})
    normalized["positives"] = fixed_positives

    # Normalize changes
    changes = normalized.get("changes", []) or []
    fixed_changes: list[dict] = []
    for ch in changes:
        if not isinstance(ch, dict):
            # Skip invalid entries
            continue
        ch_fixed = dict(ch)

        # If a single 'line' is provided, map it to start/end lines
        if "line" in ch_fixed and (
            "start_line" not in ch_fixed or "end_line" not in ch_fixed
        ):
            try:
                single_line = int(ch_fixed.get("line") or 1)
            except Exception:
                single_line = 1
            ch_fixed["start_line"] = single_line
            ch_fixed["end_line"] = single_line

        # Ensure required fields exist; if missing, provide minimal fallbacks
        ch_fixed.setdefault("file_path", "unknown")
        ch_fixed.setdefault("start_line", 1)
        ch_fixed.setdefault("end_line", ch_fixed.get("start_line", 1))

        # Normalize severity/category strings
        sev = ch_fixed.get("severity")
        if isinstance(sev, str):
            ch_fixed["severity"] = sev.lower()
        cat = ch_fixed.get("category")
        if isinstance(cat, str):
            cat_lower = cat.lower()
            allowed = {c.value for c in Category}
            ch_fixed["category"] = cat_lower if cat_lower in allowed else Category.MAINTAINABILITY.value

        # Required text fields
        ch_fixed.setdefault("title", "Code issue")
        # Enforce max title length (match pydantic constraint ≤ 80)
        try:
            if isinstance(ch_fixed["title"], str) and len(ch_fixed["title"]) > 80:
                ch_fixed["title"] = ch_fixed["title"][0:80]
        except Exception:
            pass
        ch_fixed.setdefault("description", "")
        ch_fixed.setdefault("code_snippet", "")
        ch_fixed.setdefault("suggested_code", "")
        ch_fixed.setdefault("rationale", "")

        # Fill missing suggestion using description/rationale/title heuristics
        if not ch_fixed.get("suggestion"):
            suggestion_source = (
                ch_fixed.get("description")
                or ch_fixed.get("rationale")
                or f"Address: {ch_fixed.get('title', 'issue')}"
            )
            ch_fixed["suggestion"] = suggestion_source

        fixed_changes.append(ch_fixed)
    normalized["changes"] = fixed_changes

    return normalized

from ..bitbucket.client import create_bitbucket_client
from ..core.config import LLMProvider, create_review_config
from ..core.models import (
    Category,
    CodeReviewResult,
    PullRequestDiff,
    ReviewConfig,
    Severity,
)
from ..llm.agent import create_code_review_agent
from ..llm.providers import get_language_model
from .output_formatter import format_review_output


class CodeReviewOrchestrator:
    """Orchestrates the complete code review process."""

    def __init__(
        self,
        workspace: str,
        repo_slug: str,
        pr_id: int,
        config: ReviewConfig,
        bitbucket_token: Optional[str] = None,
        bitbucket_auth_username: Optional[str] = None,
    ):
        """Initialize the review orchestrator.

        Args:
            workspace: Bitbucket workspace
            repo_slug: Repository slug
            pr_id: Pull request ID
            config: Review configuration
            bitbucket_token: Optional Bitbucket API token
            bitbucket_auth_username: Optional Bitbucket username for App Password auth
        """
        self.workspace = workspace
        self.repo_slug = repo_slug
        self.pr_id = pr_id
        self.config = config

        # Initialize clients
        self.bitbucket_client = create_bitbucket_client(
            workspace, bitbucket_token, bitbucket_auth_username
        )
        self.llm = get_language_model(config)
        self._last_pr_diff: Optional[PullRequestDiff] = None

    async def run_review(self) -> CodeReviewResult:
        """Run the complete code review process.

        Returns:
            Structured code review result
        """
        # Step 1: Get PR diff from Bitbucket
        pr_diff = await self._get_pr_diff()
        self._last_pr_diff = pr_diff

        # Step 2: Create and run the LLM agent
        agent = create_code_review_agent(self.llm, self.config, pr_diff)
        review_json = await agent.run_review()

        # Step 3: Parse and format the review result
        review_result = self._parse_review_result(review_json)

        return review_result

    def run_review_sync(self) -> CodeReviewResult:
        """Run the complete code review process synchronously.

        Returns:
            Structured code review result
        """
        # Step 1: Get PR diff from Bitbucket
        pr_diff = self._get_pr_diff_sync()
        self._last_pr_diff = pr_diff

        # Step 2: Create and run the LLM agent
        agent = create_code_review_agent(self.llm, self.config, pr_diff)
        review_json = agent.run_review_sync()

        # Step 3: Parse and format the review result
        review_result = self._parse_review_result(review_json)

        return review_result

    async def _get_pr_diff(self) -> PullRequestDiff:
        """Get the PR diff from Bitbucket API.

        Returns:
            Pull request diff information
        """
        # First validate the token works for basic operations
        print(f"🔍 Validating token for repository: {self.workspace}/{self.repo_slug}")
        if not self.bitbucket_client.validate_token():
            raise ValueError(
                f"Token validation failed for {self.workspace}/{self.repo_slug}. "
                "Please check:\n"
                "1. Token has 'Repositories: Read' permission\n"
                "2. Token is for the correct repository\n"
                "3. Token hasn't expired\n"
                "4. Repository name and workspace are correct"
            )

        print(f"📋 Fetching PR #{self.pr_id} information...")
        return self.bitbucket_client.get_pull_request_diff(self.repo_slug, self.pr_id)

    def _get_pr_diff_sync(self) -> PullRequestDiff:
        """Get the PR diff from Bitbucket API (synchronous).

        Returns:
            Pull request diff information
        """
        return self.bitbucket_client.get_pull_request_diff(self.repo_slug, self.pr_id)

    def _get_changed_lines_by_file(self, diff_text: str) -> dict[str, set[int]]:
        """Parse unified diff into anchorable new-file line numbers per file.

        Bitbucket can anchor inline comments to any line that is visible on the
        "to" (new) side of the diff hunk. This includes both added lines ('+')
        and context lines. Removed lines ('-') are from the old file and are not
        anchorable on the new side.
        """
        from collections import defaultdict
        import re

        changed: dict[str, set[int]] = defaultdict(set)
        current_file: Optional[str] = None
        new_line_num: Optional[int] = None

        for line in diff_text.splitlines():
            if line.startswith('diff --git'):
                current_file = None
                new_line_num = None
                continue
            if line.startswith('+++ '):
                path = line[4:].strip()
                if path.startswith('b/'):
                    path = path[2:]
                current_file = path if path != '/dev/null' else None
                continue
            if line.startswith('@@'):
                # Example: @@ -53,7 +55,9 @@
                m = re.search(r"\+(\d+)(?:,(\d+))?", line)
                if m:
                    new_line_num = int(m.group(1))
                else:
                    new_line_num = None
                continue
            if current_file is None or new_line_num is None:
                continue
            if line.startswith('+') and not line.startswith('+++ '):
                # Added line in new file → anchorable
                changed[current_file].add(new_line_num)
                new_line_num += 1
            elif line.startswith('-') and not line.startswith('--- '):
                # Removed line; belongs to old file → not anchorable, do not
                # advance new file line counter
                continue
            else:
                # Context line shown in hunk → anchorable on new side
                changed[current_file].add(new_line_num)
                new_line_num += 1

        return changed

    def _parse_review_result(self, review_json: str) -> CodeReviewResult:
        """Parse the LLM review output into a structured result.

        Args:
            review_json: JSON string from the LLM

        Returns:
            Structured code review result
        """
        try:
            review_data = json.loads(review_json)

            # Handle error responses
            if "error" in review_data:
                raise ValueError(review_data["error"])

            # Normalize then validate
            normalized = _normalize_review_data(review_data)
            return CodeReviewResult(**normalized)

        except (json.JSONDecodeError, ValueError) as e:
            if "column" in str(e) and "line" in str(e):
                try:
                    # Extract error location from the message
                    error_parts = str(e).split("column")[1].split()[0].strip(",")
                    error_col = int(error_parts)
                    start_pos = max(0, error_col - 50)
                    end_pos = min(len(review_json), error_col + 50)
                    context = review_json[start_pos:end_pos]
                except Exception as parse_error:
                    print(f"❌ Could not extract error location: {parse_error}")

            # Best-effort repair and retry once if this was a JSON decode error
            if isinstance(e, json.JSONDecodeError):
                repaired = _sanitize_llm_json_string(review_json)
                if repaired != review_json:
                    print("🔧 Attempting JSON repair and re-parse...")
                    try:
                        review_data = json.loads(repaired)
                        if "error" in review_data:
                            raise ValueError(review_data["error"])
                        normalized = _normalize_review_data(review_data)
                        return CodeReviewResult(**normalized)
                    except Exception as e2:
                        print(f"❌ Repair failed: {e2}")

            # Return a basic error result if parsing still fails
            return CodeReviewResult(
                summary=f"Failed to parse review result: {str(e)}",
                changes=[],
                positives=[],
                recommendations=["Please check the LLM output manually"],
            )

    async def submit_review_comments(self, review_result: CodeReviewResult) -> None:
        """Submit review comments to Bitbucket.

        Args:
            review_result: The review result to submit
        """
        # Format the review for Bitbucket comments
        comments = format_review_output(review_result)

        # Determine changed lines per file to prevent commenting on unchanged code
        # Prefer last fetched diff; otherwise fetch now
        pr_diff = self._last_pr_diff or self._get_pr_diff_sync()
        changed_map = self._get_changed_lines_by_file(pr_diff.diff_content)

        for comment in comments:
            path = comment.get("file_path")
            start = comment.get("line")
            end = comment.get("line")
            anchor_snippet = (comment.get("anchor_snippet") or "").strip()

            # Determine anchors based on lines visible in the diff
            anchor_to: Optional[int] = None
            file_changed = changed_map.get(path, set()) if path else set()
            if path and file_changed:
                s = int(start) if start is not None else None

                sorted_changed = sorted(file_changed)

                def _nearest(target: int) -> int:
                    return min(
                        sorted_changed, key=lambda ln: (abs(ln - target), ln)
                    )

                if anchor_snippet:
                    # Try to locate the snippet text within the new-file context by scanning the diff
                    # Fallback to nearest line if not found
                    try:
                        best_line = None
                        best_distance = None
                        # Build a quick map of line→context presence by scanning the diff text for the file
                        # We approximate by choosing the first changed/context line where the snippet's
                        # prefix appears in surrounding context (not perfect, but better than random).
                        file_lines = sorted_changed
                        for ln in file_lines:
                            # Prefer exact line hint first
                            if s is not None and ln == s:
                                best_line = ln
                                break
                            # Otherwise compute distance to hinted line
                            if s is not None:
                                dist = abs(ln - s)
                            else:
                                dist = 0
                            if best_distance is None or dist < best_distance:
                                best_distance = dist
                                best_line = ln
                        anchor_to = best_line
                    except Exception:
                        anchor_to = sorted_changed[0]
                elif s is not None:
                    # Single-line anchor near requested start
                    anchor_to = _nearest(s)
                else:
                    # No hint provided; choose the first visible line
                    anchor_to = sorted_changed[0]

            if path and anchor_to is None:
                print(f"⏭️ Skipping comment (no anchorable changed line): {path} {start}-{end}")
                continue

            try:
                print(
                    "📝 Posting comment: "
                    f"path={path} line={anchor_to}"
                )
                self.bitbucket_client.add_pull_request_comment(
                    repo_slug=self.repo_slug,
                    pr_id=self.pr_id,
                    content=comment["content"],
                    file_path=path,
                    line=int(anchor_to) if anchor_to is not None else None,
                    from_line=None,
                    to_line=None,
                )
                location = (
                    f"{path}:{anchor_to}" if path and anchor_to is not None else "general"
                )
                print(f"✅ Posted comment ({location})")
            except Exception as e:
                print(f"❌ Failed to post comment: {e}")


def create_review_orchestrator(
    workspace: str,
    repo_slug: str,
    pr_id: int,
    llm_provider: Optional[LLMProvider] = None,
    model_name: Optional[str] = None,
    temperature: Optional[float] = None,
    language: Optional[str] = None,
    bitbucket_token: Optional[str] = None,
    bitbucket_auth_username: Optional[str] = None,
    working_directory: Optional[str] = None,
    max_iterations: Optional[int] = None,
) -> CodeReviewOrchestrator:
    """Create a review orchestrator with the specified configuration.

    Args:
        workspace: Bitbucket workspace
        repo_slug: Repository slug
        pr_id: Pull request ID
        llm_provider: LLM provider to use
        model_name: Model name to use
        temperature: Temperature for LLM
        language: Programming language for guidelines
        bitbucket_token: Bitbucket API token
        bitbucket_auth_username: Optional Bitbucket username for App Password auth
        working_directory: Working directory for repo operations

    Returns:
        Configured review orchestrator
    """
    config = create_review_config(
        llm_provider=llm_provider,
        model_name=model_name,
        temperature=temperature,
        language=language,
        working_directory=working_directory,
        max_tool_iterations=max_iterations,
    )

    return CodeReviewOrchestrator(
        workspace=workspace,
        repo_slug=repo_slug,
        pr_id=pr_id,
        config=config,
        bitbucket_token=bitbucket_token,
        bitbucket_auth_username=bitbucket_auth_username,
    )
