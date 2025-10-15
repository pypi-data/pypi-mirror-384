"""
Test suite for the Euno SDK.

This module contains tests for the core functionality and CLI commands.
"""

from click.testing import CliRunner
from euno.core import hello_world, get_version
from euno.cli import main


class TestCore:
    """Test cases for core functionality."""

    def test_hello_world_default(self):
        """Test hello_world with default parameter."""
        result = hello_world()
        assert result == "Hello, World! Welcome to the Euno SDK!"

    def test_hello_world_custom_name(self):
        """Test hello_world with custom name."""
        result = hello_world("Euno")
        assert result == "Hello, Euno! Welcome to the Euno SDK!"

    def test_get_version(self):
        """Test get_version returns a string."""
        version = get_version()
        assert isinstance(version, str)
        assert len(version) > 0


class TestCLI:
    """Test cases for CLI functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.runner = CliRunner()

    def test_hello_world_command_default(self):
        """Test hello-world command with default name."""
        result = self.runner.invoke(main, ["hello-world"])
        assert result.exit_code == 0
        assert "Hello, World! Welcome to the Euno SDK!" in result.output

    def test_hello_world_command_custom_name(self):
        """Test hello-world command with custom name."""
        result = self.runner.invoke(main, ["hello-world", "--name", "Euno"])
        assert result.exit_code == 0
        assert "Hello, Euno! Welcome to the Euno SDK!" in result.output

    def test_version_command(self):
        """Test version command."""
        result = self.runner.invoke(main, ["version"])
        assert result.exit_code == 0
        assert "Euno SDK version:" in result.output

    def test_main_help(self):
        """Test main command help."""
        result = self.runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Euno SDK" in result.output
