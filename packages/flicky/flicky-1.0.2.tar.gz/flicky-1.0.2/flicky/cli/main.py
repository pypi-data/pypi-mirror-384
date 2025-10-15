"""Flicky CLI - Command-line interface for the Flick framework."""

import click
from rich.console import Console
from .commands.create import create_widget

console = Console()

@click.group()
@click.version_option(version="1.0.1", prog_name="flicky")
def cli():
    """Flicky - ChatGPT Widget Framework
    
    Build interactive ChatGPT widgets with zero boilerplate.
    """
    pass

@cli.command()
@click.argument("project_name")
def init(project_name):
    """Initialize a new Flicky project."""
    console.print(f"[green]Creating new Flicky project: {project_name}[/green]")
    console.print("[yellow]This feature will be implemented in Phase 4[/yellow]")
    console.print("\n[cyan]For now, see the example project:[/cyan]")
    console.print("  https://github.com/flick-framework/flicky/tree/main/example")

@cli.command()
@click.argument("widget_name")
def create(widget_name):
    """Create a new widget with tool and component files.
    
    Example:
        flicky create mywidget
        flicky create my-cool-widget
    """
    create_widget(widget_name)

@cli.command()
def dev():
    """Start development server with hot reload."""
    console.print("[green]Starting development server...[/green]")
    console.print("[yellow]This feature will be implemented in Phase 4[/yellow]")
    console.print("\n[cyan]For now, use:[/cyan]")
    console.print("  python server/main.py")

@cli.command()
def build():
    """Build widgets for production."""
    console.print("[green]Building widgets...[/green]")
    console.print("[yellow]This feature will be implemented in Phase 4[/yellow]")
    console.print("\n[cyan]For now, use:[/cyan]")
    console.print("  npm run build")

if __name__ == "__main__":
    cli()
