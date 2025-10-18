# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

"""
Unit tests for the replace_str function in the envs app.

"""
import datetime
import sys
from unittest.mock import patch

from qbraid_core.system.generic import get_current_utc_datetime_as_string, replace_str


def test_replace_str(tmp_path):
    """Test replacing a string in a file."""
    file_path = tmp_path / "test_file.txt"
    initial_content = "Hello world! Hello everyone!"
    target = "Hello"
    replacement = "Hi"
    file_path.write_text(initial_content, encoding="utf-8")

    replace_str(target, replacement, str(file_path))

    # Verify that the content has been correctly replaced
    updated_content = file_path.read_text(encoding="utf-8")
    expected_content = initial_content.replace(target, replacement)
    assert updated_content == expected_content, "The file's content was not updated as expected."


@patch("datetime.datetime")
def test_get_current_utc_datetime_as_string(mock_datetime):
    """Test getting the current UTC datetime as a string."""
    mock_current_datetime = "2025-05-28T12:34:56Z"

    if sys.version_info >= (3, 11):
        mock_datetime.now.return_value.strftime.return_value = mock_current_datetime
    else:
        mock_datetime.utcnow.return_value.strftime.return_value = mock_current_datetime

    result = get_current_utc_datetime_as_string()

    if sys.version_info >= (3, 11):
        mock_datetime.now.assert_called_once_with(datetime.timezone.utc)
        mock_datetime.utcnow.assert_not_called()
    else:
        mock_datetime.utcnow.assert_called_once()
        mock_datetime.now.assert_not_called()

    assert (
        result == mock_current_datetime
    ), "Failed: The datetime string does not match the expected format."
