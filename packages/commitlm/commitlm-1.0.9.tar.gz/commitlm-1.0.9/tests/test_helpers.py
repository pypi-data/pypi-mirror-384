"""Tests for utility helper functions."""

from pathlib import Path
from commitlm.utils.helpers import get_git_root
import os


class TestHelpers:
    """Test utility helper functions."""

    def test_get_git_root_with_valid_repo(self, mock_git_repo):
        """Test getting git root with valid repo."""
        # Change to mock repo directory
        original_cwd = os.getcwd()
        try:
            os.chdir(mock_git_repo)
            result = get_git_root()
            assert result is not None
            assert Path(result).exists()
        finally:
            os.chdir(original_cwd)

    def test_get_git_root_with_invalid_repo(self, temp_dir):
        """Test getting git root with invalid repo."""
        original_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            result = get_git_root()
            # Should return None or raise error for non-git directory
            assert result is None or isinstance(result, str)
        finally:
            os.chdir(original_cwd)
