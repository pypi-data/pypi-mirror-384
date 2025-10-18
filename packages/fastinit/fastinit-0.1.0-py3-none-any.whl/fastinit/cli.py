"""Main CLI application using Typer."""

import typer
from rich.console import Console
from rich.panel import Panel
from rich import print as rprint

from fastinit.commands import init, new

app = typer.Typer(
    name="fastinit",
    help="🚀 Bootstrap FastAPI applications with best practices",
    add_completion=True,
)
console = Console()

# Add init command directly
app.command(name="init", help="Initialize a new FastAPI project")(init.main)

# Add new subcommands
app.add_typer(
    new.app, name="new", help="Generate new components (models, services, routes)"
)


@app.command()
def version():
    """Show the version of fastinit."""
    from fastinit import __version__

    rprint(
        Panel.fit(
            f"[bold cyan]FastInit[/bold cyan] version [green]{__version__}[/green]",
            border_style="cyan",
        )
    )


@app.callback()
def main():
    """
    FastInit - A CLI tool to bootstrap FastAPI applications with best practices.
    """
    pass


if __name__ == "__main__":
    app()
