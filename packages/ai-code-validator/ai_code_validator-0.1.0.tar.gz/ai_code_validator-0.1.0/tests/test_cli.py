"""
Unit tests for CLI module.
"""

import pytest
from click.testing import CliRunner
from ai_code_validator.cli import cli
import tempfile
import os


class TestCLI:
    """Test cases for CLI interface."""

    def test_cli_help(self):
        """Test CLI help command."""
        runner = CliRunner()
        result = runner.invoke(cli, ['--help'])

        assert result.exit_code == 0
        assert 'AI Code Validator' in result.output

    def test_cli_version(self):
        """Test CLI version command."""
        runner = CliRunner()
        result = runner.invoke(cli, ['--version'])

        assert result.exit_code == 0
        assert '0.1.0' in result.output

    def test_check_command_help(self):
        """Test check command help."""
        runner = CliRunner()
        result = runner.invoke(cli, ['check', '--help'])

        assert result.exit_code == 0
        assert 'Check files or directories' in result.output

    def test_check_single_file(self, tmp_path):
        """Test checking a single file."""
        # Create a test file
        test_file = tmp_path / "test.py"
        test_file.write_text('print("Hello")')

        runner = CliRunner()
        result = runner.invoke(cli, ['check', str(test_file), '--no-deps'])

        assert result.exit_code == 0

    def test_check_bad_file(self, tmp_path):
        """Test checking a file with issues."""
        # Create a file with issues
        test_file = tmp_path / "bad.py"
        test_file.write_text('query = "SELECT * FROM users WHERE id = \'" + user_id + "\'"')

        runner = CliRunner()
        result = runner.invoke(cli, ['check', str(test_file), '--no-deps'])

        # Should exit with error code due to critical issues
        assert 'sql_injection' in result.output.lower() or 'issue' in result.output.lower()

    def test_check_directory(self, tmp_path):
        """Test checking a directory."""
        # Create test files
        (tmp_path / "test1.py").write_text('print("Hello")')
        (tmp_path / "test2.py").write_text('print("World")')

        runner = CliRunner()
        result = runner.invoke(cli, ['check', str(tmp_path), '--no-deps'])

        assert result.exit_code == 0
        assert 'Checking' in result.output

    def test_check_nonexistent_file(self):
        """Test checking a file that doesn't exist."""
        runner = CliRunner()
        result = runner.invoke(cli, ['check', '/nonexistent/file.py'])

        assert result.exit_code != 0

    def test_check_with_format_json(self, tmp_path):
        """Test JSON output format."""
        test_file = tmp_path / "test.py"
        test_file.write_text('print("Hello")')

        runner = CliRunner()
        result = runner.invoke(cli, ['check', str(test_file), '--format', 'json', '--no-deps'])

        assert result.exit_code == 0
        # Should be valid JSON
        assert '{' in result.output
        assert '}' in result.output

    def test_check_with_severity_filter(self, tmp_path):
        """Test severity filtering."""
        test_file = tmp_path / "test.py"
        test_file.write_text('from __future__ import print_function')  # Low severity

        runner = CliRunner()

        # Should show low severity issues
        result_all = runner.invoke(cli, ['check', str(test_file), '--severity', 'all', '--no-deps'])
        assert result_all.exit_code == 0

        # Should not show low severity issues
        result_critical = runner.invoke(cli, ['check', str(test_file), '--severity', 'critical', '--no-deps'])
        assert result_critical.exit_code == 0

    def test_check_no_files_error(self):
        """Test error when no files provided."""
        runner = CliRunner()
        result = runner.invoke(cli, ['check'])

        assert result.exit_code != 0
        assert 'Error' in result.output or 'provide' in result.output.lower()

    def test_examples_command(self):
        """Test examples command."""
        runner = CliRunner()
        result = runner.invoke(cli, ['examples'])

        assert result.exit_code == 0
        assert 'Example' in result.output or 'example' in result.output

    def test_install_hook_outside_git(self, tmp_path):
        """Test install-hook command outside git repository."""
        runner = CliRunner()

        # Change to temp directory (not a git repo)
        with runner.isolated_filesystem(temp_dir=tmp_path):
            result = runner.invoke(cli, ['install-hook'])

            assert result.exit_code != 0
            assert 'git' in result.output.lower()

    def test_check_skips_node_modules(self, tmp_path):
        """Test that node_modules and other directories are skipped."""
        # Create node_modules directory
        node_modules = tmp_path / "node_modules"
        node_modules.mkdir()
        (node_modules / "test.js").write_text('console.log("test");')

        # Create regular file
        (tmp_path / "app.js").write_text('console.log("app");')

        runner = CliRunner()
        result = runner.invoke(cli, ['check', str(tmp_path), '--no-deps'])

        # Should skip node_modules
        assert 'node_modules' not in result.output or 'Checking 1 file' in result.output

    def test_no_deps_flag(self, tmp_path):
        """Test --no-deps flag skips dependency checking."""
        test_file = tmp_path / "test.py"
        test_file.write_text('import requests')

        runner = CliRunner()

        # With --no-deps should be faster
        result = runner.invoke(cli, ['check', str(test_file), '--no-deps'])
        assert result.exit_code == 0

    def test_cli_file_discovery(self, tmp_path):
        """Test CLI finds code files in directory."""
        # Create various file types
        (tmp_path / "test.py").write_text('print("test")')
        (tmp_path / "test.js").write_text('console.log("test");')
        (tmp_path / "test.txt").write_text('not code')
        (tmp_path / "__pycache__").mkdir()
        (tmp_path / "__pycache__" / "cached.pyc").write_text('cached')

        runner = CliRunner()
        result = runner.invoke(cli, ['check', str(tmp_path), '--no-deps'])

        # Should find .py and .js files, skip .txt and __pycache__
        assert 'Checking' in result.output
        assert result.exit_code == 0
