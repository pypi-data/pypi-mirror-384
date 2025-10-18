"""Initialize command to bootstrap a new FastAPI project."""

import typer
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm, Prompt
from rich import print as rprint

from fastinit.generators.project import ProjectGenerator
from fastinit.models.config import ProjectConfig

console = Console()


def main(
    project_name: str = typer.Argument(..., help="Name of the project to create"),
    output_dir: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output directory (defaults to current directory)",
    ),
    db: bool = typer.Option(
        False, "--db", help="Include database support (SQLAlchemy)"
    ),
    db_type: str = typer.Option(
        "postgresql",
        "--db-type",
        help="Database type (postgresql, mysql, sqlite)",
    ),
    jwt: bool = typer.Option(
        False, "--jwt", help="Include JWT authentication with PyJWT"
    ),
    logging: bool = typer.Option(
        False, "--logging", help="Include logging configuration"
    ),
    docker: bool = typer.Option(False, "--docker", help="Include Docker configuration"),
    interactive: bool = typer.Option(
        False,
        "--interactive",
        "-i",
        help="Interactive mode - prompt for all options",
    ),
    python_version: str = typer.Option(
        "3.11",
        "--python-version",
        help="Python version to use",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        "-f",
        help="Overwrite existing directory if it exists",
    ),
):
    """
    Initialize a new FastAPI project with optional features.

    Examples:

        FastInit init my-project

        FastInit init my-project --db --jwt --logging

        FastInit init my-project --interactive
    """
    # Display welcome banner
    rprint(
        Panel.fit(
            "[bold cyan]FastInit[/bold cyan] - FastAPI Project Generator",
            border_style="cyan",
        )
    )

    # Interactive mode
    if interactive:
        console.print("\n[bold]Let's configure your FastAPI project![/bold]\n")
        db = Confirm.ask("Include database support?", default=db)
        if db:
            db_type = Prompt.ask(
                "Database type",
                choices=["postgresql", "mysql", "sqlite"],
                default=db_type,
            )
        jwt = Confirm.ask("Include JWT authentication?", default=jwt)
        logging = Confirm.ask("Include logging configuration?", default=logging)
        docker = Confirm.ask("Include Docker configuration?", default=docker)
        python_version = Prompt.ask("Python version", default=python_version)

    # Validate database type
    if db and db_type not in ["postgresql", "mysql", "sqlite"]:
        console.print(f"[red]Error:[/red] Invalid database type '{db_type}'")
        console.print("Valid options: postgresql, mysql, sqlite")
        raise typer.Exit(1)

    # Set output directory
    if output_dir is None:
        output_dir = Path.cwd()

    project_path = output_dir / project_name

    # Check if directory exists
    if project_path.exists() and not force:
        console.print(f"[red]Error:[/red] Directory '{project_path}' already exists")
        console.print("Use --force to overwrite")
        raise typer.Exit(1)

    # Create project configuration
    config = ProjectConfig(
        project_name=project_name,
        output_dir=output_dir,
        use_db=db,
        db_type=db_type if db else None,
        use_jwt=jwt,
        use_logging=logging,
        use_docker=docker,
        python_version=python_version,
    )

    # Display configuration
    console.print("\n[bold]Project Configuration:[/bold]")
    console.print(f"  Name: [cyan]{project_name}[/cyan]")
    console.print(f"  Location: [cyan]{project_path}[/cyan]")
    console.print(f"  Python Version: [cyan]{python_version}[/cyan]")
    console.print(f"  Database: [cyan]{db_type if db else 'None'}[/cyan]")
    console.print(f"  JWT Auth: [cyan]{'Yes' if jwt else 'No'}[/cyan]")
    console.print(f"  Logging: [cyan]{'Yes' if logging else 'No'}[/cyan]")
    console.print(f"  Docker: [cyan]{'Yes' if docker else 'No'}[/cyan]")
    console.print()

    # Generate project
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Generating project...", total=None)

            generator = ProjectGenerator(config)
            generator.generate()

            progress.update(task, completed=True)

        # Success message
        console.print()
        console.print(
            Panel.fit(
                f"[bold green]✓[/bold green] Project '{project_name}' created successfully!",
                border_style="green",
            )
        )

        # Next steps
        console.print("\n[bold]Next steps:[/bold]")
        console.print(f"  1. cd {project_name}")
        console.print("  2. python -m venv venv")
        console.print(
            "  3. venv\\Scripts\\activate (Windows) or source venv/bin/activate (Unix)"
        )
        console.print("  4. pip install -r requirements.txt")
        if db:
            console.print("  5. Copy .env.example to .env and configure your database")
            console.print("  6. cd app")
            console.print("  7. uvicorn main:app --reload (or: fastapi dev main.py)")
        else:
            console.print("  5. cd app")
            console.print("  6. uvicorn main:app --reload (or: fastapi dev main.py)")
        console.print()

    except Exception as e:
        console.print(f"\n[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)


if __name__ == "__main__":
    typer.run(main)
