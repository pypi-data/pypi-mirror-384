# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

"""
Unit tests for context manager functions.

"""
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from qbraid_core.context import ensure_directory


@contextmanager
def temporary_directory():
    """Create a temporary directory for testing."""
    temp_dir = Path("temp_dir")
    temp_dir.mkdir(exist_ok=True)
    yield temp_dir
    temp_dir.rmdir()


def test_ensure_directory_created_and_removed():
    """Test that ensure_directory creates and removes a directory as expected."""
    with temporary_directory() as temp_dir:
        with (
            patch("qbraid_core.context.Path.exists", return_value=False),
            patch("qbraid_core.context.Path.mkdir") as mock_mkdir,
            patch("qbraid_core.context.Path.rmdir") as mock_rmdir,
        ):
            with ensure_directory(temp_dir, remove_if_created=True):
                pass
            mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
            mock_rmdir.assert_called_once()


def test_ensure_directory_not_removed():
    """Test that ensure_directory does not remove an existing directory when specified to do so."""
    with temporary_directory() as temp_dir:
        with (
            patch("qbraid_core.context.Path.exists", return_value=True),
            patch("qbraid_core.context.Path.mkdir") as mock_mkdir,
            patch("qbraid_core.context.Path.rmdir") as mock_rmdir,
        ):
            with ensure_directory(temp_dir, remove_if_created=True):
                pass
            mock_mkdir.assert_not_called()
            mock_rmdir.assert_not_called()


def test_ensure_directory_not_created():
    """Test that ensure_directory does not create a directory when it already exists."""
    with temporary_directory() as temp_dir:
        with (
            patch("qbraid_core.context.Path.exists", return_value=True),
            patch("qbraid_core.context.Path.mkdir") as mock_mkdir,
            patch("qbraid_core.context.Path.rmdir") as mock_rmdir,
        ):
            with ensure_directory(temp_dir, remove_if_created=False):
                pass
            mock_mkdir.assert_not_called()
            mock_rmdir.assert_not_called()
