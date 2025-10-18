# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

# pylint: disable=redefined-outer-name

"""
Unit tests for the load_config function in the configure app.

"""

import configparser
from pathlib import Path
from unittest.mock import patch

import pytest

from qbraid_core.config import ConfigError, load_config, save_config, update_config_option


@pytest.fixture
def config():
    """Return a new ConfigParser instance."""
    config = configparser.ConfigParser()
    config.add_section("test_section")
    return config


def test_update_config_option_new_value(config):
    """Test updating a new value in the configuration."""
    value = "new_value"
    result_config = update_config_option(config, "test_section", "test_option", value)
    assert result_config.get("test_section", "test_option") == value


def test_update_config_option_existing_value(config):
    """Test updating an existing value in the configuration."""
    value = "existing_value"
    config.set("test_section", "test_option", value)
    result_config = update_config_option(config, "test_section", "test_option", value)
    assert result_config.get("test_section", "test_option") == value


def test_update_config_option_none_value(config):
    """Test updating an existing value to None does not modfiy the configuration."""
    initial_value = "initial_value"
    config.set("test_section", "test_option", initial_value)
    result_config = update_config_option(config, "test_section", "test_option", None)
    assert result_config.get("test_section", "test_option") == initial_value


@patch("qbraid_core.config.str", side_effect=TypeError)
def test_update_config_option_invalid_value(config):
    """Test updating a configuration option with an invalid value."""
    with pytest.raises(ValueError):
        update_config_option(config, "test_section", "test_option", 123)


def test_load_config_success():
    """Test loading configuration successfully."""
    with (
        patch.object(Path, "home", return_value=Path("/fake/home")),
        patch.object(configparser.ConfigParser, "read"),
    ):
        config = load_config()
        assert isinstance(config, configparser.ConfigParser), "Config should be loaded successfully"


def test_load_config_file_not_found_error():
    """Test loading configuration when the file is not found."""
    with (
        patch.object(Path, "home", return_value=Path("/fake/home")),
        patch.object(configparser.ConfigParser, "read") as mock_config_parser,
    ):
        mock_config_parser.side_effect = FileNotFoundError("File not found")

        with pytest.raises(ConfigError):
            load_config()


def test_load_config_permission_error():
    """Test loading configuration when there's a permission error."""
    with (
        patch.object(Path, "home", return_value=Path("/fake/home")),
        patch.object(configparser.ConfigParser, "read") as mock_config_parser,
    ):
        mock_config_parser.side_effect = PermissionError("Permission denied")

        with pytest.raises(ConfigError):
            load_config()


def test_load_config_parsing_error():
    """Test loading configuration when there's a parsing error."""
    with (
        patch.object(Path, "home", return_value=Path("/fake/home")),
        patch.object(configparser.ConfigParser, "read") as mock_config_parser,
    ):
        mock_config_parser.side_effect = configparser.Error("Parsing error")

        with pytest.raises(ConfigError):
            load_config()


@pytest.mark.parametrize("section,key,value", [("test", "qbraid", "cli")])
def test_save_config(section, key, value):
    """Test functionality of save configuration"""
    mock_config = configparser.ConfigParser()
    mock_config.add_section(section)
    mock_config.set(section, key, value)

    qbraid_path = Path.home() / ".qbraid"
    qbraidrc_path_tmp = qbraid_path / "qbraidrc.tmp"

    if qbraidrc_path_tmp.exists():
        qbraidrc_path_tmp.unlink()

    try:
        save_config(mock_config, filepath=qbraidrc_path_tmp)

        assert qbraid_path.exists(), "The .qbraid directory was not created."
        assert qbraidrc_path_tmp.exists(), "The qbraidrc file was not created."

        config_read_back = configparser.ConfigParser()
        config_read_back.read(qbraidrc_path_tmp)
        assert config_read_back.get(section, key) == value, "The file content is not as expected."
    finally:
        if qbraidrc_path_tmp.exists():
            qbraidrc_path_tmp.unlink()
