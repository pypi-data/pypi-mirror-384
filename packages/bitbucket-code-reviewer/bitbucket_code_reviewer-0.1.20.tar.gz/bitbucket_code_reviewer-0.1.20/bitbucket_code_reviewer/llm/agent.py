"""LangChain agent for code review with tool-calling capabilities."""

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
    ):
        """Initialize the code review agent.

        Args:
            llm: Configured language model
            config: Review configuration
            pr_diff: Pull request diff information
        """
        self.llm = llm
        self.config = config
        self.pr_diff = pr_diff

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

            # Create the initial message
            initial_message = self._create_initial_message()

            # Create the prompt template
            prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", system_prompt),
                    ("human", initial_message),
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

        for file_change in self.pr_diff.files[:10]:  # Limit to first 10 files
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

        if len(self.pr_diff.files) > 10:
            message_parts.append(f"... and {len(self.pr_diff.files) - 10} more files")

        message_parts.extend(
            [
                "",
                "IMPORTANT: Respond ONLY with valid JSON. The JSON must contain exactly these fields:",
                "- summary: string describing overall code quality",
                "- severity_counts: object with integer counts for critical/major/minor/info",
                "- changes: array of issue objects",
                "- positives: array of strings with positive feedback",
                "- recommendations: array of strings with suggestions",
                "",
                "Each change object must have: file_path, start_line, end_line, severity, category, title, description, suggestion, code_snippet, suggested_code, rationale",
                "",
                "Valid severity values: 'critical', 'major', 'minor', 'info'",
                "Valid category values: 'security', 'performance', 'maintainability', 'architecture', 'style'",
                "",
                "Do NOT include markdown, explanations, or text outside the JSON structure.",
                "",
                "Focus on changed files. If strictly necessary to validate correctness (imports/config), you may read up to 2 non-diff files; keep it minimal and explain why.",
            ]
        )

        return "\n".join(message_parts)

    async def run_review(self) -> str:
        """Run the code review process.

        Returns:
            Review result as JSON string
        """
        try:
            result = await self.agent_executor.ainvoke({})
            return result["output"]
        except Exception as e:
            return f'{{"error": "Review failed: {str(e)}"}}'

    def run_review_sync(self) -> str:
        """Run the code review process synchronously.

        Returns:
            Review result as JSON string
        """
        try:
            import time
            print("🤖 Starting LLM code review analysis...", flush=True)
            print("🤖 About to start timing...", flush=True)

            # Time the entire agent execution
            total_start_time = time.time()
            print(f"⏱️  Started at: {time.strftime('%H:%M:%S', time.localtime(total_start_time))}", flush=True)
            print("🤖 About to invoke agent executor...", flush=True)

            print("🤖 Calling agent_executor.invoke() now...", flush=True)
            try:
                result = self.agent_executor.invoke({})
                print("🤖 agent_executor.invoke() returned successfully!", flush=True)
            except KeyboardInterrupt:
                elapsed_so_far = time.time() - total_start_time
                print(f"\n⏹️  Code review interrupted by user (ran for {elapsed_so_far:.2f}s)", flush=True)
                raise

            total_elapsed_time = time.time() - total_start_time

            print("🤖 Agent executor completed successfully")
            llm_output = result["output"]
            print(f"🤖 LLM returned {len(llm_output)} characters")
            print(f"🤖 Total execution time: {total_elapsed_time:.2f}s")
            print(f"🤖 LLM output preview: {llm_output[:200]}...")

            # Always print full response for debugging
            print(f"🤖 FULL LLM RESPONSE: {repr(llm_output)}")

            return llm_output
        except Exception as e:
            error_msg = f'{{"error": "Review failed: {str(e)}"}}'
            print(f"❌ LLM ERROR: {str(e)}")
            return error_msg


def create_code_review_agent(
    llm: BaseLanguageModel,
    config: ReviewConfig,
    pr_diff: PullRequestDiff,
) -> CodeReviewAgent:
    """Create a code review agent instance.

    Args:
        llm: Configured language model
        config: Review configuration
        pr_diff: Pull request diff information

    Returns:
        Configured code review agent
    """
    return CodeReviewAgent(llm, config, pr_diff)
