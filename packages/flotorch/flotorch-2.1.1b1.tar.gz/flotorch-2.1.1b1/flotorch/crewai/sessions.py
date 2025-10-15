"""FlotorchCrewAISession - CrewAI Short Term storage implementation using Flotorch Session."""


import os
import uuid
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from flotorch.sdk.session import FlotorchSession
from crewai.memory.storage.interface import Storage

# Load environment variables from .env file if present
load_dotenv()


class FlotorchCrewAISession(Storage):
    """
    CrewAI Storage backend using Flotorch Sessions.

    Args:
        base_url (Optional[str]): Base URL for the Flotorch API. Defaults to `FLOTORCH_BASE_URL` from env.
        api_key (Optional[str]): API key for the Flotorch API. Defaults to `FLOTORCH_API_KEY` from env.
        app_name (str): Logical grouping name for the app in Flotorch.
        user_id (str): Identifier for the user whose session is being stored.
        
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        app_name: str = "crewai_session_app",
        user_id: str = "crewai_user",
    ) -> None:
        """
        Initialize the storage backend.

        Args:
            base_url (Optional[str]): Base URL for Flotorch API.
            api_key (Optional[str]): API key for Flotorch API.
            app_name (str): Application name for session grouping.
            user_id (str): ID for the user associated with the session.
            
        """
        self._base_url = base_url
        self._api_key = api_key
        self._session_client = FlotorchSession(api_key=self._api_key, base_url=self._base_url)

        # Logical grouping for session storage
        self._app_name: str = app_name
        self._user_id: str = user_id
        self._session_id: Optional[str] = None

    def _ensure_session(self) -> str:
        """
        Ensure that a valid Flotorch session exists.

        If an existing session is available and still valid, reuse it.
        Otherwise, create a new session via the Flotorch API.

        Returns:
            str: The session ID of the active session.
        """
        if self._session_id:
            try:
                data = self._session_client.get(uid=self._session_id)
                if data:
                    return self._session_id
            except Exception:
                self._session_id = None

        created = self._session_client.create(
            app_name=self._app_name,
            user_id=self._user_id,
        )
        self._session_id = created.get("uid") or created.get("id") or str(uuid.uuid4())
        return self._session_id

    @staticmethod
    def _extract_text_from_event(event: Dict[str, Any]) -> Optional[str]:
        """
        Extract readable text content from a Flotorch session event.

        Args:
            event (Dict[str, Any]): The event object from Flotorch.

        Returns:
            Optional[str]: Extracted text content or None if not found.
        """
        content = event.get("content")
        if isinstance(content, dict):
            parts = content.get("parts")
            if isinstance(parts, list) and parts:
                for part in parts:
                    if isinstance(part, dict) and part.get("text"):
                        text = str(part["text"])
                        if "Final Answer:" in text:
                            start_idx = text.find("Final Answer:") + len("Final Answer:")
                            return text[start_idx:].strip()
                        return text

        if isinstance(event.get("text"), str):
            return event.get("text")
        return None

    def save(self, value: Any, metadata: Dict[str, Any]) -> None:
        """
        Save a value (user message or data) to the current session as an event.

        Args:
            value (Any): The value to be saved, typically text.
            metadata (Dict[str, Any]): Optional metadata associated with the event.

        Raises:
            RuntimeError: If the Flotorch API call to save the event fails.
        """
        session_id = self._ensure_session()
        invocation_id = str(uuid.uuid4())

        try:
            self._session_client.add_event(
                uid=session_id,
                invocation_id=invocation_id,
                author="user",
                content={
                    "parts": [{"text": str(value)}]
                },
                grounding_metadata=metadata if isinstance(metadata, dict) and metadata else None,
            )
        except Exception as e:
            raise RuntimeError(f"Failed to save session event: {e}")

    def search(
        self,
        query: str,
        limit: int,
        score_threshold: float = 0.0,
        **kwargs,
    ) -> List[Dict[str, Any]]:
        """
        Search for events in the current session matching the given query.

        Args:
            query (str): Search query string.
            score_threshold (float): Not used; kept for API compatibility.
            **kwargs: Additional ignored parameters for compatibility.

        Returns:
            List[Dict[str, Any]]: List of matching events with "context" and "metadata".
        """
        if not query or not self._session_id:
            return []

        try:
            events = self._session_client.get_events(self._session_id) or []
        except Exception as e:
            raise RuntimeError(f"Failed to fetch session events: {e}")

        results: List[Dict[str, Any]] = []

        for event in events:
            text = self._extract_text_from_event(event)
            if not text:
                continue
            
            results.append(
                {
                    "content": text,
                    "metadata": event.get("groundingMetadata", {}) if isinstance(event, dict) else {},
                }
            )
           

        return results

    def reset(self) -> None:
        """
        Delete the current session in Flotorch and reset the local session state.

        If deletion fails, the error is ignored (best effort cleanup).
        """
        if not self._session_id:
            return
        try:
            self._session_client.delete(self._session_id)
        except Exception:
            pass
        finally:
            self._session_id = None
