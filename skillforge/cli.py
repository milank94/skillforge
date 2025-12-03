"""
CLI interface for SkillForge.

This module provides the command-line interface using Typer,
with rich formatting for enhanced user experience.
"""

import os
from pathlib import Path
from typing import Optional

import typer
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from skillforge import __version__
from skillforge.core.course_generator import CourseGenerator
from skillforge.models.config import AppConfig, LLMConfig
from skillforge.models.course import Course
from skillforge.models.enums import Difficulty, LLMProvider
from skillforge.utils.llm_client import LLMClientFactory
from skillforge.utils.serialization import save_to_file

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


def load_config(provider: Optional[str] = None) -> AppConfig:
    """Load configuration from environment variables.

    Args:
        provider: Optional provider override

    Returns:
        AppConfig with LLM configuration

    Raises:
        typer.Exit: If configuration is invalid
    """
    # Determine provider
    if provider:
        provider_enum = LLMProvider(provider.lower())
    else:
        provider_str = os.getenv("SKILLFORGE_LLM_PROVIDER", "anthropic")
        provider_enum = LLMProvider(provider_str.lower())

    # Get model and temperature
    if provider_enum == LLMProvider.ANTHROPIC:
        default_model = "claude-sonnet-4-5-20250929"
    else:
        default_model = "gpt-4"

    model = os.getenv("SKILLFORGE_MODEL", default_model)
    temperature = float(os.getenv("SKILLFORGE_TEMPERATURE", "0.7"))

    llm_config = LLMConfig(provider=provider_enum, model=model, temperature=temperature)

    data_dir = os.getenv("SKILLFORGE_DATA_DIR", "~/.skillforge")
    return AppConfig(llm=llm_config, data_dir=data_dir)


def display_course_overview(course: Course) -> None:
    """Display course structure using Rich formatting.

    Args:
        course: Course object to display
    """
    # Course header
    console.print(
        Panel.fit(
            f"[bold cyan]{course.topic}[/bold cyan]\n\n"
            f"{course.description}\n\n"
            f"[dim]Difficulty: {course.difficulty.value.title()} | "
            f"Lessons: {course.total_lessons()} | "
            f"Exercises: {course.total_exercises()}[/dim]",
            title="📚 Course Overview",
            border_style="cyan",
        )
    )

    # Lessons table
    table = Table(
        title="\n📖 Course Curriculum",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold magenta",
    )
    table.add_column("#", style="dim", width=3)
    table.add_column("Lesson", style="cyan")
    table.add_column("Exercises", justify="center", style="green")
    table.add_column("Objectives", style="yellow")

    for i, lesson in enumerate(course.lessons, 1):
        objectives_str = "\n".join(f"• {obj}" for obj in lesson.objectives[:2])
        if len(lesson.objectives) > 2:
            objectives_str += f"\n[dim]...and {len(lesson.objectives) - 2} more[/dim]"

        table.add_row(
            str(i), lesson.title, str(lesson.total_exercises()), objectives_str
        )

    console.print(table)


def save_course(course: Course) -> None:
    """Save course to disk.

    Args:
        course: Course object to save
    """
    course_dir = Path.home() / ".skillforge" / "courses"
    course_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{course.id}.json"
    filepath = course_dir / filename

    save_to_file(course, filepath)
    console.print(f"\n[green]✓[/green] Course saved to: [dim]{filepath}[/dim]")


@app.command()
def learn(
    topic: str = typer.Argument(..., help="The topic you want to learn"),
    difficulty: str = typer.Option(
        "beginner",
        "--difficulty",
        "-d",
        help="Difficulty level: beginner, intermediate, or advanced",
    ),
    lessons: int = typer.Option(
        5, "--lessons", "-l", help="Number of lessons to generate (1-20)"
    ),
    provider: Optional[str] = typer.Option(
        None,
        "--provider",
        "-p",
        help="LLM provider: anthropic or openai (default: from env)",
    ),
    interactive: bool = typer.Option(
        True, "--interactive/--no-interactive", help="Enable interactive mode"
    ),
) -> None:
    """
    Start a new learning session with AI-generated course.

    Examples:
        skillforge learn "pytorch basics"
        skillforge learn "docker fundamentals" --difficulty advanced
        skillforge learn "kubernetes" --lessons 7 --provider openai
    """
    # Validate difficulty
    try:
        difficulty_enum = Difficulty(difficulty.lower())
    except ValueError:
        console.print(
            f"[bold red]Error:[/bold red] Invalid difficulty '{difficulty}'. "
            f"Must be: beginner, intermediate, or advanced"
        )
        raise typer.Exit(1)

    # Validate lesson count
    if lessons < 1 or lessons > 20:
        console.print(
            "[bold red]Error:[/bold red] Number of lessons must be between 1 and 20"
        )
        raise typer.Exit(1)

    # Load configuration
    try:
        config = load_config(provider)
    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] Failed to load configuration: {e}")
        raise typer.Exit(1)

    # Create LLM client
    try:
        llm_client = LLMClientFactory.create_client(config.llm)
    except ValueError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        console.print("\n[yellow]Make sure your API key is set:[/yellow]")
        if config.llm.provider == LLMProvider.ANTHROPIC:
            console.print("  export ANTHROPIC_API_KEY=your-key")
        else:
            console.print("  export OPENAI_API_KEY=your-key")
        raise typer.Exit(1)

    # Display generation info
    console.print(f"\n[bold cyan]Generating course:[/bold cyan] {topic}")
    console.print(
        f"[dim]Difficulty: {difficulty_enum.value.title()} | "
        f"Lessons: {lessons} | "
        f"Provider: {config.llm.provider.value}[/dim]\n"
    )

    # Generate course with progress indicator
    with console.status(
        "[bold green]Generating your personalized course...[/bold green]",
        spinner="dots",
    ):
        try:
            generator = CourseGenerator(llm_client)
            course = generator.generate_course(
                topic=topic, difficulty=difficulty_enum, num_lessons=lessons
            )
        except Exception as e:
            console.print(
                f"\n[bold red]Error:[/bold red] Failed to generate course: {e}"
            )
            raise typer.Exit(1)

    # Display course overview
    console.print("\n")
    display_course_overview(course)

    # Offer to save course
    console.print()
    if typer.confirm("Save this course for later?", default=True):
        save_course(course)

    # Interactive mode note (Phase 4)
    if interactive:
        console.print(
            "\n[yellow]Note:[/yellow] Interactive learning sessions coming in Phase 4!"
        )
        console.print(
            "[dim]For now, you can view the course structure above and "
            "practice on your own.[/dim]"
        )

    console.print("\n[bold green]✓[/bold green] Course generation complete!\n")


@app.command()
def cache_clear() -> None:
    """Clear the course generation cache."""
    # Load minimal config just to create generator
    try:
        config = load_config()
        llm_client = LLMClientFactory.create_client(config.llm)
        generator = CourseGenerator(llm_client)

        count = generator.clear_cache()

        if count > 0:
            plural = "s" if count != 1 else ""
            console.print(
                f"[green]✓[/green] Cleared {count} cached course{plural}"
            )
        else:
            console.print("[yellow]No cached courses found[/yellow]")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] Failed to clear cache: {e}")
        raise typer.Exit(1)


@app.command()
def cache_info() -> None:
    """Show cache statistics."""
    try:
        config = load_config()
        llm_client = LLMClientFactory.create_client(config.llm)
        generator = CourseGenerator(llm_client)

        stats = generator.get_cache_stats()

        table = Table(title="📊 Cache Statistics", box=box.ROUNDED)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Cached Courses", str(stats["cached_courses"]))
        table.add_row("Total Size", f"{stats['total_size_bytes'] / 1024:.2f} KB")
        table.add_row("Cache Directory", stats["cache_dir"])

        console.print()
        console.print(table)
        console.print()

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] Failed to get cache info: {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
