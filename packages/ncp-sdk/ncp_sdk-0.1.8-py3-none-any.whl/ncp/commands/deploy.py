"""Agent deployment command."""

import click
import requests
import urllib3
import tarfile
import toml
import tempfile
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from ..utils import get_platform_and_key

# Disable SSL warnings for localhost development
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

console = Console()


def extract_agent_name_from_package(package_path: Path) -> str:
    """Extract agent name from package's ncp.toml.

    Args:
        package_path: Path to .ncp package file

    Returns:
        Agent name from package

    Raises:
        ValueError: If agent name cannot be extracted
    """
    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Extract tar.gz
            with tarfile.open(package_path, "r:gz") as tar:
                tar.extractall(temp_path)

            # Find ncp.toml
            ncp_toml_files = list(temp_path.rglob("ncp.toml"))
            if not ncp_toml_files:
                raise ValueError("No ncp.toml found in package")

            # Read agent name from config
            config = toml.load(ncp_toml_files[0])
            agent_name = config.get("project", {}).get("name")

            if not agent_name:
                raise ValueError("No agent name found in ncp.toml")

            return agent_name

    except Exception as e:
        raise ValueError(f"Failed to extract agent name: {str(e)}")


def deploy_agent(package_file: str, platform: str = None, api_key: str = None, update: bool = False):
    """Deploy an agent package to the NCP platform.

    Args:
        package_file: Path to .ncp package file
        platform: NCP platform URL
        api_key: Optional API key for authentication
        update: If True, update existing agent with same name
    """
    package_path = Path(package_file)

    if not package_path.exists():
        console.print(f"\n[red]✗[/red] Package file not found: {package_file}\n")
        raise click.Abort()

    if not package_path.suffix == ".ncp":
        console.print("[yellow]⚠[/yellow]  Warning: File does not have .ncp extension")

    # Extract agent name for update
    update_agent_name = None
    if update:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Extracting agent info...", total=None)
            try:
                update_agent_name = extract_agent_name_from_package(package_path)
            except ValueError as e:
                console.print(f"\n[red]✗[/red] {e}\n")
                raise click.Abort()

    # Get platform credentials
    try:
        platform_url, api_key_to_use = get_platform_and_key(platform, api_key)
    except click.UsageError as e:
        console.print(f"\n[red]✗[/red] {e}\n")
        raise click.Abort()

    # Show deployment info
    info_text = f"[cyan]Platform:[/cyan] {platform_url}\n"
    info_text += f"[cyan]Package:[/cyan]  {package_path.name}\n"
    if update_agent_name:
        info_text += f"[cyan]Action:[/cyan]   Update existing agent\n"
        info_text += f"[cyan]Agent:[/cyan]    {update_agent_name}\n"
    else:
        info_text += f"[cyan]Action:[/cyan]   Deploy new agent\n"
    if api_key_to_use:
        info_text += f"[cyan]Auth:[/cyan]     Authenticated ✓"

    console.print()
    console.print(Panel(info_text, title="[bold]Deployment Configuration[/bold]", border_style="cyan"))
    console.print()

    try:
        # Prepare the file upload
        with open(package_path, 'rb') as f:
            files = {'file': (package_path.name, f, 'application/gzip')}

            # Prepare headers
            headers = {}
            if api_key_to_use:
                headers['Authorization'] = f'Bearer {api_key_to_use}'

            # Prepare query params
            params = {}
            if update_agent_name:
                params['update'] = update_agent_name

            # Make the API request
            deploy_url = f"{platform_url}/api/v1/sdk_agents/deploy"

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Uploading package...", total=None)

                response = requests.post(
                    deploy_url,
                    files=files,
                    headers=headers,
                    params=params,
                    verify=False  # Skip SSL verification for localhost
                )

            # Check response
            if response.status_code == 200:
                result = response.json()

                success_text = f"[green]Agent:[/green]     {result.get('agent_name')}\n"
                success_text += f"[green]Agent ID:[/green]  {result.get('agent_id')}\n\n"
                success_text += f"[dim]Next steps:[/dim]\n"
                success_text += f"  • Test in playground: [cyan]ncp playground --agent {result.get('agent_name')}[/cyan]\n"
                success_text += f"  • View all agents:    [cyan]ncp list[/cyan]"

                console.print(Panel(success_text, title="[bold green]✓ Deployment Complete[/bold green]", border_style="green"))
                console.print()

            elif response.status_code == 409:
                error = response.json()
                console.print()
                console.print(f"[red]✗[/red] {error.get('detail', 'Agent already exists')}")
                console.print(f"[dim]Tip: Use the [cyan]--update[/cyan] flag to update an existing agent[/dim]")
                console.print()
                raise click.Abort()

            else:
                error = response.json() if response.headers.get('content-type') == 'application/json' else {'detail': response.text}
                console.print()
                console.print(f"[red]✗[/red] Deployment failed: {error.get('detail', 'Unknown error')}")
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
        console.print(f"[red]✗[/red] Deployment failed: {str(e)}")
        console.print()
        raise click.Abort()
