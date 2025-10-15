"""
FlotorchStore - A LangGraph store adapter that uses FlotorchMemory for backend operations.

This module provides a seamless integration between LangGraph's store interface and
Flotorch's memory system, allowing LangGraph agents to use Flotorch's memory capabilities
as their persistent store.
"""

from __future__ import annotations
from collections.abc import Iterable
from datetime import datetime
from typing import Any, Dict, Optional
import re
import json
from dotenv import load_dotenv

from flotorch.sdk.memory import FlotorchMemory, FlotorchAsyncMemory
from langgraph.store.base import (
    BaseStore,
    GetOp,
    Item,
    ListNamespacesOp,
    Op,
    PutOp,
    Result,
    SearchItem,
    SearchOp
)
import logging

logger = logging.getLogger(__name__)

load_dotenv()


class FlotorchStore(BaseStore):
    """
    A LangGraph store adapter that uses FlotorchMemory for backend operations.

    This store implements the LangGraph BaseStore interface and delegates all
    operations to FlotorchMemory, providing seamless integration between
    LangGraph agents and Flotorch's memory system.
    """

    supports_ttl: bool = False

    def __init__(
            self,
            api_key: str,
            base_url: str,
            provider_name: str,
            userId: Optional[str] = None,
            agentId: Optional[str] = None,
            appId: Optional[str] = None,
            sessionId: Optional[str] = None
    ) -> None:
        """
        Initialize the FlotorchStore.

        Args:
            api_key: API key for FlotorchMemory authentication
            base_url: Base URL for FlotorchMemory API
            provider_name: Provider name for FlotorchMemory
            userId: User ID for memory operations (default for gateway)
            agentId: Agent ID for memory operations (default for gateway)
            appId: App ID for memory operations (default for gateway)
            sessionId: Session ID for memory operations (default for gateway)
        """
        super().__init__()

        # Initialize FlotorchMemory instances
        self._memory = FlotorchMemory(api_key, base_url, provider_name)
        self._async_memory = FlotorchAsyncMemory(api_key, base_url, provider_name)

        # Store configuration
        self.api_key = api_key
        self.base_url = base_url
        self.provider_name = provider_name
        self.userId = userId
        self.agentId = agentId
        self.appId = appId
        self.sessionId = sessionId


    def _namespace_to_gateway_ids(self, namespace: tuple[str, ...]) -> Dict[str, str]:
        """
        Map LangGraph namespace to gateway IDs with class-level config fallback.

        Examples:
        ("users") -> {"appId": "users"}  # Single level = appId
        ("users", "profiles") -> {"appId": "users", "userId": "profiles"}
        """
        gateway_ids = {}

        # Start with class-level configuration as base
        if self.appId:
            gateway_ids["appId"] = self.appId
        if self.userId:
            gateway_ids["userId"] = self.userId
        if self.agentId:
            gateway_ids["agentId"] = self.agentId
        if self.sessionId:
            gateway_ids["sessionId"] = self.sessionId

        # Override with namespace values
        if len(namespace) >= 1:
            gateway_ids["appId"] = namespace[0]
        if len(namespace) >= 2:
            gateway_ids["userId"] = namespace[1]

        return gateway_ids

    def _is_memory_id(self, key: str) -> bool:
        """Check if key is a valid memory ID (UUID format)."""
        uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
        return bool(uuid_pattern.match(key))

    def _memory_data_to_item(self, memory_data: Dict[str, Any], namespace: tuple[str, ...], key: str) -> Item:
        """Convert gateway memory data to LangGraph Item."""
        memory_content = memory_data.get("content", "")
        try:
            value = json.loads(memory_content) if memory_content else {}
        except json.JSONDecodeError:
            value = {"text": memory_content}

        created_at = datetime.fromisoformat(memory_data.get("createdAt", datetime.now().isoformat()))
        updated_at = datetime.fromisoformat(memory_data.get("updatedAt", datetime.now().isoformat()))

        return Item(
            value=value,
            key=key,
            namespace=namespace,
            created_at=created_at,
            updated_at=updated_at,
        )

    def _memory_data_to_search_item(self, memory_data: Dict[str, Any], op: SearchOp = None) -> SearchItem:
        """Convert gateway memory data to LangGraph SearchItem."""
        metadata = memory_data.get("metadata", {})
        namespace = tuple(metadata.get("langgraph_namespace", []))
        key = metadata.get("langgraph_key", memory_data.get("id", "unknown"))

        # Parse memory content
        memory_content = memory_data.get("content", "")
        try:
            value = json.loads(memory_content) if memory_content else {}
        except json.JSONDecodeError:
            value = {"text": memory_content}

        created_at = datetime.fromisoformat(memory_data.get("createdAt", datetime.now().isoformat()))
        updated_at = datetime.fromisoformat(memory_data.get("updatedAt", datetime.now().isoformat()))

        return SearchItem(
            namespace=namespace or op.namespace_prefix,
            key=key,
            value=value,
            created_at=created_at,
            updated_at=updated_at,
            score=memory_data.get("importance", 0.5)
        )

    def _response_to_item(self, response: Dict[str, Any], namespace: tuple[str, ...], key: str) -> Item:
        """Convert gateway response to LangGraph Item."""
        if response and "data" in response:
            memory_data = response["data"]
            return self._memory_data_to_item(memory_data, namespace, key)
        return None

    def batch(self, ops: Iterable[Op]) -> list[Result]:
        """Execute multiple operations synchronously in a single batch."""
        results = []

        for op in ops:
            try:
                if isinstance(op, GetOp):
                    result = self._handle_get(op)
                elif isinstance(op, PutOp):
                    result = self._handle_put(op)
                elif isinstance(op, SearchOp):
                    result = self._handle_search(op)
                elif isinstance(op, ListNamespacesOp):
                    result = self._handle_list_namespaces(op)
                else:
                    raise ValueError(f"Unknown operation type: {type(op)}")

                results.append(result)
            except Exception as e:
                # Log error and return None for failed operations
                logger.error(f"Error in batch operation {type(op).__name__}: {e}")
                results.append(None)

        return results

    async def abatch(self, ops: Iterable[Op]) -> list[Result]:
        """Execute multiple operations asynchronously in a single batch."""
        results = []

        for op in ops:
            try:
                if isinstance(op, GetOp):
                    result = await self._handle_aget(op)
                elif isinstance(op, PutOp):
                    result = await self._handle_aput(op)
                elif isinstance(op, SearchOp):
                    result = await self._handle_asearch(op)
                elif isinstance(op, ListNamespacesOp):
                    result = await self._handle_alist_namespaces(op)
                else:
                    raise ValueError(f"Unknown operation type: {type(op)}")

                results.append(result)
            except Exception as e:
                # Log error and return None for failed operations
                logger.error(f"Error in async batch operation {type(op).__name__}: {e}")
                results.append(None)

        return results

    def _handle_get(self, op: GetOp) -> Item | None:
        """Handle GetOp with namespace-based gateway ID mapping."""
        try:
            # Check if key is a memory ID (UUID format)
            if self._is_memory_id(op.key):
                # Direct memory ID access
                response = self._memory.get(op.key)
                if response and "data" in response:
                    return self._response_to_item(response, op.namespace, op.key)
            else:
                # Search by namespace/key with limit 1
                gateway_ids = self._namespace_to_gateway_ids(op.namespace)

                # Add metadata filter for the specific key
                search_params = {
                    **gateway_ids,
                    "limit": 1,
                    "metadata": {
                        "langgraph_key": op.key,
                        "langgraph_namespace": list(op.namespace),
                        "source": "langgraph_store"
                    }
                }

                response = self._memory.search(**search_params)
                data_fetched = None
                if response and "data" in response and response["data"]:
                    for memory_data in response["data"]:
                        if op.key in memory_data.get("metadata", {}).get("tags", []):
                            if not data_fetched:
                                data_fetched = self._memory_data_to_item(memory_data, op.namespace, op.key)
                            else:
                                data_fetched.value['text'] += ', ' + memory_data.get("content", "")
                    return data_fetched

            return None
        except Exception as e:
            logger.error(f"Error in _handle_get: {e}")
            return None

    async def _handle_aget(self, op: GetOp) -> Item | None:
        """Handle GetOp asynchronously with namespace-based gateway ID mapping."""
        try:
            # Check if key is a memory ID (UUID format)
            if self._is_memory_id(op.key):
                # Direct memory ID access
                response = await self._async_memory.get(op.key)
                if response and "data" in response:
                    return self._response_to_item(response, op.namespace, op.key)
            else:
                # Search by namespace/key with limit 1
                gateway_ids = self._namespace_to_gateway_ids(op.namespace)

                # Add metadata filter for the specific key
                search_params = {
                    **gateway_ids,
                    "limit": 1,
                    "metadata": {
                        "langgraph_key": op.key,
                        "langgraph_namespace": list(op.namespace),
                        "source": "langgraph_store"
                    }
                }

                response = await self._async_memory.search(**search_params)
                data_fetched = None
                if response and "data" in response and response["data"]:
                    for memory_data in response["data"]:
                        if op.key in memory_data.get("metadata", {}).get("tags", []):
                            if not data_fetched:
                                data_fetched = self._memory_data_to_item(memory_data, op.namespace, op.key)
                            else:
                                data_fetched.value['text'] = memory_data.get("content", "")
                    return data_fetched

            return None
        except Exception as e:
            logger.error(f"Error in _handle_aget: {e}")
            return None

    def _handle_put(self, op: PutOp) -> None:
        """Handle PutOp with namespace-based gateway ID mapping."""
        if op.value is None:
            # Delete operation
            if self._is_memory_id(op.key):
                self._memory.delete(op.key)
            else:
                # Search and delete by namespace/key
                gateway_ids = self._namespace_to_gateway_ids(op.namespace)
                search_params = {
                    **gateway_ids,
                    "limit": 1,
                    "metadata": {
                        "langgraph_key": op.key,
                        "langgraph_namespace": list(op.namespace),
                        "source": "langgraph_store"
                    }
                }
                response = self._memory.search(**search_params)
                if response and "data" in response and response["data"]:
                    memory_id = response["data"][0]["id"]
                    self._memory.delete(memory_id)
        else:
            # Store operation
            gateway_ids = self._namespace_to_gateway_ids(op.namespace)

            # Convert value to message format
            content = json.dumps(op.value, ensure_ascii=False)

            # Store with metadata for LangGraph compatibility
            metadata = {
                "source": "langgraph_store",
                "tags": [op.key],
            }

            add_params = {
                **gateway_ids,
                "messages": [{"role": "user", "content": content}],
                "metadata": metadata
            }

            self._memory.add(**add_params)

    async def _handle_aput(self, op: PutOp) -> None:
        """Handle PutOp asynchronously with namespace-based gateway ID mapping."""
        if op.value is None:
            # Delete operation
            if self._is_memory_id(op.key):
                await self._async_memory.delete(op.key)
            else:
                # Search and delete by namespace/key
                gateway_ids = self._namespace_to_gateway_ids(op.namespace)
                search_params = {
                    **gateway_ids,
                    "limit": 1,
                    "metadata": {
                        "source": "langgraph_store",
                        "tags": [op.key]
                    }
                }
                response = await self._async_memory.search(**search_params)
                if response and "data" in response and response["data"]:
                    memory_id = response["data"][0]["id"]
                    await self._async_memory.delete(memory_id)
        else:
            # Store operation
            gateway_ids = self._namespace_to_gateway_ids(op.namespace)

            # Convert value to message format
            content = json.dumps(op.value, ensure_ascii=False)

            # Store with metadata for LangGraph compatibility
            metadata = {
                "source": "langgraph_store",
                "tags": [op.key],
            }

            add_params = {
                **gateway_ids,
                "messages": [{"role": "user", "content": content}],
                "metadata": metadata
            }

            await self._async_memory.add(**add_params)

    def _handle_search(self, op: SearchOp) -> list[SearchItem]:
        """Handle SearchOp with namespace-based gateway ID mapping and semantic search."""
        try:
            gateway_ids = self._namespace_to_gateway_ids(op.namespace_prefix)

            # Use query for semantic search via keywords
            search_params = {
                **gateway_ids,
                "query": str(op.query),  # Semantic search using query
                "limit": op.limit or 20,
            }

            response = self._memory.search(**search_params)

            if response and "data" in response:
                items = []
                for memory_data in response["data"]:
                    items.append(self._memory_data_to_search_item(memory_data, op))
                    if op.limit and len(items) == op.limit:
                        break
                return items

        except Exception as e:
            logger.error(f"Error in _handle_search: {e}")

        return []

    async def _handle_asearch(self, op: SearchOp) -> list[SearchItem]:
        """Handle SearchOp asynchronously with namespace-based gateway ID mapping and semantic search."""
        try:
            gateway_ids = self._namespace_to_gateway_ids(op.namespace_prefix)

            # Use query for semantic search via keywords
            search_params = {
                **gateway_ids,
                "query": str(op.query),  # Semantic search using query
                "limit": op.limit or 20,
                "page": 1
            }

            response = await self._async_memory.search(**search_params)

            if response and "data" in response:
                items = []
                for memory_data in response["data"]:
                    items.append(self._memory_data_to_search_item(memory_data, op))
                    if op.limit and len(items) == op.limit:
                        break
                return items

        except Exception as e:
            logger.error(f"Error in _handle_asearch: {e}")

        return []



# Convenience function for creating FlotorchStore
def create_flotorch_store(
        api_key: str,
        base_url: str,
        provider_name: str,
        userId: Optional[str] = None,
        agentId: Optional[str] = None,
        appId: Optional[str] = None,
        sessionId: Optional[str] = None
) -> FlotorchStore:
    """
    Create a FlotorchStore instance with the given configuration.

    Args:
        api_key: API key for FlotorchMemory authentication
        base_url: Base URL for FlotorchMemory API
        provider_name: Provider name for FlotorchMemory
        userId: User ID for memory operations (default for gateway)
        agentId: Agent ID for memory operations (default for gateway)
        appId: App ID for memory operations (default for gateway)
        sessionId: Session ID for memory operations (default for gateway)
        index: Index configuration for vector search (currently not used)
        ttl_config: TTL configuration (not supported)

    Returns:
        Configured FlotorchStore instance
    """
    return FlotorchStore(
        api_key=api_key,
        base_url=base_url,
        provider_name=provider_name,
        userId=userId,
        agentId=agentId,
        appId=appId,
        sessionId=sessionId
    )