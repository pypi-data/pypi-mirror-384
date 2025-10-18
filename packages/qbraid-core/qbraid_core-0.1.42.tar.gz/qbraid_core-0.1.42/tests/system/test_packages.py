# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

"""
Unit tests for qBraid core helper functions related to system site-packages.

"""
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

from qbraid_core.exceptions import QbraidException
from qbraid_core.system.exceptions import QbraidSystemError
from qbraid_core.system.packages import (
    extract_include_sys_site_pkgs_value,
    get_active_site_packages_path,
    get_local_package_path,
    set_include_sys_site_pkgs_value,
)

# pylint: disable=unused-argument


def test_active_site_pkgs_from_sys_exe():
    """Test the get_active_site_packages_path function for default python system executable."""
    with (
        patch("sys.executable", "/usr/bin/python"),
        patch("qbraid_core.system.executables.subprocess.run", "/usr/bin/python"),
        patch("site.getsitepackages", return_value=["/usr/lib/python3.9/site-packages"]),
    ):
        assert get_active_site_packages_path() == Path(
            "/usr/lib/python3.9/site-packages"
        ), "Should return the global site-packages path"


def test_active_site_pkgs_from_virtual_env():
    """Test the get_active_site_packages_path function when virtual env is active."""
    with (
        patch("sys.executable", "/envs/testenv/bin/python"),
        patch(
            "qbraid_core.system.executables.get_active_python_path",
            return_value=Path("/usr/bin/python"),
        ),
        patch("subprocess.run") as mock_run,
    ):
        mock_run.return_value = MagicMock(stdout="['/envs/testenv/lib/python3.9/site-packages']\n")

        active_site_packages = get_active_site_packages_path()
        expected_site_packages = Path("/envs/testenv/lib/python3.9/site-packages")
        assert str(active_site_packages) == str(
            expected_site_packages
        ), "Should return the virtual env's site-packages path"


def test_active_site_pkgs_raises_for_not_found():
    """Test the get_active_site_packages_path function when the site-packages path is not found."""
    with (
        patch("sys.executable", "/envs/testenv/bin/python"),
        patch(
            "qbraid_core.system.executables.get_active_python_path",
            return_value=Path("/usr/bin/python"),
        ),
        patch("subprocess.run") as mock_run,
    ):
        mock_run.return_value = MagicMock(stdout="[]\n")

        with pytest.raises(QbraidSystemError):
            get_active_site_packages_path()


def test_active_site_pkgs_correct_path_from_multiple():
    """Test the get_active_site_packages_path function when multiple
    site-packages paths are found."""
    with (
        patch("sys.executable", "/usr/envs/testenv/bin/python"),
        patch(
            "qbraid_core.system.executables.get_active_python_path",
            return_value=Path("/usr/envs/testenv/bin/python"),
        ),
        patch("subprocess.run") as mock_run,
    ):
        mock_run.return_value = MagicMock(
            stdout=(
                "['/usr/envs/testenv/lib/python3.9/site-packages', \
                '/usr/.local/lib/python3.9/site-packages']\n"
            )
        )

        active_site_packages = get_active_site_packages_path()
        expected_site_packages = Path("/usr/envs/testenv/lib/python3.9/site-packages")
        assert str(active_site_packages) == str(
            expected_site_packages
        ), "Should return the site-packages path matching the current environment"


@patch(
    "qbraid_core.system.packages.get_active_site_packages_path",
    return_value=Path("/path/to/site-packages"),
)
def test_get_local_package_path_exists(mock_get_active_site_packages_path):
    """Test the get_local_package_path function with an existing package."""
    package_name = "existing_package"
    expected_path = "/path/to/site-packages/existing_package"
    assert get_local_package_path(package_name) == Path(expected_path)


@patch(
    "qbraid_core.system.packages.get_active_site_packages_path",
    side_effect=QbraidException("Failed to find site-packages path."),
)
def test_get_local_package_path_error(mock_get_active_site_packages_path):
    """Test get_local_package_path function raises exception when site-packages not found."""
    package_name = "nonexistent_package"
    with pytest.raises(QbraidException):
        get_local_package_path(package_name)


def test_extract_true_value():
    """Test extract_include_sys_site_pkgs_value function with 'true' value."""
    with patch("builtins.open", mock_open(read_data="include-system-site-packages = true")):
        assert extract_include_sys_site_pkgs_value("fake_path") is True


def test_extract_false_value():
    """Test extract_include_sys_site_pkgs_value function with 'false' value."""
    with patch("builtins.open", mock_open(read_data="include-system-site-packages = false")):
        assert extract_include_sys_site_pkgs_value("fake_path") is False


def test_extract_value_no_target_line():
    """Test extract_include_sys_site_pkgs_value function with no target line."""
    with patch("builtins.open", mock_open(read_data="some-other-setting = true")):
        assert extract_include_sys_site_pkgs_value("fake_path") is None


def test_extract_value_improper_format():
    """Test extract_include_sys_site_pkgs_value function with improper format."""
    with patch("builtins.open", mock_open(read_data="include-system-site-packages true")):
        assert extract_include_sys_site_pkgs_value("fake_path") is None


def test_extract_value_file_not_found_error():
    """Test extract_include_sys_site_pkgs_value function with FileNotFoundError."""
    with patch("builtins.open", side_effect=FileNotFoundError):
        with pytest.raises(FileNotFoundError):
            extract_include_sys_site_pkgs_value("nonexistent_path")


def test_extract_value_unexpected_error():
    """Test extract_include_sys_site_pkgs_value function with unexpected error."""
    with patch("builtins.open", side_effect=Exception):
        with pytest.raises(QbraidSystemError):
            extract_include_sys_site_pkgs_value("fake_path")


def test_set_value_file_not_found_error():
    """Test set_include_sys_site_pkgs_value function with FileNotFoundError."""
    with patch("builtins.open", side_effect=FileNotFoundError):
        with pytest.raises(FileNotFoundError):
            set_include_sys_site_pkgs_value(True, "nonexistent_path")


def test_set_value_unexpected_error():
    """Test set_include_sys_site_pkgs_value function with unexpected error."""
    with patch("builtins.open", side_effect=Exception):
        with pytest.raises(QbraidSystemError):
            set_include_sys_site_pkgs_value(True, "fake_path")
