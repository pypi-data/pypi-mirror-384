# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

"""
Unit tests for create_local_venv function to test the
creation of the local virtual environment.

"""
# pylint: disable=duplicate-code

import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
import yaml

from qbraid_core.services.environments.create import create_local_venv
from qbraid_core.services.environments.schema import EnvironmentConfig


def test_create_local_venv_success(tmp_path):
    """Test the successful creation of a virtual environment and PS1 name swap."""
    prompt = "test_env"
    slug_path = tmp_path / "test_slug"
    slug_path.mkdir()

    with (
        patch("qbraid_core.services.environments.create.subprocess.run") as mock_run,
        patch("qbraid_core.services.environments.create.replace_str") as mock_replace_str,
        patch(
            "qbraid_core.services.environments.create.set_include_sys_site_pkgs_value"
        ) as mock_set_include_sys_site_pkgs_value,
        patch("qbraid_core.services.environments.create.update_state_json") as mock_update_state,
    ):
        create_local_venv(slug_path, prompt)
        venv_path = slug_path / "pyenv"

        # Verify subprocess was called correctly
        mock_run.assert_called_once_with([sys.executable, "-m", "venv", str(venv_path)], check=True)
        mock_set_include_sys_site_pkgs_value.assert_called_once_with(True, venv_path / "pyvenv.cfg")

        # Verify PS1 name was attempted to be replaced
        scripts_path = venv_path / ("Scripts" if sys.platform == "win32" else "bin")
        activate_files = (
            ["activate.bat", "Activate.ps1"]
            if sys.platform == "win32"
            else ["activate", "activate.csh", "activate.fish"]
        )
        for file in activate_files:
            if (scripts_path / file).exists():
                mock_replace_str.assert_any_call("(pyenv)", f"({prompt})", str(scripts_path / file))

        # Verify update_install_status was called with success
        mock_update_state.assert_called_once_with(slug_path, 1, 1)


def test_create_local_venv_failure(tmp_path):
    """Test the behavior when subprocess fails to create the virtual environment."""
    prompt = "test_env"
    slug_path = tmp_path / "test_slug"
    slug_path.mkdir()

    with (
        patch("qbraid_core.services.environments.create.subprocess.run") as mock_run,
        patch("qbraid_core.services.environments.create.logger.error") as mock_logger_error,
        patch("qbraid_core.services.environments.create.update_state_json") as mock_update_state,
    ):
        mock_run.side_effect = Exception("Test Error")

        create_local_venv(slug_path, prompt)

        # Verify logger captured the exception
        mock_logger_error.assert_called_once()

        # Verify update_install_status was called with failure
        mock_update_state.assert_called_once_with(slug_path, 1, 0, message="Test Error")


def test_yaml_serialize():
    """Test that the YAML file is correctly serialized."""

    yaml_files = ["fixtures/correct-icon-absolute.yaml", "fixtures/correct-icon-relative.yaml"]
    file_paths = [Path(__file__).resolve().parent / yaml_file for yaml_file in yaml_files]

    for file_path in file_paths:
        with (
            patch(
                "qbraid_core.services.environments.schema.package_has_match_on_pypi",
                return_value=True,
            ),
        ):
            parsed_data = EnvironmentConfig.from_yaml(file_path)

            actual_data_dict = parsed_data.model_dump()

            expected_data_dict = {
                "name": "test_env",
                "description": "This is a test qBraid environment for demonstration purposes.",
                "tags": "test,qbraid,environment",
                # updated acc to relative or absolute path
                "icon": "",
                # test that version is overridden with the sys version
                "python_version": "3.11.6",
                "kernel_name": "sample_kernel",
                "shell_prompt": "sample_prompt",
                "python_packages": "numpy>=1.21.0\nopenqasm3~=0.5.0\nqiskit\ncirq==1.0.0",
                "visibility": "private",
            }
            if "relative" in file_path.name:
                expected_data_dict["icon"] = str(file_path.parent / "icon.png")
            else:
                expected_data_dict["icon"] = str(Path("tests/environments/fixtures/icon.png"))
            assert actual_data_dict == expected_data_dict


def test_to_yaml():
    """Test that the YAML file is correctly serialized."""
    yaml_file = "fixtures/correct-icon-relative.yaml"
    file_path = Path(__file__).resolve().parent / yaml_file
    with (
        patch(
            "qbraid_core.services.environments.schema.package_has_match_on_pypi", return_value=True
        ),
    ):
        parsed_data = EnvironmentConfig.from_yaml(file_path)

    temp_yaml_path = Path(__file__).resolve().parent / "fixtures/actual.yaml"
    parsed_data.to_yaml(temp_yaml_path)

    with open(temp_yaml_path, "r", encoding="utf-8") as f:
        saved_yaml = yaml.safe_load(f)

    with open(file_path, "r", encoding="utf-8") as f:
        expected_yaml = yaml.safe_load(f)

    # update the icon path to platform independent absolute path
    expected_yaml["icon"] = str(file_path.parent / "icon.png")

    assert saved_yaml == expected_yaml

    os.remove(temp_yaml_path)


@pytest.mark.parametrize(
    "file_path, expected_error",
    [
        (
            "fixtures/invalid_py_version.yaml",
            "Python version must start with 3.",
        ),
        (
            "fixtures/invalid_py_version_semantic.yaml",
            "Python version must be a valid semantic version x.y.z",
        ),
        (
            "fixtures/invalid_py_package_version.yaml",
            "Version must be a valid combination of a binary op and semantic version x.y.z",
        ),
        (
            "fixtures/invalid_icon_path.yaml",
            "Icon file not found at path ",
        ),
        (
            "fixtures/invalid_icon_path_ext.yaml",
            "Icon file must be a .png file,",
        ),
        (
            "fixtures/incorrect.yaml",
            "Invalid YAML data",
        ),
        (
            "fixtures/missing_pypi_package.yaml",
            "Package 'random_123' 'v100.100.100' not found on PyPI",
        ),
    ],
)
def test_invalid_yaml_cases(file_path, expected_error):
    """Test various invalid YAML cases."""
    file_path = Path(__file__).resolve().parent / file_path

    with pytest.raises(ValueError, match=expected_error):
        EnvironmentConfig.from_yaml(file_path)
