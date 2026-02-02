"""Tests for the SessionDisplay output utilities."""

from io import StringIO
from unittest.mock import patch

from rich.console import Console

from skillforge.core.validator import ValidationResult, ValidationStatus
from skillforge.models.course import Course
from skillforge.models.enums import Difficulty, ProgressStatus
from skillforge.models.lesson import Exercise, Lesson
from skillforge.models.progress import (
    CourseProgress,
    ExerciseProgress,
    LessonProgress,
)
from skillforge.utils.output import SessionDisplay


def make_console() -> tuple[Console, StringIO]:
    """Create a Console that writes to a StringIO buffer."""
    buf = StringIO()
    console = Console(file=buf, force_terminal=True, width=120)
    return console, buf


def make_course() -> Course:
    """Create a sample course for testing."""
    return Course(
        id="c1",
        topic="Git Basics",
        description="Learn git fundamentals",
        difficulty=Difficulty.BEGINNER,
        lessons=[
            Lesson(
                id="l1",
                title="Introduction to Git",
                objectives=["Understand VCS", "Install git"],
                exercises=[
                    Exercise(
                        id="e1",
                        instruction="Run git init",
                        expected_output="Initialized empty Git repository",
                        hints=["Try: git init"],
                    ),
                    Exercise(
                        id="e2",
                        instruction="Check git status",
                        expected_output="On branch main",
                    ),
                ],
            ),
            Lesson(
                id="l2",
                title="Branching",
                objectives=["Create branches"],
                exercises=[
                    Exercise(id="e3", instruction="Create a branch"),
                ],
            ),
        ],
    )


def make_progress() -> CourseProgress:
    """Create sample progress."""
    return CourseProgress(
        course_id="c1",
        user_id="user1",
        status=ProgressStatus.IN_PROGRESS,
        lesson_progress=[
            LessonProgress(
                lesson_id="l1",
                status=ProgressStatus.COMPLETED,
                exercise_progress=[
                    ExerciseProgress(
                        exercise_id="e1", status=ProgressStatus.COMPLETED, attempts=1
                    ),
                    ExerciseProgress(
                        exercise_id="e2", status=ProgressStatus.COMPLETED, attempts=2
                    ),
                ],
            ),
            LessonProgress(
                lesson_id="l2",
                status=ProgressStatus.NOT_STARTED,
                exercise_progress=[
                    ExerciseProgress(
                        exercise_id="e3", status=ProgressStatus.NOT_STARTED
                    ),
                ],
            ),
        ],
    )


class TestSessionDisplayWelcome:
    """Tests for display_welcome."""

    def test_welcome_shows_topic(self) -> None:
        console, buf = make_console()
        display = SessionDisplay(console)
        display.display_welcome(make_course())
        output = buf.getvalue()
        assert "Git Basics" in output

    def test_welcome_shows_description(self) -> None:
        console, buf = make_console()
        display = SessionDisplay(console)
        display.display_welcome(make_course())
        output = buf.getvalue()
        assert "git fundamentals" in output

    def test_welcome_shows_commands(self) -> None:
        console, buf = make_console()
        display = SessionDisplay(console)
        display.display_welcome(make_course())
        output = buf.getvalue()
        assert "hint" in output
        assert "skip" in output
        assert "quit" in output


class TestSessionDisplayLessonHeader:
    """Tests for display_lesson_header."""

    def test_shows_lesson_title(self) -> None:
        console, buf = make_console()
        display = SessionDisplay(console)
        course = make_course()
        display.display_lesson_header(course.lessons[0], 1, 2)
        output = buf.getvalue()
        assert "Introduction to Git" in output

    def test_shows_objectives(self) -> None:
        console, buf = make_console()
        display = SessionDisplay(console)
        course = make_course()
        display.display_lesson_header(course.lessons[0], 1, 2)
        output = buf.getvalue()
        assert "Understand VCS" in output

    def test_shows_lesson_number(self) -> None:
        console, buf = make_console()
        display = SessionDisplay(console)
        course = make_course()
        display.display_lesson_header(course.lessons[0], 1, 2)
        output = buf.getvalue()
        assert "1/2" in output


class TestSessionDisplayExercise:
    """Tests for display_exercise."""

    def test_shows_instruction(self) -> None:
        console, buf = make_console()
        display = SessionDisplay(console)
        ex = Exercise(id="e1", instruction="Run git init")
        display.display_exercise(ex, 1, 3)
        output = buf.getvalue()
        assert "Run git init" in output

    def test_shows_exercise_number(self) -> None:
        console, buf = make_console()
        display = SessionDisplay(console)
        ex = Exercise(id="e1", instruction="Run git init")
        display.display_exercise(ex, 2, 5)
        output = buf.getvalue()
        assert "2/5" in output


class TestSessionDisplaySimulationResult:
    """Tests for display_simulation_result."""

    def test_shows_output(self) -> None:
        console, buf = make_console()
        display = SessionDisplay(console)
        display.display_simulation_result("hello world")
        output = buf.getvalue()
        assert "hello world" in output

    def test_empty_output_no_panel(self) -> None:
        console, buf = make_console()
        display = SessionDisplay(console)
        display.display_simulation_result("")
        output = buf.getvalue()
        assert "Output" not in output


class TestSessionDisplayValidationResult:
    """Tests for display_validation_result."""

    def test_correct_shows_green(self) -> None:
        console, buf = make_console()
        display = SessionDisplay(console)
        result = ValidationResult(
            status=ValidationStatus.CORRECT, score=1.0, feedback="Well done!"
        )
        display.display_validation_result(result)
        output = buf.getvalue()
        assert "Well done!" in output

    def test_incorrect_shows_feedback(self) -> None:
        console, buf = make_console()
        display = SessionDisplay(console)
        result = ValidationResult(
            status=ValidationStatus.INCORRECT, score=0.0, feedback="Try again."
        )
        display.display_validation_result(result)
        output = buf.getvalue()
        assert "Try again." in output

    def test_partial_shows_feedback(self) -> None:
        console, buf = make_console()
        display = SessionDisplay(console)
        result = ValidationResult(
            status=ValidationStatus.PARTIAL, score=0.5, feedback="Almost there."
        )
        display.display_validation_result(result)
        output = buf.getvalue()
        assert "Almost there." in output


class TestSessionDisplayHint:
    """Tests for display_hint."""

    def test_shows_hint_text(self) -> None:
        console, buf = make_console()
        display = SessionDisplay(console)
        display.display_hint("Try using git init", 1)
        output = buf.getvalue()
        assert "Try using git init" in output

    def test_shows_attempt_number(self) -> None:
        console, buf = make_console()
        display = SessionDisplay(console)
        display.display_hint("Another hint", 3)
        output = buf.getvalue()
        assert "3" in output


class TestSessionDisplayLessonComplete:
    """Tests for display_lesson_complete."""

    def test_shows_completion(self) -> None:
        console, buf = make_console()
        display = SessionDisplay(console)
        course = make_course()
        progress = make_progress()
        display.display_lesson_complete(course.lessons[0], progress.lesson_progress[0])
        output = buf.getvalue()
        assert "Lesson Complete" in output
        assert "Introduction to Git" in output


class TestSessionDisplayCourseComplete:
    """Tests for display_course_complete."""

    def test_shows_congratulations(self) -> None:
        console, buf = make_console()
        display = SessionDisplay(console)
        progress = make_progress()
        display.display_course_complete(progress)
        output = buf.getvalue()
        assert "Course Complete" in output


class TestSessionDisplayProgressSummary:
    """Tests for display_progress_summary."""

    def test_shows_lesson_progress(self) -> None:
        console, buf = make_console()
        display = SessionDisplay(console)
        progress = make_progress()
        display.display_progress_summary(progress)
        output = buf.getvalue()
        assert "l1" in output
        assert "l2" in output

    def test_shows_completion_percentage(self) -> None:
        console, buf = make_console()
        display = SessionDisplay(console)
        progress = make_progress()
        display.display_progress_summary(progress)
        output = buf.getvalue()
        assert "100%" in output


class TestSessionDisplayCommandsHelp:
    """Tests for display_commands_help."""

    def test_shows_all_commands(self) -> None:
        console, buf = make_console()
        display = SessionDisplay(console)
        display.display_commands_help()
        output = buf.getvalue()
        assert "hint" in output
        assert "skip" in output
        assert "quit" in output
        assert "help" in output
        assert "status" in output


class TestSessionDisplayPrompts:
    """Tests for prompt methods."""

    def test_prompt_answer_returns_input(self) -> None:
        console, buf = make_console()
        display = SessionDisplay(console)
        with patch.object(console, "input", return_value="git init"):
            result = display.prompt_answer()
        assert result == "git init"

    def test_prompt_continue_yes(self) -> None:
        console, buf = make_console()
        display = SessionDisplay(console)
        with patch.object(console, "input", return_value=""):
            assert display.prompt_continue() is True

    def test_prompt_continue_no(self) -> None:
        console, buf = make_console()
        display = SessionDisplay(console)
        with patch.object(console, "input", return_value="n"):
            assert display.prompt_continue() is False

    def test_prompt_continue_yes_explicit(self) -> None:
        console, buf = make_console()
        display = SessionDisplay(console)
        with patch.object(console, "input", return_value="y"):
            assert display.prompt_continue() is True


class TestSessionDisplayInit:
    """Tests for SessionDisplay initialization."""

    def test_default_console(self) -> None:
        display = SessionDisplay()
        assert display.console is not None

    def test_custom_console(self) -> None:
        console = Console()
        display = SessionDisplay(console)
        assert display.console is console
