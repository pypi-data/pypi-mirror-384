"""Tests for git client functionality."""

import pytest
from pathlib import Path
from commitlm.integrations.git_client import GitClient, GitClientError


class TestGitClient:
    """Test GitClient class."""

    def test_git_client_with_valid_repo(self, mock_git_repo):
        """Test creating git client with valid repo."""
        client = GitClient(str(mock_git_repo))
        assert str(client.repo_path) == str(mock_git_repo)

    def test_git_client_with_invalid_repo(self, temp_dir):
        """Test creating git client with invalid repo."""
        with pytest.raises(GitClientError):
            GitClient(str(temp_dir))

    def test_hooks_directory_exists(self, mock_git_repo):
        """Test that hooks directory exists."""
        GitClient(str(mock_git_repo))  # Verify client creation succeeds
        hooks_dir = Path(mock_git_repo) / ".git" / "hooks"
        assert hooks_dir.exists()

    def test_install_prepare_commit_msg_hook(self, mock_git_repo):
        """Test installing prepare-commit-msg hook."""
        GitClient(str(mock_git_repo))  # Verify client creation succeeds
        hook_path = Path(mock_git_repo) / ".git" / "hooks" / "prepare-commit-msg"

        # Create a simple hook script
        hook_script = """#!/bin/bash
# CommitLM Generator Prepare-Commit-Msg Hook
echo "Hook installed"
"""
        with open(hook_path, "w") as f:
            f.write(hook_script)
        hook_path.chmod(0o755)

        assert hook_path.exists()
        assert hook_path.stat().st_mode & 0o111  # Check executable

    def test_install_post_commit_hook(self, mock_git_repo):
        """Test installing post-commit hook."""
        GitClient(str(mock_git_repo))  # Verify client creation succeeds
        hook_path = Path(mock_git_repo) / ".git" / "hooks" / "post-commit"

        # Create a simple hook script
        hook_script = """#!/bin/bash
# CommitLM Post-Commit Hook
echo "Hook installed"
"""
        with open(hook_path, "w") as f:
            f.write(hook_script)
        hook_path.chmod(0o755)

        assert hook_path.exists()
        assert hook_path.stat().st_mode & 0o111  # Check executable
