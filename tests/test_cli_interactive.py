"""Tests for CLI interactive mode, resume, and status commands."""

from unittest.mock import MagicMock, patch

from typer.testing import CliRunner

from skillforge.cli import app
from skillforge.models.course import Course

runner = CliRunner()


def make_course_json() -> dict:  # type: ignore[type-arg]
    """Create a minimal course dict for mocking."""
    return {
        "id": "c1",
        "topic": "Git Basics",
        "description": "Learn git",
        "difficulty": "beginner",
        "lessons": [
            {
                "id": "l1",
                "title": "Intro",
                "objectives": ["Learn git"],
                "exercises": [
                    {
                        "id": "e1",
                        "instruction": "Run git init",
                        "expected_output": "git init",
                        "hints": [],
                    }
                ],
            }
        ],
    }


def make_course() -> Course:
    return Course.model_validate(make_course_json())


class TestLearnInteractive:
    """Tests for the learn command with interactive mode."""

    @patch("skillforge.cli._start_interactive_session")
    @patch("skillforge.cli.LLMClientFactory.create_client")
    @patch("skillforge.cli.CourseGenerator")
    def test_interactive_starts_session(
        self,
        mock_gen_cls: MagicMock,
        mock_factory: MagicMock,
        mock_start: MagicMock,
    ) -> None:
        mock_factory.return_value = MagicMock()
        mock_gen = MagicMock()
        mock_gen.generate_course.return_value = make_course()
        mock_gen_cls.return_value = mock_gen

        runner.invoke(
            app, ["learn", "git basics", "--interactive"], input="y\n"
        )
        mock_start.assert_called_once()

    @patch("skillforge.cli.LLMClientFactory.create_client")
    @patch("skillforge.cli.CourseGenerator")
    def test_no_interactive_skips_session(
        self,
        mock_gen_cls: MagicMock,
        mock_factory: MagicMock,
    ) -> None:
        mock_factory.return_value = MagicMock()
        mock_gen = MagicMock()
        mock_gen.generate_course.return_value = make_course()
        mock_gen_cls.return_value = mock_gen

        result = runner.invoke(
            app, ["learn", "git basics", "--no-interactive"], input="n\n"
        )
        assert "Course generation complete" in result.output


class TestResumeCommand:
    """Tests for the resume command."""

    @patch("skillforge.cli.load_config")
    @patch("skillforge.cli.find_saved_sessions")
    def test_list_sessions_when_no_id(
        self,
        mock_find: MagicMock,
        mock_config: MagicMock,
    ) -> None:
        mock_config.return_value = MagicMock(data_dir="/tmp/test")
        mock_find.return_value = [
            {
                "session_id": "abc12345-full-id",
                "topic": "Git Basics",
                "state": "paused",
                "last_activity": "2026-01-01T00:00:00",
            }
        ]

        result = runner.invoke(app, ["resume"])
        assert "Git Basics" in result.output
        assert "paused" in result.output

    @patch("skillforge.cli.load_config")
    @patch("skillforge.cli.find_saved_sessions")
    def test_no_sessions_message(
        self,
        mock_find: MagicMock,
        mock_config: MagicMock,
    ) -> None:
        mock_config.return_value = MagicMock(data_dir="/tmp/test")
        mock_find.return_value = []

        result = runner.invoke(app, ["resume"])
        assert "No saved sessions" in result.output

    @patch("skillforge.cli.load_config")
    @patch("skillforge.cli.find_saved_sessions")
    @patch("skillforge.cli.LLMClientFactory.create_client")
    @patch("skillforge.cli.SessionManager.load_session")
    def test_resume_specific_session(
        self,
        mock_load: MagicMock,
        mock_factory: MagicMock,
        mock_find: MagicMock,
        mock_config: MagicMock,
    ) -> None:
        mock_config.return_value = MagicMock(data_dir="/tmp/test")
        mock_find.return_value = [
            {
                "session_id": "abc12345",
                "topic": "Git Basics",
                "state": "paused",
                "last_activity": "2026-01-01",
            }
        ]
        mock_factory.return_value = MagicMock()
        mock_mgr = MagicMock()
        mock_load.return_value = mock_mgr

        result = runner.invoke(app, ["resume", "abc"])
        assert "Resuming session" in result.output
        mock_mgr.run.assert_called_once()

    @patch("skillforge.cli.load_config")
    @patch("skillforge.cli.find_saved_sessions")
    @patch("skillforge.cli.LLMClientFactory.create_client")
    def test_resume_no_match(
        self,
        mock_factory: MagicMock,
        mock_find: MagicMock,
        mock_config: MagicMock,
    ) -> None:
        mock_config.return_value = MagicMock(data_dir="/tmp/test")
        mock_find.return_value = []
        mock_factory.return_value = MagicMock()

        result = runner.invoke(app, ["resume", "nonexistent"])
        assert "No session found" in result.output


class TestStatusCommand:
    """Tests for the status command."""

    @patch("skillforge.cli.load_config")
    @patch("skillforge.cli.find_saved_sessions")
    def test_status_no_match(
        self,
        mock_find: MagicMock,
        mock_config: MagicMock,
    ) -> None:
        mock_config.return_value = MagicMock(data_dir="/tmp/test")
        mock_find.return_value = []

        result = runner.invoke(app, ["status", "nonexistent"])
        assert "No session found" in result.output

    @patch("skillforge.cli.load_config")
    @patch("skillforge.cli.find_saved_sessions")
    @patch("skillforge.cli.load_from_file")
    def test_status_shows_progress(
        self,
        mock_load_file: MagicMock,
        mock_find: MagicMock,
        mock_config: MagicMock,
    ) -> None:
        from skillforge.models.enums import ProgressStatus, SessionState
        from skillforge.models.progress import (
            CourseProgress,
            ExerciseProgress,
            LessonProgress,
        )
        from skillforge.models.session import LearningSession

        course = make_course()
        session = LearningSession(
            session_id="abc12345",
            course=course,
            progress=CourseProgress(
                course_id="c1",
                user_id="default",
                started_at=None,
                completed_at=None,
                lesson_progress=[
                    LessonProgress(
                        lesson_id="l1",
                        started_at=None,
                        completed_at=None,
                        exercise_progress=[
                            ExerciseProgress(
                                exercise_id="e1",
                                status=ProgressStatus.COMPLETED,
                                attempts=1,
                                user_answer=None,
                                completed_at=None,
                            )
                        ],
                    )
                ],
            ),
            state=SessionState.PAUSED,
            paused_at=None,
            completed_at=None,
        )

        mock_config.return_value = MagicMock(data_dir="/tmp/test")
        mock_find.return_value = [
            {
                "session_id": "abc12345",
                "topic": "Git Basics",
                "state": "paused",
                "last_activity": "",
            }
        ]
        mock_load_file.return_value = session

        result = runner.invoke(app, ["status", "abc"])
        assert "Git Basics" in result.output
        assert "paused" in result.output
