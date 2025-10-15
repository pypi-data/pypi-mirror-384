import copy
import time
import datetime
from typing import Any, Optional
import uuid

from typing_extensions import override

from flotorch.sdk.session import FlotorchSession
from flotorch.sdk.utils.logging_utils import log_object_creation,log_error,log_warning,log_info
from google.adk.events.event import Event
from google.adk.sessions.base_session_service import BaseSessionService
from google.adk.sessions.base_session_service import GetSessionConfig
from google.adk.sessions.base_session_service import ListSessionsResponse
from google.adk.sessions.session import Session
from google.adk.sessions.state import State
from google.adk.events.event_actions import EventActions
from google.genai import types
        


class FlotorchADKSession(BaseSessionService):
    """A Flotorch-based implementation of the session service.

    Uses FlotorchSession from SDK for session management while maintaining
    ADK-compatible interface.
    """

    def __init__(self, api_key: str, base_url: str):
        """Initialize FlotorchADKSession.

        Args:
            api_key: The API key for Flotorch service.
            base_url: The base URL for Flotorch service.
        """
        
        # Flotorch session for session management
        self._flotorch_session = FlotorchSession(
            api_key=api_key,
            base_url=base_url,
        )
        
        # In-memory state management (for app_state and user_state)
        # These are kept in memory as they're not part of FlotorchSession
        self.user_state: dict[str, dict[str, dict[str, Any]]] = {}
        self.app_state: dict[str, dict[str, Any]] = {}
        
        # Log object creation
        log_object_creation("FlotorchADKSession", base_url=base_url)

    @override
    async def create_session(
        self,
        *,
        app_name: str,
        user_id: str,
        state: Optional[dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> Session:
        return self._create_session_impl(
            app_name=app_name,
            user_id=user_id,
            state=state,
            session_id=session_id,
        )

    def create_session_sync(
        self,
        *,
        app_name: str,
        user_id: str,
        state: Optional[dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> Session:
        # logger.warning('Deprecated. Please migrate to the async method.')
        return self._create_session_impl(
            app_name=app_name,
            user_id=user_id,
            state=state,
            session_id=session_id,
        )

    def _create_session_impl(
        self,
        *,
        app_name: str,
        user_id: str,
        state: Optional[dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> Session:
        session_id = (
            session_id.strip()
            if session_id and session_id.strip()
            else str(uuid.uuid4())
        )
        
        # Create session using FlotorchSession
        try:
            session_data = self._flotorch_session.create(
                app_name=app_name,
                user_id=user_id,
                uid=session_id,
                state=state or {},
            )
        except Exception as e:
            log_error("FlotorchADKSession._create_session_impl", e)
            raise
        
        # Create ADK Session object
        session = Session(
            app_name=app_name,
            user_id=user_id,
            id=session_id,
            state=session_data.get('state', {}),
            last_update_time=session_data.get('last_update_time', time.time()),
        )

        copied_session = copy.deepcopy(session)
        return self._merge_state(app_name, user_id, copied_session)

    @override
    async def get_session(
        self,
        *,
        app_name: str,
        user_id: str,
        session_id: str,
        config: Optional[GetSessionConfig] = None,
    ) -> Optional[Session]:
        return self._get_session_impl(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id,
            config=config,
        )

    def get_session_sync(
        self,
        *,
        app_name: str,
        user_id: str,
        session_id: str,
        config: Optional[GetSessionConfig] = None,
    ) -> Optional[Session]:
        # logger.warning('Deprecated. Please migrate to the async method.')
        return self._get_session_impl(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id,
            config=config,
        )

    def _get_session_impl(
        self,
        *,
        app_name: str,
        user_id: str,
        session_id: str,
        config: Optional[GetSessionConfig] = None,
    ) -> Optional[Session]:
        # Get session using FlotorchSession
        try:
            session_data = self._flotorch_session.get(
                uid=session_id,
                after_timestamp=config.after_timestamp if config else None,
                num_recent_events=config.num_recent_events if config else None,
            )
        except Exception as e:
            log_error("FlotorchADKSession._get_session_impl", e)
            return None
        
        if not session_data:
            return None

        # Create ADK Session object
        session = Session(
            app_name=app_name,
            user_id=user_id,
            id=session_id,
            state=session_data.get('state', {}),
            last_update_time=session_data.get('last_update_time', time.time()),
        )
        
        # Add events if available
        events_data = session_data.get('events', [])
        try:
            session.events = [
                self._convert_flotorch_event_to_adk(event_data)
                for event_data in events_data
            ]
        except Exception as e:
            log_error("FlotorchADKSession._get_session_impl", e)
            session.events = []  # Fallback to empty events list

        copied_session = copy.deepcopy(session)
        return self._merge_state(app_name, user_id, copied_session)

    def _merge_state(
        self, app_name: str, user_id: str, copied_session: Session
    ) -> Session:
        # Merge app state
        if app_name in self.app_state:
            for key in self.app_state[app_name].keys():
                copied_session.state[State.APP_PREFIX + key] = self.app_state[app_name][
                    key
                ]

        if (
            app_name not in self.user_state
            or user_id not in self.user_state[app_name]
        ):
            return copied_session

        # Merge session state with user state.
        for key in self.user_state[app_name][user_id].keys():
            copied_session.state[State.USER_PREFIX + key] = self.user_state[app_name][
                user_id
            ][key]
        return copied_session

    @override
    async def list_sessions(
        self, *, app_name: str, user_id: str
    ) -> ListSessionsResponse:
        return self._list_sessions_impl(app_name=app_name, user_id=user_id)

    def list_sessions_sync(
        self, *, app_name: str, user_id: str
    ) -> ListSessionsResponse:
        # logger.warning('Deprecated. Please migrate to the async method.')
        return self._list_sessions_impl(app_name=app_name, user_id=user_id)

    def _list_sessions_impl(
        self, *, app_name: str, user_id: str
    ) -> ListSessionsResponse:
        # List sessions using FlotorchSession
        try:
            sessions_data = self._flotorch_session.list(
                app_name=app_name,
                user_id=user_id,
            )
        except Exception as e:
            log_error("FlotorchADKSession._list_sessions_impl", e)
            return ListSessionsResponse(sessions=[])
        
        sessions_without_events = []
        for session_data in sessions_data:
            session = Session(
                app_name=app_name,
                user_id=user_id,
                id=session_data.get('uid', ''),
                state=session_data.get('state', {}),
                last_update_time=session_data.get('last_update_time', time.time()),
            )
            session.events = []  # Don't include events in list response
            copied_session = copy.deepcopy(session)
            copied_session = self._merge_state(app_name, user_id, copied_session)
            sessions_without_events.append(copied_session)
            
        return ListSessionsResponse(sessions=sessions_without_events)

    @override
    async def delete_session(
        self, *, app_name: str, user_id: str, session_id: str
    ) -> None:
        self._delete_session_impl(
            app_name=app_name, user_id=user_id, session_id=session_id
        )

    def delete_session_sync(
        self, *, app_name: str, user_id: str, session_id: str
    ) -> None:
        # logger.warning('Deprecated. Please migrate to the async method.')
        self._delete_session_impl(
            app_name=app_name, user_id=user_id, session_id=session_id
        )

    def _delete_session_impl(
        self, *, app_name: str, user_id: str, session_id: str
    ) -> None:
        if (
            self._get_session_impl(
                app_name=app_name, user_id=user_id, session_id=session_id
            )
            is None
        ):
            return

        # Delete session using FlotorchSession
        try:
            self._flotorch_session.delete(session_id)
        except Exception as e:
            log_error("FlotorchADKSession._delete_session_impl", e)
            raise

    @override
    async def append_event(self, session: Session, event: Event) -> Event:
        # Update the in-memory session.
        await super().append_event(session=session, event=event)
        session.last_update_time = event.timestamp

        # Update the storage session
        app_name = session.app_name
        user_id = session.user_id
        session_id = session.id



        # Verify session exists
        try:
            session_data = self._flotorch_session.get(uid=session_id)
        except Exception as e:
            log_error("FlotorchADKSession.append_event", e)
            return event
            
        if not session_data:
            log_warning(f'session_id {session_id} not found in FlotorchSession')
            return event

        # Handle state delta updates
        if event.actions and event.actions.state_delta:
            for key in event.actions.state_delta:
                if key.startswith(State.APP_PREFIX):
                    self.app_state.setdefault(app_name, {})[
                        key.removeprefix(State.APP_PREFIX)
                    ] = event.actions.state_delta[key]

                if key.startswith(State.USER_PREFIX):
                    self.user_state.setdefault(app_name, {}).setdefault(user_id, {})[
                        key.removeprefix(State.USER_PREFIX)
                    ] = event.actions.state_delta[key]

        # Add event using FlotorchSession
        try:
            event_data = self._convert_adk_event_to_flotorch(event)
            self._flotorch_session.add_event(
                uid=session_id,
                invocation_id=event.invocation_id,
                author=event.author,
                content=event_data.get('content'),
                actions=event_data.get('actions'),
                **event_data.get('metadata', {})
            )
        except Exception as e:
            log_error("FlotorchADKSession.append_event", e)
            raise

        return event

    def _convert_flotorch_event_to_adk(self, event_data: dict[str, Any]) -> Event:
        """Convert Flotorch event data to ADK Event object."""
       
        
        event_actions = EventActions()
        if event_data.get('actions'):
            event_actions = EventActions(
                state_delta=event_data['actions'].get('state_delta', {}),
                # Add other action fields as needed
            )

        # Handle timestamp conversion
        timestamp = event_data.get('timestamp', time.time())
        if isinstance(timestamp, str):
            try:
                # Parse ISO format timestamp
                dt = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                timestamp = dt.timestamp()
            except (ValueError, AttributeError) as e:
                # Fallback to current time if parsing fails
                log_warning(f"Failed to parse timestamp: {timestamp}", error=str(e))
                timestamp = time.time()

        # Convert content if present
        content = None
        if event_data.get('content'):
            content_dict = event_data['content']
            parts = []
            
            if content_dict.get('parts'):
                for part_dict in content_dict['parts']:
                    # Create part using the correct method
                    if 'text' in part_dict:
                        part = types.Part(text=part_dict['text'])
                    elif 'tool_calls' in part_dict and part_dict['tool_calls']:
                        # Handle tool calls
                        tool_calls = []
                        for tool_call_dict in part_dict['tool_calls']:
                            if 'function' in tool_call_dict:
                                func_call = types.FunctionCall(
                                    name=tool_call_dict['function'].get('name', ''),
                                    args=tool_call_dict['function'].get('arguments', {})
                                )
                                tool_call = types.ToolCall(
                                    id=tool_call_dict.get('id', str(uuid.uuid4())),
                                    function=func_call
                                )
                                tool_calls.append(tool_call)
                        part = types.Part(tool_calls=tool_calls)
                    elif 'tool_call_id' in part_dict and part_dict['tool_call_id']:
                        # Handle function response
                        part = types.Part.from_function_response(
                            name=part_dict.get('function_response', {}).get('name', ''),
                            response=part_dict.get('function_response', {}).get('response', {})
                        )
                    else:
                        # Default text part
                        part = types.Part(text="")
                    
                    parts.append(part)
            
            if parts:
                content = types.Content(role=content_dict.get('role', 'user'), parts=parts)

        event = Event(
            id=event_data.get('uid_event', ''),
            invocation_id=event_data.get('invocation_id', ''),
            author=event_data.get('author', ''),
            actions=event_actions,
            content=content,
            timestamp=timestamp,
            error_code=event_data.get('error_code'),
            error_message=event_data.get('error_message'),
        )
        
        return event

    def _convert_adk_event_to_flotorch(self, event: Event) -> dict[str, Any]:
        """Convert ADK Event object to Flotorch event data."""
        # Simplified approach - just store basic event info like InMemorySession
        event_data = {
            'content': None,
            'actions': {},
            'metadata': {}
        }
        
        # Only store basic content info to avoid serialization issues
        if event.content and event.content.parts:
            content_parts = []
            for part in event.content.parts:
                if hasattr(part, 'text') and part.text:
                    content_parts.append({'text': str(part.text)})
                elif hasattr(part, 'tool_calls') and part.tool_calls:
                    # Store tool call info in a simple format
                    tool_calls = []
                    for tool_call in part.tool_calls:
                        tool_calls.append({
                            'id': str(tool_call.id) if hasattr(tool_call, 'id') and tool_call.id else str(uuid.uuid4()),
                            'name': str(tool_call.function.name) if hasattr(tool_call, 'function') and tool_call.function else '',
                            'arguments': tool_call.function.args if hasattr(tool_call, 'function') and tool_call.function else {}
                        })
                    content_parts.append({'tool_calls': tool_calls})
            
            if content_parts:
                event_data['content'] = {
                    'role': event.content.role,
                    'parts': content_parts
                }
        
        # Store actions
        if event.actions and event.actions.state_delta:
            event_data['actions'] = {
                'state_delta': event.actions.state_delta
            }
        
        # Store basic metadata
        if event.partial is not None:
            event_data['metadata']['partial'] = event.partial
        if event.turn_complete is not None:
            event_data['metadata']['turn_complete'] = event.turn_complete
            
        return event_data
