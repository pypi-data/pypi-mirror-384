# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

# pylint: disable=unused-argument,redefined-outer-name

"""
Unit tests for adding and removing kernels.

"""
import shutil
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from qbraid_core.services.environments.kernels import add_kernels, remove_kernels


@pytest.fixture
def temporary_qbraid_envs_dir():
    """Creates a temporary .qbraid/environments directory."""
    home_path = Path.home()
    qbraid_path = home_path / ".qbraid"
    qbraid_envs_path = qbraid_path / "environments"
    backup_path = qbraid_path / "environments_backup"

    # Check if the .qbraid/environments directory exists and move it if it does
    if qbraid_envs_path.exists():
        shutil.move(str(qbraid_envs_path), str(backup_path))

    # Ensure the .qbraid/environments directory is created for the test
    qbraid_envs_path.mkdir(parents=True, exist_ok=True)

    yield qbraid_envs_path

    # Cleanup after the test
    shutil.rmtree(qbraid_envs_path)

    # Restore the original .qbraid/environments directory if it was moved
    if backup_path.exists():
        shutil.move(str(backup_path), str(qbraid_envs_path))


@patch("qbraid_core.services.environments.kernels._get_kernels_path")
@patch("qbraid_core.services.environments.kernels.KernelSpecManager")
def test_add_kernels_local(
    mock_kernel_spec_manager_cls, mock_get_kernels_path, temporary_qbraid_envs_dir
):
    """Test adding a kernel at the local jupyter kernels path."""
    kernel_spec_manager = mock_kernel_spec_manager_cls.return_value
    mock_kernels_path = MagicMock()
    mock_kernels_path.iterdir.return_value = [Path("/path/to/kernel1"), Path("/path/to/kernel2")]
    mock_get_kernels_path.return_value = mock_kernels_path

    home_path = Path.home()
    local_path = home_path / ".local"

    with patch("sys.prefix", str(local_path)):
        add_kernels("test_env")

    kernel_spec_manager.install_kernel_spec.assert_has_calls(
        [
            call(source_dir=str(Path("/path/to/kernel1")), prefix=str(local_path)),
            call(source_dir=str(Path("/path/to/kernel2")), prefix=str(local_path)),
        ]
    )


def test_add_kernels_not_found(temporary_qbraid_envs_dir):
    """Test adding kernels to a non-existent environment."""
    environment = "non_existent_env"

    with pytest.raises(ValueError) as exc_info:
        add_kernels(environment)

    assert str(exc_info.value) == f"Environment '{environment}' not found."


@patch("qbraid_core.services.environments.kernels._get_kernels_path")
@patch("qbraid_core.services.environments.kernels.KernelSpecManager")
def test_remove_kernels(
    mock_kernel_spec_manager_cls, mock_get_kernels_path, temporary_qbraid_envs_dir
):
    """Test removing a kernel."""
    kernel_spec_manager = mock_kernel_spec_manager_cls.return_value
    mock_kernels_path = MagicMock()
    mock_kernels_path.iterdir.return_value = [Path("/path/to/kernel1")]
    mock_get_kernels_path.return_value = mock_kernels_path
    remove_kernels("kernel1")
    kernel_spec_manager.remove_kernel_spec.assert_called_with("kernel1")


def test_remove_fake_kernel(temporary_qbraid_envs_dir):
    """Test removing a kernel that does not exist."""
    with pytest.raises(ValueError) as exc_info:
        remove_kernels("this_env_does_not_exist")

    assert str(exc_info.value) == "Environment 'this_env_does_not_exist' not found."
