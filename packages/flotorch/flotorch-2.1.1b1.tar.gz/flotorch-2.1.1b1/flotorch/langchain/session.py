"""LangChain-compatible session memory backed by Flotorch Sessions.

This module implements a minimal `BaseMemory` that persists user/assistant
turns as Flotorch session events and exposes a single history string under
`memory_key` for prompt formatting.
"""

from typing import Any, Dict, List, Optional
import uuid

from langchain.schema import BaseMemory
from flotorch.sdk.session import FlotorchSession
from flotorch.sdk.utils.logging_utils import (
    log_error,
    log_object_creation,
    log_warning,
)


class FlotorchLangChainSession(BaseMemory):
    """A LangChain `BaseMemory` that stores history in Flotorch Sessions.

    - Persists user/assistant turns as Flotorch session events.
    - Loads previous turns and exposes them as a single history string
      under `memory_key` for prompt formatting.

    Only `api_key` and `base_url` are required at construction time.
    `app_name` and `user_id` provide sensible defaults for standalone usage.
    """

    memory_key: str = "history"

    # Required
    api_key: Optional[str] = None
    base_url: Optional[str] = None

    # Defaults for session grouping
    app_name: str = "langchain_session_app"
    user_id: str = "langchain_user"

    # Internal client/state
    session_client: Optional[FlotorchSession] = None
    _session_id: Optional[str] = None

    def __init__(
        self,
        api_key: str,
        base_url: str,
        app_name :Optional[str] = "default_app",
        user_id: Optional[str] = "default_user"
        
    ) -> None:
        """Initialize the session memory and underlying Flotorch client.

        Parameters
        - api_key: Flotorch API key for authentication.
        - base_url: Flotorch Gateway base URL.
        - memory_key: Prompt variable name used to inject history.
        """
        memory_key  = "history"
        super().__init__(
            api_key=api_key,
            base_url=base_url,
            user_id=user_id,
            app_id=app_name,
            memory_key= memory_key
        )

        if not api_key:
            log_warning("FlotorchLangChainSession: api_key is not set.")
        if not base_url:
            log_warning("FlotorchLangChainSession: base_url is not set.")

        
        self.session_client = FlotorchSession(api_key=api_key, base_url=base_url)

        # Object creation log with relevant context.
        log_object_creation(
            "FlotorchLangChainSession",
            base_url=base_url,
            app_name=self.app_name,
            user_id=self.user_id,
            memory_key=self.memory_key,
        )

    @property
    def memory_variables(self) -> List[str]:
        """Names of variables this memory adds to the prompt.

        Returns a single-element list containing `self.memory_key`.
        """
        return [self.memory_key]

    def load_memory_variables(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Load conversation history from Flotorch session events as a string."""
        try:
            session_id = self._ensure_session()
            events = self.session_client.get_events(session_id) or []
            if not events:
                log_warning(
                    "FlotorchLangChainSession.load_memory_variables: no events found."
                )
            # Ensure chronological order (oldest -> newest) for prompt readability
            events = list(events)[::-1]
            lines = self._extract_text_lines_from_events(events)
            return {self.memory_key: "\n".join(lines)}
        except Exception as e:
            log_error("FlotorchLangChainSession.load_memory_variables", e)
            return {self.memory_key: ""}

    def save_context(self, inputs: Dict[str, Any], outputs: Dict[str, str]) -> None:
        """Persist the latest user input and assistant response to the session."""
        try:
            session_id = self._ensure_session()
            user_text = inputs.get("input") or next(iter(inputs.values()))
            assistant_text = (
                outputs.get("response")
                or outputs.get("output")
                or next(iter(outputs.values()))
            )
            if not user_text:
                log_warning(
                    "FlotorchLangChainSession.save_context: empty user text."
                )
            if not assistant_text:
                log_warning(
                    "FlotorchLangChainSession.save_context: empty assistant text."
                )

            # Save user event
            self.session_client.add_event(
                uid=session_id,
                invocation_id=str(uuid.uuid4()),
                author="user",
                content={"parts": [{"text": str(user_text)}]},
            )

            # Save assistant event (mark turn complete)
            self.session_client.add_event(
                uid=session_id,
                invocation_id=str(uuid.uuid4()),
                author="assistant",
                content={"parts": [{"text": str(assistant_text)}]},
                turn_complete=True,
            )
        except Exception as e:
            # Best-effort; do not break the chain
            log_error("FlotorchLangChainSession.save_context", e)

    def clear(self) -> None:
        """Delete the active session remotely and reset local state."""
        try:
            if self._session_id:
                try:
                    self.session_client.delete(self._session_id)
                finally:
                    self._session_id = None
                log_warning(
                    "FlotorchLangChainSession.clear: session cleared and local state reset."
                )
        except Exception as e:
            # Ignore cleanup errors but log for observability
            log_error("FlotorchLangChainSession.clear", e)
            self._session_id = None

    # --- Internal helpers ---

    def _ensure_session(self) -> str:
        if self._session_id:
            try:
                data = self.session_client.get(uid=self._session_id)
                if data:
                    return self._session_id
            except Exception:
                log_warning(
                    "FlotorchLangChainSession._ensure_session: previous session invalid."
                )
                self._session_id = None

        created = self.session_client.create(
            app_name=self.app_name,
            user_id=self.user_id,
        )
        self._session_id = (
            created.get("uid")
            or created.get("id")
            or str(uuid.uuid4())
        )
        # Note: session creation is transient and frequent; avoid verbose object
        # creation logs here to prevent noise.
        return self._session_id

    @staticmethod
    def _extract_text_lines_from_events(events: List[Dict[str, Any]]) -> List[str]:
        """Extract text lines from events, prefixed with the event author if present.

        Produces lines like "user: hello" and "assistant: hi" when the
        `author` field is available; otherwise, falls back to plain text.
        """
        lines: List[str] = []
        for event in events:
            author = event.get("author")
            prefix = f"{author}: " if isinstance(author, str) and author else ""

            content = event.get("content")
            if isinstance(content, dict):
                parts = content.get("parts")
                if isinstance(parts, list):
                    for part in parts:
                        text = part.get("text") if isinstance(part, dict) else None
                        if isinstance(text, str) and text.strip():
                            lines.append(f"{prefix}{text.strip()}")
                            continue

            text_fallback = event.get("text")
            if isinstance(text_fallback, str) and text_fallback.strip():
                lines.append(f"{prefix}{text_fallback.strip()}")
        return lines


