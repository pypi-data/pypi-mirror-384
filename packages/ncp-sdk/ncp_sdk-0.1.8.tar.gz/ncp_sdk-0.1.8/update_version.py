#!/usr/bin/env python3
"""Update version across all files in the NCP SDK project.

This script updates the version number in:
- pyproject.toml
- setup.py
- ncp/__init__.py

Usage:
    python update_version.py 0.4.0
    python update_version.py 1.0.0
    python update_version.py --bump major|minor|patch
"""

import argparse
import re
import sys
from pathlib import Path

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
except ImportError:
    print("Error: 'rich' module not installed")
    print("Install it with: pip install rich")
    sys.exit(1)

console = Console()


def get_current_version():
    """Get the current version from pyproject.toml."""
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        console.print("[red]Error: pyproject.toml not found[/red]")
        sys.exit(1)

    content = pyproject_path.read_text()
    match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', content)
    if match:
        return match.group(1)

    console.print("[red]Error: Could not find version in pyproject.toml[/red]")
    sys.exit(1)


def parse_version(version_string):
    """Parse a version string into (major, minor, patch)."""
    parts = version_string.split('.')
    if len(parts) != 3:
        console.print(f"[red]Error: Invalid version format '{version_string}'[/red]")
        console.print("Version must be in format: MAJOR.MINOR.PATCH (e.g., 1.2.3)")
        sys.exit(1)

    try:
        return tuple(int(p) for p in parts)
    except ValueError:
        console.print(f"[red]Error: Version parts must be integers: '{version_string}'[/red]")
        sys.exit(1)


def bump_version(current_version, bump_type):
    """Bump version based on type (major, minor, patch)."""
    major, minor, patch = parse_version(current_version)

    if bump_type == "major":
        return f"{major + 1}.0.0"
    elif bump_type == "minor":
        return f"{major}.{minor + 1}.0"
    elif bump_type == "patch":
        return f"{major}.{minor}.{patch + 1}"
    else:
        console.print(f"[red]Error: Invalid bump type '{bump_type}'[/red]")
        console.print("Must be one of: major, minor, patch")
        sys.exit(1)


def update_file(file_path, pattern, replacement, description):
    """Update version in a file using regex pattern."""
    path = Path(file_path)

    if not path.exists():
        console.print(f"[yellow]Warning: {file_path} not found, skipping[/yellow]")
        return False

    content = path.read_text()
    new_content, count = re.subn(pattern, replacement, content)

    if count == 0:
        console.print(f"[yellow]Warning: Version pattern not found in {file_path}[/yellow]")
        return False

    path.write_text(new_content)
    console.print(f"[green]✓[/green] Updated {description}")
    return True


def update_all_versions(new_version):
    """Update version in all relevant files."""
    console.print(f"\n[cyan]Updating to version {new_version}...[/cyan]\n")

    updates = [
        # pyproject.toml
        (
            "pyproject.toml",
            r'version\s*=\s*["\'][^"\']+["\']',
            f'version = "{new_version}"',
            "pyproject.toml"
        ),
        # setup.py
        (
            "setup.py",
            r'version\s*=\s*["\'][^"\']+["\']',
            f'version="{new_version}"',
            "setup.py"
        ),
        # ncp/__init__.py
        (
            "ncp/__init__.py",
            r'__version__\s*=\s*["\'][^"\']+["\']',
            f'__version__ = "{new_version}"',
            "ncp/__init__.py"
        ),
    ]

    success_count = 0
    for file_path, pattern, replacement, description in updates:
        if update_file(file_path, pattern, replacement, description):
            success_count += 1

    return success_count


def show_current_versions():
    """Show current version in all files."""
    table = Table(title="Current Versions")
    table.add_column("File", style="cyan")
    table.add_column("Version", style="green")

    files_to_check = [
        ("pyproject.toml", r'version\s*=\s*["\']([^"\']+)["\']'),
        ("setup.py", r'version\s*=\s*["\']([^"\']+)["\']'),
        ("ncp/__init__.py", r'__version__\s*=\s*["\']([^"\']+)["\']'),
    ]

    versions_found = set()

    for file_path, pattern in files_to_check:
        path = Path(file_path)
        if path.exists():
            content = path.read_text()
            match = re.search(pattern, content)
            if match:
                version = match.group(1)
                table.add_row(file_path, version)
                versions_found.add(version)

    console.print(table)

    if len(versions_found) > 1:
        console.print("\n[yellow]⚠️  Warning: Versions are inconsistent across files![/yellow]")

    return list(versions_found)[0] if len(versions_found) == 1 else None


def main():
    parser = argparse.ArgumentParser(
        description="Update version across all NCP SDK files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python update_version.py 0.4.0        # Set version to 0.4.0
  python update_version.py --bump patch # Bump patch version (0.3.0 -> 0.3.1)
  python update_version.py --bump minor # Bump minor version (0.3.0 -> 0.4.0)
  python update_version.py --bump major # Bump major version (0.3.0 -> 1.0.0)
  python update_version.py --show       # Show current versions
        """,
    )

    parser.add_argument(
        "version",
        nargs="?",
        help="New version number (e.g., 0.4.0)"
    )
    parser.add_argument(
        "--bump",
        choices=["major", "minor", "patch"],
        help="Bump version (major, minor, or patch)"
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Show current versions without updating"
    )

    args = parser.parse_args()

    # Show header
    console.print(Panel.fit(
        "[bold]NCP SDK Version Manager[/bold]",
        border_style="cyan"
    ))

    # Show current versions
    if args.show:
        show_current_versions()
        return

    current_version = get_current_version()
    console.print(f"Current version: [yellow]{current_version}[/yellow]")

    # Determine new version
    if args.bump:
        new_version = bump_version(current_version, args.bump)
        console.print(f"Bumping [cyan]{args.bump}[/cyan] version")
    elif args.version:
        new_version = args.version
        # Validate version format
        parse_version(new_version)
    else:
        console.print("[red]Error: Must provide either version or --bump[/red]")
        parser.print_help()
        sys.exit(1)

    console.print(f"New version: [green]{new_version}[/green]")

    # Confirm
    response = input("\nProceed with version update? (yes/no): ")
    if response.lower() != "yes":
        console.print("[yellow]Update cancelled.[/yellow]")
        sys.exit(0)

    # Update all files
    success_count = update_all_versions(new_version)

    if success_count > 0:
        console.print(f"\n[bold green]✓ Version updated to {new_version}![/bold green]")
        console.print("\n[cyan]Next steps:[/cyan]")
        console.print("  1. Review changes: git diff")
        console.print("  2. Update CHANGELOG.md")
        console.print("  3. Commit: git add -u && git commit -m 'Bump version to {}'".format(new_version))
        console.print(f"  4. Tag: git tag v{new_version}")
        console.print("  5. Build and publish: python publish.py")
    else:
        console.print("\n[red]❌ No files were updated[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
