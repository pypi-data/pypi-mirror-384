"""Tests for the simplified CLI of folder2md4llms.

This module tests the command-line interface functionality.
"""

import subprocess
import sys
from pathlib import Path

from click.testing import CliRunner

from folder2md4llms.cli import main


class TestSimplifiedCLI:
    """Test the simplified CLI interface."""

    def test_cli_basic_usage(self, sample_repo):
        """Test basic CLI usage without any flags."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(main, [str(sample_repo)])
            assert result.exit_code == 0, result.output
            assert "Repository processed successfully" in result.output
            assert Path("output.md").exists()

    def test_cli_custom_output(self, sample_repo):
        """Test the --output flag."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(main, [str(sample_repo), "-o", "custom.md"])
            assert result.exit_code == 0, result.output
            assert "custom.md" in result.output
            assert Path("custom.md").exists()

    def test_cli_limit_tokens(self, sample_repo):
        """Test the --limit flag with tokens."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(main, [str(sample_repo), "--limit", "5000t"])
            assert result.exit_code == 0, result.output
            # Check that smart condensing was triggered implicitly
            # A more robust test would mock the processor and check its config
            assert "Repository processed successfully" in result.output

    def test_cli_limit_characters(self, sample_repo):
        """Test the --limit flag with characters."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(main, [str(sample_repo), "--limit", "10000c"])
            assert result.exit_code == 0, result.output
            assert "Repository processed successfully" in result.output

    def test_cli_invalid_limit_format(self, sample_repo):
        """Test the --limit flag with an invalid format."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(main, [str(sample_repo), "--limit", "10000x"])
            assert result.exit_code == 1
            assert "Invalid limit format" in result.output

    def test_cli_condense_flag(self, sample_repo):
        """Test the --condense flag."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(main, [str(sample_repo), "--condense"])
            assert result.exit_code == 0, result.output
            # A more robust test would check if condensing was actually applied
            assert "Repository processed successfully" in result.output

    def test_cli_clipboard_option(self, sample_repo, mocker):
        """Test the --clipboard flag."""
        mocker.patch("pyperclip.copy")
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(main, [str(sample_repo), "--clipboard"])
            assert result.exit_code == 0, result.output
            assert "Output copied to clipboard" in result.output

    def test_cli_verbose_mode(self, sample_repo):
        """Test the --verbose flag."""
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(main, [str(sample_repo), "--verbose"])
            assert result.exit_code == 0, result.output
            assert "Repository processed successfully" in result.output

    def test_cli_init_ignore(self, tmp_path):
        """Test the --init-ignore flag."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=tmp_path) as td:
            result = runner.invoke(main, ["--init-ignore", str(td)])
            assert result.exit_code == 0, result.output
            assert "Generated .folder2md_ignore template" in result.output
            assert (Path(td) / ".folder2md_ignore").exists()

    def test_cli_help_message(self):
        """Test the --help message."""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Usage:" in result.output
        assert "folder2md" in result.output
        assert "--limit" in result.output
        assert "--condense" in result.output
        assert "--output" in result.output

    def test_cli_version_message(self):
        """Test the --version message."""
        runner = CliRunner()
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "folder2md4llms, version" in result.output

    def test_nonexistent_directory(self):
        """Test CLI with a nonexistent directory."""
        runner = CliRunner()
        result = runner.invoke(main, ["/nonexistent/path"])
        assert result.exit_code != 0
        assert "Directory '/nonexistent/path' does not exist" in result.output


class TestMainModule:
    """Test the __main__.py module entry point."""

    def test_main_module_help(self):
        """Test running the module with --help."""
        result = subprocess.run(
            [sys.executable, "-m", "folder2md4llms", "--help"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
        assert "Usage:" in result.stdout
        assert "folder2md" in result.stdout

    def test_main_module_version(self):
        """Test running the module with --version."""
        result = subprocess.run(
            [sys.executable, "-m", "folder2md4llms", "--version"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0
        assert "folder2md4llms, version" in result.stdout

    def test_main_module_basic_functionality(self, tmp_path):
        """Test running the module with basic functionality."""
        # Create a simple test directory
        test_dir = tmp_path / "test_project"
        test_dir.mkdir()
        (test_dir / "test.py").write_text("print('hello world')")
        (test_dir / "README.md").write_text("# Test Project")

        # Run the module
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "folder2md4llms",
                str(test_dir),
                "--output",
                str(tmp_path / "output.md"),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0
        assert (tmp_path / "output.md").exists()

        # Check that the output contains our test content
        output_content = (tmp_path / "output.md").read_text()
        assert "hello world" in output_content
        assert "Test Project" in output_content
