"""Interactive playground command for testing agents."""

import click
import requests
import urllib3
import json
import asyncio
import websockets
import re
from pathlib import Path
from ..utils import get_platform_and_key, find_project_root

# Disable SSL warnings for localhost development
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


async def run_websocket_chat(
    agent: str, platform_url: str, api_key: str, show_tools: bool = False
):
    """Run WebSocket chat with agent.

    Args:
        agent: Agent name
        platform_url: Platform URL
        api_key: API key for authentication
        show_tools: Whether to show tool calls and results
    """
    # Convert HTTP URL to WebSocket URL
    ws_url = platform_url.replace("https://", "wss://").replace("http://", "ws://")
    ws_url = f"{ws_url}/api/v1/sdk_agents/playground/chat/ws"

    click.echo(f"🔌 Connecting to WebSocket")
    click.echo()

    conversation_id = None
    max_retries = 3
    retry_count = 0
    first_connection = True  # Track if this is the first connection
    pending_message = None  # Track message that needs response after reconnect

    # Disable SSL verification for development
    import ssl

    ssl_context = ssl.SSLContext()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    # Outer reconnection loop - handles connection failures transparently
    while retry_count < max_retries:
        try:
            # Enable keep-alive pings to prevent idle timeout
            # Pings are automatic and don't interfere with agent execution
            async with websockets.connect(
                ws_url,
                ssl=ssl_context,
                ping_interval=20,  # Send ping every 20 seconds
                ping_timeout=10,  # Consider dead if no pong in 10 seconds
            ) as websocket:
                # Reset retry count on successful connection
                retry_count = 0

                # Authenticate
                auth_message = {"type": "auth", "token": f"Bearer {api_key}"}
                await websocket.send(json.dumps(auth_message))

                # Wait for auth response
                auth_response = await websocket.recv()
                auth_data = json.loads(auth_response)

                if auth_data.get("type") == "error":
                    click.echo(
                        f"❌ Authentication failed: {auth_data.get('error')}", err=True
                    )
                    return

                if auth_data.get("type") == "auth" and auth_data.get("status") == "ok":
                    # Only show connection message on first connection, not on reconnects
                    if first_connection:
                        click.echo(f"✅ Connected as: {auth_data.get('username')}")
                        click.echo()
                        first_connection = False

                # Main chat loop
                while True:
                    # Check if we have a pending message from before disconnect
                    is_resend = False
                    if pending_message:
                        user_input = pending_message
                        pending_message = None
                        is_resend = True
                        # Don't prompt for input, just resend the message
                    else:
                        # Get user input
                        user_input = click.prompt("You", type=str, prompt_suffix="> ")

                        if not user_input.strip():
                            continue

                    # Handle special commands
                    if user_input.strip().lower() == "/exit":
                        click.echo("👋 Goodbye!")
                        return  # Exit completely
                    elif user_input.strip().lower() == "/help":
                        click.echo()
                        click.echo("Available commands:")
                        click.echo("  /help   - Show this help message")
                        click.echo("  /exit   - Exit playground")
                        click.echo("  /reset  - Reset conversation history")
                        click.echo("  /clear  - Clear screen")
                        click.echo()
                        continue
                    elif user_input.strip().lower() == "/reset":
                        conversation_id = None
                        click.echo("🔄 Conversation reset")
                        click.echo()
                        continue
                    elif user_input.strip().lower() == "/clear":
                        click.clear()
                        click.echo("🎮 NCP Agent Playground")
                        click.echo()
                        continue

                    # Send chat message
                    chat_message = {
                        "type": "chat",
                        "agent_name": agent,
                        "message": user_input,
                    }

                    # Only send conversation_history if we don't have a conversation_id
                    # If we have a conversation_id, the platform will load history from DB
                    if conversation_id:
                        chat_message["conversation_id"] = conversation_id
                    else:
                        chat_message["conversation_history"] = []

                    await websocket.send(json.dumps(chat_message))

                    # Track this message in case we need to resend after reconnect
                    pending_message = user_input

                    # Display response header (only if not a resend - already shown)
                    if not is_resend:
                        click.echo()
                        click.echo("Agent> ", nl=False)

                    # Receive and display streaming response
                    agent_response = ""
                    tool_calls = []

                    while True:
                        try:
                            response_data = await websocket.recv()
                            event = json.loads(response_data)
                            event_type = event.get("type")

                            if event_type == "text":
                                text_chunk = event.get("content", "")
                                agent_response += text_chunk

                                # Filter out Llama bracket notation (will be shown as formatted tool calls)
                                # Pattern matches: [func_name(args), func_name2(args), ...]
                                # Only if the entire chunk is ONLY the bracket notation
                                stripped = text_chunk.strip()
                                is_tool_call_notation = bool(
                                    re.match(
                                        r"^\[\w+\([^)]*\)(,\s*\w+\([^)]*\))*\]$",
                                        stripped,
                                    )
                                )

                                if not is_tool_call_notation:
                                    # Display normal text immediately for streaming
                                    click.echo(text_chunk, nl=False)

                            elif event_type == "tool_call":
                                tool_data = event.get("data", {})
                                tool_calls.append(tool_data)

                                if show_tools:
                                    # Clear the line and show tool call
                                    click.echo()  # New line

                                    # Show tool call details
                                    tool_name = tool_data.get("name", "unknown")
                                    tool_args = tool_data.get("arguments", {})

                                    # Format arguments nicely
                                    args_str = ", ".join(
                                        [f"{k}={repr(v)}" for k, v in tool_args.items()]
                                    )
                                    click.echo(f"🔧 {tool_name}({args_str})")

                            elif event_type == "tool_result":
                                if show_tools:
                                    # Show tool result
                                    result = event.get("tool_result")
                                    error = event.get("error")

                                    if error:
                                        click.echo(f"   ❌ Error: {error}")
                                    else:
                                        # Format result nicely
                                        result_str = (
                                            str(result) if result else "Success"
                                        )
                                        if len(result_str) > 100:
                                            result_str = result_str[:100] + "..."
                                        click.echo(f"   → {result_str}")

                            elif event_type == "conversation_id":
                                # Store conversation ID for subsequent messages
                                conversation_id = event.get("conversation_id")
                                # Platform will manage conversation history using this ID

                            elif event_type == "done":
                                # Execution complete
                                # SDK doesn't need the full history - platform manages it
                                pending_message = None  # Clear pending message - response received successfully
                                break

                            elif event_type == "error":
                                # Display error
                                click.echo()
                                error_msg = event.get("error", "Unknown error")
                                click.echo(f"\n❌ Error: {error_msg}", err=True)
                                pending_message = (
                                    None  # Clear pending message - don't retry errors
                                )
                                break

                        except json.JSONDecodeError as e:
                            click.echo(
                                f"\n❌ Failed to parse response: {str(e)}", err=True
                            )
                            pending_message = (
                                None  # Clear pending message - don't retry parse errors
                            )
                            break

                    # New line after response
                    click.echo()
                    click.echo()

        except (
            websockets.exceptions.ConnectionClosed,
            websockets.exceptions.WebSocketException,
        ) as e:
            # Connection lost - retry silently
            retry_count += 1
            if retry_count < max_retries:
                # Exponential backoff: 1s, 2s, 4s
                await asyncio.sleep(2 ** (retry_count - 1))
                # Loop will retry connection automatically
                continue
            else:
                # All retries failed
                click.echo(f"\n❌ WebSocket error: {str(e)}", err=True)
                return

        except Exception as e:
            # Other errors - don't retry
            click.echo(f"\n❌ Error: {str(e)}", err=True)
            return


def run_playground(
    agent: str = None,
    platform: str = None,
    api_key: str = None,
    local: bool = False,
    show_tools: bool = False,
):
    """Run interactive playground for testing agents.

    Args:
        agent: Agent name or path to agent package
        platform: Platform URL (optional if stored in config)
        api_key: API key (optional if stored in config)
        local: Run agent locally instead of on platform
        show_tools: Show tool calls and results (default: False)
    """
    click.echo("🎮 NCP Agent Playground")
    click.echo()

    # Determine what to run
    if agent:
        # Specific agent provided
        agent_path = Path(agent)
        if agent_path.exists() and agent_path.suffix == ".ncp":
            click.echo(f"📦 Loading agent from package: {agent}")
        else:
            click.echo(f"🤖 Agent: {agent}")
    else:
        # Try to find agent in current project
        project_root = find_project_root()
        if project_root is None:
            click.echo(
                "❌ No agent specified and no ncp.toml found in current directory",
                err=True,
            )
            click.echo(
                "   Either provide --agent or run from within a project directory",
                err=True,
            )
            raise click.Abort()

        click.echo(f"📁 Project: {project_root.name}")
        agent = project_root.name

    if local:
        click.echo("💻 Mode: Local execution")
        click.echo()
        click.echo("⚠️  Local execution not yet implemented")
        click.echo("   Agent will be tested on the platform")
        click.echo()
    else:
        # Get platform credentials
        try:
            platform_url, api_key_to_use = get_platform_and_key(platform, api_key)
            click.echo(f"🌐 Platform: {platform_url}")
        except click.UsageError as e:
            click.echo(f"❌ {e}", err=True)
            raise click.Abort()

    click.echo()
    click.echo("─" * 60)
    click.echo()

    click.echo("💬 Interactive Chat Mode (Ctrl+C to exit)")
    click.echo("   Type your message and press Enter to send")
    click.echo()

    # Run WebSocket chat
    try:
        asyncio.run(run_websocket_chat(agent, platform_url, api_key_to_use, show_tools))
    except (KeyboardInterrupt, EOFError):
        click.echo()
        click.echo("👋 Goodbye!")
        click.echo()
