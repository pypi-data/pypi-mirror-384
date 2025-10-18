# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

"""
Unit tests for the create_qbraid_env_assets function in the envs app.

"""

import json
import os
import pathlib
import shutil
from unittest import mock  # pylint: disable=unused-variable
from unittest.mock import mock_open, patch

import pytest

from qbraid_core.services.environments.create import create_qbraid_env_assets
from qbraid_core.services.environments.schema import EnvironmentConfig


@pytest.mark.parametrize("img_data_url", [None, "data:image/png;base64,random_data"])
def test_create_qbraid_env_assets(tmp_path, img_data_url):  # pylint: disable=too-many-locals
    """Test creating the assets for a qbraid environment."""
    slug = "test_slug"
    slug_path = str(tmp_path)

    kernel_spec_mock = {
        "python3": {
            "spec": {
                "argv": ["python", "-m", "ipykernel_launcher", "-f", "{connection_file}"],
                "display_name": "Python 3",
                "language": "python",
            },
            "resource_dir": "/path/to/default/resources",
        }
    }

    env_config = EnvironmentConfig.from_yaml(
        file_path=pathlib.Path(__file__).resolve().parent / "fixtures/correct-icon-relative.yaml"
    )

    with (
        patch("os.makedirs"),
        patch("os.path.isfile", return_value=True),
        patch("shutil.copy"),
        patch("json.dump"),
        patch("builtins.open", mock_open()),
        patch(
            "qbraid_core.services.environments.create.update_state_json"
        ) as mock_update_state_json,
        patch(
            "jupyter_client.kernelspec.KernelSpecManager.get_all_specs",
            return_value=kernel_spec_mock,
        ),
        patch(
            "qbraid_core.services.environments.schema.package_has_match_on_pypi", return_value=True
        ),
        patch.object(EnvironmentConfig, "to_yaml") as mock_to_yaml,
        patch(
            "qbraid_core.services.environments.create.save_image_from_data_url", return_value=None
        ) as mock_save_image_from_data_url,
    ):
        create_qbraid_env_assets(slug, slug_path, env_config, img_data_url)

        # Verify that update_state_json and create_venv are called with correct arguments
        mock_update_state_json.assert_called_once_with(slug_path, 0, 0)

        # Verify kernel.json creation and contents
        expected_kernel_json_path = os.path.join(
            slug_path, "kernels", f"python3_{slug}", "kernel.json"
        )
        open.assert_any_call(expected_kernel_json_path, "w", encoding="utf-8")
        # Prepare the expected data for kernel.json,
        # modifying argv[0] to match the expected python_exec_path
        expected_kernel_data = kernel_spec_mock["python3"]["spec"]
        if os.name == "nt":
            expected_kernel_data["argv"][0] = os.path.join(
                slug_path, "pyenv", "Scripts", "python.exe"
            )
        else:
            expected_kernel_data["argv"][0] = os.path.join(slug_path, "pyenv", "bin", "python")
        expected_kernel_data["display_name"] = env_config.kernel_name

        # Assert json.dump was called with the expected kernel data
        json.dump.assert_called_with(  # pylint: disable=no-member
            expected_kernel_data, mock.ANY, indent=4
        )  # mock.ANY is used because we don't have the file object directly

        if img_data_url:
            # Verify saving of the logo file
            mock_save_image_from_data_url.assert_called_with(
                img_data_url,
                os.path.join(slug_path, "kernels", f"python3_{slug}", "logo-64x64.png"),
            )
        else:
            # Verify copying of logo files
            sys_resource_dir = kernel_spec_mock["python3"]["resource_dir"]
            for file_name in ["logo-32x32.png", "logo-64x64.png", "logo-svg.svg"]:
                sys_path = os.path.join(sys_resource_dir, file_name)
                loc_path = os.path.join(slug_path, "kernels", f"python3_{slug}", file_name)
                shutil.copy.assert_any_call(sys_path, loc_path)  # pylint: disable=no-member

        # Assert that to_yaml was called with the expected yaml path
        mock_to_yaml.assert_called_with(os.path.join(slug_path, "qbraid.yaml"))
