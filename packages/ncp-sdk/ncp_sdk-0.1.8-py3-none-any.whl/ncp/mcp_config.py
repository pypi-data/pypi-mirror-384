"""Model Context Protocol (MCP) configuration for external tool servers.

MCP enables agents to connect to external services and data sources.
"""

from dataclasses import dataclass
from typing import Dict, List, Literal, Optional

TransportType = Literal["stdio", "sse", "streamable-http"]


@dataclass
class MCPConfig:
    """Configuration for connecting to an MCP server.

    MCP servers provide external tools to agents via different transport mechanisms:

    - **stdio**: Launch a local process and communicate via stdin/stdout
    - **sse**: Connect to a Server-Sent Events endpoint (URL-based)
    - **streamable-http**: Connect via streaming HTTP (URL-based)

    Attributes:
        transport_type: Type of transport to use
        command: Command to execute (stdio only)
        args: Command arguments (stdio only)
        env: Environment variables for the process (stdio only)
        cwd: Working directory (stdio only)
        url: Server URL (sse/streamable-http only)
        headers: HTTP headers (sse/streamable-http only)
        timeout: Connection timeout in seconds

    Examples:
        stdio transport (local MCP server):

        >>> config = MCPConfig(
        ...     transport_type="stdio",
        ...     command="npx",
        ...     args=["-y", "@modelcontextprotocol/server-fetch"]
        ... )

        >>> config = MCPConfig(
        ...     transport_type="stdio",
        ...     command="mcp-server-filesystem",
        ...     args=["/path/to/data"],
        ...     env={"LOG_LEVEL": "debug"}
        ... )

        SSE transport (remote MCP server):

        >>> config = MCPConfig(
        ...     transport_type="sse",
        ...     url="https://api.example.com/mcp"
        ... )

        >>> config = MCPConfig(
        ...     transport_type="sse",
        ...     url="https://api.example.com/mcp",
        ...     headers={"Authorization": "Bearer token123"}
        ... )

        Streamable HTTP transport:

        >>> config = MCPConfig(
        ...     transport_type="streamable-http",
        ...     url="https://streaming-api.example.com/mcp"
        ... )
    """

    transport_type: TransportType
    command: Optional[str] = None
    args: Optional[List[str]] = None
    env: Optional[Dict[str, str]] = None
    cwd: Optional[str] = None
    url: Optional[str] = None
    headers: Optional[Dict[str, str]] = None
    timeout: float = 30.0

    def __post_init__(self):
        """Validate configuration based on transport type."""
        if self.timeout <= 0:
            raise ValueError("Timeout must be positive")

        if self.transport_type == "stdio":
            if not self.command:
                raise ValueError("command is required for stdio transport")
            # Initialize optional lists/dicts
            if self.args is None:
                self.args = []
            if self.env is None:
                self.env = {}
        elif self.transport_type in ["sse", "streamable-http"]:
            if not self.url:
                raise ValueError(f"url is required for {self.transport_type} transport")
            # Initialize optional dict
            if self.headers is None:
                self.headers = {}

    @classmethod
    def stdio(
        cls,
        command: str,
        args: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None,
        cwd: Optional[str] = None,
        timeout: float = 30.0,
    ) -> "MCPConfig":
        """Create stdio transport configuration (convenience method).

        Args:
            command: Command to execute
            args: Command arguments
            env: Environment variables
            cwd: Working directory
            timeout: Connection timeout

        Returns:
            MCPConfig for stdio transport

        Example:
            >>> config = MCPConfig.stdio(
            ...     command="mcp-server-filesystem",
            ...     args=["/data"],
            ...     env={"DEBUG": "1"}
            ... )
        """
        return cls(
            transport_type="stdio",
            command=command,
            args=args or [],
            env=env,
            cwd=cwd,
            timeout=timeout,
        )

    @classmethod
    def sse(
        cls,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 30.0,
    ) -> "MCPConfig":
        """Create SSE transport configuration (convenience method).

        Args:
            url: Server-Sent Events endpoint URL
            headers: HTTP headers
            timeout: Connection timeout

        Returns:
            MCPConfig for SSE transport

        Example:
            >>> config = MCPConfig.sse(
            ...     url="https://api.example.com/mcp",
            ...     headers={"Authorization": "Bearer token"}
            ... )
        """
        return cls(
            transport_type="sse",
            url=url,
            headers=headers,
            timeout=timeout,
        )

    @classmethod
    def streamable_http(
        cls,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        timeout: float = 30.0,
    ) -> "MCPConfig":
        """Create streamable HTTP transport configuration (convenience method).

        Args:
            url: HTTP endpoint URL
            headers: HTTP headers
            timeout: Connection timeout

        Returns:
            MCPConfig for streamable HTTP transport

        Example:
            >>> config = MCPConfig.streamable_http(
            ...     url="https://streaming.example.com/mcp"
            ... )
        """
        return cls(
            transport_type="streamable-http",
            url=url,
            headers=headers,
            timeout=timeout,
        )

    def __repr__(self) -> str:
        """String representation."""
        if self.transport_type == "stdio":
            return f"MCPConfig(stdio, command='{self.command}')"
        else:
            return f"MCPConfig({self.transport_type}, url='{self.url}')"
