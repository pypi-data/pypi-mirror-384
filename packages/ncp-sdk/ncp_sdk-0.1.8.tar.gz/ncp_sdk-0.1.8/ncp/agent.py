"""Agent definition for NCP platform deployment.

Agents combine instructions, tools, and configuration to create AI assistants.
"""

from dataclasses import dataclass, field
from typing import List, Optional

from .mcp_config import MCPConfig
from .model_config import LLMConfig
from .tool import Tool


@dataclass
class Agent:
    """An AI agent definition for deployment on the NCP platform.

    Agents combine instructions, tools, and LLM configuration to create AI assistants
    that can be deployed and executed on the NCP platform.

    Attributes:
        name: Agent name (must be unique within project)
        description: Brief description of agent capabilities
        instructions: System instructions defining agent behavior
        tools: List of Tool instances (created with @tool decorator)
        connectors: List of data connector names (resolved by platform)
        mcp_servers: List of MCP server configurations for external tools
        llm_config: Optional LLM configuration (uses platform defaults if not specified)

    Examples:
        Basic agent with local tools:

        >>> from ncp import Agent, tool, LLMConfig
        >>>
        >>> @tool
        ... def get_weather(location: str) -> dict:
        ...     '''Get weather for a location.'''
        ...     return {"temperature": 22, "condition": "sunny"}
        >>>
        >>> agent = Agent(
        ...     name="WeatherBot",
        ...     description="Provides weather information",
        ...     instructions="You are a helpful weather assistant. Be concise.",
        ...     tools=[get_weather],
        ...     llm_config=LLMConfig(temperature=0.7, max_tokens=1500)
        ... )

        Agent with MCP servers:

        >>> from ncp import MCPConfig
        >>>
        >>> agent = Agent(
        ...     name="FileAgent",
        ...     description="Agent with file system access",
        ...     instructions="Help users manage files and directories.",
        ...     mcp_servers=[
        ...         MCPConfig.stdio(
        ...             command="mcp-server-filesystem",
        ...             args=["/data"]
        ...         )
        ...     ]
        ... )

        Agent with both local tools and MCP servers:

        >>> @tool
        ... def calculate(expression: str) -> float:
        ...     '''Evaluate a mathematical expression.'''
        ...     return eval(expression)
        >>>
        >>> agent = Agent(
        ...     name="MultiAgent",
        ...     description="Agent with local tools and external services",
        ...     instructions="You can calculate math and fetch web content.",
        ...     tools=[calculate],
        ...     mcp_servers=[
        ...         MCPConfig.stdio(
        ...             command="npx",
        ...             args=["-y", "@modelcontextprotocol/server-fetch"]
        ...         )
        ...     ]
        ... )
    """

    name: str
    description: str
    instructions: str
    tools: List[Tool] = field(default_factory=list)
    connectors: List[str] = field(default_factory=list)
    mcp_servers: List[MCPConfig] = field(default_factory=list)
    llm_config: Optional[LLMConfig] = None

    def __post_init__(self):
        """Validate agent configuration."""
        if not self.name or not self.name.strip():
            raise ValueError("Agent name is required")
        if not self.description or not self.description.strip():
            raise ValueError("Agent description is required")
        if not self.instructions or not self.instructions.strip():
            raise ValueError("Agent instructions are required")

        # Validate that tools are Tool instances
        for i, tool in enumerate(self.tools):
            if not isinstance(tool, Tool):
                raise ValueError(
                    f"Tool at index {i} is not a Tool instance. "
                    f"Make sure to use the @tool decorator on your functions."
                )

        # Validate MCP configs
        for i, mcp_config in enumerate(self.mcp_servers):
            if not isinstance(mcp_config, MCPConfig):
                raise ValueError(
                    f"MCP server at index {i} is not an MCPConfig instance."
                )

    def add_tool(self, tool: Tool) -> None:
        """Add a tool to the agent.

        Args:
            tool: Tool instance (created with @tool decorator)

        Raises:
            ValueError: If tool is not a Tool instance

        Example:
            >>> @tool
            ... def ping(ip: str) -> bool:
            ...     '''Ping an IP address.'''
            ...     return True
            >>>
            >>> agent = Agent(name="Net", description="Network agent", instructions="...")
            >>> agent.add_tool(ping)
        """
        if not isinstance(tool, Tool):
            raise ValueError(
                "tool must be a Tool instance. Use @tool decorator on your function."
            )
        self.tools.append(tool)

    def add_mcp_server(self, server_config: MCPConfig) -> None:
        """Add an MCP server configuration.

        Args:
            server_config: MCP server configuration

        Example:
            >>> config = MCPConfig.sse(url="https://api.example.com/mcp")
            >>> agent.add_mcp_server(config)
        """
        if not isinstance(server_config, MCPConfig):
            raise ValueError("server_config must be an MCPConfig instance")
        self.mcp_servers.append(server_config)

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"Agent(name='{self.name}', "
            f"tools={len(self.tools)}, "
            f"connectors={len(self.connectors)}, "
            f"mcp_servers={len(self.mcp_servers)})"
        )
