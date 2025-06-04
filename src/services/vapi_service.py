from vapi import Vapi

from src.config.settings import settings
from src.models.schemas import AssistantResponse, VapiAssistant, VapiDeepgramTranscriber, VapiCustomLlmModel, \
    VapiOpenAiMessage, VapiOpenAiVoice
from src.utils import setup_logger

logger = setup_logger(__name__)

class VapiService:
    def __init__(self) -> None:
        self._client = Vapi(token=settings.vapi_api_private_key)

    async def load_all_assistants(self) -> AssistantResponse:
        assistants = self._client.assistants.list()

        for assistant in assistants:
            logger.info(f"Assistant: {assistant}")

        vapi_assistants = [
            VapiAssistant.from_client_assistant(assistant)
            for assistant in assistants
        ]

        return AssistantResponse(names=vapi_assistants)

    async def create_new_assistant(self) -> VapiAssistant:
        assistants = self._client.assistants.list()
        assistant_name = settings.vapi_assistant_name

        existing_assistant = next(
            (assistant for assistant in assistants if assistant.name == assistant_name),
            None
        )

        if existing_assistant:
            logger.info(f"Found existing assistant: {assistant_name}")
            return existing_assistant

        logger.info(f"Assistant '{assistant_name}' not found, creating new one...")

        return await self._create_custom_assistant()

    async def _create_custom_assistant(self) -> VapiAssistant:
        transcriber = VapiDeepgramTranscriber(
            provider='deepgram',
            model='nova-3',
            language='en'
        )

        model = VapiCustomLlmModel(
            messages=[VapiOpenAiMessage(content='You are an EV charging station assistant.', role='system')],
            provider='custom-llm',
            url=settings.vapi_custom_llm_url,
            model='gpt-4o'
        )

        voice = VapiOpenAiVoice(
            provider='openai',
            voiceId='alloy',
            model='gpt-4o-mini-tts',
            inputMinCharacters=10
        )

        assistant = self._client.assistants.create(
            transcriber=transcriber,
            model=model,
            voice=voice,
            first_message='Hello. I am Mike. How can I assist you?',
            name=settings.vapi_assistant_name,
            voicemail_message="Please call back when you're available.",
            end_call_message='Goodbye.'
        )

        logger.info(f"Created custom assistant: {assistant.name}")
        return VapiAssistant.from_client_assistant(assistant)


