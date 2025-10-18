"""Callback handlers for instrumenting LLM behavior (e.g., timing)."""

from __future__ import annotations

import time
from typing import Any, Dict, Optional

from langchain_core.callbacks.base import BaseCallbackHandler


class LLMTimingCallback(BaseCallbackHandler):
    """Measure and print the duration of each LLM roundtrip.

    Prints a single concise line on LLM end (and on error) including provider
    and model names, along with duration in seconds. If token usage metadata is
    available on the response, it will also print prompt/completion/total
    tokens.
    """

    def __init__(self, provider_name: str, model_name: str) -> None:
        self.provider_name = provider_name
        self.model_name = model_name
        self._start_times: Dict[str, float] = {}

    # LLM lifecycle ---------------------------------------------------------
    def on_llm_start(
        self,
        serialized: Dict[str, Any],
        prompts: list[str],
        run_id: Any,
        parent_run_id: Optional[Any] = None,
        **kwargs: Any,
    ) -> None:
        self._start_times[str(run_id)] = time.perf_counter()

    def on_llm_end(
        self,
        response: Any,
        run_id: Any,
        parent_run_id: Optional[Any] = None,
        **kwargs: Any,
    ) -> None:
        key = str(run_id)
        start = self._start_times.pop(key, None)
        if start is None:
            return

        elapsed = time.perf_counter() - start

        # Try to extract token usage information if present.
        tokens_suffix = self._format_token_usage_suffix(response)

        print(
            (
                f"🤖 LLM roundtrip ({self.provider_name}/{self.model_name}) "
                f"took {elapsed:.2f}s{tokens_suffix}"
            ),
            flush=True,
        )

    def on_llm_error(
        self,
        error: Exception,
        run_id: Any,
        parent_run_id: Optional[Any] = None,
        **kwargs: Any,
    ) -> None:
        key = str(run_id)
        start = self._start_times.pop(key, None)
        if start is None:
            return

        elapsed = time.perf_counter() - start
        print(
            (
                f"❌ LLM roundtrip ({self.provider_name}/{self.model_name}) "
                f"failed after {elapsed:.2f}s: {error}"
            ),
            flush=True,
        )

    # Helpers ---------------------------------------------------------------
    @staticmethod
    def _format_token_usage_suffix(response: Any) -> str:
        """Return a formatted token usage suffix if available on response.

        Supports common shapes like
        response.llm_output["token_usage"] or ["usage"].
        """
        try:
            llm_output = getattr(response, "llm_output", None)
            if isinstance(llm_output, dict):
                usage = (
                    llm_output.get("token_usage")
                    or llm_output.get("usage")
                    or {}
                )
                if isinstance(usage, dict):
                    prompt = usage.get("prompt_tokens")
                    completion = usage.get("completion_tokens")
                    total = usage.get("total_tokens")
                    if total is None and (
                        isinstance(prompt, int) or isinstance(completion, int)
                    ):
                        total = (prompt or 0) + (completion or 0)

                    if any(v is not None for v in (prompt, completion, total)):
                        return (
                            f" | tokens p/c/t="
                            f"{prompt if prompt is not None else '-'}"
                            f"/"
                            f"{completion if completion is not None else '-'}"
                            f"/"
                            f"{total if total is not None else '-'}"
                        )
        except Exception:
            # Be resilient to schema differences.
            return ""
        return ""


