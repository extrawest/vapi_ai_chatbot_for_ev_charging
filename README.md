# 🤖 EV Charging Station Assistant

[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)]()
[![Maintainer](https://img.shields.io/static/v1?label=Yevhen%20Ruban&message=Maintainer&color=red)](mailto:yevhen.ruban@extrawest.com)
[![Ask Me Anything !](https://img.shields.io/badge/Ask%20me-anything-1abc9c.svg)]()
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
![GitHub release](https://img.shields.io/badge/release-v1.0.0-blue)

AI-powered support system for EV charging stations with LangGraph orchestration, multi-provider LLM support, and voice interface through VAPI integration for phone calling. This system allows users to check station status, reboot charging stations, and get assistance through text or voice interactions.

## 🌟 Features

- 🤖 **Intelligent Chatbot**: LangGraph-based agent with tool calling capabilities and state management
- ⚡ **Station Management**: Check status and reboot EV charging stations with safety limits
- 🔄 **Multi-LLM Support**: Dynamic selection between OpenAI, Ollama, Together AI, Groq, and Gemini
- 💬 **Interactive UI**: Modern Chainlit interface with problem selection buttons and provider switching
- 🎤 **Voice Interface**: VAPI integration for voice-based interactions and phone calls
- 🚨 **Safety Controls**: Limits station reboots to three attempts per 5 minutes
- 🔧 **FastAPI Backend**: REST API with streaming support and session management (OpenAI Compatible)
- 💾 **Singleton Services**: Persistent state management across requests

## Text Chat Demo: Interactive EV Assistant in Action




https://github.com/user-attachments/assets/172f3ada-9253-4576-b449-cd8289731dcd




## Voice Call Demo: Hands-Free EV Charging Support




https://github.com/user-attachments/assets/f490688e-d41b-4c48-be60-dd7285993b0f




## Phone Assistant Demo: EV Support On The Go




https://github.com/user-attachments/assets/7045794b-be91-4dda-89a4-1a9a62eb06cb




## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/extrawest/vapi_ai_chatbot_for_ev_charging.git
cd vapi_ai_chatbot_for_ev_charging

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Copy the example environment file and configure your settings:

```bash
cp .env.example .env
```

### 3. Running the Application

#### Option A: FastAPI Server Only

```bash
# Run the FastAPI server without UI
python -m src.main
```

Open http://localhost:8001 in your browser.

#### Option B: Chainlit UI (Recommended for users)

```bash
# Run the Chainlit interface
python run_chanilit.app
```

API documentation: http://localhost:8000/docs

## 💬 Usage

### Chainlit Chat Interface

1. **LLM Provider Selection**: Choose your preferred AI model from available providers
   - 🧠 OpenAI (GPT models)
   - 🦙 Ollama (local open-source models)
   - 🤝 Together AI (various open models)
   - ⚡ Groq (optimized for speed)
   - 👨‍🚀 Gemini (Google's models)

2. **Common Issues**: Quick access buttons for frequent problems
   - 🔄 Reboot Station
   - 🔌 Connector Stuck
   - 📴 Station Offline

3. **Voice Interface**: Start a voice call for hands-free assistance
   - Click the "🎤 Start Voice Call" button
   - Speak naturally to the assistant
   - The system will process your voice commands and respond verbally

4. **Station Operations Flow**:
   - Provide your station ID (e.g., "ST001")
   - System checks station status automatically
   - If issues are detected, system guides through troubleshooting
   - Reboot option with safety limits (max 3 reboots per 5 minutes)

### API Endpoints

#### Chat Completions (OpenAI Compatible)
```bash
curl -X POST "http://localhost:8000/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello"}],
    "provider": "openai",  # Optional: specify LLM provider
    "stream": true,
    "session_id": "user-session-123",
    "user_id": "user-123"
  }'
```

## 🤖 LLM Providers

The application supports multiple LLM providers through a unified interface. Users can dynamically switch between providers during a chat session via the UI buttons or API parameters.

### Supported Providers

| Provider | Icon | Configuration                       |
|----------|---|-------------------------------------|
| **OpenAI** | 🧠 | `OPENAI_API_KEY` and `OPENAI_MODEL` |
| **Ollama** | 🦙 | `OLLAMA_BASE_URL` and `OLLAMA_MODEL`|
| **Together AI** | 🤝 | `TOGETHER_API_KEY` and `TOGETHER_MODEL`|
| **Groq** | ⚡ | `GROQ_API_KEY` and `GROQ_MODEL`|
| **Gemini** | 👨‍🚀 | `GEMINI_API_KEY` and `GEMINI_MODEL`|

### Provider Selection

1. **Default Provider**: Set in `.env` with `LLM_PROVIDER` variable
2. **UI Selection**: Click provider buttons at chat start
3. **API Override**: Specify `provider` parameter in API requests

## 🎤 VAPI Integration

The application integrates with VAPI (Voice API) to provide voice-based interactions with the chatbot.

### Voice Assistant Features

- **Natural Voice Conversations**: Speak directly to the assistant. Phone calling
- **Custom Voice Configuration**: Configurable voice model and characteristics
- **Direct LLM Integration**: Uses the same LLM backend as the chat interface

### LangGraph Workflow

The chatbot uses LangGraph to orchestrate conversation flow with a structured state graph:

#### Graph Structure

1. **Message Processing**:
   - Receive user input and session context
   - Loads persistent state from `ChatService`
   - Formats system instructions for the LLM

2. **Tool Node**:
   - Analyzes user intent with the selected LLM provider
   - Decides whether to use station tools
   - Handles tool execution and result processing

3. **Reboot Management**:
   - Tracks reboot attempts with safety limits (3 per 5 minutes)
   - Stores timestamps for rate limiting
   - Provides appropriate feedback when limits are reached

4. **Response Generation**:
   - Formats responses based on tool execution results
   - Saves conversation history to persistent storage
   - Returns structured responses to the UI

### Message Streaming

The application implements real-time message streaming using LangGraph's built-in capabilities:

This enables:

- Progressive updates as the LLM generates responses
- Real-time feedback during tool execution (e.g., "Checking station status...")
- Improved user experience with immediate feedback
