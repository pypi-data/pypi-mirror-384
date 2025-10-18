# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

"""
Unit tests for qBraid core helper functions related to system executables.

"""
import os
import platform
import stat
import subprocess
import sys
from pathlib import Path
from subprocess import CalledProcessError
from unittest.mock import MagicMock, mock_open, patch

import pytest

from qbraid_core.system.executables import (
    _extract_python_version,
    check_python_env,
    get_active_python_path,
    get_python_executables,
    get_python_version,
    get_python_version_from_cfg,
    get_python_version_from_exe,
    is_exe,
    is_notebook_environment,
    is_valid_python,
    parallel_check_envs,
    python_paths_equivalent,
)


def test_get_active_python_path_same_as_sys_executable():
    """
    Test that get_active_python_path() matches sys.executable when executed with
    the same Python executable.

    """
    with (
        patch("qbraid_core.system.executables.sys.executable", "/opt/conda/bin/python"),
        patch("qbraid_core.system.executables.subprocess.run") as mock_run,
    ):
        mock_run.return_value = MagicMock(returncode=0, stdout="/opt/conda/bin/python\n")

        assert get_active_python_path() == Path(
            sys.executable
        ), "The path should match sys.executable"


def test_get_active_python_path_virtualenv():
    """
    Test that get_active_python_path() returns the same path as
    `which python` in a virtual environment.

    """
    virtual_env_path = "/home/jovyan/.qbraid/environments/mynewe_kc5ixd/pyenv/bin/python"
    with (
        patch("qbraid_core.system.executables.sys.executable", "/opt/conda/bin/python"),
        patch("qbraid_core.system.executables.subprocess.run") as mock_run,
    ):
        mock_run.return_value = MagicMock(returncode=0, stdout=f"{virtual_env_path}\n")

        active_path = get_active_python_path()
        expected_path = Path(virtual_env_path)
        assert str(active_path) == str(
            expected_path
        ), "The path should match the virtual environment's Python"


@pytest.mark.parametrize(
    "version_string, expected_version",
    [
        ("python", None),
        ("python2", 2),
        ("python2.7", 2),
        ("python3.8", 3),
        ("python 3.9", 3),
        ("python-3.10", 3),
    ],
)
def test_extract_python_version(version_string, expected_version):
    """Test that the Python version is correctly extracted from a string."""
    assert _extract_python_version(version_string) == expected_version


@pytest.mark.skipif(sys.platform == "win32", reason="Test only for Unix-like systems")
@pytest.mark.parametrize(
    "path1, path2, expected",
    [
        # Test cases where paths should be equivalent
        ("/usr/bin/python3.7", "/usr/bin/python", True),  # Not passing on Windows?
        (Path("/usr/bin/python3.7"), Path("/usr/bin/python"), True),
        ("/usr/bin/python3.7", Path("/usr/bin/python"), True),
        ("/opt/pythonista3/bin/python-3.8", "/opt/pythonista3/bin/python", True),
        # Test cases where paths should not be equivalent
        ("/usr/bin/python3.7", "/usr/local/bin/python", False),
        (Path("/usr/bin/python3.8"), "/usr/local/bin/python2.7", False),
        ("/opt/pythonista3/bin/python3.10", "/opt/pythonista3/bin/python2.7", False),
        ("/bin/python3.9-debug/bin/python3.9", "/bin/python-debug/bin/python2", False),
    ],
)
def test_python_paths_equivalence(path1, path2, expected):
    """Test that python paths are considered equivalent correctly."""
    assert python_paths_equivalent(path1, path2) == expected


def test_is_exe_file_does_not_exist(monkeypatch):
    """Test that is_exe returns False when the file does not exist."""
    # Setup: Ensure the file does not exist
    monkeypatch.setattr(Path, "exists", MagicMock(return_value=False))
    assert not is_exe("/nonexistent/file")


def test_is_exe_file_exists_but_is_directory(monkeypatch):
    """Test that is_exe returns False when the path is a directory."""
    monkeypatch.setattr(Path, "exists", MagicMock(return_value=True))
    monkeypatch.setattr(Path, "is_file", MagicMock(return_value=False))
    assert not is_exe("/path/to/directory")


def test_is_exe_no_access_rights(monkeypatch):
    """Test that is_exe returns False when the file has no access rights."""
    monkeypatch.setattr(Path, "exists", MagicMock(return_value=True))
    monkeypatch.setattr(Path, "is_file", MagicMock(return_value=True))
    with patch("os.access", return_value=False):
        assert not is_exe("/path/to/locked/file")


@pytest.mark.parametrize(
    "system, extension, expected",
    [
        ("Windows", ".exe", True),
        ("Windows", ".bat", True),
        ("Windows", ".cmd", True),
        ("Windows", ".sh", False),
        ("Linux", ".sh", True),
        ("Linux", ".exe", False),
    ],
)
def test_os_specific_checks(monkeypatch, system, extension, expected):
    """Test is_exe against different file extensions in varrying operating systems."""
    monkeypatch.setattr(Path, "exists", MagicMock(return_value=True))
    monkeypatch.setattr(Path, "is_file", MagicMock(return_value=True))
    monkeypatch.setattr(platform, "system", MagicMock(return_value=system))
    test_path = f"/fake/path/file{extension}"

    if system == "Windows":
        with patch("os.access", return_value=True):
            assert is_exe(test_path) is expected
    else:
        with patch("os.access") as mock_access:

            def side_effect(path, mode):  # pylint: disable=unused-argument
                if mode & os.X_OK:
                    return True
                if mode == os.F_OK:
                    return True
                return False

            mock_access.side_effect = side_effect

            # Mock stat result to simulate executable permission
            st_mode = stat.S_IXUSR if expected else 0
            with patch.object(Path, "stat", return_value=MagicMock(st_mode=st_mode)):
                assert is_exe(test_path) is expected


def test_executable_flag_check_unix(monkeypatch):
    """Test that is_exe returns True for an executable file on Unix."""
    monkeypatch.setattr(platform, "system", MagicMock(return_value="Linux"))
    monkeypatch.setattr(Path, "exists", MagicMock(return_value=True))
    monkeypatch.setattr(Path, "is_file", MagicMock(return_value=True))
    with (
        patch("os.access", return_value=True),
        patch.object(Path, "stat", return_value=MagicMock(st_mode=stat.S_IXUSR)),
    ):
        assert is_exe("/unix/executable/file")


def test_non_executable_file_unix(monkeypatch):
    """Test that is_exe returns False for a non-executable file on Unix."""
    monkeypatch.setattr(platform, "system", MagicMock(return_value="Linux"))
    monkeypatch.setattr(Path, "exists", MagicMock(return_value=True))
    monkeypatch.setattr(Path, "is_file", MagicMock(return_value=True))
    with patch("os.access", return_value=False):
        assert not is_exe("/unix/non-executable/file")


def test_is_valid_python():
    """
    Test that is_valid_python() returns True for a valid Python executable.
    """
    assert is_valid_python(Path(sys.executable))


def test_invalid_python():
    """
    Test that is_valid_python() returns False for an invalid Python executable.
    """
    assert not is_valid_python(Path("/invalid/python/path"))


@patch("subprocess.run")
@patch("shutil.which")
def test_get_python_version_valid(mock_which, mock_run):
    """Test that the get_python_version function returns the correct version."""
    mock_which.return_value = True
    mock_run.return_value.stdout = "Python 3.8.5"
    mock_run.return_value.returncode = 0

    version = get_python_version(Path("/usr/bin/python3"))
    assert version == "3.8.5"


@patch("subprocess.run")
@patch("sys.platform")
def test_get_valid_python_version_from_exe(mock_platform, mock_run):
    """
    Test that get_python_version_from_exe() returns the correct version.
    """
    venv_path = Path("path/to/env")
    mock_platform.return_value = "linux"
    mock_run.return_value.returncode = 0
    mock_run.return_value.stdout = "Python 3.8.5"

    assert get_python_version_from_exe(venv_path) == "3.8.5"


@pytest.mark.parametrize(
    "exception",
    [
        subprocess.CalledProcessError(returncode=1, cmd="python --version"),
        Exception("General error"),
    ],
)
@patch("subprocess.run")
@patch("sys.platform")
def test_get_python_version_from_exe_raises_exceptions(mock_platform, mock_run, exception):
    """
    Test that get_python_version_from_exe() returns None for different exceptions.
    """
    venv_path = Path("path/to/env")
    mock_platform.return_value = "linux"
    mock_run.side_effect = exception

    # Call the function and assert that it returns None
    assert get_python_version_from_exe(venv_path) is None

    # Verify that the subprocess.run was called with the expected arguments
    python_executable = venv_path / "bin" / "python"
    mock_run.assert_called_once_with(
        [str(python_executable), "--version"],
        capture_output=True,
        text=True,
        check=True,
    )


@patch("builtins.open", new_callable=mock_open, read_data="version = 3.11.7\n")
@patch("pathlib.Path.exists")
def test_get_python_version_from_cfg_valid(mock_exists, _):
    """
    Test that get_python_version_from_cfg() returns the correct version.
    """
    mock_exists.return_value = True

    venv_path = Path("path/to/env")
    assert get_python_version_from_cfg(venv_path) == "3.11"


@patch("builtins.open", new_callable=mock_open, read_data="version = 3.11.7\n")
@patch("pathlib.Path.exists")
def test_get_python_version_from_cfg_file_not_found(mock_exists, _):
    """
    Test that get_python_version_from_cfg() returns None if the pyvenv.cfg file does not exist.
    """
    mock_exists.return_value = False
    venv_path = Path("path/to/env")
    assert get_python_version_from_cfg(venv_path) is None


@pytest.mark.parametrize("exception", [IOError("IO error"), Exception("General error")])
@patch("builtins.open", new_callable=mock_open, read_data="version = 3.11.7\n")
@patch("pathlib.Path.exists")
def test_get_python_version_from_cfg_raises_exceptions(mock_exists, mock_open_test, exception):
    """
    Test that get_python_version_from_cfg() returns None for different exceptions.
    """
    mock_exists.return_value = True
    venv_path = Path("path/to/env")
    mock_open_test.side_effect = exception

    # Call the function and assert that it returns None
    assert get_python_version_from_cfg(venv_path) is None


@patch("subprocess.run")
@patch("shutil.which")
def test_get_python_version_executable_not_found(
    mock_which, mock_run
):  # pylint: disable=unused-argument
    """Test that the get_python_version function raises an error for a non-existent executable."""
    mock_which.return_value = None

    err_path = Path("/invalid/path/python")
    with pytest.raises(ValueError) as exc_info:
        get_python_version(err_path)

    assert str(exc_info.value) == f"Python executable not found: {err_path}"


@patch("subprocess.run")
@patch("shutil.which")
def test_get_python_version_semantically_invalid(mock_which, mock_run):
    """Test that the get_python_version function returns the correct version."""
    mock_which.return_value = True
    mock_run.return_value.stdout = "Python 3.8a*5"
    mock_run.return_value.returncode = 0

    with pytest.raises(ValueError):
        get_python_version(Path("/usr/bin/python3"))


@pytest.mark.skipif(sys.platform == "win32", reason="Test only for Unix-like systems")
@patch("subprocess.run")
@patch("qbraid_core.system.executables.is_exe")
@patch("shutil.which")
def test_get_python_version_invalid_executable(mock_which, mock_is_exe, mock_run):
    """Test that the get_python_version function raises an error for an invalid executable."""
    mock_which.return_value = "valid/path/python"
    mock_is_exe.return_value = False
    mock_run.return_value.stdout = "Python 3.8.5"
    mock_run.return_value.returncode = 0

    err_path = Path("/invalid/exe/python")
    with pytest.raises(ValueError) as exc_info:
        get_python_version(err_path)

    assert str(exc_info.value) == f"Invalid Python executable: {err_path}"


@patch("subprocess.run")
@patch("qbraid_core.system.executables.is_exe")
@patch("shutil.which")
def test_get_python_version_err_valid_executable(mock_which, mock_is_exe, mock_run):
    """Test that the get_python_version function raises an error for a corrupted executable."""
    mock_which.return_value = "valid/path/python"
    mock_is_exe.return_value = True
    mock_run.side_effect = subprocess.CalledProcessError(1, "python_err")

    valid_exe_path = Path("/valid/exe/python")
    with pytest.raises(RuntimeError) as exc_info:
        get_python_version(valid_exe_path)

    assert str(exc_info.value) == f"Failed to get Python version for {valid_exe_path}"


@patch("subprocess.run")
def test_get_python_version_invalid_output(mock_run):
    """Test that the get_python_version function raises an error for invalid output."""
    mock_run.return_value.stdout = "Not a Python version"
    mock_run.return_value.returncode = 0

    with pytest.raises(ValueError):
        get_python_version(Path("/usr/bin/python3"))


@patch("subprocess.run")
def test_is_notebook_environment_installed(mock_run):
    """
    Test that the is_notebook_environment function returns True
    for a notebook environment.
    """
    mock_run.return_value.returncode = 0

    result = is_notebook_environment(Path("/usr/bin/python3"))
    assert result is True


@patch("subprocess.run")
def test_is_notebook_environment_not_installed(mock_run):
    """
    Test that the is_notebook_environment function returns False for
    a non-notebook environment.
    """
    mock_run.side_effect = CalledProcessError(1, "python")

    result = is_notebook_environment(Path("/usr/bin/python3"))
    assert result is False


@patch("qbraid_core.system.executables.is_notebook_environment")
def test_check_python_env_invalid(mock_is_notebook):
    """Test that the check_python_env function returns None for an invalid environment."""
    mock_is_notebook.return_value = False

    version, path = check_python_env(Path("/invalid/env"))
    assert version is None
    assert path is None


@patch("subprocess.run")
@patch("qbraid_core.system.executables.parallel_check_envs")
def test_get_python_executables(mock_parallel_check, mock_run):
    """
    Test that the get_python_executables function returns the correct
    conda and system executables.
    """
    mock_run.return_value.stdout = "base /opt/conda\n"
    mock_parallel_check.return_value = {"3.8.5": Path("/env1/bin/python")}

    result = get_python_executables()
    assert "system" in result
    assert "conda" in result


@patch("qbraid_core.system.executables.check_python_env")
def test_parallel_check_envs(mock_check_python_env):
    """
    Test that the parallel_check_envs function returns the correct
    version to path mappings.
    """
    mock_check_python_env.side_effect = [
        ("3.8.5", Path("/env1/bin/python")),
        ("3.9.0", Path("/env2/bin/python")),
    ]

    env_paths = [Path("/env1"), Path("/env2")]
    result = parallel_check_envs(env_paths)
    expected_result = {
        "3.8.5": Path("/env1/bin/python"),
        "3.9.0": Path("/env2/bin/python"),
    }
    assert result == expected_result
