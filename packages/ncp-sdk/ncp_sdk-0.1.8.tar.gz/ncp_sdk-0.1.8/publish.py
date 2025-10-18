#!/usr/bin/env python3
"""Build and publish NCP SDK to PyPI.

This script handles:
- Cleaning old build artifacts
- Building the package
- Publishing to PyPI or Test PyPI

Usage:
    python publish.py              # Publish to production PyPI
    python publish.py --test       # Publish to Test PyPI
    python publish.py --build-only # Only build, don't publish
    python publish.py --clean      # Only clean build artifacts
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
except ImportError:
    print("Error: Missing required packages.")
    print("Install them with: pip install python-dotenv rich")
    sys.exit(1)

console = Console()


def clean_build_artifacts():
    """Remove old build artifacts."""
    dirs_to_remove = ["build", "dist", "*.egg-info"]

    console.print("\n[yellow]Cleaning build artifacts...[/yellow]")

    for pattern in dirs_to_remove:
        if "*" in pattern:
            # Handle glob patterns
            for path in Path(".").glob(pattern):
                if path.is_dir():
                    console.print(f"  Removing: {path}")
                    shutil.rmtree(path)
        else:
            path = Path(pattern)
            if path.exists():
                console.print(f"  Removing: {path}")
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()

    console.print("[green]✓ Build artifacts cleaned[/green]")


def run_command(cmd, description):
    """Run a shell command with progress indicator."""
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(description, total=None)

        try:
            result = subprocess.run(
                cmd,
                shell=True,
                check=True,
                capture_output=True,
                text=True,
            )
            progress.update(task, completed=True)
            return result
        except subprocess.CalledProcessError as e:
            progress.update(task, completed=True)
            console.print(f"[red]✗ Failed: {description}[/red]")
            console.print(f"[red]Error output:[/red]\n{e.stderr}")
            raise


def build_package():
    """Build the package using python -m build."""
    console.print("\n[yellow]Building package...[/yellow]")

    # Check if build module is installed
    try:
        import build
    except ImportError:
        console.print("[red]Error: 'build' module not installed[/red]")
        console.print("Install it with: pip install build")
        sys.exit(1)

    run_command(
        "python -m build",
        "Building source distribution and wheel..."
    )

    console.print("[green]✓ Package built successfully[/green]")

    # Show what was built
    dist_dir = Path("dist")
    if dist_dir.exists():
        files = list(dist_dir.glob("*"))
        if files:
            console.print("\n[cyan]Built packages:[/cyan]")
            for file in files:
                size = file.stat().st_size / 1024  # KB
                console.print(f"  • {file.name} ({size:.1f} KB)")


def publish_package(test_pypi=False):
    """Publish package to PyPI using twine."""
    console.print("\n[yellow]Publishing package...[/yellow]")

    # Check if twine is installed
    try:
        import twine
    except ImportError:
        console.print("[red]Error: 'twine' module not installed[/red]")
        console.print("Install it with: pip install twine")
        sys.exit(1)

    # Load environment variables
    load_dotenv()

    if test_pypi:
        token = os.getenv("PYPI_TEST_TOKEN")
        if not token:
            console.print("[red]Error: PYPI_TEST_TOKEN not found in .env file[/red]")
            sys.exit(1)

        repository_url = "https://test.pypi.org/legacy/"
        console.print("[cyan]Publishing to Test PyPI...[/cyan]")
    else:
        token = os.getenv("PYPI_TOKEN")
        if not token:
            console.print("[red]Error: PYPI_TOKEN not found in .env file[/red]")
            console.print("\nCreate a .env file with:")
            console.print("  PYPI_TOKEN=pypi-xxxxxxxxxxxxx")
            sys.exit(1)

        repository_url = "https://upload.pypi.org/legacy/"
        console.print("[cyan]Publishing to Production PyPI...[/cyan]")

    # Confirm publication to production
    if not test_pypi:
        console.print("\n[bold yellow]⚠️  You are about to publish to PRODUCTION PyPI![/bold yellow]")
        response = input("Are you sure? (yes/no): ")
        if response.lower() != "yes":
            console.print("[yellow]Publication cancelled.[/yellow]")
            sys.exit(0)

    # Publish using twine
    cmd = (
        f'python -m twine upload '
        f'--repository-url {repository_url} '
        f'--username __token__ '
        f'--password {token} '
        f'dist/*'
    )

    run_command(cmd, "Uploading to PyPI...")

    console.print("[green]✓ Package published successfully![/green]")

    # Show installation command
    if test_pypi:
        console.print("\n[cyan]Install from Test PyPI with:[/cyan]")
        console.print("  pip install --index-url https://test.pypi.org/simple/ ncp-sdk")
    else:
        console.print("\n[cyan]Install with:[/cyan]")
        console.print("  pip install ncp-sdk")


def get_version():
    """Extract version from pyproject.toml."""
    try:
        import toml
        with open("pyproject.toml", "r") as f:
            data = toml.load(f)
            return data["project"]["version"]
    except Exception:
        # Fallback to reading setup.py
        with open("setup.py", "r") as f:
            for line in f:
                if "version=" in line:
                    return line.split('"')[1]
    return "unknown"


def main():
    parser = argparse.ArgumentParser(
        description="Build and publish NCP SDK to PyPI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python publish.py                # Build and publish to PyPI
  python publish.py --test         # Build and publish to Test PyPI
  python publish.py --build-only   # Only build the package
  python publish.py --clean        # Only clean build artifacts
        """,
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Publish to Test PyPI instead of production",
    )
    parser.add_argument(
        "--build-only",
        action="store_true",
        help="Only build the package without publishing",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Only clean build artifacts without building",
    )
    parser.add_argument(
        "--skip-clean",
        action="store_true",
        help="Skip cleaning before building",
    )

    args = parser.parse_args()

    # Show header
    version = get_version()
    console.print(Panel.fit(
        f"[bold]NCP SDK Publisher[/bold]\n"
        f"Version: {version}",
        border_style="cyan",
    ))

    try:
        if args.clean:
            # Only clean
            clean_build_artifacts()
            return

        # Clean (unless skipped)
        if not args.skip_clean:
            clean_build_artifacts()

        # Build
        build_package()

        if args.build_only:
            console.print("\n[cyan]Build complete. Skipping publication.[/cyan]")
            return

        # Publish
        publish_package(test_pypi=args.test)

        console.print("\n[bold green]🎉 All done![/bold green]")

    except subprocess.CalledProcessError:
        console.print("\n[bold red]❌ Publication failed![/bold red]")
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled by user.[/yellow]")
        sys.exit(1)


if __name__ == "__main__":
    main()
