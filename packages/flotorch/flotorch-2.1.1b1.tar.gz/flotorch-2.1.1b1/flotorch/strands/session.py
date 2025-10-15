"""Flotorch Strands session repository implementation following Strands documentation."""

import os
import uuid
from typing import Any, Optional
from flotorch.sdk.session import FlotorchSession
from flotorch.sdk.utils.logging_utils import log_object_creation, log_error
from strands.session.session_repository import SessionRepository
from strands.types.session import Session, SessionAgent, SessionMessage, SessionType
from strands.types.content import Message

class FlotorchStrandsSession(SessionRepository):
    """
        Custom session repository for Strands using Flotorch backend.
    """
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        app_name: str = "strands_app",
        user_id: str = "strands_user",
    ):
        """Initialize the repository.
        
        Args:
            api_key: Flotorch API key. Defaults to FLOTORCH_API_KEY env var.
            base_url: Flotorch base URL. Defaults to FLOTORCH_BASE_URL env var.
            app_name: Application name for session grouping.
            user_id: User ID for session grouping.
        """
        self.api_key = api_key or os.getenv("FLOTORCH_API_KEY")
        self.base_url = base_url or os.getenv("FLOTORCH_BASE_URL")
        self.app_name = app_name
        self.user_id = user_id
        
        if not self.api_key or not self.base_url:
            raise ValueError("FLOTORCH_API_KEY and FLOTORCH_BASE_URL are required")
        
        self.session_client = FlotorchSession(api_key=self.api_key, base_url=self.base_url)
        log_object_creation("FlotorchStrandsSession", base_url=self.base_url)

    def create_session(self, session: Session, **kwargs: Any) -> Session:
        """Create a new session in the Flotorch backend."""
        try:

            user_state = kwargs.get('state')
            if user_state is not None:
                state = user_state
            else:
                state = {
                    "session_type": str(session.session_type),
                    "created_at": str(uuid.uuid4()),
                    "metadata": getattr(session, 'metadata', {})
                }
            
            self.session_client.create(
                app_name=self.app_name,
                user_id=self.user_id,
                uid=session.session_id,
                state=state
            )
            return session
        except Exception as e:
            log_error("FlotorchStrandsSession.create_session", e)
            return session

    def read_session(self, session_id: str, **kwargs: Any) -> Optional[Session]:
        """Read a session from the Flotorch backend."""
        try:
            data = self.session_client.get(uid=session_id)
            if not data:
                return None
            
            return Session(
                session_id=session_id,
                session_type=SessionType.AGENT
            )
        except Exception as e:
            log_error("FlotorchStrandsSession.read_session", e)
            return None

    def create_agent(self, session_id: str, session_agent: SessionAgent, **kwargs: Any) -> None:
        """Create an agent in the session."""
        try:
            agent_type = kwargs.get('agent_type', 'agent_creation')
            
            agent_data = {
                "type": agent_type,
                "agent_id": session_agent.agent_id,
                "state": session_agent.state,
                "conversation_manager_state": session_agent.conversation_manager_state,
                "timestamp": str(uuid.uuid4())
            }
            
            self.session_client.add_event(
                uid=session_id,
                invocation_id=str(uuid.uuid4()),
                author="system",
                content={"parts": [agent_data]}
            )
            
        except Exception as e:
            log_error("FlotorchStrandsSession.create_agent", e)

    def read_agent(self, session_id: str, agent_id: str, **kwargs: Any) -> Optional[SessionAgent]:
        """Read an agent from the session."""
        try:
            session = self.session_client.get(uid=session_id)
            if not session or not session.events:
                return None

            for i, event in enumerate(reversed(session.events)):
                if event.author == "system":
                    content = event.content
                    content_data = {}
                    
                    if content and hasattr(content, 'parts') and content.parts:
                        content_data = content.parts[0] if content.parts else {}
                    elif content:
                        try:
                            content_dict = content.to_dict()
                            if content_dict.get('parts') and content_dict['parts']:
                                content_data = content_dict['parts'][0]
                        except:
                            pass
                    
                    if content_data.get('type') in ['agent_creation', 'agent_update']:
                        if content_data.get('agent_id') == agent_id:
                            return SessionAgent(
                                agent_id=content_data['agent_id'],
                                state=content_data['state'],
                                conversation_manager_state=content_data['conversation_manager_state']
                            )
            
            return None
        except Exception as e:
            log_error("FlotorchStrandsSession.read_agent", e)
            return None

    def update_agent(self, session_id: str, session_agent: SessionAgent, **kwargs: Any) -> None:
        """Update an agent in the session."""
        try:
            agent_type = kwargs.get('agent_type', 'agent_update')
            
            agent_data = {
                "type": agent_type,
                "agent_id": session_agent.agent_id,
                "state": session_agent.state,
                "conversation_manager_state": session_agent.conversation_manager_state,
                "timestamp": str(uuid.uuid4())
            }
            
            self.session_client.add_event(
                uid=session_id,
                invocation_id=str(uuid.uuid4()),
                author="system",
                content={"parts": [agent_data]}
            )
            
        except Exception as e:
            log_error("FlotorchStrandsSession.update_agent", e)

    def create_message(self, session_id: str, agent_id: str, session_message: SessionMessage, **kwargs: Any) -> None:
        """Create a message in the session."""
        try:

            if hasattr(session_message.message, 'role'):
                role = session_message.message.role
                content = session_message.message.content
            elif isinstance(session_message.message, dict):
                role = session_message.message.get('role', 'user')
                content = session_message.message.get('content', '')
                
                if isinstance(content, list) and len(content) > 0:
                    if isinstance(content[0], dict) and 'text' in content[0]:
                        content = content[0]['text']
                    else:
                        content = str(content[0])
                elif not isinstance(content, str):
                    content = str(content)
            else:
                role = 'user'
                content = str(session_message.message)
            
            message_data = {
                "parts": [{"text": str(content)}]
            }
            
            grounding_metadata = {
                "agent_id": agent_id,
                "message_id": session_message.message_id,
                "role": role
            }
            
            self.session_client.add_event(
                uid=session_id,
                invocation_id=str(uuid.uuid4()),
                author="user" if role == "user" else "assistant",
                content=message_data,
                grounding_metadata=grounding_metadata
            )
            
        except Exception as e:
            log_error("FlotorchStrandsSession.create_message", e)

    def read_message(self, session_id: str, agent_id: str, message_id: int, **kwargs: Any) -> Optional[SessionMessage]:
        """Read a specific message from the session."""
        try:
            session = self.session_client.get(uid=session_id)
            if not session or not session.events:
                return None
            
            for event in session.events:
                grounding_metadata = event.groundingMetadata or {}
                if (grounding_metadata.get('agent_id') == agent_id and 
                    grounding_metadata.get('message_id') == message_id):
                    
                    content = event.content
                    if content and hasattr(content, 'parts') and content.parts:
                        for part in content.parts:
                            text_content = part.get('text', '') if isinstance(part, dict) else str(part)
                            if text_content:
                                role = grounding_metadata.get('role', 'user')
                                
                                message = Message(content=text_content, role=role)
                                return SessionMessage.from_message(message, message_id)
            return None
        except Exception as e:
            log_error("FlotorchStrandsSession.read_message", e)
            return None

    def update_message(self, session_id: str, agent_id: str, session_message: SessionMessage, **kwargs: Any) -> None:
        """Update a message in the session (usually for redaction)."""
        try:
            self.session_client.add_event(
                uid=session_id,
                invocation_id=str(uuid.uuid4()),
                author="system",
                content={"parts": [{
                    "type": "message_update",
                    "agent_id": agent_id,
                    "message_id": session_message.message_id,
                    "content": session_message.content,
                    "role": session_message.role,
                    "redact_message": session_message.redact_message,
                    "timestamp": str(uuid.uuid4())
                }]}
            )
        except Exception as e:
            log_error("FlotorchStrandsSession.update_message", e)

    def list_messages(
        self, 
        session_id: str, 
        agent_id: str, 
        limit: Optional[int] = None, 
        offset: int = 0, 
        **kwargs: Any
    ) -> list[SessionMessage]:
        """List messages for an agent with pagination."""
        try:
            session = self.session_client.get(uid=session_id)
            if not session or not session.events:
                return []
            
            messages = []
            for event in session.events:
                grounding_metadata = event.groundingMetadata or {}
                if grounding_metadata.get('agent_id') == agent_id:
                    content = event.content
                    if content and hasattr(content, 'parts') and content.parts:
                        for part in content.parts:
                            text_content = part.get('text', '') if isinstance(part, dict) else str(part)
                            if text_content:
                                role = grounding_metadata.get('role', 'user')
                                message_id = grounding_metadata.get('message_id', 0)
                                
                                message = Message(content=text_content, role=role)
                                session_message = SessionMessage.from_message(message, message_id)
                                messages.append(session_message)
            
            messages.sort(key=lambda m: m.message_id)
            if offset > 0:
                messages = messages[offset:]
            if limit:
                messages = messages[:limit]
            
            return messages
        except Exception as e:
            log_error("FlotorchStrandsSession.list_messages", e)
            return []
