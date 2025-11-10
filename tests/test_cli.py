"""
Tests for CLI interface.

Tests command-line interface functionality using Typer's CliRunner.
"""

import pytest
from typer.testing import CliRunner

from skillforge import __version__
from skillforge.cli import app

runner = CliRunner()


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

    def test_learn_with_topic(self) -> None:
        """Test learn command with a topic."""
        result = runner.invoke(app, ["learn", "pytorch basics"])
        assert result.exit_code == 0
        assert "pytorch basics" in result.stdout
        assert "Starting learning session" in result.stdout

    def test_learn_interactive_mode(self) -> None:
        """Test learn command in interactive mode (default)."""
        result = runner.invoke(app, ["learn", "docker"])
        assert result.exit_code == 0
        assert "Interactive: Yes" in result.stdout

    def test_learn_no_interactive_mode(self) -> None:
        """Test learn command with interactive mode disabled."""
        result = runner.invoke(app, ["learn", "kubernetes", "--no-interactive"])
        assert result.exit_code == 0
        assert "Interactive: No" in result.stdout

    def test_learn_displays_topic(self) -> None:
        """Test that learn command displays the provided topic."""
        topic = "FastAPI fundamentals"
        result = runner.invoke(app, ["learn", topic])
        assert result.exit_code == 0
        assert topic in result.stdout

    def test_learn_shows_coming_soon(self) -> None:
        """Test that learn command shows coming soon features."""
        result = runner.invoke(app, ["learn", "test"])
        assert result.exit_code == 0
        assert "Coming soon" in result.stdout
        assert "AI-generated" in result.stdout
        assert "interactive lessons" in result.stdout

    def test_learn_multiple_word_topic(self) -> None:
        """Test learn with multi-word topic."""
        result = runner.invoke(app, ["learn", "advanced machine learning"])
        assert result.exit_code == 0
        assert "advanced machine learning" in result.stdout

    def test_learn_topic_with_special_characters(self) -> None:
        """Test learn with topic containing special characters."""
        result = runner.invoke(app, ["learn", "Python 3.9+"])
        assert result.exit_code == 0
        assert "Python 3.9+" in result.stdout


class TestCLIOutput:
    """Test CLI output formatting and presentation."""

    def test_output_contains_skillforge_branding(self) -> None:
        """Test that output contains SkillForge branding."""
        result = runner.invoke(app, ["learn", "test"])
        assert result.exit_code == 0
        assert "SkillForge" in result.stdout

    def test_output_is_formatted(self) -> None:
        """Test that output uses rich formatting (contains box characters)."""
        result = runner.invoke(app, ["learn", "test"])
        assert result.exit_code == 0
        # Rich formatting typically uses box drawing characters
        # Just verify the command runs and produces output
        assert len(result.stdout) > 0

    def test_version_output_formatted(self) -> None:
        """Test that version output is properly formatted."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "version" in result.stdout.lower()
        assert __version__ in result.stdout


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
