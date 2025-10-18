"""LangChain agent for code review with tool-calling capabilities."""

import json
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.language_models import BaseLanguageModel
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from ..core.models import PullRequestDiff, ReviewConfig
from ..prompts import get_system_prompt
from .tools import create_code_review_tools
from .callbacks import LLMTimingCallback


class CodeReviewAgent:
    """LangChain agent for performing code reviews."""

    def __init__(
        self,
        llm: BaseLanguageModel,
        config: ReviewConfig,
        pr_diff: PullRequestDiff,
        previous_comments: list = None,
    ):
        """Initialize the code review agent.

        Args:
            llm: Configured language model
            config: Review configuration
            pr_diff: Pull request diff information
            previous_comments: List of previous bot comments on this PR
        """
        self.llm = llm
        self.config = config
        self.pr_diff = pr_diff
        self.previous_comments = previous_comments or []

        # Create tools with working directory
        self.tools = create_code_review_tools(config.working_directory)

        # Create the agent
        self.agent_executor = self._create_agent()

    def _create_agent(self) -> AgentExecutor:
        """Create the LangChain agent with tools.

        Returns:
            Configured agent executor
        """
        try:
            # Get the system prompt
            system_prompt = get_system_prompt(language=self.config.language)

            # Create the prompt template
            prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", system_prompt),
                    ("human", "{input}"),
                    MessagesPlaceholder(variable_name="agent_scratchpad"),
                ]
            )
        except Exception as e:
            print(f"❌ ERROR during agent creation: {str(e)}")
            raise

        # Attach per-LLM roundtrip timing via callback
        try:
            provider_name = getattr(self.config.llm_provider, "value", str(self.config.llm_provider))
            timing_callback = LLMTimingCallback(
                provider_name=provider_name,
                model_name=self.config.model_name,
            )
            instrumented_llm = self.llm.with_config(callbacks=[timing_callback])
        except Exception:
            # Fall back gracefully to the raw LLM if instrumentation fails
            instrumented_llm = self.llm

        # Create the agent
        agent = create_openai_tools_agent(
            llm=instrumented_llm,
            tools=self.tools,
            prompt=prompt,
        )

        # Create the agent executor
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=False,  # Disable verbose output
            max_iterations=self.config.max_tool_iterations,
            handle_parsing_errors=True,
        )

    def _create_initial_message(self) -> str:
        """Create the initial human message with PR context.

        Returns:
            Initial message for the agent
        """
        pr_info = self.pr_diff.pull_request

        message_parts = [
            "Please review this pull request:",
            f"Title: {pr_info.title}",
            f"Author: {pr_info.author}",
            f"Source Branch: {pr_info.source_branch}",
            f"Target Branch: {pr_info.target_branch}",
            "",
            "Files changed:",
        ]

        for file_change in self.pr_diff.files:
            status_emoji = {
                "added": "➕",
                "modified": "✏️",
                "removed": "➖",
                "renamed": "📝",
            }.get(file_change.status, "❓")

            message_parts.append(
                f"{status_emoji} {file_change.filename} "
                f"(+{file_change.additions}, -{file_change.deletions})"
            )

        # Add previous comments section if any exist
        if self.previous_comments:
            message_parts.extend(
                [
                    "",
                    "=" * 60,
                    "PREVIOUS BOT COMMENTS ON THIS PR:",
                    "=" * 60,
                ]
            )
            
            for comment in self.previous_comments:
                comment_location = "General comment"
                if comment.get("file_path"):
                    location_str = comment["file_path"]
                    if comment.get("line"):
                        location_str += f":{comment['line']}"
                    comment_location = f"Inline comment at {location_str}"
                
                message_parts.extend(
                    [
                        f"• {comment_location}",
                        f"  Created: {comment.get('created_date', 'Unknown')}",
                        f"  Content: {comment.get('content', '')[:200]}...",
                        "",
                    ]
                )
            
            message_parts.extend(
                [
                    "=" * 60,
                    "IMPORTANT: These issues have already been commented on in previous reviews.",
                    "Do NOT create duplicate comments on the same issues.",
                    "Only comment on NEW issues or issues in DIFFERENT locations.",
                    "=" * 60,
                    "",
                ]
            )

        # Add explicit file path reminder
        file_paths = [f.filename for f in self.pr_diff.files]
        message_parts.extend(
            [
                "",
                "=" * 60,
                "⚠️  VALID FILE PATHS FOR THIS REVIEW (use ONLY these):",
                "=" * 60,
            ]
        )
        for fp in file_paths:
            message_parts.append(f"  - {fp}")
        
        message_parts.extend(
            [
                "=" * 60,
                "",
                "CRITICAL RULES:",
                "1. You MUST ONLY use file paths from the list above",
                "2. COPY the exact file path - do NOT invent variations",
                "3. If you use a file path NOT in the list above, your comment will be REJECTED",
                "",
                "IMPORTANT: Respond ONLY with valid JSON. Use EXACT field names as shown:",
                "",
                "Required top-level fields:",
                "- summary: string describing overall code quality",
                "- severity_counts: object with integer counts {critical: 0, major: 0, minor: 0, info: 0}",
                "- changes: array of issue objects (MUST use exact field names below)",
                "- positives: array of {description: string} objects",
                "- recommendations: array of strings",
                "",
                "Each change object MUST have these EXACT field names:",
                "- file_path (string) - MUST be an exact match from 'Files changed' list - NOT 'file' or 'path'",
                "- start_line (number)",
                "- end_line (number)",
                "- severity (string: 'critical'|'major'|'minor'|'info')",
                "- category (string: 'security'|'performance'|'maintainability'|'architecture'|'style')",
                "- title (string, max 80 chars) - brief issue title",
                "- description (string) - detailed explanation - NOT 'message' or 'details'",
                "- suggestion (string) - how to fix - NOT 'proposed_fix' or 'recommendation'",
                "- code_snippet (string) - problematic code",
                "- suggested_code (string) - improved code",
                "- rationale (string) - why this improves the code",
                "",
                "=" * 60,
                "⚠️⚠️⚠️ CRITICAL: VALID FILE PATHS (copy EXACTLY) ⚠️⚠️⚠️",
                "=" * 60,
            ]
        )
        for fp in file_paths:
            message_parts.append(f"✓ {fp}")
        
        message_parts.extend(
            [
                "=" * 60,
                "",
                "Do NOT use alternative field names like 'message', 'proposed_fix', or 'fix'.",
                "Do NOT include markdown code blocks, explanations, or text outside the JSON structure.",
                "Do NOT invent file paths - use ONLY the paths marked with ✓ above.",
                "If you find an issue but are unsure which file, SKIP that issue rather than guessing the path.",
                "",
                "Focus on changed files. If strictly necessary to validate correctness (imports/config), you may read up to 2 non-diff files; keep it minimal and explain why.",
            ]
        )

        return "\n".join(message_parts)

    def _sanitize_json_string(self, raw: str) -> str:
        """Best-effort repair of common JSON issues from LLM output.
        
        Args:
            raw: Raw JSON string from LLM
            
        Returns:
            Cleaned JSON string
        """
        # Strip markdown code blocks
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            # Find the first newline after the opening ```
            first_newline = cleaned.find("\n")
            if first_newline != -1:
                cleaned = cleaned[first_newline + 1 :]
            # Remove trailing ```
            if cleaned.endswith("```"):
                cleaned = cleaned[: -3].rstrip()
        
        return cleaned

    def _validate_json(self, json_string: str) -> tuple[bool, str, str]:
        """Validate JSON and return error details if invalid.
        
        Args:
            json_string: JSON string to validate
            
        Returns:
            Tuple of (is_valid, error_message, error_context)
        """
        try:
            cleaned = self._sanitize_json_string(json_string)
            parsed = json.loads(cleaned)
            
            # Validate required structure
            if "changes" not in parsed:
                return False, "Missing required field 'changes'", ""
            if not isinstance(parsed["changes"], list):
                return False, "Field 'changes' must be a list", ""
            
            return True, "", ""
            
        except json.JSONDecodeError as e:
            # Extract context around the error
            error_pos = e.pos
            context_start = max(0, error_pos - 100)
            context_end = min(len(json_string), error_pos + 100)
            error_context = json_string[context_start:context_end]
            
            error_message = f"JSON parsing error: {e.msg} (line {e.lineno}, column {e.colno})"
            return False, error_message, error_context
            
        except Exception as e:
            return False, f"JSON validation error: {str(e)}", ""

    def _create_retry_feedback(self, error_message: str, error_context: str) -> str:
        """Create feedback message for LLM when JSON parsing fails.
        
        Args:
            error_message: Description of the JSON error
            error_context: Text context around the error
            
        Returns:
            Feedback message for the LLM
        """
        feedback_parts = [
            "❌ JSON PARSING ERROR DETECTED",
            "",
            f"Error: {error_message}",
            "",
        ]
        
        if error_context:
            feedback_parts.extend([
                "Context around error:",
                "```",
                f"...{error_context}...",
                "```",
                "",
            ])
        
        feedback_parts.extend([
            "Please regenerate the COMPLETE code review JSON with this error fixed.",
            "",
            "Requirements:",
            "- All strings must be properly escaped (especially quotes, newlines, backslashes)",
            "- All brackets and braces must be balanced",
            "- No trailing commas in arrays or objects",
            "- Valid JSON structure throughout",
            "",
            "Generate the corrected JSON now (ONLY valid JSON, no markdown or explanations):",
        ])
        
        return "\n".join(feedback_parts)

    async def run_review(self, max_retries: int = 3) -> str:
        """Run the code review process with retry on JSON parsing failures.

        Args:
            max_retries: Maximum number of retry attempts for JSON parsing errors

        Returns:
            Review result as JSON string
        """
        try:
            initial_message = self._create_initial_message()
            current_message = initial_message
            
            for attempt in range(max_retries):
                # Invoke the agent
                result = await self.agent_executor.ainvoke({"input": current_message})
                output = result["output"]
                
                # Validate JSON
                is_valid, error_msg, error_context = self._validate_json(output)
                
                if is_valid:
                    # Success!
                    if attempt > 0:
                        print(f"✅ JSON validation successful on retry attempt {attempt + 1}")
                    return output
                
                # JSON validation failed
                print(f"⚠️ Attempt {attempt + 1}/{max_retries}: {error_msg}")
                
                if attempt < max_retries - 1:
                    # Create feedback for retry
                    current_message = self._create_retry_feedback(error_msg, error_context)
                    print(f"🔄 Retrying with feedback to LLM...")
                else:
                    # Final attempt failed
                    print(f"❌ All {max_retries} attempts failed. Returning last output.")
                    return output
            
            return output
            
        except Exception as e:
            return f'{{"error": "Review failed: {str(e)}"}}'

    def run_review_sync(self, max_retries: int = 3) -> str:
        """Run the code review process synchronously with retry on JSON parsing failures.

        Args:
            max_retries: Maximum number of retry attempts for JSON parsing errors

        Returns:
            Review result as JSON string
        """
        try:
            import time
            print("🤖 Starting LLM code review analysis...", flush=True)

            # Time the entire agent execution
            total_start_time = time.time()
            print(f"⏱️  Started at: {time.strftime('%H:%M:%S', time.localtime(total_start_time))}", flush=True)

            initial_message = self._create_initial_message()
            current_message = initial_message
            
            for attempt in range(max_retries):
                print(f"🤖 Calling agent_executor.invoke() (attempt {attempt + 1}/{max_retries})...", flush=True)
                
                try:
                    result = self.agent_executor.invoke({"input": current_message})
                    print("🤖 agent_executor.invoke() returned successfully!", flush=True)
                except KeyboardInterrupt:
                    elapsed_so_far = time.time() - total_start_time
                    print(f"\n⏹️  Code review interrupted by user (ran for {elapsed_so_far:.2f}s)", flush=True)
                    raise

                llm_output = result["output"]
                print(f"🤖 LLM returned {len(llm_output)} characters")
                
                # Validate JSON
                is_valid, error_msg, error_context = self._validate_json(llm_output)
                
                if is_valid:
                    # Success!
                    total_elapsed_time = time.time() - total_start_time
                    if attempt > 0:
                        print(f"✅ JSON validation successful on retry attempt {attempt + 1}")
                    print(f"🤖 Total execution time: {total_elapsed_time:.2f}s")
                    print(f"🤖 LLM output preview: {llm_output[:200]}...")
                    return llm_output
                
                # JSON validation failed
                print(f"⚠️ Attempt {attempt + 1}/{max_retries}: {error_msg}", flush=True)
                
                if attempt < max_retries - 1:
                    # Create feedback for retry
                    current_message = self._create_retry_feedback(error_msg, error_context)
                    print(f"🔄 Retrying with feedback to LLM...", flush=True)
                else:
                    # Final attempt failed
                    print(f"❌ All {max_retries} attempts failed. Returning last output.", flush=True)
                    total_elapsed_time = time.time() - total_start_time
                    print(f"🤖 Total execution time: {total_elapsed_time:.2f}s")
                    return llm_output
            
            return llm_output
            
        except Exception as e:
            error_msg = f'{{"error": "Review failed: {str(e)}"}}'
            print(f"❌ LLM ERROR: {str(e)}")
            return error_msg


def create_code_review_agent(
    llm: BaseLanguageModel,
    config: ReviewConfig,
    pr_diff: PullRequestDiff,
    previous_comments: list = None,
) -> CodeReviewAgent:
    """Create a code review agent instance.

    Args:
        llm: Configured language model
        config: Review configuration
        pr_diff: Pull request diff information
        previous_comments: List of previous bot comments on this PR

    Returns:
        Configured code review agent
    """
    return CodeReviewAgent(llm, config, pr_diff, previous_comments)
