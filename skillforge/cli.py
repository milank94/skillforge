"""
CLI interface for SkillForge.

This module provides the command-line interface using Typer,
with rich formatting for enhanced user experience.
"""

import typer
from rich.console import Console
from rich.panel import Panel

from skillforge import __version__

# Initialize Typer app and Rich console
app = typer.Typer(
    name="skillforge",
    help="AI-powered interactive learning CLI for developers",
    add_completion=False,
)
console = Console()


def version_callback(value: bool) -> None:
    """Display version information and exit."""
    if value:
        console.print(
            f"[bold cyan]SkillForge[/bold cyan] version [green]{__version__}[/green]"
        )
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        help="Show version and exit",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    """
    SkillForge - AI-powered interactive learning for developers.

    Learn new technologies through hands-on practice in safe, simulated environments.
    """
    pass


@app.command()
def learn(
    topic: str = typer.Argument(..., help="The topic you want to learn"),
    interactive: bool = typer.Option(
        True, "--interactive/--no-interactive", help="Enable interactive mode"
    ),
) -> None:
    """
    Start a new learning session on a specific topic.

    Examples:
        skillforge learn "pytorch basics"
        skillforge learn "docker fundamentals"
        skillforge learn "kubernetes"
    """
    console.print(
        Panel.fit(
            f"[bold green]Starting learning session![/bold green]\n\n"
            f"Topic: [cyan]{topic}[/cyan]\n"
            f"Interactive: [yellow]{'Yes' if interactive else 'No'}[/yellow]\n\n"
            f"[dim]Note: Full course generation will be implemented "
            f"in the next phase.[/dim]",
            title="SkillForge",
            border_style="green",
        )
    )

    console.print("\n[yellow]Coming soon:[/yellow]")
    console.print("  • AI-generated personalized curriculum")
    console.print("  • Step-by-step interactive lessons")
    console.print("  • Safe command simulation")
    console.print("  • Real-time feedback and validation")
    console.print()


if __name__ == "__main__":
    app()
