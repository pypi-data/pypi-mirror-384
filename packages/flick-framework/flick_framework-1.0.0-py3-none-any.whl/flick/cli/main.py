"""Flick CLI - Command-line interface for the Flick framework."""

import click
from rich.console import Console

console = Console()

@click.group()
@click.version_option(version="1.0.0", prog_name="flick")
def cli():
    """Flick - ChatGPT Widget Framework"""
    pass

@cli.command()
@click.argument("project_name")
def init(project_name):
    """Initialize a new Flick project."""
    console.print(f"[green]Creating new Flick project: {project_name}[/green]")
    console.print("[yellow]This feature will be implemented in Phase 4[/yellow]")

@cli.command()
@click.argument("widget_name")
def create(widget_name):
    """Create a new widget."""
    console.print(f"[green]Creating widget: {widget_name}[/green]")
    console.print("[yellow]This feature will be implemented in Phase 4[/yellow]")

@cli.command()
def dev():
    """Start development server with hot reload."""
    console.print("[green]Starting development server...[/green]")
    console.print("[yellow]This feature will be implemented in Phase 4[/yellow]")

@cli.command()
def build():
    """Build widgets for production."""
    console.print("[green]Building widgets...[/green]")
    console.print("[yellow]This feature will be implemented in Phase 4[/yellow]")

if __name__ == "__main__":
    cli()

