# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

"""
Unit tests related to qBraid core functionality and system configurations.

"""
import pytest

from qbraid_core._compat import _warn_new_version

check_version_data = [
    # local, API, warn
    ("0.1.0", "0.1.1", False),
    ("1.0.7", "1.0.8", False),
    ("1.3.2", "2.0.6", True),
    ("0.1.0", "0.3.0", True),
    ("0.2.4.dev1", "0.2.4", False),
    ("0.1.0", "0.1.0.dev0", False),
    ("0.1.6.dev2", "0.1.6.dev5", False),
    ("0.1.6.dev5", "0.1.6.dev2", False),
    ("0.2.0", "0.1.4", False),
]


@pytest.mark.parametrize("test_data", check_version_data)
def test_check_version(test_data):
    """Test function that compares local/api package versions to determine if
    update is needed."""
    local, api, warn_bool = test_data
    assert warn_bool == _warn_new_version(local, api)
