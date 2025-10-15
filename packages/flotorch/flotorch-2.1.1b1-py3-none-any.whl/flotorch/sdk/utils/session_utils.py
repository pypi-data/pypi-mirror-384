import uuid
from typing import List, Dict, Optional, Any, Union
from flotorch.sdk.utils.http_utils import (
    async_http_post, http_post, http_get, async_http_get, async_http_delete, http_delete
)

# Types
SessionState = Dict[str, Any]
SessionEvent = Dict[str, Any]
JSONType = Union[Dict[str, Any], List[Any]]


def get_session_id():
    return str(uuid.uuid4())


def _build_headers(api_key: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }


def _build_sessions_url(base_url: str) -> str:
    return f"{base_url.rstrip('/')}/v1/sessions"


# ---------------------- LIST SESSIONS ----------------------
async def async_list_sessions(
    base_url: str,
    api_key: str,
    app_name: Optional[str] = None,
    user_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Asynchronously list all sessions with optional filtering by app name and user ID.
    """
    url = _build_sessions_url(base_url)
    headers = _build_headers(api_key)
    params = {}
    
    if app_name:
        params["appName"] = app_name
    if user_id:
        params["userId"] = user_id
    
    return await async_http_get(url, headers=headers, params=params)


def list_sessions(
    base_url: str,
    api_key: str,
    app_name: Optional[str] = None,
    user_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    List all sessions with optional filtering by app name and user ID.
    """
    url = _build_sessions_url(base_url)
    headers = _build_headers(api_key)
    params = {}
    
    if app_name:
        params["appName"] = app_name
    if user_id:
        params["userId"] = user_id
    
    return http_get(url, headers=headers, params=params)


# ---------------------- CREATE SESSION ----------------------
async def async_create_session(
    base_url: str,
    api_key: str,
    app_name: str,
    user_id: str,
    uid: Optional[str] = None,
    state: Optional[SessionState] = None,
) -> Dict[str, Any]:
    """
    Asynchronously create a new session with optional initial state.
    """
    url = _build_sessions_url(base_url)
    headers = _build_headers(api_key)
    payload = {
        "appName": app_name,
        "userId": user_id,
        "uid": uid,
        "state": state,
    }
    clean_payload = {k: v for k, v in payload.items() if v is not None}
    return await async_http_post(url, headers=headers, json=clean_payload)


def create_session(
    base_url: str,
    api_key: str,
    app_name: str,
    user_id: str,
    uid: Optional[str] = None,
    state: Optional[SessionState] = None,
) -> Dict[str, Any]:
    """
    Create a new session with optional initial state.
    """
    url = _build_sessions_url(base_url)
    headers = _build_headers(api_key)
    payload = {
        "appName": app_name,
        "userId": user_id,
        "uid": uid,
        "state": state,
    }
    clean_payload = {k: v for k, v in payload.items() if v is not None}
    return http_post(url, headers=headers, json=clean_payload)


# ---------------------- GET SESSION ----------------------
async def async_get_session(
    base_url: str,
    api_key: str,
    uid: str,
    after_timestamp: Optional[int] = None,
    num_recent_events: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Asynchronously retrieve a specific session with its events and merged state.
    """
    url = f"{_build_sessions_url(base_url)}/{uid}"
    headers = _build_headers(api_key)
    params = {}
    
    if after_timestamp is not None:
        params["afterTimestamp"] = after_timestamp
    if num_recent_events is not None:
        params["numRecentEvents"] = num_recent_events
    
    return await async_http_get(url, headers=headers, params=params)


def get_session(
    base_url: str,
    api_key: str,
    uid: str,
    after_timestamp: Optional[int] = None,
    num_recent_events: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Retrieve a specific session with its events and merged state.
    """
    url = f"{_build_sessions_url(base_url)}/{uid}"
    headers = _build_headers(api_key)
    params = {}
    
    if after_timestamp is not None:
        params["afterTimestamp"] = after_timestamp
    if num_recent_events is not None:
        params["numRecentEvents"] = num_recent_events
    
    return http_get(url, headers=headers, params=params)


# ---------------------- DELETE SESSION ----------------------
async def async_delete_session(
    base_url: str,
    api_key: str,
    uid: str,
) -> Dict[str, Any]:
    """
    Asynchronously delete a specific session and all its associated data.
    """
    url = f"{_build_sessions_url(base_url)}/{uid}"
    headers = _build_headers(api_key)
    return await async_http_delete(url, headers=headers)


def delete_session(
    base_url: str,
    api_key: str,
    uid: str,
) -> Dict[str, Any]:
    """
    Delete a specific session and all its associated data.
    """
    url = f"{_build_sessions_url(base_url)}/{uid}"
    headers = _build_headers(api_key)
    return http_delete(url, headers=headers)


# ---------------------- GET SESSION EVENTS ----------------------
async def async_get_session_events(
    base_url: str,
    api_key: str,
    uid: str,
) -> List[Dict[str, Any]]:
    """
    Asynchronously retrieve all events for a specific session.
    """
    url = f"{_build_sessions_url(base_url)}/{uid}/events"
    headers = _build_headers(api_key)
    return await async_http_get(url, headers=headers)


def get_session_events(
    base_url: str,
    api_key: str,
    uid: str,
) -> List[Dict[str, Any]]:
    """
    Retrieve all events for a specific session.
    """
    url = f"{_build_sessions_url(base_url)}/{uid}/events"
    headers = _build_headers(api_key)
    return http_get(url, headers=headers)


# ---------------------- ADD EVENT TO SESSION ----------------------
async def async_add_session_event(
    base_url: str,
    api_key: str,
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
    """
    Asynchronously add a new event to an existing session.
    """
    url = f"{_build_sessions_url(base_url)}/{uid}/events"
    headers = _build_headers(api_key)
    payload = {
        "uid": uid_event,
        "invocationId": invocation_id,
        "author": author,
        "branch": branch,
        "content": content,
        "actions": actions,
        "longRunningToolIdsJson": long_running_tool_ids_json,
        "groundingMetadata": grounding_metadata,
        "partial": partial,
        "turnComplete": turn_complete,
        "errorCode": error_code,
        "errorMessage": error_message,
        "interrupted": interrupted,
    }
    clean_payload = {k: v for k, v in payload.items() if v is not None}
    return await async_http_post(url, headers=headers, json=clean_payload)


def add_session_event(
    base_url: str,
    api_key: str,
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
    """
    Add a new event to an existing session.
    """
    url = f"{_build_sessions_url(base_url)}/{uid}/events"
    headers = _build_headers(api_key)
    payload = {
        "uid": uid_event,
        "invocationId": invocation_id,
        "author": author,
        "branch": branch,
        "content": content,
        "actions": actions,
        "longRunningToolIdsJson": long_running_tool_ids_json,
        "groundingMetadata": grounding_metadata,
        "partial": partial,
        "turnComplete": turn_complete,
        "errorCode": error_code,
        "errorMessage": error_message,
        "interrupted": interrupted,
    }
    clean_payload = {k: v for k, v in payload.items() if v is not None}
    return http_post(url, headers=headers, json=clean_payload)


# ---------------------- HELPER FUNCTIONS ----------------------

def create_state_delta(
    app_state: Optional[Dict[str, Any]] = None,
    user_state: Optional[Dict[str, Any]] = None,
    session_state: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create a state delta structure for updating session state.
    
    Args:
        app_state: App-wide state (feature flags, configuration)
        user_state: User-specific state (preferences, personal settings)
        session_state: Session-specific state (conversation history, context)
    
    Returns:
        State delta structure for use in event actions
    """
    state_delta = {}
    
    if app_state:
        state_delta["app"] = app_state
    if user_state:
        state_delta["user"] = user_state
    if session_state:
        state_delta["session"] = session_state
    
    return state_delta


def create_event_actions(
    state_delta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create an actions structure for session events.
    
    Args:
        state_delta: State delta structure from create_state_delta()
    
    Returns:
        Actions structure for use in add_session_event()
    """
    actions = {}
    
    if state_delta:
        actions["stateDelta"] = state_delta
    
    return actions


def extract_session_messages(session_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract conversation messages from session state.
    
    Args:
        session_data: Session data from get_session()
    
    Returns:
        List of conversation messages
    """
    state = session_data.get("state", {})
    session_state = state.get("session", {})
    conversation = session_state.get("conversation", {})
    return conversation.get("messages", [])


def extract_session_context(session_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract conversation context from session state.
    
    Args:
        session_data: Session data from get_session()
    
    Returns:
        Conversation context dictionary
    """
    state = session_data.get("state", {})
    session_state = state.get("session", {})
    conversation = session_state.get("conversation", {})
    return conversation.get("context", {})


def extract_session_events(session_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract events from session data.
    
    Args:
        session_data: Session data from get_session()
    
    Returns:
        List of session events
    """
    return session_data.get("events", [])