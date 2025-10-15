"""Floydr CLI - Command-line interface for the Floydr framework."""

import click
from rich.console import Console
from .commands.create import create_widget

console = Console()

@click.group()
@click.version_option(version="1.0.3", prog_name="floydr")
def cli():
    """Floydr - ChatGPT Widget Framework
    
    Build interactive ChatGPT widgets with zero boilerplate.
    """
    pass

@cli.command()
@click.argument("project_name")
def init(project_name):
    """Initialize a new Floydr project."""
    console.print(f"[green]Creating new Floydr project: {project_name}[/green]")
    console.print("[yellow]This feature will be implemented in Phase 4[/yellow]")
    console.print("\n[cyan]For now, see the example project:[/cyan]")
    console.print("  https://github.com/floydr-framework/floydr/tree/main/example")

@cli.command()
@click.argument("widget_name")
def create(widget_name):
    """Create a new widget with tool and component files.
    
    Example:
        floydr create mywidget
        floydr create my-cool-widget
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
