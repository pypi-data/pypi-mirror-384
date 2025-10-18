"""Generate new components (models, services, routes)."""

import typer
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.panel import Panel

from fastinit.generators.component import ComponentGenerator

app = typer.Typer()
console = Console()


@app.command()
def model(
    name: str = typer.Argument(..., help="Name of the model to generate"),
    project_dir: Optional[Path] = typer.Option(
        None,
        "--project-dir",
        "-p",
        help="Project directory (defaults to current directory)",
    ),
    fields: Optional[str] = typer.Option(
        None,
        "--fields",
        "-f",
        help="Fields in format 'name:type,email:str,age:int'",
    ),
):
    """
    Generate a new SQLAlchemy model.

    Example:
        FastInit new model User --fields "name:str,email:str,age:int"
    """
    if project_dir is None:
        project_dir = Path.cwd()

    try:
        generator = ComponentGenerator(project_dir)

        # Parse fields if provided
        field_dict = {}
        if fields:
            for field in fields.split(","):
                field_name, field_type = field.split(":")
                field_dict[field_name.strip()] = field_type.strip()

        generator.generate_model(name, field_dict if field_dict else None)

        console.print(
            Panel.fit(
                f"[bold green]✓[/bold green] Model '{name}' generated successfully!",
                border_style="green",
            )
        )
        console.print(f"\n  Location: [cyan]app/models/{name.lower()}.py[/cyan]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)


@app.command()
def service(
    name: str = typer.Argument(..., help="Name of the service to generate"),
    project_dir: Optional[Path] = typer.Option(
        None,
        "--project-dir",
        "-p",
        help="Project directory (defaults to current directory)",
    ),
    model: Optional[str] = typer.Option(
        None,
        "--model",
        "-m",
        help="Associated model name",
    ),
    pagination: str = typer.Option(
        "limit-offset",
        "--pagination",
        help="Pagination type: 'limit-offset', 'cursor', or 'none'",
    ),
):
    """
    Generate a new service class.

    Example:
        FastInit new service UserService --model User
        FastInit new service UserService --pagination cursor
    """
    if project_dir is None:
        project_dir = Path.cwd()

    # Validate pagination option
    valid_pagination = ["limit-offset", "cursor", "none"]
    if pagination not in valid_pagination:
        console.print(
            f"[red]Error:[/red] Invalid pagination type '{pagination}'. "
            f"Must be one of: {', '.join(valid_pagination)}"
        )
        raise typer.Exit(1)

    try:
        generator = ComponentGenerator(project_dir)
        generator.generate_service(name, model, pagination_type=pagination)

        console.print(
            Panel.fit(
                f"[bold green]✓[/bold green] Service '{name}' generated successfully!",
                border_style="green",
            )
        )
        console.print(
            f"\n  Location: [cyan]app/services/{name.lower().replace('service', '')}_service.py[/cyan]"
        )

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)


@app.command()
def route(
    name: str = typer.Argument(..., help="Name of the route to generate"),
    project_dir: Optional[Path] = typer.Option(
        None,
        "--project-dir",
        "-p",
        help="Project directory (defaults to current directory)",
    ),
    service: Optional[str] = typer.Option(
        None,
        "--service",
        "-s",
        help="Associated service name",
    ),
    pagination: str = typer.Option(
        "limit-offset",
        "--pagination",
        help="Pagination type: 'limit-offset', 'cursor', or 'none'",
    ),
):
    """
    Generate a new API route.

    Example:
        FastInit new route users --service UserService
        FastInit new route users --pagination cursor
        FastInit new route users --pagination none
    """
    if project_dir is None:
        project_dir = Path.cwd()

    # Validate pagination option
    valid_pagination = ["limit-offset", "cursor", "none"]
    if pagination not in valid_pagination:
        console.print(
            f"[red]Error:[/red] Invalid pagination type '{pagination}'. "
            f"Must be one of: {', '.join(valid_pagination)}"
        )
        raise typer.Exit(1)

    try:
        generator = ComponentGenerator(project_dir)
        generator.generate_route(name, service, pagination_type=pagination)

        console.print(
            Panel.fit(
                f"[bold green]✓[/bold green] Route '{name}' generated successfully!",
                border_style="green",
            )
        )
        console.print(f"\n  Location: [cyan]app/api/routes/{name.lower()}.py[/cyan]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)


@app.command()
def schema(
    name: str = typer.Argument(..., help="Name of the schema to generate"),
    project_dir: Optional[Path] = typer.Option(
        None,
        "--project-dir",
        "-p",
        help="Project directory (defaults to current directory)",
    ),
    fields: Optional[str] = typer.Option(
        None,
        "--fields",
        "-f",
        help="Fields in format 'name:type,email:str,age:int'",
    ),
):
    """
    Generate Pydantic schemas.

    Example:
        FastInit new schema User --fields "name:str,email:str,age:int"
    """
    if project_dir is None:
        project_dir = Path.cwd()

    try:
        generator = ComponentGenerator(project_dir)

        # Parse fields if provided
        field_dict = {}
        if fields:
            for field in fields.split(","):
                field_name, field_type = field.split(":")
                field_dict[field_name.strip()] = field_type.strip()

        generator.generate_schema(name, field_dict if field_dict else None)

        console.print(
            Panel.fit(
                f"[bold green]✓[/bold green] Schema '{name}' generated successfully!",
                border_style="green",
            )
        )
        console.print(f"\n  Location: [cyan]app/schemas/{name.lower()}.py[/cyan]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)


@app.command()
def crud(
    name: str = typer.Argument(..., help="Name of the entity (model name)"),
    project_dir: Optional[Path] = typer.Option(
        None,
        "--project-dir",
        "-p",
        help="Project directory (defaults to current directory)",
    ),
    fields: Optional[str] = typer.Option(
        None,
        "--fields",
        "-f",
        help="Fields in format 'name:type,email:str,age:int'",
    ),
    pagination: str = typer.Option(
        "limit-offset",
        "--pagination",
        help="Pagination type: 'limit-offset', 'cursor', or 'none'",
    ),
):
    """
    Generate a complete CRUD setup (model + service + route).

    Example:
        FastInit new crud Product --fields "name:str,price:float,description:str"
        FastInit new crud Product --pagination cursor
        FastInit new crud Product --pagination none
    """
    if project_dir is None:
        project_dir = Path.cwd()

    # Validate pagination option
    valid_pagination = ["limit-offset", "cursor", "none"]
    if pagination not in valid_pagination:
        console.print(
            f"[red]Error:[/red] Invalid pagination type '{pagination}'. "
            f"Must be one of: {', '.join(valid_pagination)}"
        )
        raise typer.Exit(1)

    try:
        generator = ComponentGenerator(project_dir)

        # Parse fields if provided
        field_dict = {}
        if fields:
            for field in fields.split(","):
                field_name, field_type = field.split(":")
                field_dict[field_name.strip()] = field_type.strip()

        # Check if any files already exist before generating
        model_file = generator.app_dir / "models" / f"{name.lower()}.py"
        service_file = generator.app_dir / "services" / f"{name.lower()}_service.py"
        route_file = generator.app_dir / "api" / "routes" / f"{name.lower()}s.py"
        schema_file = generator.app_dir / "schemas" / f"{name.lower()}.py"

        existing_files = []
        if model_file.exists():
            existing_files.append(f"app/models/{name.lower()}.py")
        if service_file.exists():
            existing_files.append(f"app/services/{name.lower()}_service.py")
        if route_file.exists():
            existing_files.append(f"app/api/routes/{name.lower()}s.py")
        if schema_file.exists():
            existing_files.append(f"app/schemas/{name.lower()}.py")

        if existing_files:
            console.print("[red]Error:[/red] The following files already exist:")
            for file in existing_files:
                console.print(f"  • [yellow]{file}[/yellow]")
            console.print("\nPlease delete these files or use a different name.")
            raise typer.Exit(1)

        console.print(f"\n[bold]Generating CRUD for '{name}'...[/bold]\n")

        # Generate model
        console.print("  [cyan]→[/cyan] Creating model...")
        generator.generate_model(name, field_dict if field_dict else None)

        # Generate schema
        console.print("  [cyan]→[/cyan] Creating schema...")
        generator.generate_schema(name, field_dict if field_dict else None)

        # Generate service
        console.print("  [cyan]→[/cyan] Creating service...")
        service_name = f"{name}Service"
        generator.generate_service(service_name, name, pagination_type=pagination)

        # Generate route
        console.print("  [cyan]→[/cyan] Creating route...")
        route_name = f"{name.lower()}s"
        generator.generate_route(route_name, service_name, pagination_type=pagination)

        console.print()
        console.print(
            Panel.fit(
                f"[bold green]✓[/bold green] CRUD for '{name}' generated successfully!",
                border_style="green",
            )
        )
        console.print("\n[bold]Generated files:[/bold]")
        console.print(f"  • [cyan]app/models/{name.lower()}.py[/cyan]")
        console.print(f"  • [cyan]app/schemas/{name.lower()}.py[/cyan]")
        console.print(f"  • [cyan]app/services/{name.lower()}_service.py[/cyan]")
        console.print(f"  • [cyan]app/api/routes/{route_name}.py[/cyan]")
        console.print()

    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
