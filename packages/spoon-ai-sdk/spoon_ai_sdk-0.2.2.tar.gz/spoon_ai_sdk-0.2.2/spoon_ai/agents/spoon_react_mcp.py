import asyncio
from spoon_ai.agents.spoon_react import SpoonReactAI
from spoon_ai.tools.tool_manager import ToolManager
from pydantic import Field
import logging

logger = logging.getLogger(__name__)

class SpoonReactMCP(SpoonReactAI):
    name: str = "spoon_react_mcp"
    description: str = "A smart ai agent in neo blockchain with mcp"
    avaliable_tools: ToolManager = Field(default_factory=lambda: ToolManager([]))

    def __init__(self, tools=None, **kwargs):
        # Handle tools parameter
        if tools is not None:
            from spoon_ai.tools.tool_manager import ToolManager
            kwargs['avaliable_tools'] = ToolManager(tools)

        # Initialize SpoonReactAI
        super().__init__(**kwargs)
        logger.info(f"Initialized SpoonReactMCP agent: {self.name}")

    async def list_mcp_tools(self):
        """Return MCP tools from avaliable_tools manager"""
        # Import here to avoid circular imports
        from mcp.types import Tool as MCPTool

        # Return MCP tools that are available in the tool manager
        # Create proper MCPTool objects that match the expected interface
        mcp_tools = []

        # Pre-load parameters for all MCP tools concurrently
        async def load_tool_params(tool):
            if hasattr(tool, 'ensure_parameters_loaded'):
                try:
                    # Derive a sensible timeout from the tool's own connection timeout
                    base_timeout = float(getattr(tool, '_connection_timeout', 30))
                    preload_timeout = max(15.0, min(base_timeout + 10.0, 60.0))
                    await asyncio.wait_for(tool.ensure_parameters_loaded(), timeout=preload_timeout)
                except asyncio.TimeoutError:
                    logger.warning(f"Timeout loading parameters for tool: {tool.name}")
                except Exception as e:
                    logger.warning(f"Failed loading parameters for tool {tool.name}: {e}")
            return tool

        mcp_tool_instances = [tool for tool in self.avaliable_tools.tool_map.values() if hasattr(tool, 'mcp_config')]
        loaded_tools = await asyncio.gather(*[load_tool_params(tool) for tool in mcp_tool_instances])

        # Some MCP tools may have updated their name after fetching server schema
        # Ensure the ToolManager reflects any dynamic renames
        try:
            if hasattr(self, 'avaliable_tools') and hasattr(self.avaliable_tools, 'reindex'):
                self.avaliable_tools.reindex()
        except Exception:
            pass

        for tool in loaded_tools:
            # Create proper MCPTool instance for the tool system
            mcp_tool = MCPTool(
                name=tool.name,
                description=tool.description,
                inputSchema=tool.parameters if tool.parameters else {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            )
            mcp_tools.append(mcp_tool)

        if mcp_tools:
            logger.info(f"Found {len(mcp_tools)} MCP tools: {[t.name for t in mcp_tools]}")
        else:
            logger.info("No MCP tools found in available tools")

        return mcp_tools
