"""Flotorch memory integration for AutoGen."""
import os
from typing import Any, Optional

from autogen_core import CancellationToken
from autogen_core.model_context import ChatCompletionContext
from autogen_core.memory import (
    Memory,
    MemoryContent,
    MemoryQueryResult,
    UpdateContextResult,
    MemoryMimeType,
)
from autogen_core.models import SystemMessage
from flotorch.sdk.memory import FlotorchMemory
from flotorch.sdk.utils.logging_utils import log_error, log_object_creation


class FlotorchAutogenMemory(Memory):
    """Flotorch memory integration for AutoGen."""
    def __init__(
        self,
        name: str,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        user_id: Optional[str] = None,
        app_id: Optional[str] = None,
        limit: Optional[int] = 50,
    ):
        self._name = name
        self._user_id = user_id
        self._app_id = app_id
        self._limit = limit
        self._base_url = base_url or os.getenv("FLOTORCH_BASE_URL")
        self._api_key = api_key or os.getenv("FLOTORCH_API_KEY")
        if not self._base_url:
            raise ValueError(
                "FLOTORCH_BASE_URL environment variable or base_url parameter is required"
            )
        if not self._api_key:
            raise ValueError(
                "FLOTORCH_API_KEY environment variable or api_key parameter is required"
            )
        self._memory = FlotorchMemory(
            api_key=self._api_key, base_url=self._base_url, provider_name=self._name
        )
        # Track the last query and results to prevent duplicates
        self._last_query = None
        self._last_results_hash = None
        # Log object creation
        log_object_creation(
            "FlotorchMemoryService", provider_name=name, base_url=self._base_url
        )

    def _get_results_hash(self, results: MemoryQueryResult) -> str:
        """Generate a hash of the memory results for deduplication."""
        if not results.results:
            return "empty"
        # Create a hash based on the content of all memory items
        content_strings = [str(memory.content) for memory in results.results]
        return hash(tuple(sorted(content_strings)))

    async def update_context(
        self,
        model_context: ChatCompletionContext,
    ) -> UpdateContextResult:
        """Update the model context with relevant memories.

        This method retrieves the conversation history from the model context,
        uses the last message as a query to find relevant memories, and then
        adds those memories to the context as a system message.

        Args:
            model_context: The model context to update.

        Returns:
            UpdateContextResult containing memories added to the context.
        """
        # Get messages from context
        messages = await model_context.get_messages()
        if not messages:
            return UpdateContextResult(memories=MemoryQueryResult(results=[]))

        # Use the last message as query
        last_message = messages[-1]
        query_text = (
            last_message.content
            if isinstance(last_message.content, str)
            else str(last_message)
        )
        
        # Check if this is the same query we've already processed
        if query_text == self._last_query:
            # Return empty result to prevent duplicate processing
            return UpdateContextResult(memories=MemoryQueryResult(results=[]))
        
        # Query memory
        query_results = await self.query(query_text, limit=self._limit)
        
        # Generate hash of current results
        current_results_hash = self._get_results_hash(query_results)
        
        # Check if we've already added these exact results
        if current_results_hash == self._last_results_hash:
            # Return empty result to prevent duplicate processing
            return UpdateContextResult(memories=MemoryQueryResult(results=[]))

        # If we have results, add them to the context
        if isinstance(query_results, MemoryQueryResult):
            if query_results.results:
                # Format memories as numbered list
                memory_strings = [
                    f"{i}. {str(memory.content)}"
                    for i, memory in enumerate(query_results.results, 1)
                ]
                memory_context = "\nRelevant memories:\n" + "\n".join(memory_strings)

                # Add as system message
                await model_context.add_message(SystemMessage(content=memory_context))
                
                # Update our tracking state
                self._last_query = query_text
                self._last_results_hash = current_results_hash

        return UpdateContextResult(memories=query_results)

    async def query(
        self,
        query: str | MemoryContent = "",
        cancellation_token: CancellationToken | None = None,
        **kwargs: Any,
    ) -> MemoryQueryResult:
        """Return all memories without any filtering.

        Args:
            query: Ignored in this implementation
            cancellation_token: Optional token to cancel operation
            **kwargs: Additional parameters (ignored)

        Returns:
            MemoryQueryResult containing all stored memories
        """
        # Extract query text
        if isinstance(query, str):
            query_text = query
        elif hasattr(query, "content"):
            query_text = str(query.content)
        else:
            query_text = str(query)
        # Use the search method from FlotorchMemory
        try:
            result = self._memory.search(
                userId=self._user_id if self._user_id else None,
                appId=self._app_id if self._app_id else None,
                query=query_text,
                page=1,
                limit=self._limit,
            )
        except Exception as e:
            log_error("FlotorchAutogenMemory.query.search", e)
            # Preserve behavior by propagating
            raise
        raw_memories = result.get("data", [])
        # If no memories found, return empty response
        if not raw_memories:
            return MemoryQueryResult(results = [MemoryContent(content="No memories found", mime_type=MemoryMimeType.TEXT)])
        memory_entries = []
        for memory in raw_memories:
            memory_text = memory.get("content","")
            if memory_text:
                memory_entries.append(
                    MemoryContent(content=memory_text, mime_type=MemoryMimeType.TEXT)
                )
        return MemoryQueryResult(results=memory_entries)

    async def add(
        self,
        content: MemoryContent,
        cancellation_token: CancellationToken | None = None,
    ) -> None:
        """Add new content to memory.

        Args:
            content: Memory content to store
            cancellation_token: Optional token to cancel operation
        """
        try:

            messages = [{"role": "user", "content": content.content}]
            metadata = {
                "source": "adk_session",
                "importance": 0.5,
                "category": "conversation",
                "tags": ["adk", "session"],
            }

            self._memory.add(
                messages=messages,
                userId=self._user_id if self._user_id else None,
                appId=self._app_id if self._app_id else None,
                metadata=metadata,
            )
        except Exception as e:
            log_error("FlotorchMemoryService.add_session_to_memory", e)

    async def clear(self) -> None:
        """Clear all memory content."""
        pass

    async def close(self) -> None:
        """Cleanup resources if needed."""
        pass