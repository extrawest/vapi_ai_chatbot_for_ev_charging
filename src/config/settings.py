from typing import Literal, Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    host: str = Field(default="0.0.0.0", description="Host address")
    port: int = Field(default=8000, description="Port number")

    llm_provider: Literal["ollama", "together", "openai", "groq", "gemini"] = Field(
        default="openai", description="LLM provider to use"
    )

    ollama_base_url: str = Field(default="http://localhost:11434", description="Ollama base URL")
    ollama_model: str = Field(default="llama3", description="Ollama model name")

    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    openai_model: Optional[str] = Field(default=None, description="OpenAI model name")

    together_api_key: Optional[str] = Field(default=None, description="Together AI API key")
    together_model: str = Field(default="meta-llama/Llama-2-7b-chat-hf", description="Together AI model")

    groq_api_key: Optional[str] = Field(default=None, description="Groq API key")
    groq_model: str = Field(default="llama3-8b-8192", description="Groq model name")

    gemini_api_key: Optional[str] = Field(default=None, description="Gemini API key for Gemini")
    gemini_model: Optional[str] = Field(default=None, description="Gemini model name")

    vapi_session_id: Optional[str] = Field(default=None, description="VAPI Session ID")
    vapi_api_public_key: Optional[str] = Field(default=None, description="VAPI API public key")
    vapi_api_private_key: Optional[str] = Field(default=None, description="VAPI API private key")
    vapi_assistant_name: Optional[str] = Field(default=None, description="VAPI assistant name")
    vapi_assistant_id: Optional[str] = Field(default=None, description="VAPI assistant ID")
    vapi_custom_llm_url: Optional[str] = Field(default=None, description="Custom LLM URL for VAPI integration")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"

settings = Settings()