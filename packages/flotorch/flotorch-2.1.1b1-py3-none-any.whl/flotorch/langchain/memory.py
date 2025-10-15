"""LangChain-compatible memory backed by Flotorch.

This module provides a minimal `BaseMemory` implementation that persists
conversation history to Flotorch and returns a single history string under
`memory_key` for prompt formatting.
"""

from typing import Any, Dict, List, Optional

from langchain.schema import BaseMemory

from flotorch.sdk.memory import FlotorchMemory
from flotorch.sdk.utils.logging_utils import (
    log_error,
    log_object_creation,
    log_warning,
)

class FlotorchLangChainMemory(BaseMemory):
    """A LangChain `BaseMemory` that uses Flotorch for long-term storage.

    This class persists conversation turns to Flotorch and returns a single
    history string (under `memory_key`) for prompt formatting.
    """
    memory_key: str = "longterm_history"
    name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    user_id: Optional[str] = None
    app_id: Optional[str] = None
    memory_client: Optional[FlotorchMemory] = None

    def __init__(
        self,
        name: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        user_id: Optional[str] = None,
        app_id: Optional[str] = None,
    ) -> None:
        """Initialize the memory provider and underlying Flotorch client.

        Parameters
        - name: Provider name registered in Flotorch.
        - api_key: Flotorch API key for authentication.
        - base_url: Flotorch Gateway base URL.
        - user_id: Optional user identifier for scoping memory.
        - app_id: Optional application identifier for scoping memory.
        """
        memory_key = "longterm_history"
        super().__init__(
            name=name,
            api_key=api_key,
            base_url=base_url,
            user_id=user_id,
            app_id=app_id,
            memory_key= memory_key,
        )

        # Warn about missing configuration that may impact behavior, but do not
        # alter control flow or raise errors to preserve existing logic.
        if not api_key:
            log_warning("FlotorchLangChainMemory: api_key is not set.")
        if not base_url:
            log_warning("FlotorchLangChainMemory: base_url is not set.")
        if not user_id:
            log_warning("FlotorchLangChainMemory: user_id is not provided.")
        if not app_id:
            log_warning("FlotorchLangChainMemory: app_id is not provided.")

        self.memory_client = FlotorchMemory(
            api_key=api_key,
            base_url=base_url,
            provider_name=name,
        )

        # Object creation log with relevant context for observability.
        log_object_creation(
            "FlotorchLangChainMemory",
            provider_name=name,
            base_url=base_url,
            user_id=user_id,
            app_id=app_id,
            memory_key=self.memory_key,
        )

    @property
    def memory_variables(self) -> List[str]:
        """Return the list of variables this memory adds to the prompt.

        Returns a single-element list containing `self.memory_key`.
        """
        return [self.memory_key]

    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch relevant memory items and return a single history string.

        The input query is derived from `inputs["input"]` or the first value in
        the mapping. If no query is available, a warning is logged and the
        backend is queried with an empty string to keep behavior unchanged.
        """
        try:
            # Extract query from inputs without changing the original flow.
            query = inputs.get("input") or next(iter(inputs.values()), "")
            if not query:
                log_warning(
                    "FlotorchLangChainMemory.load_memory_variables: empty query."
                )

            result = self.memory_client.search(
                userId=self.user_id,
                appId=self.app_id,
                limit=50,
                query=query,
            )
            data_items = result.get("data", [])
            if not data_items:
                log_warning(
                    "FlotorchLangChainMemory.load_memory_variables: no items found."
                )
            history_value = self._build_history_from_data(data_items)
            return {self.memory_key: history_value}
        except Exception as e:
            log_error("FlotorchLangChainMemory.load_memory_variables", e)
            return {self.memory_key: ""}

    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> None:
        """Persist the latest user input and assistant response to Flotorch."""
        try:
            prompt = inputs.get("input") or next(iter(inputs.values()))
            response = (
                outputs.get("response")
                or outputs.get("output")
                or next(iter(outputs.values()))
            )
            if not prompt:
                log_warning(
                    "FlotorchLangChainMemory.save_context: empty user prompt."
                )
            if not response:
                log_warning(
                    "FlotorchLangChainMemory.save_context: empty assistant response."
                )

            messages = [
                {"role": "user", "content": prompt},
                {"role": "assistant", "content": response},
            ]
            self.memory_client.add(
                messages=messages,
                userId=self.user_id,
                appId=self.app_id,
            )
        except Exception as e:
            log_error("FlotorchLangChainMemory.save_context", e)

    def clear(self) -> None:
        """Delete all stored memory items in Flotorch for this scope."""
        try:
            result = self.memory_client.search(
                userId=self.user_id,
                appId=self.app_id,
                limit=1000,
            )
            deleted_count = 0
            for item in result.get("data", []):
                mem_id = item.get("id")
                if mem_id:
                    self.memory_client.delete(mem_id)
                    deleted_count += 1
            if deleted_count > 0:
                log_warning(
                    "FlotorchLangChainMemory.clear: cleared %d item(s)."
                )
        except Exception as e:
            log_error("FlotorchLangChainMemory.clear", e)

    @staticmethod
    def _build_history_from_data(data_items: List[Dict[str, Any]]) -> str:
        """Convert Flotorch search results into a prompt-ready history string.

        The API returns a list in result["data"]. Each item typically contains
        a plain "content" field with a memory fact. This extracts those strings
        and joins them with newlines for use as prompt history.
        """
        lines: List[str] = []
        for item in data_items:
            content_value = item.get("content")
            if isinstance(content_value, str) and content_value.strip():
                lines.append(content_value.strip())
                continue
            # Fallbacks if backend uses different keys
            alt_value = item.get("message") or item.get("text")
            if isinstance(alt_value, str) and alt_value.strip():
                lines.append(alt_value.strip())
        return "\n".join(lines)