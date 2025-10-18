# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

"""
Unit tests for functions that validate environment metadata.

"""
import os

import pytest

from qbraid_core.services.environments.validate import is_valid_env_name, is_valid_slug

skip_remote_tests: bool = os.getenv("QBRAID_RUN_REMOTE_TESTS", "False").lower() != "true"
REASON = "QBRAID_RUN_REMOTE_TESTS not set (requires configuration of qBraid storage)"


@pytest.mark.parametrize(
    "env_name, expected",
    [
        # Valid names
        ("valid_env", True),
        ("env123", True),
        ("_env", True),
        # Invalid names due to invalid characters
        ("env*name", False),
        ("<env>", False),
        ("env|name", False),
        # Reserved names
        ("CON", False),
        ("com1", False),
        # Names that are too long
        ("a" * 21, False),
        # Empty or whitespace names
        ("", False),
        ("   ", False),
        # Python reserved words
        ("False", False),
        ("import", False),
        # Names starting with a number
        ("1env", False),
        ("123", False),
    ],
)
def test_is_valid_env_name(env_name, expected):
    """Test function that verifies valid python venv names."""
    assert is_valid_env_name(env_name) == expected


@pytest.mark.parametrize(
    "slug, expected",
    [
        ("abc_123456", True),  # Valid slug
        ("", False),  # Empty slug
        ("a" * 7 + "_123456", True),  # Valid slug with max name length
        ("a" * 14 + "_123456", False),  # Name part too long
        ("abc_def_123456", True),  # Valid slug with underscores in name
        ("abc-def_123456", False),  # Invalid character '-' in name
        ("ABC_123456", False),  # Capital letters in the name part
        ("abc_12345a", True),  # Alphanumeric part with lowercase letters
        ("abc_12345", False),  # Alphanumeric part too short
        ("abc_!23456", False),  # Invalid character '!' in name
        ("abc_12345G", False),  # Capital letter in the alphanumeric part
        ("123_456789", True),  # Numeric name part
        ("abc123456789", False),  # Missing underscore separator
        ("abc__123456", False),  # Double underscore in name
        ("_123_123456", False),  # Starting with underscore (name part too short)
        ("a" * 7 + "_1a2b3c", True),  # Valid edge case
    ],
)
def test_is_valid_slug(slug, expected):
    """Test the is_valid_slug function."""
    assert is_valid_slug(slug) == expected


@pytest.mark.skipif(skip_remote_tests, reason=REASON)
def test_verified_slugs_are_valid(qbraid_environments):
    """Test that all existing qBraid environment slugs are deemed valid."""
    for env in qbraid_environments:
        slug = env["slug"]
        assert is_valid_slug(slug)
