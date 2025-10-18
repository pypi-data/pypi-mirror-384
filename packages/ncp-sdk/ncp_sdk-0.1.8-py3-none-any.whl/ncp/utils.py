"""Utility functions for SDK."""

import os
from pathlib import Path
from typing import Optional, Tuple
import toml
import click


def find_project_root(start_path: Path = None) -> Optional[Path]:
    """Find project root by looking for ncp.toml.

    Args:
        start_path: Starting directory (defaults to current directory)

    Returns:
        Path to project root, or None if not found
    """
    if start_path is None:
        start_path = Path.cwd()

    current = start_path.resolve()

    # Walk up the directory tree
    for parent in [current] + list(current.parents):
        ncp_toml = parent / "ncp.toml"
        if ncp_toml.exists():
            return parent

    return None


def get_credentials_from_config(project_path: Path = None) -> Tuple[Optional[str], Optional[str]]:
    """Get stored platform credentials from ncp.toml.

    Args:
        project_path: Path to project directory (defaults to current directory)

    Returns:
        Tuple of (platform_url, api_key), or (None, None) if not found
    """
    if project_path is None:
        project_path = find_project_root()

    if project_path is None:
        return None, None

    config_file = project_path / "ncp.toml"
    if not config_file.exists():
        return None, None

    try:
        config = toml.load(config_file)
        platform_config = config.get("platform", {})
        platform_url = platform_config.get("url")
        api_key = platform_config.get("api_key")
        return platform_url, api_key
    except Exception:
        return None, None


def save_credentials_to_config(
    platform_url: str,
    api_key: str,
    project_path: Path = None
) -> None:
    """Save platform credentials to ncp.toml.

    Args:
        platform_url: Platform URL
        api_key: API key
        project_path: Path to project directory (defaults to current directory)

    Raises:
        FileNotFoundError: If ncp.toml not found
    """
    if project_path is None:
        project_path = find_project_root()

    if project_path is None:
        raise FileNotFoundError("No ncp.toml found in current directory or parents")

    config_file = project_path / "ncp.toml"
    if not config_file.exists():
        raise FileNotFoundError(f"ncp.toml not found at {config_file}")

    # Load existing config
    config = toml.load(config_file)

    # Update platform section
    if "platform" not in config:
        config["platform"] = {}

    config["platform"]["url"] = platform_url
    config["platform"]["api_key"] = api_key

    # Save back to file
    with open(config_file, "w") as f:
        toml.dump(config, f)


def get_platform_and_key(
    platform: Optional[str] = None,
    api_key: Optional[str] = None
) -> Tuple[str, Optional[str]]:
    """Get platform URL and API key from args or config.

    Args:
        platform: Platform URL from command line (optional)
        api_key: API key from command line (optional)

    Returns:
        Tuple of (platform_url, api_key)

    Raises:
        click.UsageError: If platform URL not provided and not in config
    """
    # If platform provided as argument, use it
    if platform:
        return platform, api_key

    # Try to get from config
    stored_platform, stored_api_key = get_credentials_from_config()

    if stored_platform:
        # Use stored credentials
        return stored_platform, api_key or stored_api_key

    # No platform found
    raise click.UsageError(
        "Platform URL not specified. Either:\n"
        "  1. Use --platform flag\n"
        "  2. Run 'ncp authenticate' to store credentials"
    )
