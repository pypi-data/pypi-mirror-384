# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

# pylint: disable=redefined-outer-name

"""
Unit tests for qBraid core FileManager class.

"""

from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from qbraid_core.system.exceptions import UnknownFileSystemObjectError
from qbraid_core.system.filemanager import (
    FileManager,
    remove_pycache,
    remove_pycache_dirs,
    remove_pycache_loop,
)


@pytest.fixture
def file_manager():
    """Return a FileManager instance."""
    return FileManager()


@pytest.fixture
def mock_paths():
    """Mock source and destination paths."""
    source = MagicMock(spec=Path)
    destination = MagicMock(spec=Path)
    return source, destination


@pytest.fixture
def mock_path(monkeypatch):
    """Mock the Path class."""
    mock = MagicMock(spec=Path)
    monkeypatch.setattr("pathlib.Path", lambda *args, **kwargs: mock)
    return mock


def test_copy_tree_file(file_manager, mock_paths):
    """Test that copy_tree copies a file."""
    src_path, dst_path = mock_paths
    src_path.iterdir.return_value = [src_path]
    src_path.is_dir.return_value = False
    src_path.is_file.return_value = True
    src_path.name = "testfile.txt"

    with patch("shutil.copy") as mock_copy:
        file_manager.copy_tree(src_path, dst_path)
        mock_copy.assert_called_once_with(src_path, dst_path / "testfile.txt")


def test_remove_async_dir(file_manager, mock_path):
    """Test that remove_async removes directories."""
    mock_path.is_dir.return_value = True
    mock_path.is_file.return_value = False
    mock_path.is_symlink.return_value = False

    with patch.object(mock_path, "unlink") as mock_unlink:
        file_manager.remove_async(mock_path)
        mock_unlink.assert_not_called()

    with patch("shutil.rmtree") as mock_rmtree:
        file_manager.remove_async(mock_path)
        mock_rmtree.assert_called_once()


@pytest.mark.parametrize("is_file,is_symlink", [(True, False), (False, True)])
def test_remove_async_file_or_symlink(file_manager, mock_path, is_file, is_symlink):
    """Test that remove_async removes files and symbolic links."""
    mock_path.is_dir.return_value = False
    mock_path.is_file.return_value = is_file
    mock_path.is_symlink.return_value = is_symlink

    with patch.object(mock_path, "unlink") as mock_unlink:
        file_manager.remove_async(mock_path)
        mock_unlink.assert_called_once()

    with patch("shutil.rmtree") as mock_rmtree:
        file_manager.remove_async(mock_path)
        mock_rmtree.assert_not_called()


def test_thread_counter(file_manager, mock_paths):
    """Test that the thread counter is incremented and decremented correctly."""
    src_path = mock_paths[0]
    src_path.is_dir.return_value = True
    src_path.is_file.return_value = False
    src_path.is_symlink.return_value = True

    file_manager.remove_tree(src_path)
    file_manager.join_threads()
    assert file_manager.counter() > 0, "Thread counter should be incremented"


@pytest.mark.parametrize(
    "path_type",
    [
        Path().is_file,
        Path().is_dir,
        Path().is_symlink,
    ],
)
def test_copy_tree_excepts_known_file_system_object(file_manager, mock_paths, path_type):
    """Test that copy_tree does not raise UnknownFileSystemObjectError
    for known file system objects."""
    src_path, _ = mock_paths
    src_path.is_file.return_value = False
    src_path.is_dir.return_value = False
    src_path.is_symlink.return_value = False

    setattr(src_path, path_type.__name__.replace("is_", ""), True)

    try:
        file_manager.copy_tree(src_path, Path("/dummy/destination"))
    except UnknownFileSystemObjectError:
        pytest.fail(f"UnknownFileSystemObjectError raised for {path_type}")


def test_copy_tree_raises_unknown_file_system_object_error(file_manager):
    """Test that copy_tree raises UnknownFileSystemObjectError for unknown file system objects."""
    src_path = MagicMock(spec=Path)
    dst_path = MagicMock(spec=Path)

    src_path.iterdir.return_value = [src_path]
    src_path.is_file.return_value = False
    src_path.is_dir.return_value = False
    src_path.is_symlink.return_value = False
    src_path.name = "unknown_object"

    with pytest.raises(UnknownFileSystemObjectError) as exc_info:
        file_manager.copy_tree(src_path, dst_path)

    assert "The path" in str(
        exc_info.value
    ) and "is not a file, directory, or symbolic link." in str(exc_info.value)


def test_remove_pycache_dirs(tmp_path):
    """Test that remove_pycache_dirs removes all __pycache__ directories."""
    d = tmp_path / "project"
    d.mkdir()
    (d / "__pycache__").mkdir()
    sub = d / "sub"
    sub.mkdir()
    (sub / "__pycache__").mkdir()

    with patch("shutil.rmtree") as mock_rmtree:
        remove_pycache_dirs(str(d))

        assert mock_rmtree.call_count == 2
        expected_calls = [call(str(d / "__pycache__")), call(str(sub / "__pycache__"))]
        mock_rmtree.assert_has_calls(expected_calls, any_order=True)


@pytest.mark.asyncio
async def test_remove_pycache_loop(tmp_path):
    """Test that remove_pycache_loop removes all __pycache__ directories."""
    d = tmp_path / "venv"
    d.mkdir()
    (d / "lib").mkdir()
    (d / "lib" / "__pycache__").mkdir()

    with patch("qbraid_core.system.filemanager.remove_pycache_dirs") as mock_remove_dirs:
        await remove_pycache_loop(str(d))
        assert mock_remove_dirs.called


def test_remove_pycache(tmp_path):
    """Test that remove_pycache calls remove_pycache_loop."""
    with patch("qbraid_core.system.filemanager.remove_pycache_loop") as mock_remove_loop:
        remove_pycache(str(tmp_path))
        mock_remove_loop.assert_called_once_with(str(tmp_path))
