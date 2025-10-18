"""NCP SDK - Build and deploy AI agents on the Network Copilot Platform.

This SDK provides tools for defining agents locally that can be deployed
to the NCP platform for execution.

Key Components:
    - Agent: Define an AI agent with tools and configuration
    - tool: Decorator to create tools from Python functions
    - LLMConfig: Configure LLM generation parameters
    - MCPConfig: Connect to external MCP servers
    - TransportType: Type hint for MCP transport types
    - Metrics: Query network metrics and device data (platform runtime)

Example:
    >>> from ncp import Agent, tool, LLMConfig, MCPConfig, Metrics
    >>>
    >>> @tool
    ... def greet(name: str) -> str:
    ...     '''Greet someone by name.'''
    ...     return f"Hello, {name}!"
    >>>
    >>> @tool
    ... def check_cpu(hostname: str) -> dict:
    ...     '''Check CPU utilization for a device.'''
    ...     metrics = Metrics()
    ...     cpu = metrics.get_cpu_utilization(hostname=hostname, hours=1)
    ...     return cpu[0] if cpu else {"error": "No data"}
    >>>
    >>> agent = Agent(
    ...     name="NetworkMonitor",
    ...     description="Monitor network devices",
    ...     instructions="You are a network monitoring assistant.",
    ...     tools=[greet, check_cpu],
    ...     connectors=["splunk-prod"],  # Reference data connectors by name
    ...     llm_config=LLMConfig(temperature=0.8)
    ... )
"""

from .agent import Agent
from .data import Metrics
from .mcp_config import MCPConfig, TransportType
from .model_config import LLMConfig
from .tool import Tool, tool

__version__ = "0.1.8"

__all__ = [
    # Core classes
    "Agent",
    "Tool",
    "Metrics",
    # Decorators
    "tool",
    # Configuration
    "LLMConfig",
    "MCPConfig",
    "TransportType",
]
