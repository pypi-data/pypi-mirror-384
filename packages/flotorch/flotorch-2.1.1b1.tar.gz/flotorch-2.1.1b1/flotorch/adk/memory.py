from __future__ import annotations
import os
from google.genai import types
from google.genai.types import Content, Part
from typing import Any, Dict, List, Optional
from google.adk.memory import BaseMemoryService
from google.adk.memory.base_memory_service import SearchMemoryResponse
from google.adk.memory.memory_entry import MemoryEntry
from google.adk.sessions import Session
from typing_extensions import override
from dotenv import load_dotenv
from flotorch.sdk.memory import FlotorchMemory, FlotorchVectorStore
from flotorch.sdk.utils.logging_utils import log_object_creation, log_error

# Load environment variables from .env files
load_dotenv()

class FlotorchADKVectorMemoryService(BaseMemoryService):
    """
    A memory service that combines traditional memory search with vector search using FlotorchVectorStore.
    """

    def __init__(
            self,
            api_key: str,
            base_url: str,
            vectorstore_id: Optional[str] = None,
    ):
        self.vectorstore_id = vectorstore_id
        self.vector_store = None
        if vectorstore_id:
            self.vector_store = FlotorchVectorStore(
                base_url=base_url,
                api_key=api_key,
                vectorstore_id=vectorstore_id
            )

        log_object_creation(
            "FlotorchVectorMemoryService",
            vectorstore_id=vectorstore_id
        )

    @override
    async def search_memory(
            self,
            query: str,
            knn: Optional[int] = None,
            **kwargs
    ) -> SearchMemoryResponse:
        """
        Enhanced search that use vector search.
        """
        try:
            if self.vector_store:
                vector_results = await self._search_vector_store(query, knn)
            memory_entries = []

            for memory in vector_results:
                memory_entry = MemoryEntry(
                    content=types.Content(
                        parts=[types.Part(text=str(memory))],
                        role='user',
                    ),
                    author='user'
                )
                memory_entries.append(memory_entry)
            return SearchMemoryResponse(memories=memory_entries)


        except Exception as e:
            log_error("FlotorchVectorMemoryService.search_memory", e)
            return SearchMemoryResponse(memories=[])


    async def _search_vector_store(self, query: str, knn: Optional[int] = None) -> List[Dict[str, Any]]:
        """Perform vector search and format results."""
        if not self.vector_store:
            return []

        try:
            search_params = {
                "query": query
            }
            if knn:
                search_params["max_number_of_result"] = knn

            vector_response = self.vector_store.search(**search_params)
            formatted_results = []
            if isinstance(vector_response, dict) and "data" in vector_response:
                for result in vector_response["data"]:
                    formatted_results.append(result.get("content", {})[0].get("text", ""))

            return formatted_results

        except Exception as e:
            log_error("_search_vector_store", e)
            return []

    @override
    async def add_session_to_memory(self, session: Session) -> None:
        pass


class FlotorchMemoryService(BaseMemoryService):
    """
    A memory service that uses FlotorchMemory SDK to store and retrieve memory via Flotorch Gateway.
    Args:
        name: The memory provider name (e.g., 'mem0')
        base_url: Optional base URL for the Flotorch Gateway. Falls back to FLOTORCH_BASE_URL env var.
        api_key: Optional API key for authentication. Falls back to FLOTORCH_API_KEY env var.
    """
    def __init__(self, name: str, base_url: Optional[str] = None, api_key: Optional[str] = None):
        self._name = name
        self._base_url = base_url or os.getenv('FLOTORCH_BASE_URL')
        self._api_key = api_key or os.getenv('FLOTORCH_API_KEY')
        if not self._base_url:
            raise ValueError("FLOTORCH_BASE_URL environment variable or base_url parameter is required")
        if not self._api_key:
            raise ValueError("FLOTORCH_API_KEY environment variable or api_key parameter is required")
        self._memory = FlotorchMemory(
            api_key=self._api_key,
            base_url=self._base_url,
            provider_name=self._name
        )
        
        # Log object creation
        log_object_creation("FlotorchMemoryService", provider_name=name, base_url=self._base_url)

    def _extract_role(self, event) -> str:
        """Extract role from ADK event objects."""
        try:
            # Try to get role from content first (ADK pattern)
            if hasattr(event, 'content') and event.content is not None:
                if hasattr(event.content, 'role') and event.content.role:
                    role = event.content.role
                    return self._map_role_to_flotorch(role)
            
            # Try to get role from event directly
            if hasattr(event, 'role') and event.role:
                role = event.role
                return self._map_role_to_flotorch(role)
            
            # Try to get author as role
            if hasattr(event, 'author') and event.author:
                author = event.author
                return self._map_role_to_flotorch(author)
            
            # Fallback
            return 'user'
            
        except Exception as e:
            return 'user'
        
    def _map_role_to_flotorch(self, role: str) -> str:
        """Map ADK roles to Flotorch Gateway expected roles."""
        role_lower = role.lower()
        
        # Map common role variations to Flotorch expected roles
        role_mapping = {
            'model': 'assistant',
            'assistant': 'assistant',
            'user': 'user',
            'system': 'system',
            'tool': 'tool',
            'developer': 'developer',
            'agent': 'assistant',
            'bot': 'assistant',
            'ai': 'assistant',
            'human': 'user',
            'person': 'user'
        }
        
        return role_mapping.get(role_lower, 'user')
    
    def _get_timestamp(self, session) -> str:
        """Get timestamp for the session, with fallback to current time in ISO8601 format."""
        try:
            # Try to get timestamp from session
            created_at = getattr(session, 'created_at', None)
            if created_at is not None:
                # Ensure it's in ISO8601 format with timezone info
                if created_at.tzinfo is None:
                    # If no timezone info, assume UTC
                    from datetime import timezone
                    created_at = created_at.replace(tzinfo=timezone.utc)
                return created_at.isoformat()
            
            # Fallback to current timestamp in UTC with timezone info
            from datetime import datetime, timezone
            return datetime.now(timezone.utc).isoformat()
            
        except Exception as e:
            # Final fallback with timezone info
            from datetime import datetime, timezone
            return datetime.now(timezone.utc).isoformat()
        
    def _extract_content_text(self, event) -> str:
        """Extract text content from ADK event objects."""
        try:
            # Handle Content objects (ADK pattern)
            if hasattr(event, 'content') and event.content is not None:
                content_obj = event.content
                
                if hasattr(content_obj, 'parts') and content_obj.parts:
                    # Extract text from all parts
                    text_parts = []
                    for part in content_obj.parts:
                        if hasattr(part, 'text') and part.text:
                            text_parts.append(part.text)
                    return ' '.join(text_parts)
                elif hasattr(content_obj, 'text') and content_obj.text:
                    return content_obj.text
            
            # Handle direct text attributes
            if hasattr(event, 'text') and event.text:
                return event.text
            
            # Handle direct content attributes
            if hasattr(event, 'content') and isinstance(event.content, str):
                return event.content
            
            # If we can't extract text, return a safe string representation
            return "Content not available"
            
        except Exception as e:
            return "Content extraction error"

    @override
    async def add_session_to_memory(self, session: Session) -> None:
        """Add a session to Flotorch memory using FlotorchMemory utils."""

        try:
            events = getattr(session, 'events', None)
            if events is None:
                events = getattr(session, 'messages', [])

            messages = [
                {
                    'role': self._extract_role(event),
                    'content': self._extract_content_text(event)
                }
                for event in events
            ]

            metadata = {
                'source': 'adk_session',
                'importance': 0.5,
                'category': 'conversation',
                'tags': ['adk', 'session']
            }

            self._memory.add(
                messages=messages,
                userId=getattr(session, 'user_id', 'unknown'),
                appId=getattr(session, 'app_name', 'unknown'),
                metadata=metadata,
                timestamp=self._get_timestamp(session),
            )


        except Exception as e:
            # Log the error but don't return anything (method should return None)
            log_error("FlotorchMemoryService.add_session_to_memory", e)

    @override
    async def search_memory(self, *, app_name: str, user_id: str, query: str) -> SearchMemoryResponse:
        """Search Flotorch memory for relevant sessions using the FlotorchMemory SDK."""
        try:
            # Use the search method from FlotorchMemory
            result = self._memory.search(
                userId=user_id,
                appId=app_name,
                sessionId=None,
                categories=None,
                query=query,
                page=1,
                limit=10
            )
            raw_memories = result.get('data', [])
            
            # If no memories found, return empty response
            if not raw_memories:
                return SearchMemoryResponse()

            memory_entries = []

            for memory in raw_memories:
                # Align with CrewAI retrieval: extract text robustly
                memory_text = (
                    memory.get('memory')
                    or memory.get('content')
                    or memory.get('text')
                    or (
                        memory.get('messages')[0].get('content')
                        if isinstance(memory.get('messages'), list)
                        and memory.get('messages')
                        and isinstance(memory.get('messages')[0], dict)
                        else None
                    )
                )
                if memory_text:
                    ts = memory.get('timestamp') or memory.get('createdAt') or memory.get('updatedAt')
                    memory_entry = MemoryEntry(
                        content=types.Content(
                            parts=[types.Part(text=str(memory_text))],
                            role='user',
                        ),
                        author='user',
                        timestamp=ts
                    )
                    memory_entries.append(memory_entry)

            return SearchMemoryResponse(memories=memory_entries)
        except Exception as e:
            # Log the error and return empty response instead of raising
            log_error("FlotorchMemoryService.search_memory", e)
            return SearchMemoryResponse(memories=[]) 