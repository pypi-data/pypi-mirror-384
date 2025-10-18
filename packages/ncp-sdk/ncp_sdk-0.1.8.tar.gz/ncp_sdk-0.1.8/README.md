# NCP SDK User Guide

**Comprehensive Guide to Network Copilot SDK for AI Agent Development**

The NCP SDK enables developers to create sophisticated AI agents and deploy them on the NCP platform. This guide covers everything from basic setup to advanced features like background agents, memory systems, and MCP integrations.

---

## Table of Contents

1. [Getting Started](#getting-started)
   - [Prerequisites](#prerequisites)
   - [Installation](#installation)
   - [Quick Verification](#quick-verification)

2. [Core Concepts](#core-concepts)
   - [Tools](#tools)
   - [Agents](#agents)
   - [Project Structure](#project-structure)

3. [Advanced Features](#advanced-features)
   - [MCP Integration](#mcp-integration)
   - [Data Connectors](#data-connectors)

4. [Dependency Management](#dependency-management)
   - [Python Dependencies](#python-dependencies)
   - [System Dependencies](#system-dependencies)

5. [SDK Workflow](#sdk-workflow)
   - [Project Initialization](#project-initialization)
   - [Development](#development)
   - [Validation](#validation)
   - [Packaging](#packaging)
   - [Deployment](#deployment)

---

## Getting Started

### Prerequisites

#### Python Version

- **Python 3.8 or higher** is required
- Python 3.9+ recommended for better type support

#### Platform-Specific Setup

##### macOS

```bash
# Install Python via Homebrew (recommended)
brew install python@3.11

# Or use pyenv for version management
brew install pyenv
pyenv install 3.11.0
pyenv global 3.11.0
```

##### Linux (Ubuntu/Debian)

```bash
# Update package list
sudo apt update

# Install Python and pip
sudo apt install python3.11 python3.11-pip python3.11-venv

# Verify installation
python3.11 --version
```

##### Windows

1. Download Python from [python.org](https://python.org)
2. Run installer and **check "Add Python to PATH"**
3. Open Command Prompt or PowerShell to verify:

```cmd
python --version
pip --version
```

#### Virtual Environment

```bash
# Already included with Python 3.3+
python -m venv --help
```

### Installation

#### Step 1: Create Virtual Environment

**Using venv:**

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate

# On Windows:
.venv\Scripts\activate

# Verify activation (should show .venv in prompt)
which python
```

#### Step 2: Install NCP SDK

```bash
# Install from PyPI
pip install ncp-sdk
```

#### Step 3: Verify Installation

```bash
# Check if NCP CLI is available
ncp --help

# Check Python import
python -c "from ncp import Agent, tool; print('NCP SDK installed successfully!')"
```

### Quick Verification

Create a simple test to ensure everything works:

```python
# test_ncp.py
from ncp import Agent, tool

@tool
def hello_world(name: str = "World") -> str:
    """Say hello to someone."""
    return f"Hello, {name}!"

# This should work without errors
agent = Agent(
    name="TestAgent",
    description="A simple test agent",
    instructions="You are a test agent. Be helpful.",
    tools=[hello_world]
)

print("✅ NCP SDK is working correctly!")
```

Run the test:

```bash
python test_ncp.py
```

---

## Core Concepts

### Tools

Tools are the building blocks that give your agents capabilities. They're Python functions decorated with `@tool` that agents can call to perform actions.

#### Basic Tool Creation

```python
from ncp import tool

@tool
def ping_device(ip_address: str, timeout: int = 5) -> dict:
    """Ping a network device to check connectivity.

    Args:
        ip_address: Target IP address to ping
        timeout: Timeout in seconds (default: 5)

    Returns:
        Dictionary with ping results and connectivity status
    """
    import subprocess
    import time

    start_time = time.time()
    try:
        result = subprocess.run(['ping', '-c', '1', '-W', str(timeout), ip_address],
                              capture_output=True, text=True)
        response_time = time.time() - start_time

        return {
            "ip_address": ip_address,
            "reachable": result.returncode == 0,
            "response_time_ms": round(response_time * 1000, 2),
            "raw_output": result.stdout.strip() if result.returncode == 0 else result.stderr.strip()
        }
    except Exception as e:
        return {
            "ip_address": ip_address,
            "reachable": False,
            "error": str(e)
        }
```

#### Async Tools

For operations that might take time (API calls, file operations):

```python
import asyncio
import aiohttp

@tool
async def backup_device_config(device_ip: str, backup_type: str = "running") -> dict:
    """Backup device configuration asynchronously.

    Args:
        device_ip: IP address of the network device
        backup_type: Type of config to backup ("running" or "startup")

    Returns:
        Backup result with configuration data
    """
    import asyncio
    import aiofiles
    from datetime import datetime

    # Simulate SSH connection and config retrieval
    await asyncio.sleep(2)  # Simulate network delay

    try:
        # Simulate retrieving configuration
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"config_{device_ip}_{backup_type}_{timestamp}.cfg"

        # Mock configuration data
        config_data = f"""!
! Configuration backup from {device_ip}
! Type: {backup_type}
! Date: {timestamp}
!
version 15.1
service timestamps debug datetime msec
service timestamps log datetime msec
!
hostname Device-{device_ip.replace('.', '-')}
!
interface GigabitEthernet0/1
 ip address {device_ip} 255.255.255.0
 no shutdown
!
end
"""

        # Simulate saving to file
        async with aiofiles.open(filename, 'w') as f:
            await f.write(config_data)

        return {
            "success": True,
            "device_ip": device_ip,
            "backup_type": backup_type,
            "filename": filename,
            "size_bytes": len(config_data),
            "timestamp": timestamp
        }
    except Exception as e:
        return {
            "success": False,
            "device_ip": device_ip,
            "error": str(e)
        }
```

#### Error Handling in Tools

```python
from ncp import tool
import logging

@tool
def get_interface_status(device_ip: str, interface_name: str) -> dict:
    """Get network interface status with proper error handling.

    Args:
        device_ip: IP address of the network device
        interface_name: Name of the interface (e.g., "GigabitEthernet0/1")

    Returns:
        Interface status information

    Raises:
        ConnectionError: If device is unreachable
        ValueError: If interface doesn't exist
    """
    import logging

    try:
        # Validate interface name format
        if not interface_name or "/" not in interface_name:
            raise ValueError(f"Invalid interface name: {interface_name}")

        # Mock interface status check
        logging.info(f"Checking interface {interface_name} on {device_ip}")

        # Simulate different interface states
        if "0/1" in interface_name:
            status = {
                "device_ip": device_ip,
                "interface": interface_name,
                "admin_status": "up",
                "operational_status": "up",
                "speed": "1000 Mbps",
                "duplex": "full",
                "mtu": 1500,
                "input_errors": 0,
                "output_errors": 0
            }
        else:
            status = {
                "device_ip": device_ip,
                "interface": interface_name,
                "admin_status": "down",
                "operational_status": "down",
                "speed": "unknown",
                "duplex": "unknown",
                "mtu": 1500,
                "input_errors": 0,
                "output_errors": 0
            }

        logging.info(f"Interface status retrieved: {status}")
        return status

    except ValueError as e:
        logging.error(f"Interface validation error: {e}")
        raise ValueError(f"Interface check failed: {str(e)}")
    except Exception as e:
        logging.error(f"Unexpected error checking interface: {e}")
        raise ConnectionError(f"Failed to connect to device {device_ip}: {str(e)}")
```

#### Tool Documentation Best Practices

```python
@tool
def search_documents(
    query: str,
    max_results: int = 10,
    include_metadata: bool = True
) -> List[dict]:
    """Search through documents using semantic search.

    This tool performs semantic search across all indexed documents
    and returns the most relevant results based on the query.

    Args:
        query: Search query string. Use natural language or keywords.
        max_results: Maximum number of results to return (1-100).
        include_metadata: Whether to include document metadata in results.

    Returns:
        List of dictionaries, each containing:
        - content: Document content excerpt
        - title: Document title
        - relevance_score: Similarity score (0.0-1.0)
        - metadata: Document metadata (if include_metadata=True)

    Examples:
        >>> search_documents("Python programming", max_results=5)
        [{"content": "...", "title": "...", "relevance_score": 0.92}]

        >>> search_documents("machine learning algorithms", include_metadata=False)
        [{"content": "...", "title": "...", "relevance_score": 0.87}]
    """
    # Implementation here
    pass
```

### Agents

Agents are AI entities that use tools to accomplish tasks. They combine language models with your custom tools to create powerful automation.

#### Basic Agent Configuration

```python
from ncp import Agent

agent = Agent(
    name="NetworkMonitorBot",
    description="AI assistant for network monitoring and diagnostics",
    instructions="""
    You are a network monitoring specialist. Your goal is to:

    1. Monitor network device health and connectivity
    2. Diagnose network issues using available tools
    3. Provide clear reports on network status
    4. Alert on any critical network problems

    Always verify device connectivity before performing other operations.
    """,
    tools=[ping_device, get_interface_status, backup_device_config]
)
```

#### LLMConfig Parameters

The `LLMConfig` class controls how the language model behaves:

````python
from ncp import LLMConfig

config = LLMConfig(
    model="llama-3.3-70b",           # Required: Model identifier
    temperature=0.7,               # 0.0-2.0: Randomness (0=deterministic, 2=very random)
    max_tokens=1500,               # Maximum tokens to generate
    top_p=1.0,                     # 0.0-1.0: Nucleus sampling
    frequency_penalty=0.0,         # -2.0-2.0: Reduce repetition
    presence_penalty=0.0           # -2.0-2.0: Encourage topic diversity
)

#### Agent Instructions Best Practices

Write clear, specific instructions:

```python
# Good: Specific and actionable
instructions = """
You are a Python code reviewer. For each code submission:

1. Check for syntax errors and common bugs
2. Verify PEP 8 style compliance
3. Look for security vulnerabilities
4. Suggest performance improvements
5. Rate the code from 1-10 with explanation

Format your response as:
- Issues Found: [list of issues]
- Suggestions: [list of improvements]
- Rating: X/10 - [brief explanation]

Be constructive and educational in your feedback.
"""

# Avoid: Vague instructions
instructions = "You help with code. Be helpful."
````

### Project Structure

Understanding the standard project layout helps organize your agents effectively:

```
my-agent-project/
├── ncp.toml              # Project configuration
├── requirements.txt           # Python dependencies
├── apt-requirements.txt       # System packages (optional)
├── agents/                    # Agent definitions
│   ├── __init__.py
│   ├── main_agent.py         # Primary agent
├── tools/                     # Custom tools
│   ├── __init__.py
│   ├── data_tools.py
```

---

## Advanced Features

### MCP Integration

Model Context Protocol (MCP) enables agents to connect to external services and data sources. The NCP SDK supports all MCP transport types.

#### Transport Types Overview

```python
from ncp import MCPConfig, TransportType

# Three transport types available:
# 1. stdio - Command-based servers
# 2. sse - Server-Sent Events (URL-based)
# 3. streamable-http - HTTP streaming
```

#### stdio Transport

For command-line based MCP servers (add the MCP server packages to your requirements.txt):

```python
from ncp import Agent, MCPConfig

# Basic stdio configuration
filesystem_server = MCPConfig(
    transport_type="stdio",
    command="mcp-server-filesystem /path/to/files"
)

# With arguments
database_server = MCPConfig(
    transport_type="stdio",
    command="python -m mcp_database_server --host localhost --port 5432"
)

# Agent with MCP servers
agent = Agent(
    name="FileAgent",
    description="Agent with filesystem access",
    instructions="Help users manage files and directories",
    mcp_servers=[filesystem_server, database_server]
)
```

#### SSE Transport

For URL-based MCP servers using Server-Sent Events:

```python
# SSE configuration
sse_server = MCPConfig(
    transport_type="sse",
    url="https://api.example.com/mcp"
)

# With authentication (handled by platform)
authenticated_server = MCPConfig(
    transport_type="sse",
    url="https://secure-api.example.com/mcp/stream"
)

agent = Agent(
    name="APIAgent",
    description="Agent with API access",
    instructions="Interact with external APIs through MCP",
    mcp_servers=[sse_server]
)
```

#### streamable-http Transport

For HTTP streaming MCP servers:

```python
# HTTP streaming configuration
http_server = MCPConfig(
    transport_type="streamable-http",
    url="https://streaming-api.example.com/mcp"
)

# Agent configuration
streaming_agent = Agent(
    name="StreamingAgent",
    description="Agent with streaming data access",
    instructions="Process real-time data streams",
    mcp_servers=[http_server]
)
```

#### Multiple MCP Servers

Agents can connect to multiple MCP servers:

```python
from ncp import Agent, MCPConfig

agent = Agent(
    name="MultiServiceAgent",
    description="Agent with multiple external services",
    instructions="""
    You have access to multiple services:
    - Filesystem for file operations
    - Database for data queries
    - API service for external data

    Use the appropriate service based on the user's request.
    """,
    mcp_servers=[
        MCPConfig(
            transport_type="stdio",
            command="mcp-server-filesystem /data"
        ),
        MCPConfig(
            transport_type="sse",
            url="https://database-api.example.com/mcp"
        ),
        MCPConfig(
            transport_type="streamable-http",
            url="https://external-api.example.com/stream"
        )
    ]
)
```

### Data Connectors

Data connectors allow agents to access external data sources (like Splunk, ServiceNow, etc.) that are configured in the NCP platform. Simply reference connectors by name - no credentials needed!

#### Using Data Connectors

Admins create and configure data connectors in the NCP UI with credentials. Developers just reference them by name:

```python
from ncp import Agent, tool

@tool
def analyze_logs(query: str) -> dict:
    """Analyze logs from Splunk."""
    # Your tool implementation
    # When agent runs on platform, it will have access to Splunk tools
    return {"status": "success"}

agent = Agent(
    name="LogAnalyzer",
    description="AI assistant for log analysis",
    instructions="""
    You are a log analysis expert with access to Splunk.
    Help users search logs, identify issues, and generate reports.
    """,
    tools=[analyze_logs],
    connectors=["splunk-prod"]  # Reference by name!
)
```

#### Multiple Connectors

Agents can access multiple data connectors:

```python
agent = Agent(
    name="MultiDataAgent",
    description="Agent with access to multiple data sources",
    instructions="You can query Splunk logs and ServiceNow tickets.",
    connectors=["splunk-prod", "servicenow-dev"]
)
```

#### Combining with Tools and MCP

Use all three tool types together:

```python
from ncp import Agent, tool, MCPConfig

@tool
def custom_analysis(data: dict) -> str:
    """Perform custom analysis on data."""
    return f"Analyzed {len(data)} items"

agent = Agent(
    name="ComprehensiveAgent",
    description="Agent with all tool types",
    instructions="You have access to local tools, data connectors, and external services.",
    tools=[custom_analysis],              # Local Python tools
    connectors=["splunk-prod"],           # Platform data connectors
    mcp_servers=[                          # External MCP servers
        MCPConfig.sse(url="https://api.example.com/mcp")
    ]
)
```

#### Available Connectors

Currently supported connector types:

- **Splunk**: Search and analyze logs
- **ServiceNow**: Query tickets and incidents

More connector types are being added regularly. Check with your platform admin for available connectors.

---

## Dependency Management

### Python Dependencies

#### requirements.txt

List all Python packages your agent needs:

```txt
pandas>=1.5.0
numpy>=1.21.0
requests>=2.28.0
```

#### Version Pinning Strategies

```txt
# Exact versions (most restrictive)
requests==2.28.2
pandas==1.5.3
```

### System Dependencies

#### apt-requirements.txt

Specify system packages needed by your agent:

```txt
# Basic utilities
curl
wget
git
```

#### Managing Dependencies in Development

```bash
# Create requirements.txt from current environment
pip freeze > requirements.txt

# Install from requirements.txt
pip install -r requirements.txt

# Install with specific index
pip install -r requirements.txt -i https://pypi.org/simple/

# Install in editable mode for development
pip install -e .

# Check for security vulnerabilities
pip install safety
safety check -r requirements.txt
```

---

## SDK Workflow

### Project Initialization

#### Creating a New Project

```bash
# Basic project initialization
ncp init my-agent-project

# Navigate to project directory
cd my-agent-project

# Project structure created:
# ├── ncp.toml
# ├── requirements.txt
# ├── apt-requirements.txt
# ├── agents/
# │   └── main_agent.py
# └── tools/
#     └── __init__.py
```

#### Post-Initialization Setup

```bash
# Set up Python virtual environment
cd my-agent-project

# Verify setup
ncp validate .
```

### Development

#### Development Best Practices

1. **Start Simple**: Begin with basic tools and gradually add complexity
2. **Test Locally**: Test tool logic before integrating with agents
3. **Use Type Hints**: Leverage Python type hints for better validation
4. **Document Everything**: Write clear docstrings for tools and agents
5. **Handle Errors**: Implement proper error handling in tools

### Packaging

#### Basic Packaging

```bash
# Package the current project
ncp package .

# Output: my-agent-project.ncp (created in current directory)

# Package with custom output name
ncp package . --output my-custom-agent.ncp

# Package to specific directory
ncp package . --output /path/to/output/agent.ncp
```

#### Packaging Best Practices

```bash
# Always validate before packaging
ncp validate . && ncp package .

# Use semantic versioning
ncp package . --version 1.0.0
```

### Deployment

#### Authentication

Before deploying, authenticate with your NCP platform to store credentials:

```bash
# Navigate to your project directory
cd my-agent-project

# Authenticate with the platform
ncp authenticate

# Or specify platform URL directly
ncp authenticate --platform https://ncp.example.com
```

This stores your credentials in `ncp.toml` so you don't need to pass `--platform` and `--api-key` flags with every command.

The authentication flow will:

1. Prompt for platform URL (if not provided)
2. Ask for username and password
3. Authenticate and receive an API key
4. Store credentials securely in your project's `ncp.toml`

**Note:** The `[platform]` section in `ncp.toml` is project-specific and should not be committed to version control. Add it to `.gitignore`:

```bash
# In your .gitignore
ncp.toml
```

Or use a separate `ncp.local.toml` for credentials (to be implemented).

#### Platform Deployment

Once authenticated, deploy your agent:

```bash
# Package your project
ncp package .

# Deploy using stored credentials
ncp deploy my-agent-project.ncp

# Or with explicit credentials (overrides stored ones)
ncp deploy my-agent-project.ncp --platform https://ncp.example.com --api-key your-key

# Update existing deployment
ncp deploy my-agent-project.ncp --update my-agent
```

#### Interactive Playground

Test your agent interactively, similar to `ollama run`:

```bash
# From your project directory (uses stored credentials)
ncp playground

# Specify an agent by name
ncp playground --agent my-agent

# Test a packaged agent
ncp playground --agent my-agent.ncp

# Override platform credentials
ncp playground --platform https://ncp.example.com --api-key your-key

```

**Playground Features:**

- **Interactive Chat**: Chat with your agent in real-time
- **Special Commands**:
  - `/help` - Show available commands
  - `/exit` - Exit playground
  - `/reset` - Reset conversation history
  - `/clear` - Clear screen
- **Live Testing**: Test your agent before full deployment
- **Conversation History**: Maintains context across messages

**Example Session:**

```
$ ncp playground
🎮 NCP Agent Playground

📁 Project: my-agent
🌐 Platform: https://ncp.example.com

────────────────────────────────────────────────────────────

💬 Interactive Chat Mode (Ctrl+C to exit)
   Type your message and press Enter to send

You> Hello! Can you help me analyze network devices?

Agent> Hello! I'd be happy to help you analyze network devices.
       I have access to tools for pinging devices, checking interface
       status, and backing up configurations. What would you like to do?

You> Check the status of 192.168.1.1

Agent> I'll check the status of 192.168.1.1 for you.
       [Using tool: ping_device]
       The device at 192.168.1.1 is reachable with a response time of
       12.5ms. Would you like me to check specific interfaces?

You> /exit
👋 Goodbye!
```

#### Post-Deployment Management

Manage deployed agents using stored credentials:

```bash
# Check deployment status (uses stored credentials)
ncp status --agent my-agent

# Remove agent
ncp remove --agent my-agent
```

All commands support `--platform` and `--api-key` flags to override stored credentials:

```bash
# Use different platform temporarily
ncp status --agent my-agent --platform https://staging.ncp.example.com --api-key staging-key
```

---
