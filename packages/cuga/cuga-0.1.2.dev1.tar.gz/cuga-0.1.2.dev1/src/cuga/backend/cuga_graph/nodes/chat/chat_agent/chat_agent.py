import asyncio
import os
from typing import Any, List, Optional

import aiohttp
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_core.messages import ToolCall, BaseMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models import BaseChatModel
from cuga.backend.activity_tracker.tracker import ActivityTracker
from cuga.backend.cuga_graph.nodes.api.variables_manager.manager import VariablesManager
from mcp.client.sse import sse_client
from mcp import ClientSession

from cuga.backend.cuga_graph.nodes.shared.base_agent import BaseAgent

from cuga.backend.llm.models import LLMManager
from cuga.backend.llm.utils.helpers import load_prompt_chat
from cuga.config import settings

from langchain_core.tools import tool, BaseTool
from loguru import logger

llm_manager = LLMManager()
tracker = ActivityTracker()
var_manager = VariablesManager()


@tool
def execute_task(task: str, relevant_variables: List[str]) -> str:
    """
    :param task: task to execute
    :param relevant_variables: relevant variables from history
    :return:
    """
    logger.debug(f"called execute task {task}")
    return "success"


@tool
def run_new_flow(user_task: str) -> str:
    """
    :param user_task: user_task to execute
    :return:
    """
    logger.debug(f"called execute task {user_task}")
    return "success"


async def check_sse_availability(url: str, timeout: int = 5) -> bool:
    """
    Asynchronously check if the SSE endpoint is available by pinging it.

    Args:
        url: The SSE URL to check
        timeout: Request timeout in seconds

    Returns:
        bool: True if SSE endpoint is available, False otherwise
    """
    try:
        timeout_config = aiohttp.ClientTimeout(total=timeout)
        async with aiohttp.ClientSession(timeout=timeout_config) as session:
            async with session.get(url) as response:
                return response.status == 200
    except (aiohttp.ClientError, asyncio.TimeoutError, Exception):
        return False


class ChatAgent(BaseAgent):
    def __init__(
        self, prompt_template: ChatPromptTemplate = None, llm: BaseChatModel = None, tools: Any = None
    ):
        super().__init__()
        self.name = "ChatAgent"
        self.sse_url = f"http://localhost:{settings.server_ports.saved_flows}/sse"
        self.agent = None
        self.session = None
        self._connection = None
        self.tools: Optional[List[BaseTool]] = None
        self.prompt_template = prompt_template
        # Check environment variable to determine execution mode
        self.use_regular_chat = None
        self.llm = llm
        self.chain = None
        self.sse_available = None
        self.agent = None
        self._is_setup = False  # Track setup state

    async def setup(self):
        """Initialize the connection and agent"""
        # Clean up any existing connections first
        await self.cleanup()

        self.sse_available = await check_sse_availability(self.sse_url)
        self.use_regular_chat = os.getenv('USE_LEGACY_EXECUTION', 'false').lower() == 'true'

        # If SSE is not available, force regular chat mode
        if not self.sse_available:
            logger.info(
                f"SSE endpoint at {self.sse_url} is not available. Falling back to regular chat mode."
            )
        if not settings.features.save_reuse:
            self.use_regular_chat = True

        if self.use_regular_chat:
            # Initialize chain for regular mode
            model = llm_manager.get_model(settings.agent.planner.model)
            self.chain = load_prompt_chat("./prompts/pmt_chat.jinja2") | model.bind_tools([execute_task])
            logger.info("Using regular chat mode (legacy execution)")
        else:
            # Connect via SSE for MCP client mode
            additional_tool = [run_new_flow]
            if self.sse_available:
                try:
                    self._connection = sse_client(self.sse_url)
                    read, write = await self._connection.__aenter__()

                    self.session = ClientSession(read, write)
                    await self.session.__aenter__()
                    await self.session.initialize()

                    # Load tools and create agent
                    self.tools = await load_mcp_tools(self.session)
                    self.tools.extend(additional_tool)
                    logger.debug("Loaded tools, {}".format(len(self.tools)))
                    model = llm_manager.get_model(settings.agent.planner.model)
                    self.agent = load_prompt_chat("./prompts/pmt.jinja2") | model.bind_tools(self.tools)
                    logger.info("MCP client mode initialized successfully")
                except Exception as e:
                    logger.error(f"Failed to initialize MCP client: {e}")
                    # Fallback to tools-only mode
                    self.tools = additional_tool
                    model = llm_manager.get_model(settings.agent.planner.model)
                    self.agent = load_prompt_chat("./prompts/pmt.jinja2") | model.bind_tools(self.tools)
                    logger.info("Initialized with basic tools only due to MCP connection failure")
            else:
                self.tools = additional_tool
                logger.debug("Loaded tools, {}".format(len(self.tools)))
                model = llm_manager.get_model(settings.agent.planner.model)
                self.agent = load_prompt_chat("./prompts/pmt.jinja2") | model.bind_tools(self.tools)
                logger.info("Initialized without MCP connection")

        self._is_setup = True

    def _is_session_valid(self) -> bool:
        """Check if the MCP session is still valid"""
        if not self.session:
            return False

        try:
            # Check if the session's streams are still open
            if hasattr(self.session, '_write_stream') and hasattr(self.session._write_stream, '_state'):
                return self.session._write_stream._state.open_send_channels > 0
        except Exception:
            pass

        return False

    async def execute_tool(self, tool_call: ToolCall):
        """Execute a tool call with proper session validation"""
        if not self._is_setup:
            raise RuntimeError("Agent not setup. Call setup() first.")

        # Check if we need to reconnect for MCP tools
        if not self.use_regular_chat and not self._is_session_valid():
            logger.warning("MCP session is invalid, attempting to reconnect...")
            try:
                await self.setup()
            except Exception as e:
                logger.error(f"Failed to reconnect MCP session: {e}")
                raise RuntimeError("Cannot execute tool: MCP session is closed and reconnection failed")

        # Find and execute the tool
        tool_name = tool_call.get("name")
        tool_args = tool_call.get("args", {})

        for tool_i in self.tools:
            if tool_i.name == tool_name:
                try:
                    return await tool_i.ainvoke(tool_args)
                except Exception as e:
                    logger.error(f"Error executing tool {tool_name}: {e}")
                    # If it's a connection error and we're using MCP, try to reconnect once
                    if not self.use_regular_chat and "ClosedResourceError" in str(type(e)):
                        logger.info("Attempting to reconnect due to closed resource error...")
                        await self.setup()
                        # Retry the tool execution with fresh session
                        for fresh_tool in self.tools:
                            if fresh_tool.name == tool_name:
                                return await fresh_tool.ainvoke(tool_args)
                    raise e

        logger.error(f"Tool {tool_name} not found in available tools")
        return None

    async def invoke(self, chat_messages: List[BaseMessage]):
        """Invoke the agent with a message"""
        if not self._is_setup:
            raise RuntimeError("Agent not setup. Call setup() first.")

        if self.use_regular_chat:
            # Use regular run method logic
            return await self._run_regular(chat_messages)
        else:
            # Validate session before invoking
            if not self._is_session_valid():
                logger.warning("MCP session invalid during invoke, reconnecting...")
                await self.setup()

            if not self.agent:
                raise RuntimeError("Agent not setup properly.")

            try:
                return await self.agent.ainvoke(
                    {
                        "conversation": self.map_chat_messages(chat_messages),
                    }
                )
            except Exception as e:
                if "ClosedResourceError" in str(type(e)):
                    logger.warning("Connection closed during invoke, attempting reconnect...")
                    await self.setup()
                    return await self.agent.ainvoke(
                        {
                            "conversation": self.map_chat_messages(chat_messages),
                        }
                    )
                raise e

    def map_chat_messages(self, chat_messages: List[BaseMessage]):
        """
        Process chat messages and return tuples of (role, content).
        Handles HumanMessage, AIMessage, and ToolMessage types properly.
        """
        result = []

        for msg in chat_messages:
            # Determine the role
            if msg.type == "human":
                role = 'human'
            elif msg.type == "ai":
                role = 'ai'
            elif msg.type == "tool":
                role = 'tool'
            else:
                logger.debug(f"Unknown message type: {msg}")
                role = 'unknown'

            # Extract content based on message type and available attributes
            content = ""

            if hasattr(msg, 'content') and msg.content:
                content = msg.content
            elif hasattr(msg, 'tool_calls') and msg.tool_calls:
                # Handle tool calls - could be a list of tool call objects
                if isinstance(msg.tool_calls, list):
                    content = [call for call in msg.tool_calls]
                else:
                    content = msg.tool_calls
            elif isinstance(msg, ToolMessage):
                # For ToolMessage, might have different attribute names
                if hasattr(msg, 'content') and msg.content:
                    content = msg.content
                elif hasattr(msg, 'result'):
                    content = msg.result

            result.append((role, content))

        logger.debug(f"Mapped chat messages: {result}")
        return result

    async def _run_regular(self, chat_messages: List[BaseMessage]) -> BaseMessage:
        """Regular run method implementation"""
        if not self.chain:
            raise RuntimeError("Chain not initialized for regular mode.")

        res = await self.chain.ainvoke(
            {
                "conversation": self.map_chat_messages(chat_messages),
                "variables_history": var_manager.get_variables_summary(last_n=10),
            }
        )
        return res

    async def _run_mcp_client(self, chat_messages: List[BaseMessage]):
        """MCP client run method implementation"""
        return await self.invoke(chat_messages)

    async def run(self, chat_messages: List[BaseMessage]) -> BaseMessage:
        """Public run method that delegates based on environment variable"""
        if not self._is_setup:
            await self.setup()

        if self.use_regular_chat:
            return await self._run_regular(chat_messages)
        else:
            return await self._run_mcp_client(chat_messages)

    async def cleanup(self):
        """Cleanup connections"""
        logger.debug("Cleaning up ChatAgent connections...")

        try:
            if not self.use_regular_chat:
                # Only cleanup MCP client connections
                if self.session:
                    try:
                        await self.session.__aexit__(None, None, None)
                    except Exception as e:
                        logger.debug(f"Error during session cleanup: {e}")
                    finally:
                        self.session = None

                if self._connection:
                    try:
                        await self._connection.__aexit__(None, None, None)
                    except Exception as e:
                        logger.debug(f"Error during connection cleanup: {e}")
                    finally:
                        self._connection = None

            # Reset state
            self.tools = None
            self.agent = None
            self._is_setup = False
            logger.debug("ChatAgent cleanup completed")

        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            # Force reset even if cleanup fails
            self.session = None
            self._connection = None
            self.tools = None
            self.agent = None
            self._is_setup = False
