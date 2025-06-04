import json
import traceback

from typing import AsyncGenerator

from src.models.schemas import LLMRequest
from fastapi.responses import StreamingResponse
from fastapi import HTTPException

from src.services.llm_service import LLMService
from src.services.chat_service import ChatService
from src.services.station_service import StationService
from src.agents.chatbot_agent import ChatbotAgent
from src.utils import setup_logger
from src.utils.openai_mapper import create_streaming_openai_chunk

logger = setup_logger(__name__)


class StreamingService:
    def __init__(
        self, 
        llm_service: LLMService,
        chat_service: ChatService,
        station_service: StationService,
        chatbot_agent: ChatbotAgent
    ):
        self.llm_service = llm_service
        self.chat_service = chat_service
        self.station_service = station_service
        self.chatbot_agent = chatbot_agent

    async def streaming_chat(self, request: LLMRequest) -> StreamingResponse:
        try:
            user_message = next((msg.get("content", "") for msg in request.messages if msg.get("role") == "user"), "")

            if not user_message:
                raise HTTPException(status_code=400, detail="No user message provided")

            async def generate_stream() -> AsyncGenerator[str, None]:
                first_chunk = await create_streaming_openai_chunk(role="assistant")
                yield f"data: {json.dumps(first_chunk)}\n\n"

                async for mode, chunk in self.chatbot_agent.stream_message(user_message, stream_mode=["updates", "custom"]):
                    logger.info(f"[STREAM] Received {mode} chunk: {chunk}")

                    if mode == "custom" and "intermediate_message" in chunk:
                        message = chunk["intermediate_message"]
                        logger.info(f"[STREAM] Sending intermediate message: {message}")
                        content_chunk = await create_streaming_openai_chunk(content=message)
                        yield f"data: {json.dumps(content_chunk)}\n\n"

                    if mode == "updates" and isinstance(chunk, dict) and "chatbot" in chunk:
                        chatbot_data = chunk["chatbot"]
                        if isinstance(chatbot_data, dict) and "messages" in chatbot_data:
                            messages = chatbot_data["messages"]
                            if messages and len(messages) > 0:
                                last_message = messages[-1]
                                if hasattr(last_message, "content") and last_message.content:
                                    content_chunk = await create_streaming_openai_chunk(content=last_message.content)
                                    yield f"data: {json.dumps(content_chunk)}\n\n"

                final_chunk = await create_streaming_openai_chunk(finish_reason="stop")
                yield f"data: {json.dumps(final_chunk)}\n\n"
                yield "data: [DONE]\n\n"

            return StreamingResponse(
                generate_stream(),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                }
            )
        except Exception as e:
            logger.error(f"Error in chat_completions: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=str(e))
