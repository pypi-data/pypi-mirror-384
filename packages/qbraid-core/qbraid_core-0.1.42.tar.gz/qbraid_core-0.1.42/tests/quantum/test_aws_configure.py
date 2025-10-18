# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

"""
Unit tests for braket proxy aws_configure function.

"""

from unittest.mock import patch

from qbraid_core.services.quantum.proxy_braket import aws_configure


def test_aws_directory_and_files_creation():
    """Test create AWS dummy configuration files."""
    with (
        patch("pathlib.Path.mkdir") as mock_mkdir,
        patch("pathlib.Path.exists", side_effect=[False, False]),
        patch("pathlib.Path.write_text") as mock_write_text,
    ):
        aws_configure()
        mock_mkdir.assert_called_once()
        assert mock_write_text.call_count == 2


def test_preservation_of_existing_files():
    """Test if the correct placeholder values are written to the files when they are created."""
    with (
        patch("pathlib.Path.exists", side_effect=[True, True]),
        patch("pathlib.Path.write_text") as mock_write_text,
    ):
        aws_configure()
        mock_write_text.assert_not_called()


def test_correct_content_in_files():
    """Test if the correct placeholder values are written to the files when they are created."""
    expected_config_content = "[default]\nregion = us-east-1\noutput = json\n"
    expected_credentials_content = (
        "[default]\naws_access_key_id = MYACCESSKEY\naws_secret_access_key = MYSECRETKEY\n"
    )

    with (
        patch("pathlib.Path.exists", side_effect=[False, False]),
        patch("pathlib.Path.write_text") as mock_write_text,
    ):
        aws_configure(aws_access_key_id="MYACCESSKEY", aws_secret_access_key="MYSECRETKEY")
        mock_write_text.assert_any_call(expected_config_content)
        mock_write_text.assert_any_call(expected_credentials_content)
