# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

# pylint: disable=redefined-outer-name

"""
Unit tests the get_all_kernels function in the kernels module.

"""
from unittest.mock import patch

from qbraid_core.services.environments.kernels import get_all_kernels


@patch("qbraid_core.services.environments.kernels.KernelSpecManager")
def test_kernels_list_no_active_kernels(mock_kernel_spec_manager):
    """Test listing kernels when no kernels are active."""
    mock_kernel_spec_manager.return_value.get_all_specs.return_value = {}

    kernelspec = get_all_kernels()
    # Check if the list of kernels is empty
    assert kernelspec == {}

    # Check if the kernel_spec_manager.get_all_specs method was called
    mock_kernel_spec_manager.return_value.get_all_specs.assert_called_once()


@patch("qbraid_core.services.environments.kernels.KernelSpecManager")
def test_kernels_list_default_python3_kernel_present(mock_kernel_spec_manager):
    """Test listing kernels when the default python3 kernel is present."""
    mock_kernel_spec_manager.return_value.get_all_specs.return_value = {
        "python3": {"resource_dir": "/path/to/python3/kernel"}
    }

    kernelspec = get_all_kernels()
    # Check if the list of kernels contains the default python3 kernel
    assert "python3" in kernelspec
    # Check if the kernel_spec_manager.get_all_specs method was called
    mock_kernel_spec_manager.return_value.get_all_specs.assert_called_once()


@patch("qbraid_core.services.environments.kernels.KernelSpecManager")
def test_long_name_kernel(mock_kernel_spec_manager):
    """Test listing multiple kernels when multiple kernels are available."""
    mock_kernel_spec_manager.return_value.get_all_specs.return_value = {
        "python3": {"resource_dir": "/path/to/python3/kernel"},
        "another_kernel_with_long_name_1@#$%(!/)": {
            "resource_dir": "/path/to/another/kernel",
            "spec": {"argv": ["/not/executable/path"]},
        },
    }

    kernelspec = get_all_kernels()

    assert "python3" in kernelspec
    assert "another_kernel_with_long_name_1@#$%(!/)" in kernelspec


@patch("qbraid_core.services.environments.kernels.KernelSpecManager")
def test_two_kernels(
    mock_kernel_spec_manager,
):
    """Test listing kernels when two kernels are present."""
    mock_kernel_spec_manager.return_value.get_all_specs.return_value = {
        "python3_qbraid": {
            "resource_dir": "/path/to/python3",
            "spec": {"argv": ["/path/to/python3"]},
        },
        "qbraid_test_env": {
            "resource_dir": "/path/to/python3_qbraid",
            "spec": {"argv": ["/invalid/path"]},
        },
    }

    kernels = get_all_kernels()
    assert "python3_qbraid" in kernels
    assert "qbraid_test_env" in kernels


@patch("qbraid_core.services.environments.kernels.KernelSpecManager")
def test_three_kernels_list(mock_kernel_spec_manager):
    """Test listing kernels when three kernelspecs are present."""
    mock_kernel_spec_manager.return_value.get_all_specs.return_value = {
        "python3": {"resource_dir": "/path/to/python3", "spec": {"argv": ["/path/to/python3"]}},
        "qbraid_test_env": {
            "resource_dir": "/path/to/python3_qbraid",
            "spec": {"argv": ["/is/executable/path"]},
        },
        "qbraid_test_env2": {
            "resource_dir": "/path/to/python3_qbraid",
            "spec": {"argv": ["/is/executable/path"]},
        },
    }

    kernels = get_all_kernels()

    assert "python3" in kernels
    assert "qbraid_test_env" in kernels


@patch("qbraid_core.services.environments.kernels.KernelSpecManager")
def test_kernel_not_exist_kernel(mock_kernel_spec_manager):
    """Test listing kernels when a is not present."""
    mock_kernel_spec_manager.return_value.get_all_specs.return_value = {
        "custom": {"resource_dir": "/path/to/python3", "spec": {"argv": ["/path/to/python3"]}},
    }

    kernels = get_all_kernels()
    assert "kernel_not_exist" not in kernels
