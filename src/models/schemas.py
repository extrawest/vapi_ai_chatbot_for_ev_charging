from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Literal
from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class ChatMessage(BaseModel):
    role: MessageRole = Field(description="Message role")
    content: str = Field(description="Message content")


class StationStatus(BaseModel):
    station_id: str = Field(description="Station identifier")
    is_online: bool = Field(description="Station online status")
    connector_status: Literal["available", "occupied", "stuck", "error"] = Field(
        description="Connector status"
    )
    last_seen: datetime = Field(description="Last communication timestamp")


class RebootRequest(BaseModel):
    station_id: str = Field(description="Station identifier")
    reason: str = Field(default="Connector stuck", description="Reason for reboot")


class RebootResponse(BaseModel):
    success: bool = Field(description="Reboot operation success")
    message: str = Field(description="Response message")
    station_id: str = Field(description="Station identifier")

class VapiAssistant(BaseModel):
    id: str = Field(description="VAPI assistant's id")
    name: str = Field(description="VAPI assistant's name")

    @classmethod
    def from_client_assistant(cls, assistant) -> 'VapiAssistant':
        return cls(id=assistant.id, name=assistant.name)

class AssistantResponse(BaseModel):
    names: List[VapiAssistant] = Field(description="VAPI assistant's names")


class VapiDeepgramTranscriber(BaseModel):
    provider: str = Field(description="Provider name")
    model: str = Field(description="Model name")
    language: str = Field(description="Language code")

class VapiOpenAiMessage(BaseModel):
    content: str = Field(description="Content of the message")
    role: str = Field(description="Role of the user")

class VapiCustomLlmModel(BaseModel):
    messages: List[VapiOpenAiMessage] = Field(description="Messages to be sent to the model")
    provider: str = Field(description="Provider of the model")
    url: str = Field(description="URL of the model")
    model: str = Field(description="Model name")

class VapiOpenAiVoice(BaseModel):
    provider: str = Field(description="Voice provider name")
    model: str = Field(description="Voice model name")
    inputMinCharacters: int = Field(description="Minimum characters for input")
    voiceId: Optional[str] = Field(None, description="Voice ID (optional)")

class ChatSession(BaseModel):
    session_id: str = Field(description="Session identifier")
    user_id: str = Field(description="User identifier")
    messages: List[ChatMessage] = Field(default_factory=list, description="Session messages")
    created_at: datetime = Field(default_factory=datetime.now, description="Session creation time")
    reboot_count: int = Field(default=0, description="Number of consecutive station reboots")
    last_reboot_time: Optional[float] = Field(default=None, description="Timestamp of last station reboot")


class LLMRequest(BaseModel):
    messages: List[Dict[str, str]] = Field(description="Chat messages")
    provider: Optional[str] = Field(default=None, description="Model name")
    session_id: Optional[str] = Field(default=None, description="Session identifier")
    user_id: Optional[str] = Field(default=None, description="User identifier")

