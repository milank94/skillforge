"""
Tests for basic package functionality.

Tests package imports, version information, and module structure.
"""

import skillforge
from skillforge import __author__, __email__, __version__


class TestPackageMetadata:
    """Test package metadata and version information."""

    def test_version_exists(self) -> None:
        """Test that version is defined."""
        assert __version__ is not None
        assert isinstance(__version__, str)

    def test_version_format(self) -> None:
        """Test that version follows semantic versioning format."""
        assert __version__ == "0.1.0"
        parts = __version__.split(".")
        assert len(parts) == 3
        assert all(part.isdigit() for part in parts)

    def test_author_exists(self) -> None:
        """Test that author is defined."""
        assert __author__ is not None
        assert isinstance(__author__, str)

    def test_email_exists(self) -> None:
        """Test that email is defined."""
        assert __email__ is not None
        assert isinstance(__email__, str)


class TestPackageImports:
    """Test package imports and module structure."""

    def test_package_import(self) -> None:
        """Test that the package can be imported."""
        assert skillforge is not None

    def test_cli_module_import(self) -> None:
        """Test that the CLI module can be imported."""
        from skillforge import cli

        assert cli is not None

    def test_cli_app_exists(self) -> None:
        """Test that the CLI app exists."""
        from skillforge.cli import app

        assert app is not None

    def test_cli_console_exists(self) -> None:
        """Test that the Rich console exists."""
        from skillforge.cli import console

        assert console is not None
