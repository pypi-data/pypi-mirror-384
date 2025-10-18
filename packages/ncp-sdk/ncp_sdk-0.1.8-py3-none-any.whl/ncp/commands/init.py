"""Project initialization command."""

import shutil
from pathlib import Path
import click
from rich.console import Console
from rich.panel import Panel
from rich.tree import Tree

console = Console()


def init_project(project_name: str, template: str = "default"):
    """Initialize a new NCP agent project.

    Args:
        project_name: Name of the project to create
        template: Template to use (default: "default")
    """
    # Get template directory
    sdk_root = Path(__file__).parent.parent
    template_dir = sdk_root / "templates" / template

    if not template_dir.exists():
        console.print()
        console.print(f"[red]✗[/red] Template '{template}' not found")
        console.print("[dim]Available templates: default[/dim]")
        console.print()
        raise click.Abort()

    # Create project directory
    project_dir = Path.cwd() / project_name
    if project_dir.exists():
        console.print()
        console.print(f"[red]✗[/red] Directory '{project_name}' already exists")
        console.print()
        raise click.Abort()

    try:
        project_dir.mkdir(parents=True)

        console.print()
        console.print(f"[cyan]Creating project:[/cyan] {project_name}")
        console.print()

        # Create tree structure
        tree = Tree(f"[bold green]{project_name}/[/bold green]", guide_style="dim")

        # Copy template files, replacing {{ project_name }} placeholders
        for src_path in template_dir.rglob("*"):
            if src_path.is_file():
                # Calculate relative path
                rel_path = src_path.relative_to(template_dir)
                dst_path = project_dir / rel_path

                # Create parent directories
                dst_path.parent.mkdir(parents=True, exist_ok=True)

                # Read and replace placeholders
                try:
                    content = src_path.read_text(encoding="utf-8")
                    content = content.replace("{{ project_name }}", project_name)
                    dst_path.write_text(content, encoding="utf-8")
                except UnicodeDecodeError:
                    # Binary file, just copy
                    shutil.copy2(src_path, dst_path)

                # Add to tree (simplified structure)
                tree.add(f"[green]{rel_path}[/green]")

        console.print(tree)
        console.print()

        # Success message with next steps
        next_steps = f"[bold]Next steps:[/bold]\n\n"
        next_steps += f"  [cyan]cd {project_name}[/cyan]\n"
        next_steps += f"  [cyan]ncp validate .[/cyan]"

        console.print(Panel(
            next_steps,
            title="[bold green]✓ Project Created Successfully[/bold green]",
            border_style="green"
        ))
        console.print()

    except Exception as e:
        console.print()
        console.print(f"[red]✗[/red] Error initializing project: {e}")
        console.print()
        # Clean up partial project
        if project_dir.exists():
            shutil.rmtree(project_dir)
        raise click.Abort()
