from typing import List, Dict, Optional, Any
from flotorch.sdk.utils import session_utils
from flotorch.sdk.utils.logging_utils import log_object_creation, log_error, log_session_operation


class FlotorchSession:
    def __init__(
        self,
        api_key: str,
        base_url: str,
    ):
        if not api_key or not api_key.strip():
            raise ValueError("API key cannot be empty.")
        
        self.api_key = api_key
        self.base_url = base_url
        
        # Log object creation
        log_object_creation("FlotorchSession", base_url=base_url)

    def create(
        self,
        app_name: str,
        user_id: str,
        uid: Optional[str] = None,
        state: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if not app_name or not app_name.strip():
            raise ValueError("App name cannot be empty.")
        if not user_id or not user_id.strip():
            raise ValueError("User ID cannot be empty.")
        
        try:
            log_session_operation("create", uid, app_name=app_name, user_id=user_id)
            result = session_utils.create_session(
                base_url=self.base_url,
                api_key=self.api_key,
                app_name=app_name,
                user_id=user_id,
                uid=uid,
                state=state,
            )
            log_session_operation("created", result.get('uid') if isinstance(result, dict) else None, app_name=app_name, user_id=user_id)
            return result
        except Exception as e:
            log_error("FlotorchSession.create", e)
            raise

    def get(
        self,
        uid: str,
        after_timestamp: Optional[int] = None,
        num_recent_events: Optional[int] = None,
    ) -> Dict[str, Any]:
        if not uid or not uid.strip():
            raise ValueError("Session UID cannot be empty.")
        
        try:
            log_session_operation("get", uid, after_timestamp=after_timestamp, num_recent_events=num_recent_events)
            result = session_utils.get_session(
                base_url=self.base_url,
                api_key=self.api_key,
                uid=uid,
                after_timestamp=after_timestamp,
                num_recent_events=num_recent_events,
            )
            events_count = len(result.get('events', [])) if isinstance(result, dict) else 0
            log_session_operation("retrieved", uid, events_count=events_count)
            return result
        except Exception as e:
            log_error("FlotorchSession.get", e)
            raise

    def list(
        self,
        app_name: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        try:
            log_session_operation("list", None, app_name=app_name, user_id=user_id)
            result = session_utils.list_sessions(
                base_url=self.base_url,
                api_key=self.api_key,
                app_name=app_name,
                user_id=user_id,
            )
            log_session_operation("listed", None, sessions_count=len(result))
            return result
        except Exception as e:
            log_error("FlotorchSession.list", e)
            raise

    def delete(self, uid: str) -> Dict[str, Any]:
        if not uid or not uid.strip():
            raise ValueError("Session UID cannot be empty.")
        
        try:
            log_session_operation("delete", uid)
            result = session_utils.delete_session(
                base_url=self.base_url,
                api_key=self.api_key,
                uid=uid,
            )
            log_session_operation("deleted", uid)
            return result
        except Exception as e:
            log_error("FlotorchSession.delete", e)
            raise

    def get_events(self, uid: str) -> List[Dict[str, Any]]:
        if not uid or not uid.strip():
            raise ValueError("Session UID cannot be empty.")
        
        return session_utils.get_session_events(
            base_url=self.base_url,
            api_key=self.api_key,
            uid=uid,
        )

    def add_event(
        self,
        uid: str,
        invocation_id: str,
        author: str,
        uid_event: Optional[str] = None,
        branch: Optional[str] = None,
        content: Optional[Dict[str, Any]] = None,
        actions: Optional[Dict[str, Any]] = None,
        long_running_tool_ids_json: Optional[str] = None,
        grounding_metadata: Optional[Dict[str, Any]] = None,
        partial: Optional[bool] = False,
        turn_complete: Optional[bool] = False,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        interrupted: Optional[bool] = False,
    ) -> Dict[str, Any]:
        if not uid or not uid.strip():
            raise ValueError("Session UID cannot be empty.")
        if not invocation_id or not invocation_id.strip():
            raise ValueError("Invocation ID cannot be empty.")
        if not author or not author.strip():
            raise ValueError("Author cannot be empty.")
        
        try:
            log_session_operation("add_event", uid, invocation_id=invocation_id, author=author, turn_complete=turn_complete)
            result = session_utils.add_session_event(
                base_url=self.base_url,
                api_key=self.api_key,
                uid=uid,
                invocation_id=invocation_id,
                author=author,
                uid_event=uid_event,
                branch=branch,
                content=content,
                actions=actions,
                long_running_tool_ids_json=long_running_tool_ids_json,
                grounding_metadata=grounding_metadata,
                partial=partial,
                turn_complete=turn_complete,
                error_code=error_code,
                error_message=error_message,
                interrupted=interrupted,
            )
            log_session_operation("event_added", uid, event_uid=result.get('uid') if isinstance(result, dict) else None)
            return result
        except Exception as e:
            log_error("FlotorchSession.add_event", e)
            raise

    # Helper methods for state management
    def create_state_delta(
        self,
        app_state: Optional[Dict[str, Any]] = None,
        user_state: Optional[Dict[str, Any]] = None,
        session_state: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return session_utils.create_state_delta(
            app_state=app_state,
            user_state=user_state,
            session_state=session_state,
        )

    def create_event_actions(
        self,
        state_delta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return session_utils.create_event_actions(state_delta)

    def extract_messages(self, session_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        return session_utils.extract_session_messages(session_data)

    def extract_context(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        return session_utils.extract_session_context(session_data)

    def extract_events(self, session_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        return session_utils.extract_session_events(session_data)


class FlotorchAsyncSession:
    def __init__(
        self,
        api_key: str,
        base_url: str,
    ):
        if not api_key or not api_key.strip():
            raise ValueError("API key cannot be empty.")
        
        self.api_key = api_key
        self.base_url = base_url
        
        # Log object creation
        log_object_creation("FlotorchAsyncSession", base_url=base_url)

    async def create(
        self,
        app_name: str,
        user_id: str,
        uid: Optional[str] = None,
        state: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if not app_name or not app_name.strip():
            raise ValueError("App name cannot be empty.")
        if not user_id or not user_id.strip():
            raise ValueError("User ID cannot be empty.")
        
        try:
            log_session_operation("create", uid, app_name=app_name, user_id=user_id)
            result = await session_utils.async_create_session(
                base_url=self.base_url,
                api_key=self.api_key,
                app_name=app_name,
                user_id=user_id,
                uid=uid,
                state=state,
            )
            log_session_operation("created", result.get('uid') if isinstance(result, dict) else None, app_name=app_name, user_id=user_id)
            return result
        except Exception as e:
            log_error("FlotorchAsyncSession.create", e)
            raise

    async def get(
        self,
        uid: str,
        after_timestamp: Optional[int] = None,
        num_recent_events: Optional[int] = None,
    ) -> Dict[str, Any]:
        if not uid or not uid.strip():
            raise ValueError("Session UID cannot be empty.")
        
        return await session_utils.async_get_session(
            base_url=self.base_url,
            api_key=self.api_key,
            uid=uid,
            after_timestamp=after_timestamp,
            num_recent_events=num_recent_events,
        )

    async def list(
        self,
        app_name: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        return await session_utils.async_list_sessions(
            base_url=self.base_url,
            api_key=self.api_key,
            app_name=app_name,
            user_id=user_id,
        )

    async def delete(self, uid: str) -> Dict[str, Any]:
        if not uid or not uid.strip():
            raise ValueError("Session UID cannot be empty.")
        
        return await session_utils.async_delete_session(
            base_url=self.base_url,
            api_key=self.api_key,
            uid=uid,
        )

    async def get_events(self, uid: str) -> List[Dict[str, Any]]:
        if not uid or not uid.strip():
            raise ValueError("Session UID cannot be empty.")
        
        return await session_utils.async_get_session_events(
            base_url=self.base_url,
            api_key=self.api_key,
            uid=uid,
        )

    async def add_event(
        self,
        uid: str,
        invocation_id: str,
        author: str,
        uid_event: Optional[str] = None,
        branch: Optional[str] = None,
        content: Optional[Dict[str, Any]] = None,
        actions: Optional[Dict[str, Any]] = None,
        long_running_tool_ids_json: Optional[str] = None,
        grounding_metadata: Optional[Dict[str, Any]] = None,
        partial: Optional[bool] = False,
        turn_complete: Optional[bool] = False,
        error_code: Optional[str] = None,
        error_message: Optional[str] = None,
        interrupted: Optional[bool] = False,
    ) -> Dict[str, Any]:
        if not uid or not uid.strip():
            raise ValueError("Session UID cannot be empty.")
        if not invocation_id or not invocation_id.strip():
            raise ValueError("Invocation ID cannot be empty.")
        if not author or not author.strip():
            raise ValueError("Author cannot be empty.")
        
        try:
            log_session_operation("add_event", uid, invocation_id=invocation_id, author=author, turn_complete=turn_complete)
            result = await session_utils.async_add_session_event(
                base_url=self.base_url,
                api_key=self.api_key,
                uid=uid,
                invocation_id=invocation_id,
                author=author,
                uid_event=uid_event,
                branch=branch,
                content=content,
                actions=actions,
                long_running_tool_ids_json=long_running_tool_ids_json,
                grounding_metadata=grounding_metadata,
                partial=partial,
                turn_complete=turn_complete,
                error_code=error_code,
                error_message=error_message,
                interrupted=interrupted,
            )
            log_session_operation("event_added", uid, event_uid=result.get('uid') if isinstance(result, dict) else None)
            return result
        except Exception as e:
            log_error("FlotorchAsyncSession.add_event", e)
            raise

    # Helper methods for state management (these are sync since they don't make API calls)
    def create_state_delta(
        self,
        app_state: Optional[Dict[str, Any]] = None,
        user_state: Optional[Dict[str, Any]] = None,
        session_state: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return session_utils.create_state_delta(
            app_state=app_state,
            user_state=user_state,
            session_state=session_state,
        )

    def create_event_actions(
        self,
        state_delta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return session_utils.create_event_actions(state_delta)

    def extract_messages(self, session_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        return session_utils.extract_session_messages(session_data)

    def extract_context(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        return session_utils.extract_session_context(session_data)

    def extract_events(self, session_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        return session_utils.extract_session_events(session_data)
