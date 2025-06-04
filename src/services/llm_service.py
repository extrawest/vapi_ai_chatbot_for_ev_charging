from typing import Any

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq

from src.config.settings import settings
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class LLMService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LLMService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self) -> None:
        if not hasattr(self, '_initialized') or not self._initialized:
            self._clients = {}
            logger.info("Initializing LLM service")
            self._initialize_clients()
            self._initialized = True

    def _initialize_clients(self) -> None:
        if settings.openai_api_key:
            logger.info("Initializing OpenAI client")
            self._clients["openai"] = ChatOpenAI(
                api_key=settings.openai_api_key,
                model="gpt-3.5-turbo",
                temperature=0.7,
            )

        if settings.ollama_base_url:
            logger.info(f"Initializing Ollama client with base URL: {settings.ollama_base_url}")
            self._clients["ollama"] = ChatOpenAI(
                base_url=settings.ollama_base_url,
                model=settings.ollama_model,
                temperature=0.7,
            )

        if settings.together_api_key:
            logger.info("Initializing Together AI client")
            self._clients["together"] = ChatOpenAI(
                api_key=settings.together_api_key,
                model=settings.together_model,
                temperature=0.7,
            )

        if settings.groq_api_key:
            logger.info("Initializing Groq client")
            self._clients["groq"] = ChatGroq(
                api_key=settings.groq_api_key,
                model=settings.groq_model,
                temperature=0.7
            )

        if settings.gemini_api_key:
            logger.info("Initializing Gemini client")
            self._clients["gemini"] = ChatGoogleGenerativeAI(
                api_key=settings.gemini_api_key,
                model="gemini-pro",
                temperature=0.7,
                convert_system_message_to_human=True
            )

    def get_llm(self, provider: str = None) -> Any:
        provider = provider or settings.llm_provider
        
        if provider not in self._clients:
            available_providers = list(self._clients.keys())
            if not available_providers:
                raise ValueError(f"No LLM providers available. Please check your API keys.")

            provider = available_providers[0]
            logger.warning(f"Provider {provider} not available, falling back to {provider}")
        
        return self._clients[provider]