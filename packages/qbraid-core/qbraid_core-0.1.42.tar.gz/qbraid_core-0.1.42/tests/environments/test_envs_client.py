# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

"""
Unit tests for the EnvironmentManagerClient class.

"""
# pylint: disable=duplicate-code

import pathlib
from unittest.mock import MagicMock, mock_open, patch

import pytest

from qbraid_core.exceptions import RequestsApiError
from qbraid_core.services.environments.client import EnvironmentManagerClient
from qbraid_core.services.environments.exceptions import EnvironmentServiceRequestError
from qbraid_core.services.environments.schema import EnvironmentConfig


@pytest.fixture
def mock_qbraid_session():
    """A fixture to mock qBraid session."""
    with patch("qbraid_core.session.QbraidSession", autospec=True) as mock:
        # Mock the necessary session methods here, e.g., get_user
        mock.return_value.get_user.return_value = {
            "personalInformation": {"organization": "qbraid", "role": "guest"}
        }
        yield mock


def test_create_environment_success_required_params():
    """Test successful environment creation."""
    client = EnvironmentManagerClient()
    environment_name = "TestEnv"

    with (
        patch("qbraid_core.services.environments.is_valid_env_name", return_value=True),
        patch.object(client.session, "post") as mock_post,
    ):
        mock_post.return_value.json.return_value = {
            "slug": "test-env-slug",
            "name": environment_name,
        }
        config = EnvironmentConfig(name=environment_name)
        result = client.create_environment(config)

        mock_post.assert_called_once()
        assert result["name"] == environment_name


def test_create_environment_success_with_optional_params():
    """Test successful environment creation with optional parameters."""
    client = EnvironmentManagerClient()
    environment_name = "TestEnv"
    environment_description = "A test environment."
    tags = ["tag1", "tag2"]
    python_packages = {"numpy": "1.21.1", "scipy": ">=1.7.1"}
    kernel_name = "python3"
    shell_prompt = "test_prompt"
    icon_path = pathlib.Path("tests/environments/fixtures/icon.png")

    with (
        patch(
            "qbraid_core.services.environments.client.QbraidClient.running_in_lab",
            return_value=False,
        ),
        patch(
            "qbraid_core.services.environments.client.get_python_executables",
            return_value={
                "system": {"3.8.0": "path/to/env"},
                "conda": {"3.8.0": "path/to/env", "3.9.0": "path/to/env"},
            },
        ),
        patch(
            "qbraid_core.services.environments.schema.package_has_match_on_pypi",
            return_value=True,
        ),
        patch("qbraid_core.services.environments.is_valid_env_name", return_value=True),
        patch.object(client.session, "post") as mock_post,
        patch("builtins.open", mock_open(read_data="fake image data")) as mock_file,
    ):
        mock_post.return_value.json.return_value = {
            "slug": "test-env-slug",
            "name": environment_name,
            "description": environment_description,
        }
        env_config = EnvironmentConfig(
            name=environment_name,
            description=environment_description,
            tags=tags,
            icon=icon_path,
            python_version="3.8.0",
            kernel_name=kernel_name,
            shell_prompt=shell_prompt,
            python_packages=python_packages,
        )
        result = client.create_environment(env_config)

        mock_post.assert_called_once()
        mock_file.assert_any_call(icon_path, "rb")
        assert result["name"] == environment_name
        assert result["description"] == environment_description


def test_create_environment_invalid_name():
    """Test environment creation with an invalid name."""
    client = EnvironmentManagerClient()
    invalid_environment_name = "Invalid Name"

    with patch("qbraid_core.services.environments.is_valid_env_name", return_value=False):
        with pytest.raises(ValueError) as exc_info:
            client.create_environment(EnvironmentConfig(name=invalid_environment_name))

        assert "Invalid environment name" in str(exc_info.value)


def test_create_environment_description_too_long():
    """Test environment creation with a too long description."""
    client = EnvironmentManagerClient()
    environment_name = "ValidName"
    long_description = "x" * 301  # 301 characters long

    with patch("qbraid_core.services.environments.is_valid_env_name", return_value=True):
        with pytest.raises(ValueError) as exc_info:
            config = EnvironmentConfig(name=environment_name, description=long_description)
            client.create_environment(config)

        assert "Description is too long" in str(exc_info.value)


def test_create_environment_api_failure():
    """Test API failure during environment creation."""
    client = EnvironmentManagerClient()
    environment_name = "ValidName"

    with (
        patch("qbraid_core.services.environments.is_valid_env_name", return_value=True),
        patch.object(client.session, "post", side_effect=RequestsApiError),
    ):
        with pytest.raises(EnvironmentServiceRequestError) as exc_info:
            client.create_environment(EnvironmentConfig(name=environment_name))

        assert "Create environment request failed" in str(exc_info.value)


def test_create_environment_invalid_api_response():
    """Test invalid or incomplete data returned by the API."""
    client = EnvironmentManagerClient()
    environment_name = "ValidName"

    with (
        patch("qbraid_core.services.environments.is_valid_env_name", return_value=True),
        patch.object(client.session, "post") as mock_post,
    ):
        mock_post.return_value.json.return_value = {}  # Empty response

        with pytest.raises(EnvironmentServiceRequestError) as exc_info:
            client.create_environment(EnvironmentConfig(name=environment_name))

        assert "invalid environment data" in str(exc_info.value)


def test_delete_environment_with_valid_session():
    """Test deleting an environment with a valid session."""
    with patch("requests.Session.delete") as mock_delete:
        # Assuming delete_environment method successfully calls the session's delete method
        mock_delete.return_value = MagicMock(status_code=204)  # Simulate successful deletion

        client = EnvironmentManagerClient()  # Initializes with a valid mocked QbraidSession
        slug = "valid_slug12"
        client.delete_environment(slug)  # Attempt to delete an environment

        mock_delete.assert_called_once_with(f"/environments/{slug}")


def test_invalid_py_version_provided_in_lab():
    """Test that an invalid Python version is caught in the client."""
    with (
        patch(
            "qbraid_core.services.environments.client.QbraidClient.running_in_lab",
            return_value=True,
        ),
        patch(
            "qbraid_core.services.environments.client.get_python_executables",
            return_value={
                "system": {"3.8.0": "path/to/env"},
                "conda": {"3.8.0": "path/to/env", "3.9.0": "path/to/env"},
            },
        ),
        patch(
            "qbraid_core.services.environments.schema.package_has_match_on_pypi",
            return_value=True,
        ),
    ):
        with pytest.raises(
            ValueError,
            match="Python version '3.11.6' not found in system or conda python installations",
        ):
            config = EnvironmentConfig.from_yaml(
                pathlib.Path(__file__).resolve().parent / "fixtures/correct-icon-relative.yaml"
            )
            client = EnvironmentManagerClient()
            client.create_environment(config)


def test_delete_environment_request_failure():
    """Test environment deletion handling when the delete request fails."""
    slug = "valid_slug12"
    with patch("requests.Session.delete") as mock_delete:
        mock_delete.side_effect = RequestsApiError("API request failed")

        client = EnvironmentManagerClient()  # Initializes with a valid mocked QbraidSession
        with pytest.raises(EnvironmentServiceRequestError):
            client.delete_environment(slug)

        mock_delete.assert_called_once_with(f"/environments/{slug}")


def test_remote_publish_environment_success():
    """Test successful remote publish of an environment."""
    client = EnvironmentManagerClient()
    config = EnvironmentConfig(
        name="TestEnv", icon=pathlib.Path("tests/environments/fixtures/icon.png")
    )

    with (
        patch.object(client.session, "post") as mock_post,
        patch("builtins.open", mock_open(read_data="fake image data")) as _,
    ):
        mock_post.return_value.json.return_value = {
            "envSlug": "test-env-slug",
            "message": "Remote environment publish scheduled successfully!",
        }
        result = client.remote_publish_environment(config=config)

        mock_post.assert_called_once()
        assert result["envSlug"] == "test-env-slug"


def test_remote_publish_environment_failure():
    """Test unsuccessful remote publish of an environment."""
    client = EnvironmentManagerClient()
    config = EnvironmentConfig(
        name="TestEnv", icon=pathlib.Path("tests/environments/fixtures/icon.png")
    )

    with (
        patch.object(client.session, "post") as mock_post,
        patch("builtins.open", mock_open(read_data="fake image data")) as _,
    ):
        with pytest.raises(EnvironmentServiceRequestError) as exc_info:
            mock_post.return_value.json.return_value = {"message": "error msg"}
            result = client.remote_publish_environment(config=config)
            assert result["message"] == "error msg"

        assert "Remote publish environment request responded with invalid data" in str(
            exc_info.value
        )


def test_remote_publish_environment_missing_config_and_file():
    """Test remote publish with missing config and file path."""
    client = EnvironmentManagerClient()

    with pytest.raises(ValueError) as exc_info:
        client.remote_publish_environment()

    assert "Either YAML file or config data must be provided for env creation" in str(
        exc_info.value
    )


def test_remote_publish_both_config_and_file():
    """Test remote publish with both config and file path provided raises error."""
    client = EnvironmentManagerClient()
    config = EnvironmentConfig(name="TestEnv")

    with pytest.raises(ValueError) as exc_info:
        client.remote_publish_environment(
            config=config, file_path=pathlib.Path("tests/environments/fixtures/correct.yaml")
        )

    assert "Only one of YAML file or config data can be provided for env creation" in str(
        exc_info.value
    )


def test_remote_publish_environment_icon_not_found():
    """Test remote publish with icon file not found."""
    client = EnvironmentManagerClient()

    with pytest.raises(ValueError) as exc_info:
        client.remote_publish_environment(
            file_path="tests/environments/fixtures/invalid_icon_path.yaml"
        )

    assert "Icon file not found at path: random_path.xyz" in str(exc_info.value)


def test_remote_publish_environment_api_failure():
    """Test API failure during remote publish."""
    client = EnvironmentManagerClient()
    config = EnvironmentConfig(
        name="TestEnv", icon=pathlib.Path("tests/environments/fixtures/icon.png")
    )

    with (
        patch.object(client.session, "post", side_effect=RequestsApiError),
        patch("builtins.open", mock_open(read_data="fake image data")) as _,
    ):
        with pytest.raises(EnvironmentServiceRequestError) as exc_info:
            client.remote_publish_environment(config=config)

        assert "Remote publish environment request failed" in str(exc_info.value)


def test_retrieve_remote_publish_status_success():
    """Test successful retrieval of remote publish status."""
    client = EnvironmentManagerClient()
    env_slug = "test-env-slug"

    with patch.object(client.session, "get") as mock_get:
        mock_get.return_value.json.return_value = {
            "status": "COMPLETE",
            "message": "Environment status retrieved successfully",
        }
        status = client.retrieve_remote_publish_status(env_slug)

        mock_get.assert_called_once_with(
            "/environments/remote/publish/status", params={"envSlug": env_slug}
        )
        assert status == "COMPLETE"


def test_retrieve_remote_publish_status_missing_env_slug():
    """Test retrieval of remote publish status with missing envSlug."""
    client = EnvironmentManagerClient()

    with patch.object(client.session, "get") as mock_get:
        mock_get.return_value.json.return_value = {"message": "envSlug is required"}
        with pytest.raises(EnvironmentServiceRequestError) as exc_info:
            client.retrieve_remote_publish_status("")

        assert "Request failed to retrieve remote publish status" in str(exc_info.value)


def test_retrieve_remote_publish_status_env_not_found():
    """Test retrieval of remote publish status with environment not found."""
    client = EnvironmentManagerClient()
    env_slug = "nonexistent-env-slug"

    with patch.object(client.session, "get") as mock_get:
        mock_get.return_value.json.return_value = {"message": f"Environment '{env_slug}' not found"}
        with pytest.raises(EnvironmentServiceRequestError) as exc_info:
            client.retrieve_remote_publish_status(env_slug)

        assert "Request failed to retrieve remote publish status" in str(exc_info.value)


def test_retrieve_remote_publish_status_status_not_found():
    """Test retrieval of remote publish status with status not found."""
    client = EnvironmentManagerClient()
    env_slug = "test-env-slug"

    with patch.object(client.session, "get") as mock_get:
        mock_get.return_value.json.return_value = {
            "message": "Status not found, ensure that remote env creation was triggered"
        }
        with pytest.raises(EnvironmentServiceRequestError) as exc_info:
            client.retrieve_remote_publish_status(env_slug)

        assert "Request failed to retrieve remote publish status" in str(exc_info.value)


def test_retrieve_remote_publish_status_api_failure():
    """Test API failure during retrieval of remote publish status."""
    client = EnvironmentManagerClient()
    env_slug = "test-env-slug"

    with patch.object(client.session, "get", side_effect=RequestsApiError):
        with pytest.raises(EnvironmentServiceRequestError) as exc_info:
            client.retrieve_remote_publish_status(env_slug)

        assert "Request failed to retrieve remote publish status" in str(exc_info.value)


def test_wait_for_env_remote_publish_success():
    """Test successful monitoring of remote publish status."""
    client = EnvironmentManagerClient()
    env_slug = "test-env-slug"

    with (
        patch.object(
            client, "retrieve_remote_publish_status", side_effect=["PENDING", "RUNNING", "COMPLETE"]
        ),
        patch("time.sleep", return_value=None),  # Mock time.sleep to avoid waiting
    ):
        result = client.wait_for_env_remote_publish(env_slug)

        assert result is True


def test_wait_for_env_remote_publish_failed():
    """Test failed remote env publish status."""
    client = EnvironmentManagerClient()
    env_slug = "test-env-slug"

    with (
        patch.object(
            client,
            "retrieve_remote_publish_status",
            side_effect=["PENDING", "RUNNING", "RUNNING", "FAILED"],
        ),
        patch("time.sleep", return_value=None),  # Mock time.sleep to avoid waiting
    ):
        result = client.wait_for_env_remote_publish(env_slug)

        assert result is False


def test_wait_for_env_remote_publish_timeout():
    """Test timeout in monitoring remote publish status."""
    client = EnvironmentManagerClient()
    env_slug = "test-env-slug"

    with (
        patch.object(
            client,
            "retrieve_remote_publish_status",
            side_effect=["PENDING", "RUNNING", "RUNNING", "RUNNING", "RUNNING"],
        ),
        patch("time.sleep", return_value=None),  # Mock time.sleep to avoid waiting
    ):
        with pytest.raises(TimeoutError):
            _ = client.wait_for_env_remote_publish(env_slug, timeout=70, poll_interval=20)
