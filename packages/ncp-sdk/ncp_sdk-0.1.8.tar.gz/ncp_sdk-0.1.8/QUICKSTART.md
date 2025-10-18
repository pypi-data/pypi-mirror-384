# NCP SDK Quick Start (v0.2.0)

**New SDK aligned with NCP Platform v2**

This guide shows you how to build and deploy AI agents using the updated NCP SDK.

---

## Installation

```bash
pip install ncp-sdk
```

---

## Core Concepts

### 1. Tools

Tools are Python functions decorated with `@tool` that agents can call:

```python
from ncp import tool

@tool
def add(a: float, b: float) -> float:
    """Add two numbers together."""
    return a + b

@tool
async def fetch_data(url: str) -> dict:
    """Fetch data from a URL (async tools supported)."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.json()
```

**Key Points:**
- Use type hints for parameters (enables IDE autocomplete)
- Docstring is required (becomes tool description)
- Both sync and async functions supported
- Return value is automatically serialized

### 2. Agents

Agents combine tools with instructions and configuration:

```python
from ncp import Agent, LLMConfig

agent = Agent(
    name="MathBot",
    description="An AI assistant that can perform calculations",
    instructions="You are a helpful math assistant. Be accurate and concise.",
    tools=[add, multiply],
    llm_config=LLMConfig(temperature=0.7, max_tokens=1500)
)
```

### 3. MCP Integration

Connect to external MCP servers for additional capabilities:

```python
from ncp import MCPConfig

agent = Agent(
    name="DataAgent",
    description="Agent with web access",
    instructions="You can fetch and analyze web data.",
    tools=[calculate],
    mcp_servers=[
        # stdio transport - local MCP server
        MCPConfig.stdio(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-fetch"]
        ),
        # SSE transport - remote MCP server
        MCPConfig.sse(
            url="https://api.example.com/mcp",
            headers={"Authorization": "Bearer token"}
        ),
    ]
)
```

---

## Complete Example

```python
from ncp import Agent, tool, LLMConfig, MCPConfig

# Define tools
@tool
def analyze_data(data: list) -> dict:
    """Analyze a list of numbers."""
    return {
        "count": len(data),
        "sum": sum(data),
        "average": sum(data) / len(data) if data else 0
    }

# Create agent
agent = Agent(
    name="DataAnalyst",
    description="AI data analyst with web access",
    instructions="""
    You are a data analyst assistant.
    - Use analyze_data for statistical analysis
    - Use MCP fetch tools to retrieve web data
    - Provide clear, data-driven insights
    """,
    tools=[analyze_data],
    mcp_servers=[
        MCPConfig.stdio(
            command="npx",
            args=["-y", "@modelcontextprotocol/server-fetch"]
        )
    ],
    llm_config=LLMConfig(
        temperature=0.5,  # More deterministic
        max_tokens=2000
    )
)
```

---

## Key Changes from v0.1.x

### 1. **Tools are now Tool instances**

**Before (v0.1.x):**
```python
@tool
def add(a: float, b: float) -> float:
    """Add numbers."""
    return a + b

# Tool was just a decorated function
```

**Now (v0.2.0):**
```python
@tool
def add(a: float, b: float) -> float:
    """Add numbers."""
    return a + b

# Tool decorator creates a Tool instance
# Type: Tool (not Callable)
# Has methods: .get_schema(), .name, .description
```

### 2. **MCPConfig supports full platform features**

**Before:**
```python
MCPConfig(transport_type="stdio", command="server-fetch")
```

**Now:**
```python
# More options for stdio
MCPConfig.stdio(
    command="npx",
    args=["-y", "@modelcontextprotocol/server-fetch"],
    env={"DEBUG": "1"},
    cwd="/path/to/dir"
)

# Convenience methods
MCPConfig.sse(url="...", headers={...})
MCPConfig.streamable_http(url="...")
```

### 3. **Agent validation is stricter**

- Tools must be Tool instances (created by @tool decorator)
- All tools must have docstrings
- MCPConfig validation happens at creation time

---

## Type Support

The SDK provides full type hints for IDE autocomplete:

```python
from ncp import Agent, Tool, LLMConfig, MCPConfig, TransportType

# Your IDE will autocomplete all properties and methods
agent: Agent = Agent(...)
tool: Tool = add
config: LLMConfig = LLMConfig(...)
mcp: MCPConfig = MCPConfig.stdio(...)
transport: TransportType = "stdio"  # Literal type
```

---

## Deployment

```bash
# Package your agent
ncp package .

# Deploy to platform
ncp deploy agent.ncp

# Test interactively
ncp playground
```

---

## Examples

Check the `examples/` directory:
- `simple_agent.py` - Basic agent with local tools
- `agent_with_mcp.py` - Agent with MCP server integration

---

## Migration from v0.1.x

1. **Update imports** - Same imports, but Tool is now exported
2. **No code changes needed** - @tool decorator works the same way
3. **MCPConfig** - Update to use new constructor or convenience methods
4. **Test thoroughly** - Validation is stricter, catch errors early

---

## What's NOT in the SDK

The SDK is for **defining** agents, not running them locally. These are platform-only:

- ❌ `AgentExecutor` - Executes agents (platform only)
- ❌ `LLMClient` - Calls LLM APIs (platform only)
- ❌ `MCPClient` - Connects to MCP servers (platform only)

Agents run on the NCP platform, not locally. The SDK just defines them!

---

## Next Steps

1. Read the full [README.md](README.md) for detailed documentation
2. Check [examples/](examples/) for more examples
3. See [DEVELOPMENT.md](DEVELOPMENT.md) for SDK development info

---

## Support

- Issues: https://github.com/your-org/ncp-sdk/issues
- Docs: https://docs.ncp.example.com
