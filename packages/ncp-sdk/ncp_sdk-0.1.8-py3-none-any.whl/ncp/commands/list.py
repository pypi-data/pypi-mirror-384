"""Agent listing command."""

import click
import requests
import urllib3
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from ..utils import get_platform_and_key

# Disable SSL warnings for localhost development
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

console = Console()


def format_datetime(dt_str: str) -> str:
    """Format datetime string to human-readable format."""
    if not dt_str:
        return "N/A"
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return dt_str


def list_agents(platform: str = None, api_key: str = None):
    """List deployed agents on the NCP platform.

    Args:
        platform: NCP platform URL
        api_key: Optional API key for authentication
    """
    # Get platform credentials
    try:
        platform_url, api_key_to_use = get_platform_and_key(platform, api_key)
    except click.UsageError as e:
        console.print(f"[red]✗[/red] {e}")
        raise click.Abort()

    # Prepare headers
    headers = {}
    if api_key_to_use:
        headers['Authorization'] = f'Bearer {api_key_to_use}'

    try:
        # Make API request
        list_url = f"{platform_url}/api/v1/sdk_agents/list"

        response = requests.get(
            list_url,
            headers=headers,
            verify=False  # Skip SSL verification for localhost
        )

        if response.status_code == 200:
            result = response.json()
            agents = result.get('agents', [])
            total = result.get('total', 0)

            if total == 0:
                console.print()
                console.print(Panel.fit(
                    "[yellow]No agents found[/yellow]\n\n"
                    "[dim]Get started by deploying your first agent:[/dim]\n"
                    "  [cyan]ncp deploy <package-file>.ncp[/cyan]",
                    title="[bold]Your Agents[/bold]",
                    border_style="yellow"
                ))
                console.print()
                return

            # Create table
            table = Table(title=f"Your Agents ({total})", show_header=True, header_style="bold cyan")
            table.add_column("Name", style="green", no_wrap=True)
            table.add_column("Description", style="dim")
            table.add_column("Version", style="yellow", justify="center")
            table.add_column("Deployed", style="blue")
            table.add_column("Updated", style="blue")

            for agent in agents:
                table.add_row(
                    agent.get('name', 'N/A'),
                    agent.get('description', '')[:50] + ('...' if len(agent.get('description', '')) > 50 else ''),
                    agent.get('version', 'N/A'),
                    format_datetime(agent.get('deployed_at')),
                    format_datetime(agent.get('updated_at')) if agent.get('updated_at') else '-'
                )

            console.print()
            console.print(table)
            console.print()

        elif response.status_code == 401:
            console.print()
            console.print("[red]✗[/red] Authentication required")
            console.print("[dim]Run [cyan]ncp authenticate[/cyan] to log in[/dim]")
            console.print()
            raise click.Abort()

        else:
            error = response.json() if response.headers.get('content-type') == 'application/json' else {'detail': response.text}
            console.print()
            console.print(f"[red]✗[/red] Failed to retrieve agents: {error.get('detail', 'Unknown error')}")
            console.print()
            raise click.Abort()

    except requests.exceptions.ConnectionError:
        console.print()
        console.print(f"[red]✗[/red] Cannot connect to platform: {platform_url}")
        console.print("[dim]Please verify the platform is running and the URL is correct[/dim]")
        console.print()
        raise click.Abort()

    except Exception as e:
        console.print()
        console.print(f"[red]✗[/red] Unexpected error: {str(e)}")
        console.print()
        raise click.Abort()
