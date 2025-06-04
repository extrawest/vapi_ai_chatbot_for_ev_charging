from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from src.models.schemas import LLMRequest, AssistantResponse, VapiAssistant
from src.services.streaming_service import StreamingService
from src.dependencies.services import get_streaming_service, get_session_info, get_vapi_service, process_vapi_request
from src.services.vapi_service import VapiService
from src.utils import setup_logger

logger = setup_logger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/completions")
async def chat_completions(
    session_info: dict = Depends(get_session_info),
    request: LLMRequest = Depends(process_vapi_request),
    streaming_service: StreamingService = Depends(get_streaming_service)
) -> StreamingResponse:
    logger.info(f"Received chat completions request for session {session_info['session_id']}")
    return await streaming_service.streaming_chat(request)

@router.post("/load_assistants")
async def load_assistants(
    vapi_service: VapiService = Depends(get_vapi_service)
) -> AssistantResponse:
    logger.info("Loading all assistants from VAPI... This may take a few minutes. Please be patient.")
    return await vapi_service.load_all_assistants()

@router.post("/create_new_assistant")
async def create_new_assistant(
    vapi_service: VapiService = Depends(get_vapi_service)
) -> VapiAssistant:
    logger.info("Creating new assistant in VAPI... This may take a few minutes. Please be patient.")
    return await vapi_service.create_new_assistant()
