"""Authentication command."""

import click
import getpass
import requests
import urllib3
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.progress import Progress, SpinnerColumn, TextColumn
from ..utils import save_credentials_to_config, find_project_root

# Disable SSL warnings for localhost development
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

console = Console()


def authenticate_user(platform: str = None):
    """Authenticate with the NCP platform and store credentials.

    Args:
        platform: Platform URL (will prompt if not provided)
    """
    console.print()
    console.print(Panel.fit("[bold cyan]Authenticate with NCP Platform[/bold cyan]", border_style="cyan"))
    console.print()

    # Check if we're in a project directory
    project_root = find_project_root()
    if project_root is None:
        console.print("[red]✗[/red] Not in an NCP project directory")
        console.print("[dim]Please run this command from within your project folder[/dim]")
        console.print()
        raise click.Abort()

    console.print(f"[cyan]Project:[/cyan] {project_root.name}")
    console.print()

    # Get platform URL
    if not platform:
        platform = Prompt.ask("[cyan]Platform URL[/cyan]")

    # Validate URL format
    if not platform.startswith(("http://", "https://")):
        console.print()
        console.print("[red]✗[/red] Platform URL must start with http:// or https://")
        console.print()
        raise click.Abort()

    # Get username and password
    username = Prompt.ask("[cyan]Username[/cyan]")
    password = getpass.getpass("Password: ")

    console.print()

    try:
        # Call authentication API
        auth_url = f"{platform}/api/v1/sdk_agents/auth/login"

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(f"Authenticating with {platform}...", total=None)

            response = requests.post(
                auth_url,
                json={
                    "username": username,
                    "password": password
                },
                verify=False  # Skip SSL verification for localhost
            )

        if response.status_code == 200:
            result = response.json()
            api_key = result.get("api_key")
            user_name = result.get("username")
            first_name = result.get("first_name", "")
            last_name = result.get("last_name", "")

            welcome_text = f"[green]Logged in as:[/green] {username}\n"
            if first_name or last_name:
                welcome_text += f"[green]Name:[/green]        {first_name} {last_name}".strip() + "\n"
            welcome_text += f"\n[dim]Credentials saved to {project_root / 'ncp.toml'}[/dim]\n\n"
            welcome_text += f"[dim]You can now use these commands without credentials:[/dim]\n"
            welcome_text += f"  • Deploy an agent:  [cyan]ncp deploy <package>.ncp[/cyan]\n"
            welcome_text += f"  • Test in playground: [cyan]ncp playground[/cyan]\n"
            welcome_text += f"  • List your agents:   [cyan]ncp list[/cyan]"

            # Save credentials to ncp.toml
            save_credentials_to_config(platform, api_key, project_root)

            console.print(Panel(welcome_text, title="[bold green]✓ Successfully Authenticated[/bold green]", border_style="green"))
            console.print()

        elif response.status_code == 401:
            error = response.json()
            console.print()
            console.print(f"[red]✗[/red] Invalid credentials")
            console.print(f"[dim]{error.get('detail', 'Please check your username and password')}[/dim]")
            console.print()
            raise click.Abort()

        else:
            error = response.json() if response.headers.get('content-type') == 'application/json' else {'detail': response.text}
            console.print()
            console.print(f"[red]✗[/red] Authentication failed: {error.get('detail', 'Unknown error')}")
            console.print()
            raise click.Abort()

    except requests.exceptions.ConnectionError:
        console.print()
        console.print(f"[red]✗[/red] Cannot connect to platform: {platform}")
        console.print("[dim]Please verify the platform is running and the URL is correct[/dim]")
        console.print()
        raise click.Abort()

    except click.Abort:
        raise

    except Exception as e:
        console.print()
        console.print(f"[red]✗[/red] Unexpected error: {e}")
        console.print()
        raise click.Abort()
