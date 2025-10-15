from typing import List, Dict, Optional, Any
from flotorch.sdk.utils import memory_utils
from flotorch.sdk.utils.logging_utils import log_object_creation, log_error, log_memory_operation, log_vectorstore_operation


def _extract_memories_count(result: Any) -> int:
    """Best-effort extraction of memory results count from various response shapes.
    Supports dicts with keys like 'memories', 'data', 'results', 'items', and
    object responses with attributes of the same names (e.g., Pydantic models).
    """
    try:
        # Dict-like
        if isinstance(result, dict):
            for key in ("memories", "data", "results", "items"):
                val = result.get(key)
                if isinstance(val, list):
                    return len(val)
                if isinstance(val, dict):
                    inner = val.get("memories")
                    if isinstance(inner, list):
                        return len(inner)
            return 0

        # Object-like (Pydantic/attr)
        for key in ("memories", "data", "results", "items"):
            if hasattr(result, key):
                val = getattr(result, key)
                if isinstance(val, list):
                    return len(val)
                if isinstance(val, dict):
                    inner = val.get("memories")
                    if isinstance(inner, list):
                        return len(inner)
        return 0
    except Exception:
        return 0


class FlotorchMemory:
    def __init__(
        self,
        api_key: str,
        base_url: str,
        provider_name: str,
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.provider_name = provider_name
        
        # Log object creation
        log_object_creation("FlotorchMemory", provider_name=provider_name, base_url=base_url)

    def add(
        self,
        messages: List[Dict[str, str]],
        userId: Optional[str] = None,
        agentId: Optional[str] = None,
        appId: Optional[str] = None,
        sessionId: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[str] = None,
        providerParams: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        try:
            result = memory_utils.add_memory(
                base_url=self.base_url,
                provider_name=self.provider_name,
                api_key=self.api_key,
                messages=messages,
                userId=userId,
                agentId=agentId,
                appId=appId,
                sessionId=sessionId,
                metadata=metadata,
                timestamp=timestamp,
                providerParams=providerParams,
            )
            log_memory_operation("added", self.provider_name, result.get('id') if isinstance(result, dict) else None, messages=messages)
            return result
        except Exception as e:
            log_error("FlotorchMemory.add", e)
            raise

    def get(self, memory_id: str) -> Dict[str, Any]:
        try:
            log_memory_operation("get", self.provider_name, memory_id)
            result = memory_utils.get_memory(
                base_url=self.base_url,
                provider_name=self.provider_name,
                api_key=self.api_key,
                memory_id=memory_id
            )
            log_memory_operation("retrieved", self.provider_name, memory_id)
            return result
        except Exception as e:
            log_error("FlotorchMemory.get", e)
            raise

    def update(self, memory_id: str, content: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            return memory_utils.update_memory(
                base_url=self.base_url,
                provider_name=self.provider_name,
                api_key=self.api_key,
                memory_id=memory_id,
                content=content,
                metadata=metadata,
            )
        except Exception as e:
            log_error("FlotorchMemory.update", e)
            raise

    def delete(self, memory_id: str) -> Dict[str, Any]:
        try:
            return memory_utils.delete_memory(
                base_url=self.base_url,
                provider_name=self.provider_name,
                api_key=self.api_key,
                memory_id=memory_id
            )
        except Exception as e:
            log_error("FlotorchMemory.delete", e)
            raise

    def search(
        self,
        userId: Optional[str] = None,
        agentId: Optional[str] = None,
        appId: Optional[str] = None,
        sessionId: Optional[str] = None,
        createFrom: Optional[str] = None,
        createTo: Optional[str] = None,
        updateFrom: Optional[str] = None,
        updateTo: Optional[str] = None,
        categories: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        page: Optional[int] = 1,
        limit: Optional[int] = 20,
        query: Optional[str] = None,
    ) -> Dict[str, Any]:
        try:
            result = memory_utils.search_memories(
                base_url=self.base_url,
                provider_name=self.provider_name,
                api_key=self.api_key,
                userId=userId,
                agentId=agentId,
                appId=appId,
                sessionId=sessionId,
                createFrom=createFrom,
                createTo=createTo,
                updateFrom=updateFrom,
                updateTo=updateTo,
                categories=categories,
                metadata=metadata,
                page=page,
                limit=limit,
                query=query,
            )
            results_count = _extract_memories_count(result)
            log_memory_operation("searched", self.provider_name, results_count=results_count, query=query)
            return result
        except Exception as e:
            log_error("FlotorchMemory.search", e)
            raise


class FlotorchAsyncMemory:
    def __init__(
        self,
        api_key: str,
        base_url: str,
        provider_name: str,
    ):
        self.api_key = api_key
        self.base_url = base_url
        self.provider_name = provider_name
        
        # Log object creation
        log_object_creation("FlotorchAsyncMemory", provider_name=provider_name, base_url=base_url)

    async def add(
        self,
        messages: List[Dict[str, str]],
        userId: Optional[str] = None,
        agentId: Optional[str] = None,
        appId: Optional[str] = None,
        sessionId: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[str] = None,
        providerParams: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        try:
            return await memory_utils.async_add_memory(
                base_url=self.base_url,
                provider_name=self.provider_name,
                api_key=self.api_key,
                messages=messages,
                userId=userId,
                agentId=agentId,
                appId=appId,
                sessionId=sessionId,
                metadata=metadata,
                timestamp=timestamp,
                providerParams=providerParams,
            )
        except Exception as e:
            log_error("FlotorchAsyncMemory.add", e)
            raise

    async def get(self, memory_id: str) -> Dict[str, Any]:
        try:
            return await memory_utils.async_get_memory(
                base_url=self.base_url,
                provider_name=self.provider_name,
                api_key=self.api_key,
                memory_id=memory_id
            )
        except Exception as e:
            log_error("FlotorchAsyncMemory.get", e)
            raise

    async def update(self, memory_id: str, content: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        try:
            return await memory_utils.async_update_memory(
                base_url=self.base_url,
                provider_name=self.provider_name,
                api_key=self.api_key,
                memory_id=memory_id,
                content=content,
                metadata=metadata,
            )
        except Exception as e:
            log_error("FlotorchAsyncMemory.update", e)
            raise

    async def delete(self, memory_id: str) -> Dict[str, Any]:
        try:
            return await memory_utils.async_delete_memory(
                base_url=self.base_url,
                provider_name=self.provider_name,
                api_key=self.api_key,
                memory_id=memory_id
            )
        except Exception as e:
            log_error("FlotorchAsyncMemory.delete", e)
            raise

    async def search(
        self,
        userId: Optional[str] = None,
        agentId: Optional[str] = None,
        appId: Optional[str] = None,
        sessionId: Optional[str] = None,
        createFrom: Optional[str] = None,
        createTo: Optional[str] = None,
        updateFrom: Optional[str] = None,
        updateTo: Optional[str] = None,
        categories: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        page: Optional[int] = 1,
        limit: Optional[int] = 20,
        query: Optional[str] = None,
    ) -> Dict[str, Any]:
        try:
            result = await memory_utils.async_search_memories(
                base_url=self.base_url,
                provider_name=self.provider_name,
                api_key=self.api_key,
                userId=userId,
                agentId=agentId,
                appId=appId,
                sessionId=sessionId,
                createFrom=createFrom,
                createTo=createTo,
                updateFrom=updateFrom,
                updateTo=updateTo,
                categories=categories,
                metadata=metadata,
                page=page,
                limit=limit,
                query=query,
            )
            results_count = _extract_memories_count(result)
            log_memory_operation("searched", self.provider_name, results_count=results_count, query=query)
            return result
        except Exception as e:
            log_error("FlotorchAsyncMemory.search", e)
            raise

class FlotorchAsyncVectorStore:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        vectorstore_id: str,
    ):
        if not api_key or not api_key.strip():
            raise ValueError("API key cannot be empty.")
        if not vectorstore_id or not vectorstore_id.strip():
            raise ValueError("Vector store ID cannot be empty.")

        self.base_url = base_url
        self.api_key = api_key
        self.vectorstore_id = vectorstore_id
        
        # Log object creation
        log_object_creation("FlotorchAsyncVectorStore", vectorstore_id=vectorstore_id, base_url=base_url)

    async def search(
        self,
        query: str,
        max_number_of_result: Optional[int] = None,
        ranker: Optional[str] = None,
        score_threshold: Optional[float] = None,
        rewrite_query: Optional[bool] = None
        ) -> Dict[str, Any]:

        if not query or not query.strip():
            raise ValueError("Search query cannot be empty.")

        try:
            override_params = {
                "max_number_of_result": max_number_of_result,
                "ranker": ranker,
                "score_threshold": score_threshold,
                "rewrite_query": rewrite_query
            }
            final_params = {k: v for k, v in override_params.items() if v is not None}

            result = await memory_utils.async_search_vectorstore(
                base_url=self.base_url,
                api_key=self.api_key,
                query=query,
                vectorstore_id=self.vectorstore_id,
                **final_params
            )
            results_count = len(result.get('data', [])) if isinstance(result, dict) else 0
            log_vectorstore_operation("searched", self.vectorstore_id, results_count=results_count, query=query)
            return result
        except Exception as e:
            log_error("FlotorchAsyncVectorStore.search", e)
            raise

class FlotorchVectorStore:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        vectorstore_id: str,
    ):
        if not api_key or not api_key.strip():
            raise ValueError("API key cannot be empty.")
        if not vectorstore_id or not vectorstore_id.strip():
            raise ValueError("Vector store ID cannot be empty.")

        self.base_url = base_url
        self.api_key = api_key
        self.vectorstore_id = vectorstore_id
        
        # Log object creation
        log_object_creation("FlotorchVectorStore", vectorstore_id=vectorstore_id, base_url=base_url)

    def search(
        self,
        query: str,
        max_number_of_result: Optional[int] = None,
        ranker: Optional[str] = None,
        score_threshold: Optional[float] = None,
        rewrite_query: Optional[bool] = None
        ) -> Dict[str, Any]:

        if not query or not query.strip():
            raise ValueError("Search query cannot be empty.")

        try:
            override_params = {
                "max_number_of_result": max_number_of_result,
                "ranker": ranker,
                "score_threshold": score_threshold,
                "rewrite_query": rewrite_query
            }
            final_params = {k: v for k, v in override_params.items() if v is not None}

            result = memory_utils.search_vectorstore(
                base_url=self.base_url,
                api_key=self.api_key,
                query=query,
                vectorstore_id=self.vectorstore_id,
                **final_params
            )
            results_count = len(result.get('data', [])) if isinstance(result, dict) else 0
            log_vectorstore_operation("searched", self.vectorstore_id, results_count=results_count, query=query)
            return result
        except Exception as e:
            log_error("FlotorchVectorStore.search", e)
            raise