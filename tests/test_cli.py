"""
Tests for CLI interface.

Tests command-line interface functionality using Typer's CliRunner.
"""

import os
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from skillforge import __version__
from skillforge.cli import app
from skillforge.models.course import Course
from skillforge.models.enums import Difficulty
from skillforge.models.lesson import Exercise, Lesson

runner = CliRunner()


@pytest.fixture
def mock_course():
    """Mock course for testing."""
    return Course(
        id="test-id",
        topic="Python Basics",
        description="Learn Python fundamentals",
        difficulty=Difficulty.BEGINNER,
        lessons=[
            Lesson(
                id="lesson-1",
                title="Variables",
                objectives=["Learn variables"],
                exercises=[
                    Exercise(
                        id="ex-1",
                        instruction="Create a variable",
                        expected_output=None,
                        hints=["Use ="],
                    )
                ],
            )
        ],
    )


class TestCLIVersion:
    """Test version-related CLI functionality."""

    def test_version_flag(self) -> None:
        """Test --version flag displays version."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert __version__ in result.stdout
        assert "SkillForge" in result.stdout

    def test_version_short_flag(self) -> None:
        """Test -v flag displays version."""
        result = runner.invoke(app, ["-v"])
        assert result.exit_code == 0
        assert __version__ in result.stdout


class TestCLIHelp:
    """Test help-related CLI functionality."""

    def test_help_flag(self) -> None:
        """Test --help flag displays help text."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "AI-powered interactive learning" in result.stdout
        assert "learn" in result.stdout

    def test_help_without_args(self) -> None:
        """Test that running without args shows usage information."""
        result = runner.invoke(app, [])
        # Typer shows usage info but exits with code 2 when no command is given
        assert result.exit_code == 2
        assert "Usage:" in result.stdout

    def test_learn_help(self) -> None:
        """Test help for learn command."""
        result = runner.invoke(app, ["learn", "--help"])
        assert result.exit_code == 0
        assert "learn" in result.stdout.lower()
        assert "topic" in result.stdout.lower()


class TestLearnCommand:
    """Test the learn command functionality."""

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"})
    @patch("skillforge.cli.CourseGenerator")
    @patch("skillforge.cli.LLMClientFactory.create_client")
    def test_learn_with_topic(
        self, mock_client_factory, mock_generator_class, mock_course
    ) -> None:
        """Test learn command with a topic."""
        mock_generator = Mock()
        mock_generator.generate_course.return_value = mock_course
        mock_generator_class.return_value = mock_generator

        result = runner.invoke(
            app, ["learn", "pytorch basics", "--no-interactive"], input="n\n"
        )
        assert result.exit_code == 0
        assert "pytorch basics" in result.stdout.lower()
        assert "Generating course" in result.stdout

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"})
    @patch("skillforge.cli.CourseGenerator")
    @patch("skillforge.cli.LLMClientFactory.create_client")
    def test_learn_with_difficulty(
        self, mock_client_factory, mock_generator_class, mock_course
    ) -> None:
        """Test learn command with difficulty option."""
        mock_generator = Mock()
        mock_generator.generate_course.return_value = mock_course
        mock_generator_class.return_value = mock_generator

        result = runner.invoke(
            app,
            ["learn", "Python", "--difficulty", "advanced", "--no-interactive"],
            input="n\n",
        )
        assert result.exit_code == 0
        assert "Advanced" in result.stdout

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"})
    @patch("skillforge.cli.CourseGenerator")
    @patch("skillforge.cli.LLMClientFactory.create_client")
    def test_learn_with_lesson_count(
        self, mock_client_factory, mock_generator_class, mock_course
    ) -> None:
        """Test learn command with custom lesson count."""
        mock_generator = Mock()
        mock_generator.generate_course.return_value = mock_course
        mock_generator_class.return_value = mock_generator

        result = runner.invoke(
            app, ["learn", "Docker", "--lessons", "7", "--no-interactive"], input="n\n"
        )
        assert result.exit_code == 0
        assert "Lessons: 7" in result.stdout

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("skillforge.cli.CourseGenerator")
    @patch("skillforge.cli.LLMClientFactory.create_client")
    def test_learn_with_provider(
        self, mock_client_factory, mock_generator_class, mock_course
    ) -> None:
        """Test learn command with provider option."""
        mock_generator = Mock()
        mock_generator.generate_course.return_value = mock_course
        mock_generator_class.return_value = mock_generator

        result = runner.invoke(
            app,
            ["learn", "Python", "--provider", "openai", "--no-interactive"],
            input="n\n",
        )
        assert result.exit_code == 0
        assert "openai" in result.stdout.lower()

    def test_learn_without_api_key(self) -> None:
        """Test learn command fails gracefully without API key."""
        with patch.dict(os.environ, {}, clear=True):
            result = runner.invoke(app, ["learn", "Python", "--no-interactive"])
            assert result.exit_code == 1
            assert "API key" in result.stdout or "ANTHROPIC_API_KEY" in result.stdout

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"})
    @patch("skillforge.cli.CourseGenerator")
    @patch("skillforge.cli.LLMClientFactory.create_client")
    def test_learn_invalid_difficulty(
        self, mock_client_factory, mock_generator_class
    ) -> None:
        """Test learn command with invalid difficulty."""
        result = runner.invoke(app, ["learn", "Python", "--difficulty", "invalid"])
        assert result.exit_code == 1
        assert "Invalid difficulty" in result.stdout

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"})
    @patch("skillforge.cli.CourseGenerator")
    @patch("skillforge.cli.LLMClientFactory.create_client")
    def test_learn_invalid_lesson_count(
        self, mock_client_factory, mock_generator_class
    ) -> None:
        """Test learn command with invalid lesson count."""
        result = runner.invoke(app, ["learn", "Python", "--lessons", "25"])
        assert result.exit_code == 1
        assert "must be between 1 and 20" in result.stdout

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"})
    @patch("skillforge.cli.CourseGenerator")
    @patch("skillforge.cli.LLMClientFactory.create_client")
    def test_learn_displays_course_overview(
        self, mock_client_factory, mock_generator_class, mock_course
    ) -> None:
        """Test that learn command displays course overview."""
        mock_generator = Mock()
        mock_generator.generate_course.return_value = mock_course
        mock_generator_class.return_value = mock_generator

        result = runner.invoke(
            app, ["learn", "Python", "--no-interactive"], input="n\n"
        )
        assert result.exit_code == 0
        assert "Course Overview" in result.stdout or "Python Basics" in result.stdout

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"})
    @patch("skillforge.cli.CourseGenerator")
    @patch("skillforge.cli.LLMClientFactory.create_client")
    @patch("skillforge.cli.save_course")
    def test_learn_save_course(
        self, mock_save, mock_client_factory, mock_generator_class, mock_course
    ) -> None:
        """Test saving course after generation."""
        mock_generator = Mock()
        mock_generator.generate_course.return_value = mock_course
        mock_generator_class.return_value = mock_generator

        result = runner.invoke(
            app, ["learn", "Python", "--no-interactive"], input="y\n"
        )
        assert result.exit_code == 0
        mock_save.assert_called_once()


class TestCacheCommands:
    """Test cache management commands."""

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"})
    @patch("skillforge.cli.CourseGenerator")
    @patch("skillforge.cli.LLMClientFactory.create_client")
    def test_cache_clear(self, mock_client_factory, mock_generator_class) -> None:
        """Test cache-clear command."""
        mock_generator = Mock()
        mock_generator.clear_cache.return_value = 3
        mock_generator_class.return_value = mock_generator

        result = runner.invoke(app, ["cache-clear"])
        assert result.exit_code == 0
        assert "3" in result.stdout
        assert "Cleared" in result.stdout or "cleared" in result.stdout

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"})
    @patch("skillforge.cli.CourseGenerator")
    @patch("skillforge.cli.LLMClientFactory.create_client")
    def test_cache_clear_empty(self, mock_client_factory, mock_generator_class) -> None:
        """Test cache-clear with no cached courses."""
        mock_generator = Mock()
        mock_generator.clear_cache.return_value = 0
        mock_generator_class.return_value = mock_generator

        result = runner.invoke(app, ["cache-clear"])
        assert result.exit_code == 0
        assert "No cached courses" in result.stdout or "0" in result.stdout

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"})
    @patch("skillforge.cli.CourseGenerator")
    @patch("skillforge.cli.LLMClientFactory.create_client")
    def test_cache_info(self, mock_client_factory, mock_generator_class) -> None:
        """Test cache-info command."""
        mock_generator = Mock()
        mock_generator.get_cache_stats.return_value = {
            "cached_courses": 5,
            "total_size_bytes": 10240,
            "cache_dir": "/test/cache",
        }
        mock_generator_class.return_value = mock_generator

        result = runner.invoke(app, ["cache-info"])
        assert result.exit_code == 0
        assert "5" in result.stdout
        assert "Cache Statistics" in result.stdout or "cache" in result.stdout.lower()


class TestCLIOutput:
    """Test CLI output formatting and presentation."""

    def test_version_output_formatted(self) -> None:
        """Test that version output is properly formatted."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "version" in result.stdout.lower()
        assert __version__ in result.stdout

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"})
    @patch("skillforge.cli.CourseGenerator")
    @patch("skillforge.cli.LLMClientFactory.create_client")
    def test_learn_output_formatted(
        self, mock_client_factory, mock_generator_class, mock_course
    ) -> None:
        """Test that learn output uses Rich formatting."""
        mock_generator = Mock()
        mock_generator.generate_course.return_value = mock_course
        mock_generator_class.return_value = mock_generator

        result = runner.invoke(
            app, ["learn", "Python", "--no-interactive"], input="n\n"
        )
        assert result.exit_code == 0
        # Verify output is generated
        assert len(result.stdout) > 100


class TestCLIErrorHandling:
    """Test CLI error handling."""

    def test_learn_without_topic_fails(self) -> None:
        """Test that learn command requires a topic argument."""
        result = runner.invoke(app, ["learn"])
        assert result.exit_code != 0
        # Should show error about missing argument

    def test_invalid_command(self) -> None:
        """Test that invalid command shows error."""
        result = runner.invoke(app, ["invalid-command"])
        assert result.exit_code != 0
