"""
Interactive session manager for SkillForge learning sessions.

This module orchestrates the interactive learning loop, tying together
the CommandSimulator, ExerciseValidator, and SessionDisplay into a
guided terminal-based experience with progress persistence.
"""

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path

from skillforge.core.simulator import CommandSimulator
from skillforge.core.validator import ExerciseValidator, ValidationStatus
from skillforge.models.course import Course
from skillforge.models.enums import ProgressStatus, SessionState
from skillforge.models.lesson import Exercise, Lesson
from skillforge.models.progress import (
    CourseProgress,
    ExerciseProgress,
    LessonProgress,
)
from skillforge.models.session import LearningSession
from skillforge.utils.output import SessionDisplay
from skillforge.utils.serialization import load_from_file, save_to_file

SPECIAL_COMMANDS = {"hint", "skip", "quit", "exit", "help", "status"}


class SessionManager:
    """Orchestrates interactive learning sessions.

    Manages the loop of presenting exercises, collecting user input,
    validating answers, and tracking progress.
    """

    def __init__(
        self,
        session: LearningSession,
        simulator: CommandSimulator,
        validator: ExerciseValidator,
        display: SessionDisplay,
        data_dir: str | Path = "~/.skillforge",
    ) -> None:
        """Initialize the session manager.

        Args:
            session: The learning session to manage
            simulator: Command simulator for exercise execution
            validator: Exercise validator for answer checking
            display: Display helper for terminal output
            data_dir: Base directory for session data
        """
        self.session = session
        self.simulator = simulator
        self.validator = validator
        self.display = display
        self.data_dir = Path(data_dir).expanduser()
        self._hint_count: int = 0

    def run(self) -> None:
        """Run the interactive learning session.

        Iterates through lessons and exercises, prompting the user,
        validating answers, and advancing through the course.
        Handles KeyboardInterrupt for graceful exit.
        """
        course = self.session.course
        progress = self.session.progress

        # Mark session and course as in-progress
        self.session.state = SessionState.ACTIVE
        progress.status = ProgressStatus.IN_PROGRESS
        if progress.started_at is None:
            progress.started_at = datetime.now()

        self.display.display_welcome(course)

        try:
            self._run_lessons()
        except KeyboardInterrupt:
            self.display.console.print(
                "\n[yellow]Session interrupted. Saving progress...[/yellow]"
            )
            self.session.pause()
            self._save_progress()
            return

        # Check if course is complete
        if progress.is_completed():
            self.session.complete()
            self.display.display_course_complete(progress)
        else:
            self.session.pause()

        self._save_progress()

    def _run_lessons(self) -> None:
        """Iterate through lessons starting from current position."""
        course = self.session.course
        progress = self.session.progress

        start_index = progress.current_lesson_index
        for lesson_idx in range(start_index, len(course.lessons)):
            progress.current_lesson_index = lesson_idx
            lesson = course.lessons[lesson_idx]
            lesson_progress = progress.lesson_progress[lesson_idx]

            # Skip completed lessons
            if lesson_progress.status == ProgressStatus.COMPLETED:
                continue

            lesson_progress.status = ProgressStatus.IN_PROGRESS
            if lesson_progress.started_at is None:
                lesson_progress.started_at = datetime.now()

            self.session.current_lesson_id = lesson.id
            self.display.display_lesson_header(
                lesson, lesson_idx + 1, len(course.lessons)
            )

            completed = self._run_lesson_exercises(lesson, lesson_progress)

            if not completed:
                # User quit
                return

            # Mark lesson complete
            lesson_progress.status = ProgressStatus.COMPLETED
            lesson_progress.completed_at = datetime.now()
            progress.mark_lesson_complete(lesson.id)
            self.display.display_lesson_complete(lesson, lesson_progress)

            # Ask to continue to next lesson (unless it's the last one)
            if lesson_idx < len(course.lessons) - 1:
                if not self.display.prompt_continue():
                    self.session.pause()
                    self._save_progress()
                    return

    def _run_lesson_exercises(
        self, lesson: Lesson, lesson_progress: LessonProgress
    ) -> bool:
        """Run all exercises in a lesson.

        Args:
            lesson: The lesson containing exercises
            lesson_progress: Progress tracker for this lesson

        Returns:
            True if all exercises completed, False if user quit
        """
        for ex_idx, exercise in enumerate(lesson.exercises):
            ex_progress = lesson_progress.exercise_progress[ex_idx]

            # Skip completed or failed (skipped) exercises
            if ex_progress.status in (
                ProgressStatus.COMPLETED,
                ProgressStatus.FAILED,
            ):
                continue

            self.session.current_exercise_id = exercise.id
            self.display.display_exercise(exercise, ex_idx + 1, len(lesson.exercises))

            # Reset simulator for each exercise
            self.simulator.reset()

            result = self._run_exercise(exercise, ex_progress)
            if result is None:
                # User quit
                return False

        return True

    def _run_exercise(
        self, exercise: Exercise, ex_progress: ExerciseProgress
    ) -> bool | None:
        """Run a single exercise interaction loop.

        Args:
            exercise: The exercise to run
            ex_progress: Progress tracker for this exercise

        Returns:
            True if completed, False if skipped, None if user quit
        """
        self._hint_count = 0
        ex_progress.status = ProgressStatus.IN_PROGRESS

        while True:
            answer = self.display.prompt_answer().strip()
            # Strip surrounding backticks (users sometimes type `command`)
            if answer.startswith("`") and answer.endswith("`") and len(answer) > 1:
                answer = answer[1:-1].strip()
            answer_stripped = answer.lower()

            # Handle special commands
            if answer_stripped in SPECIAL_COMMANDS:
                result = self._handle_special_command(
                    answer_stripped, exercise, ex_progress
                )
                if result == "quit":
                    return None
                if result == "skip":
                    return False
                # "continue" means keep prompting
                continue

            # Simulate the command
            sim_result = self.simulator.simulate(answer, context=exercise.instruction)
            if sim_result.output:
                self.display.display_simulation_result(sim_result.output)

            # Validate the answer
            ex_progress.attempts += 1
            ex_progress.user_answer = answer
            self.session.update_activity()

            validation = self.validator.validate(
                exercise, answer, context=exercise.instruction
            )
            self.display.display_validation_result(validation)

            if validation.status == ValidationStatus.CORRECT:
                ex_progress.status = ProgressStatus.COMPLETED
                ex_progress.completed_at = datetime.now()
                self._save_progress()
                return True

            # Show hint on incorrect/partial
            self._hint_count += 1
            if validation.hints:
                self.display.display_hint(validation.hints[0], self._hint_count)

    def _handle_special_command(
        self,
        command: str,
        exercise: Exercise,
        ex_progress: ExerciseProgress,
    ) -> str:
        """Handle a special command during an exercise.

        Args:
            command: The special command
            exercise: Current exercise
            ex_progress: Current exercise progress

        Returns:
            "quit", "skip", or "continue"
        """
        if command in ("quit", "exit"):
            self.session.pause()
            self._save_progress()
            self.display.console.print(
                "[yellow]Progress saved. "
                "Use 'skillforge resume' to continue.[/yellow]"
            )
            return "quit"

        if command == "skip":
            ex_progress.status = ProgressStatus.FAILED
            self.display.console.print("[yellow]Exercise skipped.[/yellow]")
            self._save_progress()
            return "skip"

        if command == "hint":
            self._hint_count += 1
            hint = self.validator.generate_hint(
                exercise,
                ex_progress.user_answer or "",
                attempt_number=self._hint_count,
            )
            self.display.display_hint(hint, self._hint_count)
            return "continue"

        if command == "help":
            self.display.display_commands_help()
            return "continue"

        if command == "status":
            self.display.display_progress_summary(self.session.progress)
            return "continue"

        return "continue"

    def _save_progress(self) -> None:
        """Persist session to disk using atomic write."""
        sessions_dir = self.data_dir / "sessions"
        sessions_dir.mkdir(parents=True, exist_ok=True)

        target = sessions_dir / f"{self.session.session_id}.json"

        # Atomic write: write to temp file then rename
        try:
            fd, tmp_path = tempfile.mkstemp(dir=str(sessions_dir), suffix=".tmp")
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(self.session.model_dump_json(indent=2))
            Path(tmp_path).replace(target)
        except OSError:
            # Best-effort fallback: direct write
            save_to_file(self.session, target)

    @classmethod
    def create_new_session(
        cls,
        course: Course,
        simulator: CommandSimulator,
        validator: ExerciseValidator,
        display: SessionDisplay,
        data_dir: str | Path = "~/.skillforge",
    ) -> "SessionManager":
        """Create a new session for a course.

        Args:
            course: The course to create a session for
            simulator: Command simulator
            validator: Exercise validator
            display: Session display
            data_dir: Base data directory

        Returns:
            A new SessionManager ready to run
        """
        lesson_progress = []
        for lesson in course.lessons:
            ex_progress = [
                ExerciseProgress(
                    exercise_id=ex.id,
                    user_answer=None,
                    completed_at=None,
                )
                for ex in lesson.exercises
            ]
            lesson_progress.append(
                LessonProgress(
                    lesson_id=lesson.id,
                    exercise_progress=ex_progress,
                    started_at=None,
                    completed_at=None,
                )
            )

        progress = CourseProgress(
            course_id=course.id,
            user_id="default",
            lesson_progress=lesson_progress,
            started_at=None,
            completed_at=None,
        )

        session = LearningSession(
            course=course,
            progress=progress,
            current_lesson_id=(course.lessons[0].id if course.lessons else None),
            current_exercise_id=(
                course.lessons[0].exercises[0].id
                if course.lessons and course.lessons[0].exercises
                else None
            ),
            paused_at=None,
            completed_at=None,
        )

        return cls(
            session=session,
            simulator=simulator,
            validator=validator,
            display=display,
            data_dir=data_dir,
        )

    @classmethod
    def load_session(
        cls,
        session_id: str,
        simulator: CommandSimulator,
        validator: ExerciseValidator,
        display: SessionDisplay,
        data_dir: str | Path = "~/.skillforge",
    ) -> "SessionManager":
        """Load a saved session.

        Args:
            session_id: The session ID to load
            simulator: Command simulator
            validator: Exercise validator
            display: Session display
            data_dir: Base data directory

        Returns:
            A SessionManager with the loaded session

        Raises:
            FileNotFoundError: If session file not found
        """
        data_path = Path(data_dir).expanduser()
        session_file = data_path / "sessions" / f"{session_id}.json"

        session = load_from_file(LearningSession, session_file)
        assert isinstance(session, LearningSession)
        session.resume()

        return cls(
            session=session,
            simulator=simulator,
            validator=validator,
            display=display,
            data_dir=data_dir,
        )


def find_saved_sessions(
    data_dir: str | Path = "~/.skillforge",
) -> list[dict[str, str]]:
    """List resumable sessions.

    Args:
        data_dir: Base data directory

    Returns:
        List of dicts with session_id, topic, state, last_activity
    """
    sessions_dir = Path(data_dir).expanduser() / "sessions"
    if not sessions_dir.exists():
        return []

    results: list[dict[str, str]] = []
    for path in sessions_dir.glob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            results.append(
                {
                    "session_id": data.get("session_id", path.stem),
                    "topic": data.get("course", {}).get("topic", "Unknown"),
                    "state": data.get("state", "unknown"),
                    "last_activity": data.get("last_activity_at", ""),
                }
            )
        except (json.JSONDecodeError, OSError):
            continue

    # Sort by last activity, newest first
    results.sort(key=lambda x: x["last_activity"], reverse=True)
    return results
