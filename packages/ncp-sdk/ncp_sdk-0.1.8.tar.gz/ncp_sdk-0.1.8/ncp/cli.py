"""NCP SDK Command Line Interface."""

import click
import sys
from pathlib import Path

from . import __version__


@click.group()
@click.version_option(version=__version__)
def cli():
    """NCP SDK - Build and deploy AI agents on the Network Copilot Platform."""
    pass


@cli.command()
@click.option(
    "--platform",
    help="Platform URL (e.g., https://ncp.example.com)"
)
def authenticate(platform: str):
    """Authenticate with the NCP platform.

    Stores credentials in ncp.toml so you don't need to provide
    --platform and --api-key flags for every command.

    Must be run from within a project directory.

    Example:
        ncp authenticate
        ncp authenticate --platform https://ncp.example.com
    """
    from .commands.authenticate import authenticate_user
    authenticate_user(platform)


@cli.command()
@click.argument("project_name")
@click.option(
    "--template",
    default="default",
    help="Project template to use (default: default)"
)
def init(project_name: str, template: str):
    """Initialize a new NCP agent project.

    Creates a new project directory with the standard structure:
    - ncp.toml (project configuration)
    - requirements.txt (Python dependencies)
    - apt-requirements.txt (system dependencies)
    - agents/ (agent definitions)
    - tools/ (custom tools)

    Example:
        ncp init my-agent-project
    """
    from .commands.init import init_project
    init_project(project_name, template)


@cli.command()
@click.argument("project_path", type=click.Path(exists=True), default=".")
def validate(project_path: str):
    """Validate an NCP agent project.

    Checks:
    - Project structure is correct
    - ncp.toml is valid
    - Agent definitions are valid
    - Dependencies are specified
    - All imports can be resolved

    Example:
        ncp validate .
        ncp validate /path/to/project
    """
    from .commands.validate import validate_project
    validate_project(project_path)


@cli.command()
@click.argument("project_path", type=click.Path(exists=True), default=".")
@click.option(
    "--output",
    "-o",
    help="Output file path (default: <project-name>.ncp)"
)
@click.option(
    "--version",
    help="Version tag for the package"
)
def package(project_path: str, output: str, version: str):
    """Package an agent project for deployment.

    Creates a .ncp package file containing:
    - Agent definitions
    - Tool implementations
    - Dependencies (requirements.txt, apt-requirements.txt)
    - Configuration (ncp.toml)

    Example:
        ncp package .
        ncp package . --output my-agent.ncp
        ncp package . --version 1.0.0
    """
    from .commands.package import package_project
    package_project(project_path, output, version)


@cli.command()
@click.option(
    "--agent",
    help="Agent name or path to .ncp package"
)
@click.option(
    "--platform",
    help="NCP platform URL (uses stored credentials if not provided)"
)
@click.option(
    "--api-key",
    help="API key for authentication (uses stored credentials if not provided)"
)
@click.option(
    "--local",
    is_flag=True,
    help="Run agent locally instead of on platform"
)
@click.option(
    "--show-tools",
    is_flag=True,
    help="Show tool calls and results during execution"
)
def playground(agent: str, platform: str, api_key: str, local: bool, show_tools: bool):
    """Interactive playground for testing agents.

    Like 'ollama run' for NCP agents - deploy and chat with your agent
    interactively. Uses stored credentials from 'ncp authenticate'.

    Example:
        ncp playground
        ncp playground --agent my-agent
        ncp playground --agent my-agent.ncp --local
        ncp playground --agent my-agent --show-tools
    """
    from .commands.playground import run_playground
    run_playground(agent, platform, api_key, local, show_tools)


@cli.command()
@click.argument("package_file", type=click.Path(exists=True))
@click.option(
    "--platform",
    help="NCP platform URL (uses stored credentials if not provided)"
)
@click.option(
    "--api-key",
    help="API key for authentication (uses stored credentials if not provided)"
)
@click.option(
    "--update",
    is_flag=True,
    help="Update existing agent (uses agent name from package)"
)
def deploy(package_file: str, platform: str, api_key: str, update: bool):
    """Deploy an agent package to the NCP platform.

    Uploads and deploys the packaged agent to a running NCP platform instance.

    Example:
        ncp deploy my-agent.ncp
        ncp deploy my-agent.ncp --update
        ncp deploy my-agent.ncp --platform https://ncp.example.com --api-key YOUR_KEY
    """
    from .commands.deploy import deploy_agent
    deploy_agent(package_file, platform, api_key, update)


@cli.command()
@click.option(
    "--platform",
    help="NCP platform URL (uses stored credentials if not provided)"
)
@click.option(
    "--api-key",
    help="API key for authentication (uses stored credentials if not provided)"
)
def list(platform: str, api_key: str):
    """List deployed agents on the platform.

    Example:
        ncp list
        ncp list --platform https://ncp.example.com
    """
    from .commands.list import list_agents
    list_agents(platform, api_key)


@cli.command()
@click.option(
    "--platform",
    help="NCP platform URL (uses stored credentials if not provided)"
)
@click.option(
    "--agent",
    required=True,
    help="Agent name to remove"
)
@click.option(
    "--api-key",
    help="API key for authentication (uses stored credentials if not provided)"
)
@click.confirmation_option(
    prompt="Are you sure you want to remove this agent?"
)
def remove(platform: str, agent: str, api_key: str):
    """Remove an agent from the platform.

    Example:
        ncp remove --platform https://ncp.example.com --agent my-agent
    """
    from .commands.remove import remove_agent
    remove_agent(platform, agent, api_key)


if __name__ == "__main__":
    cli()
