# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

"""
Unit tests for lazy and dynamic imports.

"""
import sys
from unittest.mock import patch

import pytest
from urllib3.exceptions import InsecureRequestWarning

from qbraid_core._import import LazyLoader, suppress_warning


def test_lazy_loading():
    """Test that the module is not loaded until an attribute is accessed."""
    # Remove the module from sys.modules if it's already loaded
    if "calendar" in sys.modules:
        del sys.modules["calendar"]

    calendar_loader = LazyLoader("calendar", globals(), "calendar")
    assert "calendar" not in sys.modules, "Module 'calendar' should not be loaded yet"

    # Access an attribute to trigger loading
    _ = calendar_loader.month_name
    assert (
        "calendar" in sys.modules
    ), "Module 'calendar' should be loaded after accessing an attribute"


def test_parent_globals_update():
    """Test that the parent's globals are updated after loading."""
    if "math" in sys.modules:
        del sys.modules["math"]

    math_loader = LazyLoader("math", globals(), "math")
    assert "math" not in globals(), "Global namespace should not initially contain 'math'"

    _ = math_loader.pi
    assert "math" in globals(), "Global namespace should contain 'math' after loading"


def test_attribute_access():
    """Test that attributes of the loaded module can be accessed."""
    math_loader = LazyLoader("math", globals(), "math")
    assert math_loader.pi == pytest.approx(
        3.141592653589793
    ), "Attribute 'pi' should match the math module's 'pi'"


def test_invalid_attribute():
    """Test accessing an invalid attribute."""
    math_loader = LazyLoader("math", globals(), "math")
    with pytest.raises(AttributeError):
        _ = math_loader.invalid_attribute


def test_suppress_warning_success():
    """Test that a warning is suppressed."""
    with patch("warnings.simplefilter") as mock_simplefilter:
        suppress_warning("InsecureRequestWarning", "urllib3.exceptions")
        mock_simplefilter.assert_called_once_with("ignore", InsecureRequestWarning)


def test_suppress_warning_import_error():
    """Test that an ImportError is caught"""
    with patch("warnings.simplefilter") as mock_simplefilter:
        suppress_warning("InsecureRequestWarning", "fake_urllib3.exceptions")
        mock_simplefilter.assert_not_called()


def test_suppress_warning_attribute_error():
    """Test that an AttributeError is caught and logged."""
    with patch("warnings.simplefilter") as mock_simplefilter:
        suppress_warning("FakeInsecureRequestWarning", "urllib3.exceptions")
        mock_simplefilter.assert_not_called()
