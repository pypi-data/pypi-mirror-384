# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

# pylint: disable=redefined-outer-name

"""
Unit tests for FileStorageClient class.

"""
import os
from pathlib import Path
from unittest.mock import Mock, mock_open, patch

import pytest

from qbraid_core.exceptions import RequestsApiError
from qbraid_core.services.storage.client import FileStorageClient
from qbraid_core.services.storage.exceptions import FileStorageServiceRequestError


@pytest.fixture
def file_storage_client():
    """Return a FileStorageClient instance."""
    return FileStorageClient()


def test_default_namespace(file_storage_client):
    """Test the default namespace."""
    assert file_storage_client.default_namespace == "user"


def test_set_default_namespace(file_storage_client):
    """Test setting the default namespace."""
    file_storage_client.set_default_namespace("test_namespace")
    assert file_storage_client.default_namespace == "test_namespace"


@pytest.mark.parametrize(
    "file_exists,is_file,expected_exception",
    [
        (False, True, FileNotFoundError),
        (True, False, ValueError),
    ],
)
def test_upload_file_checks(file_storage_client, file_exists, is_file, expected_exception):
    """Test file checks before upload."""
    with (
        patch("pathlib.Path.exists", return_value=file_exists),
        patch("pathlib.Path.is_file", return_value=is_file),
    ):
        if expected_exception:
            with pytest.raises(expected_exception):
                file_storage_client.upload_file("test_file.txt")
        else:
            with (
                patch("builtins.open", mock_open(read_data=b"test data")),
                patch.object(file_storage_client.session, "post") as mock_post,
            ):
                mock_post.return_value.json.return_value = {"status": "success"}
                result = file_storage_client.upload_file("test_file.txt")
                assert result == {"status": "success"}


def test_upload_file_extension_mismatch(file_storage_client):
    """Test file extension mismatch."""
    with (
        patch("pathlib.Path.exists", return_value=True),
        patch("pathlib.Path.is_file", return_value=True),
    ):
        with pytest.raises(ValueError, match="File extension mismatch"):
            file_storage_client.upload_file("test_file.txt", object_path="test_file.jpg")


def test_encode_to_base64():
    """Test encoding to base64."""
    assert FileStorageClient._encode_to_base64("test") == "dGVzdA=="


@pytest.fixture
def mock_file_storage_client():
    """Return a FileStorageClient instance with a mocked session."""
    client = FileStorageClient()
    client._session = Mock()
    return client


def test_download_success(mock_file_storage_client):
    """Test successful download."""
    mock_response = Mock()
    mock_response.headers = {"Content-Disposition": 'filename="test_file.txt"'}
    mock_response.iter_content.return_value = [b"test data"]
    mock_file_storage_client.session.get.return_value = mock_response

    with (
        patch("pathlib.Path.exists", return_value=False),
        patch("builtins.open", mock_open()) as mocked_file,
    ):
        mock_file_storage_client.download_file("test_file.txt")
        mocked_file().write.assert_called_once_with(b"test data")


def test_download_file_exists_no_overwrite(mock_file_storage_client):
    """Test download when file exists and overwrite is False."""
    mock_response = Mock()
    mock_response.headers = {"Content-Disposition": 'filename="test_file.txt"'}
    mock_file_storage_client.session.get.return_value = mock_response

    with patch("pathlib.Path.exists", return_value=True):
        with pytest.raises(FileExistsError):
            mock_file_storage_client.download_file("test_file.txt", overwrite=False)


def test_download_file_exists_with_overwrite(mock_file_storage_client):
    """Test download when file exists and overwrite is True."""
    mock_response = Mock()
    mock_response.headers = {"Content-Disposition": 'filename="test_file.txt"'}
    mock_response.iter_content.return_value = [b"test data"]
    mock_file_storage_client.session.get.return_value = mock_response

    with (
        patch("os.path.exists", return_value=True),
        patch("builtins.open", mock_open()) as mocked_file,
    ):
        mock_file_storage_client.download_file("test_file.txt", overwrite=True)
        mocked_file().write.assert_called_once_with(b"test data")


def test_download_api_error(mock_file_storage_client):
    """Test download when an API error occurs."""
    mock_file_storage_client.session.get.side_effect = RequestsApiError("API error")

    with pytest.raises(FileStorageServiceRequestError, match="Failed to download file:"):
        mock_file_storage_client.download_file("test_file.txt")


def test_download_custom_save_path(mock_file_storage_client):
    """Test download with a custom save path."""
    mock_response = Mock()
    mock_response.headers = {"Content-Disposition": 'filename="test_file.txt"'}
    mock_response.iter_content.return_value = [b"test data"]
    mock_file_storage_client.session.get.return_value = mock_response

    custom_path = os.path.join("custom", "path")
    expected_file_path = str(Path(os.path.join(custom_path, "test_file.txt")).resolve())

    with (
        patch("pathlib.Path.exists", return_value=False),
        patch("builtins.open", mock_open()) as mocked_file,
    ):
        mock_file_storage_client.download_file("test_file.txt", save_path=custom_path)
        mocked_file.assert_called_once_with(expected_file_path, "wb")
        mocked_file().write.assert_called_once_with(b"test data")
