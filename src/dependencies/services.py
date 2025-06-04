from typing import Dict

from fastapi import Depends, Request

from src.config.settings import settings
from src.models.schemas import LLMRequest
from src.services.llm_service import LLMService
from src.services.chat_service import ChatService
from src.services.station_service import StationService
from src.services.streaming_service import StreamingService
from src.agents.chatbot_agent import ChatbotAgent
from src.services.vapi_service import VapiService
from src.utils import setup_logger

logger = setup_logger(__name__)

agent_sessions: Dict[str, ChatbotAgent] = {}


def get_llm_service() -> LLMService:
    return LLMService()


def get_chat_service() -> ChatService:
    return ChatService()


def get_station_service() -> StationService:
    return StationService()

def get_vapi_service() -> VapiService:
    return VapiService()


def get_request_info(request: Request):
    return {
        "request": request
    }


async def get_session_info(request_info: dict = Depends(get_request_info)):
    request = request_info["request"]
    body = await request.json()

    session_id = body.get("session_id", settings.vapi_session_id)
    user_id = body.get("user_id", "VAPI")
    provider = body.get("provider", settings.llm_provider)
    
    return {
        "session_id": session_id,
        "user_id": user_id,
        "provider": provider
    }


async def process_vapi_request(
    request: LLMRequest,
    session_info: dict = Depends(get_session_info)
) -> LLMRequest:
    if session_info['session_id'] == settings.vapi_session_id:
        user_messages = [msg for msg in request.messages if msg.get("role") == "user"]
        if user_messages:
            last_user_message = user_messages[-1]
            request.messages = [last_user_message]
    
    return request


def get_chatbot_agent(
    session_info: dict = Depends(get_session_info),
    llm_service: LLMService = Depends(get_llm_service),
    chat_service: ChatService = Depends(get_chat_service),
    station_service: StationService = Depends(get_station_service)
) -> ChatbotAgent:
    session_id = session_info["session_id"]
    user_id = session_info["user_id"]
    provider = session_info["provider"]

    logger.info(f"session_id: {session_id}, user_id: {user_id}, provider: {provider}")

    if session_id in agent_sessions:
        agent = agent_sessions[session_id]
        logger.info(f"Using existing agent for session {session_id}")
        return agent

    logger.info(f"Creating new agent for session {session_id}")
    agent = ChatbotAgent(
        user_id=user_id,
        session_id=session_id,
        provider=provider,
        llm_service=llm_service,
        chat_service=chat_service,
        station_service=station_service
    )
    agent_sessions[session_id] = agent
    return agent


def get_streaming_service(
    session_info: dict = Depends(get_session_info),
    llm_service: LLMService = Depends(get_llm_service),
    chat_service: ChatService = Depends(get_chat_service),
    station_service: StationService = Depends(get_station_service),
    chatbot_agent: ChatbotAgent = Depends(get_chatbot_agent)
) -> StreamingService:
    logger.info(f"session_info: {session_info}")
    return StreamingService(
        llm_service=llm_service,
        chat_service=chat_service,
        station_service=station_service,
        chatbot_agent=chatbot_agent
    )
