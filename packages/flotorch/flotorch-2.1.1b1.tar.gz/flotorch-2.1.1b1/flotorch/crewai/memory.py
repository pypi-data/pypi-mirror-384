"""FlotorchMemoryStorage - CrewAI storage implementation using Flotorch Memory Bank."""

import os
import time
from typing import Any, Dict, List, Optional
from crewai.memory.storage.interface import Storage
from flotorch.sdk.memory import FlotorchMemory
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()


class FlotorchMemoryStorage(Storage):
    """CrewAI storage implementation using Flotorch Memory Bank."""

    def __init__(
        self,
        name: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        user_id: Optional[str] = None,
        app_id: Optional[str] = None
    ) -> None:
        """Initialize CrewAI Memory Storage.
        
        Args:
            name: The memory provider name
            base_url: Optional base URL for the CrewAI Gateway
            api_key: Optional API key for authentication
            user_id: Optional user ID (defaults to CREWAI_USER_ID env var)
            app_id: Optional app ID (defaults to CREWAI_APP_ID env var)
        """
        self._name = name
        self._base_url = base_url or os.getenv('FLOTORCH_BASE_URL')
        self._api_key = api_key or os.getenv('FLOTORCH_API_KEY')
        
        # Store user_id and app_id consistently
        self._user_id = user_id or 'default_user'
        self._app_id = app_id or 'default_app'
        
        if not self._base_url:
            raise ValueError("FLOTORCH_BASE_URL environment variable or base_url parameter is required")
        if not self._api_key:
            raise ValueError("FLOTORCH_API_KEY environment variable or api_key parameter is required")

        # Use consistent user_id for collection name
        self._collection_name = f"{self._user_id}_{name}"

        self._memory = FlotorchMemory(
            api_key=self._api_key,
            base_url=self._base_url,
            provider_name=self._name
        )

    def save(self, value: str, metadata: Dict[str, Any]) -> None:
        
        """Save a memory to CrewAI Memory Bank.
        
        Args:
            value: The memory content to save
            metadata: Additional metadata for the memory
        """
        try:
            # Use stored user_id and app_id, with metadata override if provided
            user_id = metadata.get("crewai_user_id", self._user_id)
            app_id = metadata.get("crewai_app_id", self._app_id)

            combined_metadata = {
                'source': 'crewai',
                'collection': self._collection_name,
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'crewai_user_id': user_id,
                'crewai_app_id': app_id
            }

            if metadata:
                combined_metadata.update(metadata)

            # Extract user message and assistant response
            user_message = None
            assistant_response = None
            
            # Extract user message from metadata messages
            if metadata and 'messages' in metadata:
                messages = metadata['messages']
                # Find the last user message
                for msg in reversed(messages):
                    if msg.get('role') == 'user':
                        user_message = msg.get('content', '').strip()
                        break
            
            # Extract final answer from the value (ReAct response)
            if value:
                # Look for "Final Answer:" in the value
                if "Final Answer:" in value:
                    final_answer_start = value.find("Final Answer:")
                    if final_answer_start != -1:
                        final_answer_content = value[final_answer_start + len("Final Answer:"):].strip()
                        # Clean up the final answer
                        assistant_response = final_answer_content.strip()
                else:
                    # If no Final Answer found, use the whole value
                    assistant_response = value.strip()
            
            # Store both user message and assistant response as separate messages
            messages_to_store = []
            
            if user_message and len(user_message.strip()) > 0:
                messages_to_store.append({'role': 'user', 'content': user_message})
            
            if assistant_response and len(assistant_response.strip()) > 0:
                messages_to_store.append({'role': 'assistant', 'content': assistant_response})
            
            # Only store if we have meaningful content
            if messages_to_store:
                self._memory.add(
                    messages=messages_to_store,
                    userId=user_id,
                    appId=app_id,
                    sessionId=None,
                    metadata=combined_metadata,
                    timestamp=datetime.now(timezone.utc).isoformat()
                )

            time.sleep(0.1)

        except Exception as e:
            raise RuntimeError(f"Failed to save memory: {e}")

    def search(self, query: str, limit: int = 30, **kwargs) -> List[Dict[str, Any]]:
        """Search memories in CrewAI Memory Bank.
        
        Args:
            query: Search query
            limit: Maximum number of results to return
        
        Returns:
            List of memory dictionaries with 'memory' and 'metadata' keys
        """
        try:
            # Use stored user_id and app_id, with kwargs override if provided
            user_id =  self._user_id
            app_id =  self._app_id

            result = self._memory.search(
                userId=user_id,
                appId=app_id,
                sessionId=None,
                query=query,
                limit=limit
            )

            memories = result.get('data', [])
            results = []

            for memory in memories:
                content = memory.get('memory') or memory.get('content') or memory.get('text')
                if content:
                    memory_metadata = memory.get('metadata', {})
                    if not isinstance(memory_metadata, dict):
                        memory_metadata = {}

                    memory_metadata.setdefault('suggestions', [])
                    memory_metadata.setdefault('quality', 0.5)

                    results.append({
                        'memory': content,
                        'metadata': memory_metadata
                    })

            # CrewAI ExternalMemory expects each item to have a 'context' key.
            # Return both 'context' and 'memory' for compatibility.
            for item in results:
                if 'content' not in item:
                    item['content'] = item.get('memory')

            return results

        except Exception as e:
            raise RuntimeError(f"Failed to search memory: {e}")

    def reset(self) -> None:
        """Reset all memories for the current user/app combination using stored values."""
        try:
            result = self._memory.search(
                userId=self._user_id,
                appId=self._app_id,
                sessionId=None,
                query="*",
                limit=30 
            )

            memories = result.get('data', [])

            for memory in memories:
                memory_id = memory.get('id')
                if memory_id:
                    self._memory.delete(memory_id)

        except Exception as e:
            raise RuntimeError(f"Failed to reset memory: {e}") 