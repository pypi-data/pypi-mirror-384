"""Project packaging command."""

import os
import tarfile
import tempfile
import shutil
from pathlib import Path
import click
import pathspec
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

console = Console()


def package_project(project_path: str, output: str = None, version: str = None):
    """Package an agent project for deployment.

    Includes all files and directories except those matched by:
    - .gitignore patterns (if .gitignore exists)
    - Default exclusions (.git, __pycache__, .env, venv, etc.)

    Args:
        project_path: Path to the project directory
        output: Output file path (optional)
        version: Version tag (optional)
    """
    project_dir = Path(project_path).resolve()

    # Validate project exists
    if not project_dir.exists():
        console.print()
        console.print(f"[red]✗[/red] Project directory not found: {project_dir}")
        console.print()
        raise click.Abort()

    # Determine output filename
    if output:
        output_file = Path(output)
    else:
        project_name = project_dir.name
        output_file = Path.cwd() / f"{project_name}.ncp"

    console.print()
    console.print(f"[cyan]Packaging:[/cyan] {project_dir.name}")
    console.print()

    try:
        # Default exclusion patterns (always excluded)
        default_exclusions = [
            ".git/",
            ".git",
            "__pycache__/",
            "*.pyc",
            "*.pyo",
            "*.pyd",
            ".Python",
            ".env",
            ".env.*",
            ".venv/",
            "venv/",
            "env/",
            "ENV/",
            "node_modules/",
            ".DS_Store",
            "*.ncp",
            ".idea/",
            ".vscode/",
            "*.egg-info/",
            "dist/",
            "build/",
            ".pytest_cache/",
            ".coverage",
            "*.log",
        ]

        # Build exclusion spec
        exclusion_spec = None
        gitignore_path = project_dir / ".gitignore"

        if gitignore_path.exists():
            # Parse .gitignore
            with open(gitignore_path, 'r') as f:
                gitignore_patterns = f.read()
            # Combine with default exclusions
            all_patterns = gitignore_patterns + "\n" + "\n".join(default_exclusions)
            exclusion_spec = pathspec.PathSpec.from_lines('gitwildmatch', all_patterns.splitlines())
        else:
            # Use only default exclusions
            exclusion_spec = pathspec.PathSpec.from_lines('gitwildmatch', default_exclusions)

        # Required files (must always be included even if ignored)
        required_files = ["ncp.toml", "requirements.txt"]

        # Create temporary directory for staging
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            package_root = temp_path / project_dir.name

            # Copy files to staging area
            files_included = []

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                console=console
            ) as progress:
                task = progress.add_task("Collecting files...", total=None)

                # Walk through all files and directories
                for root, dirs, files in os.walk(project_dir):
                    # Get relative path from project_dir
                    rel_root = Path(root).relative_to(project_dir)

                    # Filter directories (modify dirs in-place to prevent os.walk from descending)
                    dirs[:] = [
                        d for d in dirs
                        if not exclusion_spec.match_file(str(rel_root / d) + "/")
                    ]

                    # Process files
                    for file in files:
                        rel_file = rel_root / file

                        # Check if file is required
                        is_required = str(rel_file) in required_files or file in required_files

                        # Include if required OR not excluded
                        if is_required or not exclusion_spec.match_file(str(rel_file)):
                            src_file = project_dir / rel_file
                            dst_file = package_root / rel_file
                            dst_file.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(src_file, dst_file)
                            files_included.append(rel_file)

            # Verify required files are present
            if "ncp.toml" not in [str(f) for f in files_included] and Path("ncp.toml") not in files_included:
                console.print()
                console.print("[red]✗[/red] Required file 'ncp.toml' not found")
                console.print()
                raise click.Abort()

            if not files_included:
                console.print()
                console.print("[red]✗[/red] No files to package")
                console.print()
                raise click.Abort()

            # Show collected files
            console.print("[dim]Files collected:[/dim]")
            for f in files_included[:5]:  # Show first 5
                console.print(f"  [green]✓[/green] {f}")
            if len(files_included) > 5:
                console.print(f"  [dim]... and {len(files_included) - 5} more[/dim]")
            console.print()

            # Create archive
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task("Creating package archive...", total=None)
                with tarfile.open(output_file, "w:gz") as tar:
                    tar.add(package_root, arcname=project_dir.name)

            # Get file size
            file_size = output_file.stat().st_size
            size_kb = file_size / 1024
            size_display = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb/1024:.1f} MB"

            # Success message
            success_text = f"[green]Package:[/green] {output_file.name}\n"
            success_text += f"[green]Size:[/green]    {size_display}\n"
            success_text += f"[green]Files:[/green]   {len(files_included)}\n\n"
            success_text += f"[dim]Deploy your agent:[/dim]\n"
            success_text += f"  [cyan]ncp deploy {output_file.name}[/cyan]"

            console.print(Panel(
                success_text,
                title="[bold green]✓ Package Ready for Deployment[/bold green]",
                border_style="green"
            ))
            console.print()

    except Exception as e:
        console.print()
        console.print(f"[red]✗[/red] Error packaging project: {e}")
        console.print()
        if output_file.exists():
            output_file.unlink()
        raise click.Abort()
