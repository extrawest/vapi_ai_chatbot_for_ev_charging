import uuid
import time
from datetime import datetime
from typing import Dict, Optional

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

from src.models.schemas import ChatSession, ChatMessage, MessageRole
from src.utils import setup_logger

logger = setup_logger(__name__)

class ChatService:
    _instance = None
    _sessions: Dict[str, ChatSession] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ChatService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self) -> None:
        if not hasattr(self, '_initialized') or not self._initialized:
            self._initialized = True

    def create_session(self, user_id: str, session_id: str) -> ChatSession:
        session = ChatSession(
            session_id=session_id,
            user_id=user_id,
            messages=[],
            reboot_count=0,
            last_reboot_time=None,
            created_at=datetime.now()
        )

        logger.info("Session created: %s", session)
        self._sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[ChatSession]:
        session = self._sessions.get(session_id)
        logger.info("Session found: %s", session)
        return session

    def add_message(self, session_id: str, message: ChatMessage) -> bool:
        session = self._sessions.get(session_id)
        if session:
            session.messages.append(message)
            return True
        return False
        
    def get_reboot_count(self, session_id: str) -> int:
        logger.info("Checking reboot count for session id: %s", session_id)
        session = self._sessions.get(session_id)
        logger.info("Session: %s", session)
        if session:
            logger.info("Session count: %s", session.reboot_count)
        return session.reboot_count if session else 0
        
    def increment_reboot_count(self, session_id: str) -> bool:
        logger.info("Incrementing reboot count for session id: %s", session_id)
        session = self._sessions.get(session_id)
        logger.info("Session: %s", session)
        if session:
            session.reboot_count += 1
            session.last_reboot_time = time.time()
            logger.info("Session count: %s", session.reboot_count)
            return True
        return False
        
    def reset_reboot_count(self, session_id: str) -> bool:
        logger.info("Resetting reboot count for session id: %s", session_id)
        session = self._sessions.get(session_id)
        logger.info("Session: %s", session)
        if session:
            session.reboot_count = 0
            session.last_reboot_time = None
            logger.info("Session count: %s", session.reboot_count)
            return True
        return False
        
    def should_reset_reboot_count(self, session_id: str, timeout_seconds: int = 300) -> bool:
        session = self._sessions.get(session_id)
        if not session or not session.last_reboot_time:
            return False
            
        return (time.time() - session.last_reboot_time) > timeout_seconds
        
    def add_agent_message(self, session_id: str, message: BaseMessage) -> bool:
        if isinstance(message, HumanMessage):
            role = "user"
        elif isinstance(message, AIMessage):
            role = "assistant"
        elif isinstance(message, SystemMessage):
            role = "system"
        else:
            return False
            
        return self.add_message(
            session_id,
            ChatMessage(role=MessageRole(role), content=message.content)
        )