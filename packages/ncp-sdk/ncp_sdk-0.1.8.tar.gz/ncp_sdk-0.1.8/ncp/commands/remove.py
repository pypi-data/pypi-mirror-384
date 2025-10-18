"""Agent removal command."""

import click
import requests
import urllib3
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from ..utils import get_platform_and_key

# Disable SSL warnings for localhost development
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

console = Console()


def remove_agent(platform: str = None, agent: str = None, api_key: str = None):
    """Remove an agent from the platform.

    Args:
        platform: NCP platform URL
        agent: Agent name
        api_key: Optional API key for authentication
    """
    # Get platform credentials
    try:
        platform_url, api_key_to_use = get_platform_and_key(platform, api_key)
    except click.UsageError as e:
        console.print()
        console.print(f"[red]✗[/red] {e}")
        console.print()
        raise click.Abort()

    console.print()
    console.print(f"[yellow]Removing:[/yellow] {agent}")
    console.print(f"[dim]Platform:[/dim] {platform_url}")
    console.print()

    # Prepare headers
    headers = {}
    if api_key_to_use:
        headers['Authorization'] = f'Bearer {api_key_to_use}'

    try:
        # Make removal request
        remove_url = f"{platform_url}/api/v1/sdk_agents/remove/{agent}"

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Removing agent...", total=None)

            response = requests.delete(
                remove_url,
                headers=headers,
                verify=False  # Skip SSL verification for localhost
            )

        if response.status_code == 200:
            result = response.json()

            success_text = f"[green]Agent:[/green] {agent}\n"
            success_text += f"\n[dim]{result.get('message', 'The agent has been removed from the platform')}[/dim]"

            console.print(Panel(
                success_text,
                title="[bold green]✓ Successfully Removed[/bold green]",
                border_style="green"
            ))
            console.print()

        elif response.status_code == 404:
            console.print()
            console.print(f"[red]✗[/red] Agent '{agent}' not found")
            console.print(f"[dim]Use [cyan]ncp list[/cyan] to see your deployed agents[/dim]")
            console.print()
            raise click.Abort()

        elif response.status_code == 401:
            console.print()
            console.print("[red]✗[/red] Authentication required")
            console.print("[dim]Run [cyan]ncp authenticate[/cyan] to log in[/dim]")
            console.print()
            raise click.Abort()

        else:
            error = response.json() if response.headers.get('content-type') == 'application/json' else {'detail': response.text}
            console.print()
            console.print(f"[red]✗[/red] Removal failed: {error.get('detail', 'Unknown error')}")
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
