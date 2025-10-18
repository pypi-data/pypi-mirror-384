"""Project validation command."""

import sys
import importlib.util
import tarfile
import tempfile
from pathlib import Path
import toml
import click


def validate_project(project_path: str):
    """Validate an NCP agent project.

    Args:
        project_path: Path to the project directory or .ncp package file
    """
    project_path_obj = Path(project_path).resolve()
    errors = []
    warnings = []

    # Check if it's a .ncp package file
    if project_path_obj.is_file() and project_path_obj.suffix == ".ncp":
        click.echo(f"🔍 Validating package: {project_path_obj.name}")
        click.echo()

        # Extract to temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            try:
                with tarfile.open(project_path_obj, "r:gz") as tar:
                    tar.extractall(temp_path)

                # Find the extracted project directory (handle nested structure)
                ncp_toml_files = list(temp_path.rglob("ncp.toml"))
                if not ncp_toml_files:
                    click.echo("❌ Invalid package: No ncp.toml found")
                    raise click.Abort()

                project_dir = ncp_toml_files[0].parent
                _validate_project_directory(project_dir, errors, warnings)

            except tarfile.TarError as e:
                click.echo(f"❌ Invalid package: Could not extract .ncp file: {e}", err=True)
                raise click.Abort()

    elif project_path_obj.is_dir():
        click.echo(f"🔍 Validating project: {project_path_obj.name}")
        click.echo()
        _validate_project_directory(project_path_obj, errors, warnings)

    else:
        click.echo(f"❌ Path not found or invalid: {project_path}", err=True)
        raise click.Abort()


def _validate_project_directory(project_dir: Path, errors: list, warnings: list):
    """Validate a project directory structure.

    Args:
        project_dir: Path to the project directory
        errors: List to append errors to
        warnings: List to append warnings to
    """

    # Check project structure
    click.echo("📂 Checking project structure...")
    required_files = ["ncp.toml", "requirements.txt"]
    for filename in required_files:
        filepath = project_dir / filename
        if not filepath.exists():
            errors.append(f"Missing required file: {filename}")
        else:
            click.echo(f"  ✓ {filename}")

    # Optional files
    optional_files = ["apt-requirements.txt", "README.md"]
    for filename in optional_files:
        filepath = project_dir / filename
        if filepath.exists():
            click.echo(f"  ✓ {filename}")

    # Check directories
    agents_dir = project_dir / "agents"
    if not agents_dir.exists():
        errors.append("Missing required directory: agents/")
    else:
        click.echo(f"  ✓ agents/")

    tools_dir = project_dir / "tools"
    if tools_dir.exists():
        click.echo(f"  ✓ tools/")

    click.echo()

    # Validate ncp.toml
    click.echo("⚙️  Validating ncp.toml...")
    config_file = project_dir / "ncp.toml"
    if config_file.exists():
        try:
            config = toml.load(config_file)

            # Check required sections
            if "project" not in config:
                errors.append("ncp.toml missing [project] section")
            else:
                project_config = config["project"]
                if "name" not in project_config:
                    errors.append("ncp.toml [project] missing 'name'")
                else:
                    click.echo(f"  ✓ Project name: {project_config['name']}")

                if "version" in project_config:
                    click.echo(f"  ✓ Version: {project_config['version']}")

            if "build" not in config:
                warnings.append("ncp.toml missing [build] section (using defaults)")
            else:
                build_config = config["build"]
                if "entry_point" not in build_config:
                    errors.append("ncp.toml [build] missing 'entry_point'")
                else:
                    entry_point = build_config["entry_point"]
                    click.echo(f"  ✓ Entry point: {entry_point}")

        except Exception as e:
            errors.append(f"Invalid ncp.toml: {e}")

    click.echo()

    # Validate agent definitions
    click.echo("🤖 Validating agent definitions...")
    if agents_dir.exists():
        # Add project directory to path for imports
        sys.path.insert(0, str(project_dir))

        agent_files = list(agents_dir.glob("*.py"))
        agent_files = [f for f in agent_files if f.name != "__init__.py"]

        if not agent_files:
            warnings.append("No agent definition files found in agents/")
        else:
            for agent_file in agent_files:
                try:
                    # Try to load the module
                    spec = importlib.util.spec_from_file_location(
                        f"agents.{agent_file.stem}", agent_file
                    )
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)

                        # Look for Agent instances
                        agent_found = False
                        for attr_name in dir(module):
                            attr = getattr(module, attr_name)
                            # Check if it's an Agent instance (duck typing)
                            if hasattr(attr, "name") and hasattr(attr, "description") and hasattr(attr, "instructions"):
                                agent_found = True
                                click.echo(f"  ✓ {agent_file.name}: {attr.name}")
                                break

                        if not agent_found:
                            warnings.append(f"{agent_file.name}: No Agent instance found")

                except NotImplementedError as e:
                    # Silently ignore NotImplementedError from platform-only APIs (Metrics, etc.)
                    # These are type stubs that will work on the platform
                    if "only available when running on the NCP platform" in str(e):
                        # Assume agent is valid - platform will handle it
                        click.echo(f"  ✓ {agent_file.name}: (uses platform APIs)")
                    else:
                        errors.append(f"{agent_file.name}: {e}")
                except Exception as e:
                    errors.append(f"{agent_file.name}: {e}")

        # Remove from path
        sys.path.pop(0)

    click.echo()

    # Validate dependencies
    click.echo("📦 Checking dependencies...")
    requirements_file = project_dir / "requirements.txt"
    if requirements_file.exists():
        try:
            reqs = requirements_file.read_text().strip().split("\n")
            reqs = [r.strip() for r in reqs if r.strip() and not r.startswith("#")]
            if reqs:
                click.echo(f"  ✓ {len(reqs)} Python dependencies specified")
            else:
                click.echo("  ℹ No Python dependencies")
        except Exception as e:
            warnings.append(f"Could not read requirements.txt: {e}")

    apt_requirements_file = project_dir / "apt-requirements.txt"
    if apt_requirements_file.exists():
        try:
            reqs = apt_requirements_file.read_text().strip().split("\n")
            reqs = [r.strip() for r in reqs if r.strip() and not r.startswith("#")]
            if reqs:
                click.echo(f"  ✓ {len(reqs)} system dependencies specified")
            else:
                click.echo("  ℹ No system dependencies")
        except Exception as e:
            warnings.append(f"Could not read apt-requirements.txt: {e}")

    click.echo()

    # Print summary
    if warnings:
        click.echo("⚠️  Warnings:")
        for warning in warnings:
            click.echo(f"  • {warning}")
        click.echo()

    if errors:
        click.echo("❌ Validation failed with errors:")
        for error in errors:
            click.echo(f"  • {error}", err=True)
        click.echo()
        raise click.Abort()
    else:
        click.echo("✅ Validation passed!")
        if not warnings:
            click.echo("   Project is ready for packaging.")
        click.echo()
