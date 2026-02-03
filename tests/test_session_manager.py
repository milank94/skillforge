"""Tests for the SessionManager interactive session orchestrator."""

import json
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest
from rich.console import Console

from skillforge.core.session import SessionManager, find_saved_sessions
from skillforge.core.simulator import CommandSimulator
from skillforge.core.validator import (
    ExerciseValidator,
)
from skillforge.models.course import Course
from skillforge.models.enums import Difficulty, ProgressStatus, SessionState
from skillforge.models.lesson import Exercise, Lesson
from skillforge.models.progress import (
    CourseProgress,
    ExerciseProgress,
    LessonProgress,
)
from skillforge.models.session import LearningSession
from skillforge.utils.output import SessionDisplay

# --- Fixtures ---


def make_exercise(
    ex_id: str = "e1",
    instruction: str = "Run git init",
    expected: str = "git init",
) -> Exercise:
    return Exercise(
        id=ex_id,
        instruction=instruction,
        expected_output=expected,
        hints=["Try: git init", "Use the git command"],
    )


def make_course(num_lessons: int = 1, exercises_per: int = 1) -> Course:
    lessons = []
    for li in range(num_lessons):
        exercises = []
        for ei in range(exercises_per):
            exercises.append(
                make_exercise(
                    ex_id=f"e{li}_{ei}",
                    instruction=f"Exercise {li}_{ei}",
                    expected=f"answer{li}_{ei}",
                )
            )
        lessons.append(
            Lesson(
                id=f"l{li}",
                title=f"Lesson {li}",
                objectives=[f"Objective {li}"],
                exercises=exercises,
            )
        )
    return Course(
        id="c1",
        topic="Test Topic",
        description="A test course",
        difficulty=Difficulty.BEGINNER,
        lessons=lessons,
    )


def make_progress(course: Course) -> CourseProgress:
    lesson_progress = []
    for lesson in course.lessons:
        ex_progress = [ExerciseProgress(exercise_id=ex.id) for ex in lesson.exercises]
        lesson_progress.append(
            LessonProgress(lesson_id=lesson.id, exercise_progress=ex_progress)
        )
    return CourseProgress(
        course_id=course.id,
        user_id="default",
        lesson_progress=lesson_progress,
    )


def make_session(course: Course | None = None) -> LearningSession:
    c = course or make_course()
    return LearningSession(
        course=c,
        progress=make_progress(c),
        current_lesson_id=c.lessons[0].id if c.lessons else None,
        current_exercise_id=(
            c.lessons[0].exercises[0].id
            if c.lessons and c.lessons[0].exercises
            else None
        ),
    )


def make_display() -> SessionDisplay:
    buf = StringIO()
    console = Console(file=buf, force_terminal=True, width=120)
    return SessionDisplay(console)


def make_manager(
    course: Course | None = None,
    tmp_path: Path | None = None,
) -> SessionManager:
    c = course or make_course()
    session = make_session(c)
    return SessionManager(
        session=session,
        simulator=CommandSimulator(),
        validator=ExerciseValidator(),
        display=make_display(),
        data_dir=str(tmp_path) if tmp_path else "/tmp/sf_test",
    )


# --- SessionManager.__init__ ---


class TestSessionManagerInit:
    def test_init_sets_attributes(self) -> None:
        mgr = make_manager()
        assert mgr.session is not None
        assert mgr.simulator is not None
        assert mgr.validator is not None
        assert mgr.display is not None

    def test_init_expands_data_dir(self) -> None:
        mgr = make_manager()
        assert "~" not in str(mgr.data_dir)


# --- create_new_session ---


class TestCreateNewSession:
    def test_creates_progress_matching_course(self) -> None:
        course = make_course(num_lessons=2, exercises_per=3)
        mgr = SessionManager.create_new_session(
            course=course,
            simulator=CommandSimulator(),
            validator=ExerciseValidator(),
            display=make_display(),
        )
        progress = mgr.session.progress
        assert len(progress.lesson_progress) == 2
        assert len(progress.lesson_progress[0].exercise_progress) == 3

    def test_sets_current_ids(self) -> None:
        course = make_course()
        mgr = SessionManager.create_new_session(
            course=course,
            simulator=CommandSimulator(),
            validator=ExerciseValidator(),
            display=make_display(),
        )
        assert mgr.session.current_lesson_id == course.lessons[0].id
        assert mgr.session.current_exercise_id == course.lessons[0].exercises[0].id

    def test_empty_course(self) -> None:
        course = Course(
            id="c1",
            topic="Empty",
            description="No lessons",
            difficulty=Difficulty.BEGINNER,
            lessons=[],
        )
        mgr = SessionManager.create_new_session(
            course=course,
            simulator=CommandSimulator(),
            validator=ExerciseValidator(),
            display=make_display(),
        )
        assert mgr.session.current_lesson_id is None
        assert mgr.session.current_exercise_id is None

    def test_progress_status_not_started(self) -> None:
        course = make_course()
        mgr = SessionManager.create_new_session(
            course=course,
            simulator=CommandSimulator(),
            validator=ExerciseValidator(),
            display=make_display(),
        )
        assert mgr.session.progress.status == ProgressStatus.NOT_STARTED


# --- _handle_special_command ---


class TestHandleSpecialCommand:
    def test_quit_pauses_and_saves(self, tmp_path: Path) -> None:
        mgr = make_manager(tmp_path=tmp_path)
        ex = make_exercise()
        ep = ExerciseProgress(exercise_id=ex.id)
        result = mgr._handle_special_command("quit", ex, ep)
        assert result == "quit"
        assert mgr.session.state == SessionState.PAUSED

    def test_exit_pauses_and_saves(self, tmp_path: Path) -> None:
        mgr = make_manager(tmp_path=tmp_path)
        ex = make_exercise()
        ep = ExerciseProgress(exercise_id=ex.id)
        result = mgr._handle_special_command("exit", ex, ep)
        assert result == "quit"

    def test_skip_marks_failed(self, tmp_path: Path) -> None:
        mgr = make_manager(tmp_path=tmp_path)
        ex = make_exercise()
        ep = ExerciseProgress(exercise_id=ex.id)
        result = mgr._handle_special_command("skip", ex, ep)
        assert result == "skip"
        assert ep.status == ProgressStatus.FAILED

    def test_hint_returns_continue(self, tmp_path: Path) -> None:
        mgr = make_manager(tmp_path=tmp_path)
        ex = make_exercise()
        ep = ExerciseProgress(exercise_id=ex.id)
        result = mgr._handle_special_command("hint", ex, ep)
        assert result == "continue"
        assert mgr._hint_count == 1

    def test_help_returns_continue(self, tmp_path: Path) -> None:
        mgr = make_manager(tmp_path=tmp_path)
        ex = make_exercise()
        ep = ExerciseProgress(exercise_id=ex.id)
        result = mgr._handle_special_command("help", ex, ep)
        assert result == "continue"

    def test_status_returns_continue(self, tmp_path: Path) -> None:
        mgr = make_manager(tmp_path=tmp_path)
        ex = make_exercise()
        ep = ExerciseProgress(exercise_id=ex.id)
        result = mgr._handle_special_command("status", ex, ep)
        assert result == "continue"


# --- _run_exercise ---


class TestRunExercise:
    def test_correct_answer_completes(self, tmp_path: Path) -> None:
        mgr = make_manager(tmp_path=tmp_path)
        ex = make_exercise(expected="git init")
        ep = ExerciseProgress(exercise_id=ex.id)

        with patch.object(mgr.display, "prompt_answer", return_value="git init"):
            result = mgr._run_exercise(ex, ep)

        assert result is True
        assert ep.status == ProgressStatus.COMPLETED
        assert ep.attempts == 1

    def test_skip_command(self, tmp_path: Path) -> None:
        mgr = make_manager(tmp_path=tmp_path)
        ex = make_exercise()
        ep = ExerciseProgress(exercise_id=ex.id)

        with patch.object(mgr.display, "prompt_answer", return_value="skip"):
            result = mgr._run_exercise(ex, ep)

        assert result is False
        assert ep.status == ProgressStatus.FAILED

    def test_quit_command(self, tmp_path: Path) -> None:
        mgr = make_manager(tmp_path=tmp_path)
        ex = make_exercise()
        ep = ExerciseProgress(exercise_id=ex.id)

        with patch.object(mgr.display, "prompt_answer", return_value="quit"):
            result = mgr._run_exercise(ex, ep)

        assert result is None

    def test_wrong_then_correct(self, tmp_path: Path) -> None:
        mgr = make_manager(tmp_path=tmp_path)
        ex = make_exercise(expected="git init")
        ep = ExerciseProgress(exercise_id=ex.id)

        answers = iter(["wrong answer", "git init"])
        with patch.object(mgr.display, "prompt_answer", side_effect=answers):
            result = mgr._run_exercise(ex, ep)

        assert result is True
        assert ep.attempts == 2

    def test_hint_then_correct(self, tmp_path: Path) -> None:
        mgr = make_manager(tmp_path=tmp_path)
        ex = make_exercise(expected="git init")
        ep = ExerciseProgress(exercise_id=ex.id)

        answers = iter(["hint", "git init"])
        with patch.object(mgr.display, "prompt_answer", side_effect=answers):
            result = mgr._run_exercise(ex, ep)

        assert result is True
        assert ep.attempts == 1  # hint doesn't count as attempt


# --- _save_progress ---


class TestSaveProgress:
    def test_saves_to_sessions_dir(self, tmp_path: Path) -> None:
        mgr = make_manager(tmp_path=tmp_path)
        mgr._save_progress()

        session_file = tmp_path / "sessions" / f"{mgr.session.session_id}.json"
        assert session_file.exists()

    def test_saved_file_is_valid_json(self, tmp_path: Path) -> None:
        mgr = make_manager(tmp_path=tmp_path)
        mgr._save_progress()

        session_file = tmp_path / "sessions" / f"{mgr.session.session_id}.json"
        data = json.loads(session_file.read_text())
        assert data["session_id"] == mgr.session.session_id

    def test_creates_sessions_dir(self, tmp_path: Path) -> None:
        data_dir = tmp_path / "new_dir"
        mgr = make_manager(tmp_path=data_dir)
        mgr._save_progress()
        assert (data_dir / "sessions").is_dir()


# --- load_session ---


class TestLoadSession:
    def test_loads_saved_session(self, tmp_path: Path) -> None:
        mgr = make_manager(tmp_path=tmp_path)
        mgr._save_progress()

        loaded = SessionManager.load_session(
            session_id=mgr.session.session_id,
            simulator=CommandSimulator(),
            validator=ExerciseValidator(),
            display=make_display(),
            data_dir=str(tmp_path),
        )
        assert loaded.session.session_id == mgr.session.session_id
        assert loaded.session.state == SessionState.ACTIVE

    def test_load_nonexistent_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            SessionManager.load_session(
                session_id="nonexistent",
                simulator=CommandSimulator(),
                validator=ExerciseValidator(),
                display=make_display(),
                data_dir=str(tmp_path),
            )


# --- run (integration-style) ---


class TestRun:
    def test_single_exercise_correct(self, tmp_path: Path) -> None:
        course = make_course(num_lessons=1, exercises_per=1)
        mgr = make_manager(course=course, tmp_path=tmp_path)

        with patch.object(mgr.display, "prompt_answer", return_value="answer0_0"):
            mgr.run()

        assert mgr.session.state == SessionState.COMPLETED
        assert mgr.session.progress.is_completed()

    def test_keyboard_interrupt_saves(self, tmp_path: Path) -> None:
        mgr = make_manager(tmp_path=tmp_path)

        with patch.object(mgr.display, "prompt_answer", side_effect=KeyboardInterrupt):
            mgr.run()

        assert mgr.session.state == SessionState.PAUSED
        session_file = tmp_path / "sessions" / f"{mgr.session.session_id}.json"
        assert session_file.exists()

    def test_quit_during_exercise(self, tmp_path: Path) -> None:
        mgr = make_manager(tmp_path=tmp_path)

        with patch.object(mgr.display, "prompt_answer", return_value="quit"):
            mgr.run()

        assert mgr.session.state == SessionState.PAUSED

    def test_two_lessons_complete(self, tmp_path: Path) -> None:
        course = make_course(num_lessons=2, exercises_per=1)
        mgr = make_manager(course=course, tmp_path=tmp_path)

        answers = iter(["answer0_0", "answer1_0"])
        with (
            patch.object(mgr.display, "prompt_answer", side_effect=answers),
            patch.object(mgr.display, "prompt_continue", return_value=True),
        ):
            mgr.run()

        assert mgr.session.state == SessionState.COMPLETED

    def test_decline_continue_pauses(self, tmp_path: Path) -> None:
        course = make_course(num_lessons=2, exercises_per=1)
        mgr = make_manager(course=course, tmp_path=tmp_path)

        with (
            patch.object(mgr.display, "prompt_answer", return_value="answer0_0"),
            patch.object(mgr.display, "prompt_continue", return_value=False),
        ):
            mgr.run()

        assert mgr.session.state == SessionState.PAUSED

    def test_skip_exercise_still_completes_lesson(self, tmp_path: Path) -> None:
        course = make_course(num_lessons=1, exercises_per=2)
        mgr = make_manager(course=course, tmp_path=tmp_path)

        # Skip first, answer second correctly
        answers = iter(["skip", "answer0_1"])
        with patch.object(mgr.display, "prompt_answer", side_effect=answers):
            mgr.run()

        lp = mgr.session.progress.lesson_progress[0]
        assert lp.exercise_progress[0].status == ProgressStatus.FAILED
        assert lp.exercise_progress[1].status == ProgressStatus.COMPLETED

    def test_progress_started_at_set(self, tmp_path: Path) -> None:
        mgr = make_manager(tmp_path=tmp_path)

        with patch.object(mgr.display, "prompt_answer", return_value="quit"):
            mgr.run()

        assert mgr.session.progress.started_at is not None

    def test_sets_active_state_on_run(self, tmp_path: Path) -> None:
        mgr = make_manager(tmp_path=tmp_path)
        assert mgr.session.state == SessionState.ACTIVE  # default

        with patch.object(mgr.display, "prompt_answer", return_value="quit"):
            mgr.run()

        # After quit it's paused, but it was active during run
        assert mgr.session.state == SessionState.PAUSED

    def test_simulator_reset_between_exercises(self, tmp_path: Path) -> None:
        course = make_course(num_lessons=1, exercises_per=2)
        mgr = make_manager(course=course, tmp_path=tmp_path)

        reset_count = 0
        original_reset = mgr.simulator.reset

        def counting_reset() -> None:
            nonlocal reset_count
            reset_count += 1
            original_reset()

        mgr.simulator.reset = counting_reset  # type: ignore[assignment]

        answers = iter(["answer0_0", "answer0_1"])
        with patch.object(mgr.display, "prompt_answer", side_effect=answers):
            mgr.run()

        assert reset_count == 2


# --- _run_lesson_exercises ---


class TestRunLessonExercises:
    def test_skips_completed_exercises(self, tmp_path: Path) -> None:
        course = make_course(num_lessons=1, exercises_per=2)
        mgr = make_manager(course=course, tmp_path=tmp_path)

        # Mark first exercise as completed
        lp = mgr.session.progress.lesson_progress[0]
        lp.exercise_progress[0].status = ProgressStatus.COMPLETED

        # Only need answer for second exercise
        with patch.object(mgr.display, "prompt_answer", return_value="answer0_1"):
            result = mgr._run_lesson_exercises(course.lessons[0], lp)

        assert result is True

    def test_skips_failed_exercises(self, tmp_path: Path) -> None:
        course = make_course(num_lessons=1, exercises_per=2)
        mgr = make_manager(course=course, tmp_path=tmp_path)

        lp = mgr.session.progress.lesson_progress[0]
        lp.exercise_progress[0].status = ProgressStatus.FAILED

        with patch.object(mgr.display, "prompt_answer", return_value="answer0_1"):
            result = mgr._run_lesson_exercises(course.lessons[0], lp)

        assert result is True


# --- find_saved_sessions ---


class TestFindSavedSessions:
    def test_empty_dir(self, tmp_path: Path) -> None:
        result = find_saved_sessions(data_dir=str(tmp_path))
        assert result == []

    def test_finds_sessions(self, tmp_path: Path) -> None:
        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir()

        data = {
            "session_id": "abc123",
            "course": {"topic": "Git Basics"},
            "state": "paused",
            "last_activity_at": "2026-01-01T00:00:00",
        }
        (sessions_dir / "abc123.json").write_text(json.dumps(data))

        result = find_saved_sessions(data_dir=str(tmp_path))
        assert len(result) == 1
        assert result[0]["session_id"] == "abc123"
        assert result[0]["topic"] == "Git Basics"
        assert result[0]["state"] == "paused"

    def test_ignores_invalid_json(self, tmp_path: Path) -> None:
        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir()
        (sessions_dir / "bad.json").write_text("not json")

        result = find_saved_sessions(data_dir=str(tmp_path))
        assert result == []

    def test_sorts_by_last_activity(self, tmp_path: Path) -> None:
        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir()

        for i, ts in enumerate(["2026-01-01", "2026-02-01", "2025-12-01"]):
            data = {
                "session_id": f"s{i}",
                "course": {"topic": f"Topic {i}"},
                "state": "paused",
                "last_activity_at": ts,
            }
            (sessions_dir / f"s{i}.json").write_text(json.dumps(data))

        result = find_saved_sessions(data_dir=str(tmp_path))
        assert result[0]["session_id"] == "s1"  # newest first

    def test_multiple_sessions(self, tmp_path: Path) -> None:
        sessions_dir = tmp_path / "sessions"
        sessions_dir.mkdir()

        for i in range(3):
            data = {
                "session_id": f"s{i}",
                "course": {"topic": f"Topic {i}"},
                "state": "paused",
                "last_activity_at": f"2026-01-0{i + 1}",
            }
            (sessions_dir / f"s{i}.json").write_text(json.dumps(data))

        result = find_saved_sessions(data_dir=str(tmp_path))
        assert len(result) == 3
