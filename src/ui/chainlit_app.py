import uuid
import json
import chainlit as cl
import httpx
import sys
from pathlib import Path
from enum import Enum

from src.config.settings import settings
from src.utils import setup_logger
from vapi_python import Vapi

logger = setup_logger(__name__)

class CallStatus(str, Enum):
    INACTIVE = "inactive"
    ACTIVE = "active"
    LOADING = "loading"

vapi_instance = None

@cl.action_callback("reboot")
async def on_reboot(action):
    message = action.payload.get("message")
    await cl.Message(content=message, author="You").send()
    await on_message(cl.Message(content=message))

@cl.action_callback("stuck")
async def on_stuck(action):
    message = action.payload.get("message")
    await cl.Message(content=message, author="You").send()
    await on_message(cl.Message(content=message))

@cl.action_callback("offline")
async def on_offline(action):
    message = action.payload.get("message")
    await cl.Message(content=message, author="You").send()
    await on_message(cl.Message(content=message))

@cl.action_callback("provider_openai")
@cl.action_callback("provider_ollama")
@cl.action_callback("provider_together")
@cl.action_callback("provider_groq")
@cl.action_callback("provider_gemini")
async def on_provider_change(action):
    provider = action.payload.get("provider")
    if provider:
        cl.user_session.set("llm_provider", provider)
        logger.info(f"Changed LLM provider to: {provider}")
        await cl.Message(content=f"LLM provider changed to: **{provider.capitalize()}**", author="System").send()

@cl.action_callback("voice_call")
async def toggle_voice_call(action):
    global vapi_instance
    current_status = action.payload.get("status", CallStatus.INACTIVE)
    
    if current_status == CallStatus.ACTIVE:
        await cl.Message(content="Ending voice call...", author="System").send()

        if vapi_instance:
            try:
                vapi_instance.stop()
                logger.info("VAPI call stopped successfully")
            except Exception as e:
                logger.error(f"Error stopping VAPI call: {str(e)}")
        
        cl.user_session.set("call_status", CallStatus.INACTIVE)
        await show_voice_button()
        await cl.Message(content="Voice call ended.", author="System").send()
    else:
        await cl.Message(content="Initializing voice call...", author="System").send()
        cl.user_session.set("call_status", CallStatus.LOADING)
        await show_voice_button()
        
        try:
            if not settings.vapi_api_public_key:
                logger.error("VAPI API key is not set")
                raise ValueError("VAPI API key is not set. Please check your .env file.")

            logger.info(f"VAPI API key length: {len(settings.vapi_api_public_key) if settings.vapi_api_public_key else 0}")
            logger.info(f"VAPI assistant ID: {settings.vapi_assistant_id}")

            vapi_instance = Vapi(api_key=settings.vapi_api_public_key)

            assistant_overrides = {
                "recordingEnabled": False,
                "interruptionsEnabled": False,
            }

            call = vapi_instance.start(
                assistant_id=settings.vapi_assistant_id,
                assistant_overrides=assistant_overrides
            )

            logger.info(f"VAPI call started successfully {call}")
            
            cl.user_session.set("call_status", CallStatus.ACTIVE)
            await show_voice_button()
            await cl.Message(content="Voice call active! Start speaking now...", author="System").send()
        except Exception as e:
            logger.error(f"Error making VAPI call: {str(e)}")
            cl.user_session.set("call_status", CallStatus.INACTIVE)
            await show_voice_button()
            await cl.Message(content=f"Voice call initialization error: {str(e)}", author="System").send()

async def show_voice_button():
    call_status = cl.user_session.get("call_status", CallStatus.INACTIVE)

    if call_status == CallStatus.ACTIVE:
        label = "⏹️ End Voice Call"
        content = "**Voice call is active** - Click the button below to end the call"
    elif call_status == CallStatus.LOADING:
        label = "⌛ Initializing Call..."
        content = "**Voice call is initializing** - Please wait..."
    else:
        label = "🎤 Start Voice Call"
        content = "**Voice assistance available** - Click the button below to start a voice call"

    actions = [cl.Action(name="voice_call", payload={"status": call_status}, label=label)]
    await cl.Message(content=content, author="System", actions=actions).send()

@cl.on_chat_start
async def on_chat_start():
    session_id = str(uuid.uuid4())
    user_id = f"user_{session_id[:8]}"
    
    cl.user_session.set("session_id", session_id)
    cl.user_session.set("user_id", user_id)
    cl.user_session.set("call_status", CallStatus.INACTIVE)
    cl.user_session.set("llm_provider", settings.llm_provider)

    available_providers = []
    if settings.openai_api_key:
        available_providers.append("openai")
    if settings.ollama_base_url:
        available_providers.append("ollama")
    if settings.together_api_key:
        available_providers.append("together")
    if settings.groq_api_key:
        available_providers.append("groq")
    if settings.gemini_api_key:
        available_providers.append("gemini")

    if not available_providers:
        available_providers = [settings.llm_provider]

    provider_icons = {
        "openai": "🧠",
        "ollama": "🦙",
        "together": "🤝",
        "groq": "⚡",
        "gemini": "👨‍🚀"
    }
    
    provider_actions = []
    for provider in available_providers:
        icon = provider_icons.get(provider, "🤖")
        provider_actions.append(
            cl.Action(
                name=f"provider_{provider}",
                label=f"{icon} {provider.capitalize()}",
                payload={"provider": provider}
            )
        )
    
    await cl.Message(content="Welcome to the EV Charging Station Assistant! How can I help you today?").send()

    if len(available_providers) > 1:
        current_provider = cl.user_session.get("llm_provider", settings.llm_provider)
        icon = provider_icons.get(current_provider, "🤖")
        
        provider_message = f"""
### 💬 LLM Provider Settings

**Current provider:** {icon} **{current_provider.capitalize()}**

Select a different AI model to use for chat:
"""
        
        await cl.Message(
            content=provider_message,
            actions=provider_actions,
            author="System"
        ).send()

    await cl.Message(
        content="Common issues I can help with:",
        actions=[
            cl.Action(name="reboot", label="🔄 Reboot Station", payload={"message": "I need to reboot my charging station"}),
            cl.Action(name="stuck", label="🔌 Connector Stuck", payload={"message": "The connector is stuck"}),
            cl.Action(name="offline", label="📴 Station Offline", payload={"message": "My station is offline"}),
        ],
    ).send()
    
    await show_voice_button()

@cl.on_message
async def on_message(message: cl.Message) -> None:
    if message.author == "System":
        return
    
    session_id = cl.user_session.get("session_id")
    user_id = cl.user_session.get("user_id")
    llm_provider = cl.user_session.get("llm_provider", settings.llm_provider)

    if not session_id or not user_id:
        await cl.Message(content="Session error. Please refresh the page.").send()
        return

    content = ""

    msg = cl.Message(content=content)
    await msg.send()

    async with httpx.AsyncClient() as client:
        url = f"http://{settings.host}:{settings.port}/chat/completions"
        payload = {
            "messages": [{"role": "user", "content": message.content}],
            "provider": llm_provider,
            "session_id": session_id,
            "user_id": user_id
        }
        
        logger.info(f"Using LLM provider: {llm_provider}")

        headers = {
            "Accept": "text/event-stream",
            "Content-Type": "application/json"
        }

        logger.info(f"Making request to {url}")

        try:
            async with client.stream("POST", url, json=payload, headers=headers, timeout=60.0) as response:
                if response.status_code != 200:
                    error_text = await response.text()
                    msg.content = f"Error: {response.status_code} - {error_text}"
                    await msg.update()
                    return

                try:
                    async for line in response.aiter_lines():
                        if not line.strip():
                            continue

                        if line == "[DONE]" or line == "data: [DONE]":
                            logger.info("Received DONE signal, ending stream")
                            break

                        json_str = line
                        if line.startswith("data: "):
                            json_str = line[6:].strip()
                        
                        if not json_str:
                            continue
                        
                        try:
                            data = json.loads(json_str)
                            if "choices" in data and len(data["choices"]) > 0:
                                delta = data["choices"][0].get("delta", {})
                                if "content" in delta:
                                    content += delta["content"]
                                    msg.content = content
                                    await msg.update()

                            logger.info(f"Received chunk: {json_str[:50]}...")
                        except json.JSONDecodeError as e:
                            logger.error(f"Error parsing JSON: {e}, line: {json_str[:50]}...")
                            continue
                except httpx.ReadError as e:
                    logger.warning(f"Stream reading error: {e}")
                    if content:
                        msg.content = content
                        await msg.update()
                    else:
                        msg.content = "Error: Connection closed unexpectedly"
                        await msg.update()
        except httpx.NetworkError as e:
            logger.error(f"Network error: {e}")
            msg.content = "Error: Network error"
            await msg.update()
        except httpx.TimeoutException as e:
            logger.error(f"Timeout exception: {e}")
            msg.content = "Error: Timeout exception"
            await msg.update()
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            msg.content = "Error: Unexpected error"
            await msg.update()


if __name__ == "__main__":
    project_root = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(project_root))

    cl.run()