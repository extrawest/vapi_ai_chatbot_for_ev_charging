from typing import Dict, Any, List, Annotated
import traceback

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langgraph.graph.state import CompiledStateGraph
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver
from langgraph.config import get_stream_writer

from src.services.station_service import StationService
from src.services.chat_service import ChatService
from src.services.llm_service import LLMService
from src.models.schemas import ChatMessage, RebootRequest
from src.config.settings import settings
from src.utils import setup_logger

logger = setup_logger(__name__)

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]


@tool
async def send_checking_message() -> Dict[str, str]:
    """
    Send a message to the user indicating that the system is checking the station status.
    Use this tool BEFORE calling check_station_status.
    
    This tool streams an intermediate message to the user in real-time using LangGraph's
    custom streaming capability. It should be called before any operation that might
    take some time to complete, such as checking a station's status.
    
    Returns:
        Dict[str, str]: A dictionary containing the message that was sent
    """
    message = " Checking... please wait "
    logger.info(f"[TOOL] Sending intermediate message: {message}")

    try:
        writer = get_stream_writer()
        if writer:
            writer({"intermediate_message": message})
    except Exception as e:
        logger.error(f"[TOOL] Error sending stream: {e}")
    
    return {"message": message}


@tool
async def send_rebooting_message() -> Dict[str, str]:
    """
    Send a message to the user indicating that the system is rebooting the station.
    Use this tool BEFORE calling reboot_station.
    
    This tool streams an intermediate message to the user in real-time using LangGraph's
    custom streaming capability. It should be called before initiating a station reboot
    to inform the user that the operation is in progress.
    
    Returns:
        Dict[str, str]: A dictionary containing the message that was sent
    """
    message = " Rebooting the station... please wait "
    logger.info(f"[TOOL] Sending intermediate message: {message}")

    try:
        writer = get_stream_writer()
        if writer:
            writer({"intermediate_message": message})
    except Exception as e:
        logger.error(f"[TOOL] Error sending stream: {e}")
    
    return {"message": message}


@tool
async def get_station_instructions() -> Dict[str, Any]:
    """Get instructions for finding the station number on an EV charging station.

    Returns:
        A dictionary with instructions
    """
    return {
        "instructions": "To find your station number:\n"
            "1. Look for a sticker or plate on the charging station\n"
            "2. The station number usually starts with 'ST' followed by numbers (e.g., ST001)\n"
            "3. It's typically located near the charging connector or on the front panel\n"
            "4. If you can't find it, look for a QR code that might contain the station ID"
    }


class ChatbotAgent:
    def __init__(
        self, 
        user_id: str, 
        session_id: str, 
        provider: str = None,
        llm_service: LLMService = None,
        chat_service: ChatService = None,
        station_service: StationService = None
    ):
        self.user_id = user_id
        self.session_id = session_id
        self.provider = provider or settings.llm_provider

        self.llm_service = llm_service
        self.chat_service = chat_service
        self.station_service = station_service
        
        self.chat_session = self.chat_service.get_session(session_id)
        if not self.chat_session:
            self.chat_session = self.chat_service.create_session(user_id, session_id)
        
        self.llm = self.llm_service.get_llm(provider)

        self.tools = [
            send_checking_message,
            send_rebooting_message,
            get_station_instructions,
            self._create_check_station_status_tool(),
            self._create_reboot_station_tool()
        ]

        self.llm_with_tools = self.llm.bind_tools(self.tools)
        self.memory = MemorySaver()
        self.graph = self._build_graph()
    
    def _create_check_station_status_tool(self):
        async def check_station_status(station_id: str) -> Dict[str, Any]:
            """Check the status of an EV charging station.

            Args:
                station_id: The ID of the station to check (e.g., ST001)

            Returns:
                A dictionary with the station status information
            """
            logger.info(f"Checking status for station: {station_id}")
            status = await self.station_service.check_station_status(station_id)
            
            if not status:
                return {"found": False, "message": f"Station {station_id} not found"}
            
            return {
                "found": True,
                "is_online": status.is_online,
                "connector_status": status.connector_status,
                "last_seen": status.last_seen.isoformat(),
                "message": f"Station {station_id} is {'online' if status.is_online else 'offline'} with connector status: {status.connector_status}",
                "is_problematic": status.connector_status in ["stuck", "error"]
            }
        return check_station_status

    def _create_reboot_station_tool(self):
        async def reboot_station(station_id: str) -> Dict[str, Any]:
            """Reboot an EV charging station when the connector is stuck or unresponsive.

            Args:
                station_id: The ID of the station to reboot (e.g., ST001)

            Returns:
                A dictionary with the reboot result
            """
            if self.chat_service.should_reset_reboot_count(self.session_id):
                self.chat_service.reset_reboot_count(self.session_id)

            reboot_count = self.chat_service.get_reboot_count(self.session_id)
            if reboot_count >= 3:
                logger.info("Station reboot attempts are blocked as you have used 3 attempts.")
                return {
                    "success": False,
                    "station_id": station_id,
                    "message": "Station reboot attempts are blocked as you have used 3 attempts. Please try again after 5 minutes. Thank you."
                }
                
            logger.info(f"Rebooting station: {station_id}, reboot count: {reboot_count}")
            self.chat_service.increment_reboot_count(self.session_id)

            request = RebootRequest(
                station_id=station_id,
                reason="User requested reboot due to stuck connector"
            )

            result = await self.station_service.reboot_station(request)
            
            return {
                "success": result.success,
                "message": result.message,
                "station_id": result.station_id
            }
        return reboot_station

    def _build_graph(self) -> CompiledStateGraph:
        graph_builder = StateGraph(AgentState)
        
        def chatbot_node(state: AgentState) -> Dict[str, Any]:
            logger.info(f"[AGENT] Processing in chatbot_node with {len(state['messages'])} messages")

            for msg in state["messages"]:
                self.chat_service.add_agent_message(self.session_id, msg)

            messages = state["messages"]
            system_message_content = (
                "You are an EV charging station assistant. Your main task is to help users reboot stations "
                "when connectors are stuck or unresponsive. "
                "If they've requested 3 or more reboots in the last 5 minutes, "
                "inform them they've reached the limit and suggest contacting support. "
                "Otherwise, help them reboot their station. "
                "\n\nYou MUST STRICTLY follow this EXACT sequence when helping with station issues:\n"
                "1. NEVER assume a station ID. ALWAYS explicitly ask for the station ID if the user has not clearly provided one.\n"
                "2. When asking for the station ID, you MUST use the get_station_instructions tool "
                "to show the user how to find the station number.\n"
                "3. ONLY after the user has explicitly provided a valid station ID (e.g., 'ST001'), "
                "you MUST use the send_checking_message tool FIRST, and THEN use the check_station_status tool.\n"
                "4. If the check_station_status tool returns that the connector is problematic (stuck or error) OR if the station is offline AND the user insists on rebooting, "
                "you MUST use the send_rebooting_message tool FIRST, and THEN use the reboot_station tool.\n"
                "5. After rebooting, respond with 'Done! Station is rebooting... If you have any other questions, please ask'.\n"
                "\n"
                "IMPORTANT RULES:\n"
                "- NEVER use the reboot_station tool without first using check_station_status on the same station ID.\n"
                "- NEVER use check_station_status without first using send_checking_message.\n"
                "- NEVER use reboot_station without first using send_rebooting_message.\n"
                "- You MAY use check_station_status with a station ID that the user has already provided in the current conversation.\n"
                "- You MAY reboot a station if either: (1) check_station_status confirms the connector is problematic, OR (2) the station is offline AND the user insists on rebooting.\n"
                "- If the user says 'station is offline' or similar, still ask for the specific station ID.\n"
                "\n"
                "When a user first connects, welcome them with 'Welcome to the EV Station Support!' and "
                "suggest they can ask for help with common issues like 'Connector is stuck' or 'Reboot station'."
            )
            
            system_message_found = False
            for i, msg in enumerate(messages):
                if isinstance(msg, SystemMessage):
                    messages[i] = SystemMessage(content=system_message_content)
                    system_message_found = True
                    break
            
            if not system_message_found:
                messages.insert(0, SystemMessage(content=system_message_content))
            
            response = self.llm_with_tools.invoke(messages)
            logger.info(f"[AGENT] Generated response: {response.content[:50]}...")

            self.chat_service.add_agent_message(self.session_id, response)

            if hasattr(response, "tool_calls") and response.tool_calls:
                for tool_call in response.tool_calls:
                    logger.info(f"Tool with name {tool_call.get("name")} is called")
            
            return {"messages": [response]}
        
        graph_builder.add_node("chatbot", chatbot_node)
        tool_node = ToolNode(tools=self.tools)
        graph_builder.add_node("tools", tool_node)

        graph_builder.add_conditional_edges(
            "chatbot",
            tools_condition,
            "tools"
        )

        graph_builder.add_edge("tools", "chatbot")
        graph_builder.add_edge(START, "chatbot")
        
        return graph_builder.compile(checkpointer=self.memory)


    async def stream_message(self, message: str, stream_mode):
        logger.info(f"Streaming message: {message}")

        self.chat_service.add_message(
            self.session_id,
            ChatMessage(role="user", content=message)
        )

        human_message = HumanMessage(content=message)

        config:RunnableConfig = {"configurable": {"thread_id": self.session_id}}
        
        try:
            current_state = self.graph.get_state(config)
            state = {
                "messages": current_state.values.get("messages", []) + [human_message]
            }

            logger.info(f"[AGENT] Streaming graph with {len(state['messages'])} messages")
            async for mode, chunk in self.graph.astream(state, stream_mode=stream_mode, config=config):
                yield mode, chunk

            final_state = self.graph.get_state(config)

            for msg in reversed(final_state.values.get("messages", [])):
                if isinstance(msg, AIMessage):
                    logger.info(f"[AGENT] Found AI response: {msg.content[:50]}...")
                    self.chat_service.add_message(
                        self.session_id,
                        ChatMessage(role="assistant", content=msg.content)
                    )
                    break
                    
        except Exception as e:
            logger.error(f"[AGENT] Error streaming message: {e}")
            logger.error(traceback.format_exc())
            yield "error", {"error": str(e)}
