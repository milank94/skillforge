"""
Rich formatting helpers for interactive learning sessions.

This module provides the SessionDisplay class for rendering course content,
exercise prompts, validation results, and progress summaries in the terminal.
"""

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from skillforge.core.validator import ValidationResult, ValidationStatus
from skillforge.models.course import Course
from skillforge.models.lesson import Exercise, Lesson
from skillforge.models.progress import CourseProgress, LessonProgress


class SessionDisplay:
    """Rich terminal display for interactive learning sessions."""

    def __init__(self, console: Console | None = None) -> None:
        """Initialize the session display.

        Args:
            console: Rich Console instance (creates one if not provided)
        """
        self.console = console or Console()

    def display_welcome(self, course: Course) -> None:
        """Display welcome panel with course info and available commands.

        Args:
            course: The course being started
        """
        content = (
            f"[bold cyan]{course.topic}[/bold cyan]\n\n"
            f"{course.description}\n\n"
            f"[dim]Difficulty: {course.difficulty.value.title()} | "
            f"Lessons: {course.total_lessons()} | "
            f"Exercises: {course.total_exercises()}[/dim]\n\n"
            f"[yellow]Commands:[/yellow] "
            f"[dim]hint, skip, quit, help, status[/dim]"
        )
        self.console.print(
            Panel(content, title="Welcome to SkillForge", border_style="green")
        )

    def display_lesson_header(
        self, lesson: Lesson, lesson_num: int, total_lessons: int
    ) -> None:
        """Display lesson header with title and objectives.

        Args:
            lesson: The lesson to display
            lesson_num: Current lesson number (1-based)
            total_lessons: Total number of lessons
        """
        objectives = "\n".join(f"  - {obj}" for obj in lesson.objectives)
        content = (
            f"[bold]{lesson.title}[/bold]\n\n"
            f"[yellow]Objectives:[/yellow]\n{objectives}"
        )
        self.console.print(
            Panel(
                content,
                title=f"Lesson {lesson_num}/{total_lessons}",
                border_style="cyan",
            )
        )

    def display_exercise(
        self, exercise: Exercise, exercise_num: int, total_exercises: int
    ) -> None:
        """Display exercise instruction panel.

        Args:
            exercise: The exercise to display
            exercise_num: Current exercise number (1-based)
            total_exercises: Total exercises in lesson
        """
        self.console.print(
            Panel(
                exercise.instruction,
                title=f"Exercise {exercise_num}/{total_exercises}",
                border_style="blue",
            )
        )

    def display_simulation_result(self, output: str) -> None:
        """Display simulated command output.

        Args:
            output: The simulation output text
        """
        if output:
            self.console.print(Panel(output, title="Output", border_style="dim"))

    def display_validation_result(self, result: ValidationResult) -> None:
        """Display color-coded validation feedback.

        Args:
            result: The validation result to display
        """
        if result.status == ValidationStatus.CORRECT:
            style = "green"
            icon = "✓"
        elif result.status == ValidationStatus.PARTIAL:
            style = "yellow"
            icon = "~"
        else:
            style = "red"
            icon = "✗"

        self.console.print(f"[bold {style}]{icon} {result.feedback}[/bold {style}]")

    def display_hint(self, hint: str, attempt: int) -> None:
        """Display a hint panel.

        Args:
            hint: The hint text
            attempt: Current attempt number
        """
        self.console.print(
            Panel(hint, title=f"Hint (attempt {attempt})", border_style="yellow")
        )

    def display_lesson_complete(self, lesson: Lesson, progress: LessonProgress) -> None:
        """Display lesson completion summary.

        Args:
            lesson: The completed lesson
            progress: Progress data for the lesson
        """
        pct = progress.calculate_completion_percentage()
        self.console.print(
            Panel(
                f"[bold green]Lesson Complete![/bold green]\n\n"
                f"{lesson.title}\n"
                f"Completion: {pct:.0f}%",
                border_style="green",
            )
        )

    def display_course_complete(self, progress: CourseProgress) -> None:
        """Display final course completion with stats.

        Args:
            progress: Course progress data
        """
        pct = progress.calculate_completion_percentage()
        total_exercises = sum(
            len(lp.exercise_progress) for lp in progress.lesson_progress
        )
        completed_exercises = sum(
            1
            for lp in progress.lesson_progress
            for ep in lp.exercise_progress
            if ep.status.value == "completed"
        )

        self.console.print(
            Panel(
                f"[bold green]Course Complete![/bold green]\n\n"
                f"Lessons: {len(progress.lesson_progress)}\n"
                f"Exercises: {completed_exercises}/{total_exercises}\n"
                f"Overall: {pct:.0f}%",
                title="Congratulations!",
                border_style="green",
            )
        )

    def display_progress_summary(self, progress: CourseProgress) -> None:
        """Display progress table.

        Args:
            progress: Course progress data
        """
        table = Table(title="Progress", box=box.ROUNDED)
        table.add_column("Lesson", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Completion", justify="right")

        for lp in progress.lesson_progress:
            pct = lp.calculate_completion_percentage()
            table.add_row(
                lp.lesson_id,
                lp.status.value.replace("_", " ").title(),
                f"{pct:.0f}%",
            )

        self.console.print(table)

    def display_commands_help(self) -> None:
        """Display available special commands."""
        table = Table(title="Available Commands", box=box.SIMPLE)
        table.add_column("Command", style="cyan")
        table.add_column("Description")

        table.add_row("hint", "Get a hint for the current exercise")
        table.add_row("skip", "Skip the current exercise")
        table.add_row("quit / exit", "Save progress and exit")
        table.add_row("help", "Show this help")
        table.add_row("status", "Show progress summary")

        self.console.print(table)

    def prompt_answer(self) -> str:
        """Prompt the user for an answer.

        Returns:
            The user's input string
        """
        text = Text("Your answer > ", style="bold cyan")
        return self.console.input(text)

    def prompt_continue(self) -> bool:
        """Prompt the user to continue.

        Returns:
            True if user wants to continue
        """
        response = self.console.input(Text("Continue? [Y/n] > ", style="bold cyan"))
        return response.strip().lower() != "n"
