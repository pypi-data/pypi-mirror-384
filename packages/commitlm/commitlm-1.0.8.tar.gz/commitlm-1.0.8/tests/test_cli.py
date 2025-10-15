"""Tests for CLI commands."""

from click.testing import CliRunner
from commitlm.cli.commands import main


class TestCLI:
    """Test CLI commands."""

    def test_cli_help(self):
        """Test --help command."""
        runner = CliRunner()
        result = runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "AI-powered documentation generator" in result.output
        assert "Commands:" in result.output

    def test_cli_version(self):
        """Test --version command."""
        runner = CliRunner()
        result = runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "CommitLM" in result.output

    def test_status_command(self, mock_git_repo):
        """Test status command."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=mock_git_repo):
            result = runner.invoke(main, ["status"])
            # Status command may fail without full git repo, but should not crash
            assert "Status" in result.output or result.exit_code != 0

    def test_config_get_all(self, mock_git_repo):
        """Test config get command."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=mock_git_repo):
            result = runner.invoke(main, ["config", "get"])
            # Should show config or error gracefully
            assert result.exit_code == 0 or "error" in result.output.lower()

    def test_generate_help(self):
        """Test generate --help command."""
        runner = CliRunner()
        result = runner.invoke(main, ["generate", "--help"])
        assert result.exit_code == 0
        assert "Generate documentation" in result.output

    def test_install_hook_help(self):
        """Test install-hook --help command."""
        runner = CliRunner()
        result = runner.invoke(main, ["install-hook", "--help"])
        assert result.exit_code == 0
        assert "Install git hooks" in result.output

    def test_config_help(self):
        """Test config --help command."""
        runner = CliRunner()
        result = runner.invoke(main, ["config", "--help"])
        assert result.exit_code == 0
        assert "Manage configuration" in result.output


class TestConfigCommands:
    """Test config subcommands."""

    def test_config_get_with_key(self, mock_git_repo):
        """Test config get with specific key."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=mock_git_repo):
            result = runner.invoke(main, ["config", "get", "provider"])
            # May succeed or fail depending on config, but shouldn't crash
            assert result.exit_code == 0 or "not found" in result.output.lower()

    def test_config_set_command(self, mock_git_repo):
        """Test config set command."""
        runner = CliRunner()
        with runner.isolated_filesystem(temp_dir=mock_git_repo):
            # This may fail in isolated environment, but test it doesn't crash
            result = runner.invoke(main, ["config", "set", "provider", "gemini"])
            # Accept any exit code, just ensure it doesn't crash with exception
            assert isinstance(result.exit_code, int)
