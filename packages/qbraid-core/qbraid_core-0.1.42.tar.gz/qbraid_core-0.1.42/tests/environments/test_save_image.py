# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

# pylint: disable=redefined-outer-name

"""
Unit tests for functions to save image from data url.

"""
import base64

import pytest

from qbraid_core.services.environments.create import save_image_from_data_url


@pytest.fixture
def image_data() -> bytes:
    """Creates 1x1 pixel image in PNG format and returns as bytes."""
    return (
        b"\x89PNG\r\n\x1a\n"
        b"\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
        b"\x00\x00\x00\nIDATx\xdac`\x00\x00\x00\x02\x00\x01\xe2!\xbc\x33"
        b"\x00\x00\x00\x00IEND\xaeB`\x82"
    )


@pytest.fixture
def data_url(image_data) -> str:
    """Returns bytes image as data URL."""
    return f"data:image/png;base64,{base64.b64encode(image_data).decode('utf-8')}"


def test_save_image_from_data_url(tmp_path, image_data, data_url):
    """Test the save_image_from_data_url function."""
    output_path = tmp_path / "output_image.png"
    save_image_from_data_url(data_url, str(output_path))
    assert output_path.exists()
    with open(output_path, "rb") as file:
        assert file.read() == image_data


def test_save_image_from_data_url_creates_directory(tmp_path, image_data, data_url):
    """Test the save_image_from_data_url function creates the directory if it does not exist."""
    nested_output_path = tmp_path / "nested_dir" / "output_image.png"
    save_image_from_data_url(data_url, str(nested_output_path))
    assert nested_output_path.exists()
    with open(nested_output_path, "rb") as file:
        assert file.read() == image_data


def test_save_image_from_data_url_invalid_data_url():
    """Test the save_image_from_data_url function with an invalid data URL."""
    invalid_data_url = "data:image/png;base64,invalidbase64data"
    with pytest.raises(ValueError) as exc_info:
        save_image_from_data_url(invalid_data_url, "output_image.png")
    assert str(exc_info.value) == "Invalid Data URL"
