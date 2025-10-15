"""Flotorch AutoGen session management for chat completion contexts."""
import os
import uuid
from typing import List, Dict, Optional, Any, Mapping
from pydantic import Field, BaseModel
from typing_extensions import Self
import asyncio

from autogen_core.model_context import ChatCompletionContext
from autogen_core import FunctionCall, Component
from autogen_core.models import (
    LLMMessage,
    UserMessage,
    SystemMessage,
    AssistantMessage,
    FunctionExecutionResult,
    FunctionExecutionResultMessage,
)

from flotorch.sdk.session import FlotorchAsyncSession
from flotorch.sdk.utils.logging_utils import log_error, log_object_creation

class FlotorchAutogenSessionConfig(BaseModel):
    """Configuration model for FlotorchAutogenSession, used for serialization within Autogen."""

    uid: Optional[str] = None
    recent_messages_max: Optional[int] = 50
    api_key: Optional[str] = Field(None, exclude=True)
    base_url: Optional[str] = None
    provider: str = "flotorch.autogen.sessions.FlotorchAutogenSession"


class FlotorchAutogenSession(
    ChatCompletionContext, Component[FlotorchAutogenSessionConfig]
):
    """
    Flotorch Session using ChatCompletionContext. This has to be created within the FlotorchAutogenAgent.
    """

    component_config_schema = FlotorchAutogenSessionConfig

    def __init__(
        self,
        uid: Optional[str] = None,
        recent_messages_max: Optional[int] = 50,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """
        Initializes the FlotorchAsyncSession with session ID only.
        """
        self.uid = uid
        self.api_key = api_key or os.environ.get("FLOTORCH_API_KEY")
        self.base_url = base_url or os.environ.get("FLOTORCH_BASE_URL")
        self.recent_messages_max = recent_messages_max

        if not self.api_key:
            raise ValueError(
                "Flotorch API key is required. Provide it or set FLOTORCH_API_KEY."
            )
        if not self.base_url:
            raise ValueError(
                "Flotorch base URL is required. Provide it or set FLOTORCH_BASE_URL."
            )

        self.flotorch_session = FlotorchAsyncSession(
            api_key=self.api_key, base_url=self.base_url
        )
        self._messages_cache: List[LLMMessage] = []
        self._initialized = False

        log_object_creation("FlotorchAutogenSession", base_url=base_url)


    async def _initialize(self) -> None:
        """
        This should be called by the agent to initialize the session. 
        It will also load the messages from a session if session id is provided.
        """
        if self._initialized:
            return

        if self.uid:
            await self._load_from_backend()
        else:
            # Create new session with default app_name and user_id
            session_data = await self.flotorch_session.create(
                app_name="autogen_session_app",
                user_id="autogen_user"
            )
            self.uid = session_data.get("uid")
            if not self.uid:
                raise RuntimeError("Failed to create a new Flotorch session.")

        self._initialized = True

    async def _load_from_backend(self) -> None:
        """Fetches the full event history from the Flotorch Session and populates the local message cache."""
        if not self.uid:
            raise RuntimeError("Cannot load from backend without a session UID.")

        try:
            session_data = await self.flotorch_session.get(uid=self.uid)
            events = self.flotorch_session.extract_events(session_data)
        except Exception as e:
            log_error("FlotorchAutogenSession._load_from_backend", e)
            raise
        messages = [
            msg
            for event in sorted(events, key=lambda e: e.get("timestamp", 0))
            if (msg := self._flotorch_to_autogen_message(event))
        ]
        self._messages_cache = messages

    async def add_message(self, message: LLMMessage) -> None:
        """Adds a message to the context, persisting it to the Flotorch Session."""
        if not self._initialized:
            await self._initialize()
            
        if not self.uid:
            raise RuntimeError(
                "Session not initialized. The agent must initialize the session first."
            )

        author, content_payload = self._autogen_to_flotorch_event(message)
        if not author:
            return

        try:
            await self.flotorch_session.add_event(
                uid=self.uid,
                invocation_id=str(uuid.uuid4()),
                author=author,
                content=content_payload,
            )
        except Exception as e:
            log_error("FlotorchAutogenSession.add_message.add_event", e)
            raise
        self._messages_cache.append(message)

    async def get_messages(self) -> List[LLMMessage]:
        """Retrieves the last few messages for the current session from the local cache."""
        if not self._initialized:
            await self._initialize()
            
        if not self.uid:
            raise RuntimeError(
                "Session not initialized. The agent must initialize the session first."
            )

        return self._messages_cache[-self.recent_messages_max :]

    @staticmethod
    def _autogen_to_flotorch_event(
        message: LLMMessage,
    ) -> tuple[Optional[str], Dict[str, Any]]:
        """Converts an AutoGen LLMMessage to a Flotorch event payload."""
        author, content_payload = None, {}
        if isinstance(message, UserMessage) and isinstance(message.content, str):
            author, content_payload = "user", {"message": message.content}
        elif isinstance(message, SystemMessage) and isinstance(message.content, str):
            author, content_payload = "system", {"message": message.content}
        elif isinstance(message, AssistantMessage):
            author = "assistant"
            if isinstance(message.content, str):
                content_payload = {"message": message.content}
            elif isinstance(message.content, list):
                content_payload = {
                    "tool_calls": [
                        {
                            "id": call.id,
                            "function": {
                                "name": call.name,
                                "arguments": call.arguments,
                            },
                        }
                        for call in message.content
                        if isinstance(call, FunctionCall)
                    ]
                }
        elif isinstance(message, FunctionExecutionResultMessage):
            author = "tool"
            content_payload = {
                "tool_outputs": [
                    {
                        "tool_call_id": res.call_id,
                        "name": res.name,
                        "output": res.content,
                        "is_error": res.is_error,
                    }
                    for res in message.content
                ]
            }

        return author.lower() if author else None, content_payload

    @staticmethod
    def _flotorch_to_autogen_message(event: Dict[str, Any]) -> Optional[LLMMessage]:
        """Converts a Flotorch event dictionary to an AutoGen LLMMessage."""
        author, content_data = event.get("author"), event.get("content", {})
        if not author:
            return None

        if author == "user":
            return UserMessage(content=content_data.get("message", ""), source=author)
        elif author == "system":
            return SystemMessage(content=content_data.get("message", ""), source=author)
        elif author == "assistant":
            if "tool_calls" in content_data:
                calls = [
                    FunctionCall(
                        id=tc["id"],
                        name=tc["function"]["name"],
                        arguments=tc["function"]["arguments"],
                    )
                    for tc in content_data.get("tool_calls", [])
                ]
                return AssistantMessage(content=calls, source=author)
            return AssistantMessage(
                content=content_data.get("message", ""), source=author
            )
        elif author == "tool":
            results = [
                FunctionExecutionResult(
                    call_id=to["tool_call_id"],
                    name=to["name"],
                    content=to["output"],
                    is_error=to.get("is_error", False),
                )
                for to in content_data.get("tool_outputs", [])
            ]
            return FunctionExecutionResultMessage(content=results, source=author)
        return None

    async def clear(self) -> None:
        """Deletes the session from the backend and resets the local state."""
        if self.uid:
            await self.flotorch_session.delete(uid=self.uid)
        self.uid = None
        self._messages_cache = []

    async def save_state(self) -> Mapping[str, Any]:
        """Saves the essential state required to reconstruct this session."""
        return self._to_config().model_dump()

    async def load_state(self, state: Mapping[str, Any]) -> None:
        """Loads state from a dictionary, pointing this instance to a specific Flotorch session."""
        config = FlotorchAutogenSessionConfig.model_validate(state)
        self.uid = config.uid
        self.base_url = config.base_url
        self._messages_cache = []

    def _to_config(self) -> FlotorchAutogenSessionConfig:
        """Creates a serializable config object from the instance's state."""
        return FlotorchAutogenSessionConfig(
            uid=self.uid,
            base_url=self.base_url,
        )

    @classmethod
    def _from_config(cls, config: FlotorchAutogenSessionConfig) -> Self:
        """Creates an instance from a config object."""
        return cls(
            uid=config.uid,
            base_url=config.base_url,
        )

    async def _ensure_session(self) -> str:
        """
        Ensure that a valid Flotorch session exists.
        If an existing session is available and still valid, reuse it.
        Otherwise, create a new session via the Flotorch API.

        Returns:
            str: The session ID of the active session.
        """
        if self.uid:
            try:
                # Try to validate existing session
                return self.uid
            except Exception:
                self.uid = None

        # Create new session
        try:
            session_data = await self.flotorch_session.create(
                app_name="autogen_session_app",
                user_id="autogen_user"
            )
        except Exception as e:
            log_error("FlotorchAutogenSession._ensure_session.create", e)
            raise
        self.uid = session_data.get("uid")
        if not self.uid:
            self.uid = str(uuid.uuid4())
        return self.uid