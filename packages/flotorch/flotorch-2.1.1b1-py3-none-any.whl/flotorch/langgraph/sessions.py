from __future__ import annotations
from typing import Any, Sequence, Iterator
import uuid

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
    Checkpoint,
    CheckpointMetadata,
    CheckpointTuple,
    ChannelVersions,
)
from flotorch.sdk.utils.http_utils import APIError   
from flotorch.sdk.session import FlotorchSession

class FlotorchLanggraphSession(BaseCheckpointSaver[str]):
    
    def __init__(self, api_key: str, base_url: str, app_name: str, user_id: str, *args, **kwargs):
        """Initialize the FlotorchLanggraphSession with API credentials and configuration."""
        super().__init__(*args, **kwargs)
        self.session = FlotorchSession(api_key, base_url)
        self.app_name = app_name
        self.user_id = user_id
  
    def get_tuple(self, config: RunnableConfig) -> CheckpointTuple | None:
        uid = config["configurable"]["thread_id"]

        try:
            data = self.session.get(uid)
        except APIError as e:
            if e.status_code == 404:
                self.session.create(app_name=self.app_name, user_id=self.user_id, uid=uid)
                return None
            else:
                raise

        if not data:
            return None
            
        events = data.get("events", [])
        if not events:
            return None

        all_messages = self._extract_messages_from_events(events)
        if not all_messages:
            return None

        unique_messages = self._deduplicate_messages(all_messages, uid)
        
        checkpoint = self._create_checkpoint_structure(unique_messages)
        
        metadata = {
            "step": 0,
            "source": "input",
            "parents": {}
        }
        
        return CheckpointTuple(
            config=config,
            checkpoint=checkpoint,
            metadata=metadata,
        )

    async def aget_tuple(self, config: RunnableConfig) -> CheckpointTuple | None:
        """Async version of get_tuple."""
        return self.get_tuple(config)
  
    def put(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> None:

        uid = config["configurable"]["thread_id"]

        messages = checkpoint.get("messages", [])
        if not messages:
            return

        simple_messages = self._convert_messages_to_simple_format(messages)

        safe_checkpoint = {
            "messages": simple_messages,
            "v": checkpoint.get("v", 1),
            "id": checkpoint.get("id", str(uuid.uuid4())),
            "ts": checkpoint.get("ts", ""),
        }

        safe_metadata = self._sanitize_for_json(metadata)
        self.session.add_event(
            uid=uid,
            invocation_id=str(uuid.uuid4()),
            author="system",
            content={
                "metadata": safe_metadata,
                "checkpoint": safe_checkpoint,
                "new_versions": new_versions,
            }
        )

    async def aput(
        self,
        config: RunnableConfig,
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: ChannelVersions,
    ) -> None:
        """Async version of put."""
        self.put(config, checkpoint, metadata, new_versions)

    def put_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        uid = config["configurable"]["thread_id"]
        
        safe_writes = {}
        for channel, value in writes:
            safe_writes[channel] = self._sanitize_for_json(value)
        
        self.session.add_event(
            uid=uid,
            invocation_id=str(uuid.uuid4()),
            author="system",
            content={
                "writes": safe_writes,
                "task_id": task_id,
                "task_path": task_path,
            }
        )

    async def aput_writes(
        self,
        config: RunnableConfig,
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        """Async version of put_writes."""
        self.put_writes(config, writes, task_id, task_path)

    def list(
        self,
        config: RunnableConfig | None,
        *,
        filter: dict[str, Any] | None = None,
        before: RunnableConfig | None = None,
        limit: int | None = None,
    ) -> Iterator[CheckpointTuple]:
        """List all sessions for this app/user."""
        try:
            sessions = self.session.list(app_name=self.app_name, user_id=self.user_id)
            
            count = 0
            for session_data in sessions:
                if limit and count >= limit:
                    break
                    
                session_uid = session_data.get("uid")
                if not session_uid:
                    continue

                session_config = {"configurable": {"thread_id": session_uid}}
                checkpoint = {"v": 1, "id": session_uid, "ts": "", "channel_values": {"messages": []}, "channel_versions": {}}
                metadata = {"step": 0, "source": "list", "parents": {}}
                
                yield CheckpointTuple(
                    config=session_config,
                    checkpoint=checkpoint,
                    metadata=metadata,
                )
                count += 1
                
        except APIError:
            return

    async def alist(
        self,
        config: RunnableConfig | None,
        *,
        filter: dict[str, Any] | None = None,
        before: RunnableConfig | None = None,
        limit: int | None = None,
    ) -> Iterator[CheckpointTuple]:
        """Async version of list - List all sessions for this app/user."""
        return self.list(config, filter=filter, before=before, limit=limit)

    def delete_thread(self, thread_id: str) -> None:
        try:
            self.session.delete(thread_id)
        except APIError as e:
            if e.status_code == 404:
                pass
            else:
                raise
   
    def _extract_messages_from_events(self, events: list) -> list:
        """Extract messages from event data structure."""
        all_messages = []
        
        for event in events:
            content = event.get("content", {})
            
            if "checkpoint" in content:
                messages = content["checkpoint"].get("channel_values", {}).get("messages", [])
                if messages and isinstance(messages, list):
                    all_messages.extend(messages)
                    continue
            
            if "writes" in content:
                messages = content["writes"].get("messages", [])
                if isinstance(messages, list):
                    all_messages.extend(messages)
                elif isinstance(messages, str) and messages.strip():
                    # Handle case where messages is a string (user input)
                    all_messages.append({
                        "type": "human",
                        "content": messages.strip()
                    })
        
        return all_messages

    def _deduplicate_messages(self, messages: list, uid: str = None) -> list:
        """Simple deduplication that handles tool response pairing."""
        if not messages:
            return []
        
        try:
            all_tool_calls = {}
            all_tool_responses = {}
            ai_messages = []
            other_messages = []
            
            for msg in messages:
                if not isinstance(msg, dict):
                    continue
                    
                msg_type = msg.get("type")
                
                if msg_type == "ai" and msg.get("tool_calls"):
                    ai_messages.append(msg) 
                    tool_calls = msg.get("tool_calls", [])
                    if isinstance(tool_calls, list):
                        for tool_call in tool_calls:
                            if isinstance(tool_call, dict):
                                tool_call_id = tool_call.get("id")
                                if tool_call_id and isinstance(tool_call_id, str):
                                    all_tool_calls[tool_call_id] = tool_call
                                    
                elif msg_type == "tool":
                    tool_call_id = msg.get("tool_call_id")
                    if tool_call_id:
                        all_tool_responses[tool_call_id] = msg
                else:
                    other_messages.append(msg)
    
            processed_messages = []
            
            for ai_msg in ai_messages:
                tool_calls = ai_msg.get("tool_calls", [])
                if isinstance(tool_calls, list):
                    all_responses_exist = all(
                        isinstance(tool_call, dict) and 
                        tool_call.get("id") in all_tool_responses
                        for tool_call in tool_calls
                    )
                    
                    if all_responses_exist:
                        processed_messages.append(ai_msg)
                        for tool_call in tool_calls:
                            if isinstance(tool_call, dict):
                                tool_call_id = tool_call.get("id")
                                if tool_call_id in all_tool_responses:
                                    processed_messages.append(all_tool_responses[tool_call_id])
                else:
                    processed_messages.append(ai_msg)
            
            processed_messages.extend(other_messages)
            
            return processed_messages
            
        except Exception as e:
            return messages

    def _create_checkpoint_structure(self, messages: list) -> dict:
        """Create the checkpoint structure for the session."""
        return {
            "v": 4,  
            "id": str(uuid.uuid4()),
            "ts": "",
            "channel_values": {"messages": messages},
            "channel_versions": {"messages": len(messages)},
            "updated_channels": ["messages"],
            "versions_seen": {
                "__input__": {},
                "__start__": {"__start__": 1},
                "call_model": {"branch:to:call_model": 1}
            }
        }

    def _convert_messages_to_simple_format(self, messages: list) -> list:
        """Convert messages to a simple, serializable format."""
        simple_messages = []
        
        for msg in messages:
            if isinstance(msg, dict):
                simple_messages.append(self._sanitize_for_json(msg))
            else:
                simple_messages.append(str(msg))
                
        return simple_messages

    def _sanitize_for_json(self, obj: Any) -> Any:
        """Recursively sanitize objects for JSON serialization."""
        if isinstance(obj, (list, tuple)):
            return [self._sanitize_for_json(item) for item in obj]
        elif isinstance(obj, dict):
            return {key: self._sanitize_for_json(value) for key, value in obj.items()}
        elif hasattr(obj, 'dict'):
            return obj.dict()
        else:
            return str(obj)