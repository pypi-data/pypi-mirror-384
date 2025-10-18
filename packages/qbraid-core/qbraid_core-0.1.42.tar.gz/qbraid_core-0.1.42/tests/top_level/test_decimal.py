# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

# pylint: disable=missing-class-docstring,too-few-public-methods
"""
Unit tests for custom decimal.Decimal subclasses in qbraid_core.

"""
from decimal import Decimal

from qbraid_core.decimal import USD, Credits


def test_credits_initialization():
    """Test initialization of Credits."""
    c = Credits("1000")
    assert isinstance(c, Decimal)
    assert repr(c) == "Credits('1000')"
    assert str(c) == "1000"
    assert int(c) == 1000
    assert float(c) == 1000.0


def test_usd_initialization():
    """Test initialization of USD."""
    u = USD("10")
    assert isinstance(u, Decimal)
    assert repr(u) == "USD('10')"
    assert str(u) == "10"
    assert int(u) == 10
    assert float(u) == 10.0


def test_credits_to_usd():
    """Test conversion from Credits to USD."""
    qbraid_credits = Credits("1000")
    usd = qbraid_credits.to_usd()
    assert isinstance(usd, USD)
    assert repr(usd) == "USD('10')"


def test_usd_to_credits():
    """Test conversion from USD to Credits."""
    usd = USD("10")
    qbraid_credits = usd.to_credits()
    assert isinstance(qbraid_credits, Credits)
    assert repr(qbraid_credits) == "Credits('1000')"


def test_bidirectional_conversion():
    """Test that converting back and forth maintains value."""
    qbraid_credits = Credits("1000")
    usd = qbraid_credits.to_usd()
    credits_back = usd.to_credits()
    assert qbraid_credits == credits_back


def test_credits_equals_credits_same_value():
    """Test that Credits instances with the same value are equal."""
    c1 = Credits(1000)
    c2 = Credits(1000)
    assert c1 == c2


def test_credits_not_equals_credits_different_value():
    """Test that Credits instances with different values are not equal."""
    c1 = Credits(1000)
    c2 = Credits(2000)
    assert c1 != c2


def test_credits_equals_usd_equivalent_value():
    """Test that Credits equals USD when values are equivalent."""
    c = Credits(500)
    u = USD(5)
    assert c == u


def test_credits_not_equals_usd_non_equivalent_value():
    """Test that Credits does not equal USD when values are not equivalent."""
    c = Credits(500)
    u = USD(10)
    assert c != u


def test_credits_equals_decimal_same_value():
    """Test that Credits equals Decimal with the same value."""
    c = Credits(1000)
    d = Decimal(1000)
    assert c == d


def test_credits_equals_int_same_value():
    """Test that Credits equals int with the same value."""
    c = Credits(1000)
    i = 1000
    assert c == i


def test_credits_equals_float_same_value():
    """Test that Credits equals float with the same value."""
    c = Credits(1000)
    f = 1000.0
    assert c == f


def test_credits_not_equals_string():
    """Test that Credits does not equal a string."""
    c = Credits(1000)
    s = "1000"
    assert c != s


def test_credits_not_equals_none():
    """Test that Credits does not equal None."""
    c = Credits(1000)
    assert c is not None


def test_usd_equals_usd_same_value():
    """Test that USD instances with the same value are equal."""
    u1 = USD(10)
    u2 = USD(10)
    assert u1 == u2


def test_usd_not_equals_usd_different_value():
    """Test that USD instances with different values are not equal."""
    u1 = USD(10)
    u2 = USD(20)
    assert u1 != u2


def test_usd_equals_credits_equivalent_value():
    """Test that USD equals Credits when values are equivalent."""
    u = USD(15)
    c = Credits(1500)
    assert u == c


def test_usd_not_equals_credits_non_equivalent_value():
    """Test that USD does not equal Credits when values are not equivalent."""
    u = USD(15)
    c = Credits(2000)
    assert u != c


def test_usd_equals_decimal_same_value():
    """Test that USD equals Decimal with the same value."""
    u = USD(10)
    d = Decimal("10")
    assert u == d


def test_usd_equals_int_same_value():
    """Test that USD equals int with the same value."""
    u = USD(10)
    i = 10
    assert u == i


def test_usd_equals_float_same_value():
    """Test that USD equals float with the same value."""
    u = USD(10)
    f = 10.0
    assert u == f


def test_usd_not_equals_string():
    """Test that USD does not equal a string."""
    u = USD(10)
    s = "10"
    assert u != s


def test_usd_not_equals_none():
    """Test that USD does not equal None."""
    u = USD(10)
    assert u is not None


def test_credits_equality_with_different_types():
    """Test Credits equality with various types."""
    c = Credits(1000)
    assert c == Credits(1000)
    assert c == 1000
    assert c == 1000.0
    assert c == Decimal(1000)
    assert c != "1000"
    assert c is not None


def test_usd_equality_with_different_types():
    """Test USD equality with various types."""
    u = USD(10.5)
    assert u == USD(10.5)
    assert u == 10.5
    assert u == Decimal("10.5")
    assert u != "10.5"
    assert u is not None


def test_equality_with_unrelated_type():
    """Test equality with an unrelated type returns False."""
    c = Credits(1000)

    class Unrelated:
        pass

    u = Unrelated()
    assert c != u


def test_equality_with_custom_object():
    """Test that comparison with an object that knows how to compare works."""
    c = Credits(1000)

    class CustomComparable:
        def __eq__(self, other):
            return isinstance(other, Credits) and other == 1000

    custom_obj = CustomComparable()
    assert c == custom_obj
    assert custom_obj == c


def test_credits_not_equals_usd_with_different_values():
    """Test Credits not equal to USD when values are close but not equal."""
    c = Credits(1234)
    u = USD(12.33)
    assert c != u


def test_usd_not_equals_credits_with_different_values():
    """Test USD not equal to Credits when values are close but not equal."""
    u = USD(12.34)
    c = Credits(1233)
    assert u != c


def test_usd_equality_with_high_precision():
    """Test USD equality with high precision values."""
    u1 = USD(12.3456)
    u2 = USD(12.3456)
    assert u1 == u2


def test_usd_not_equal_due_to_rounding():
    """Test that USD instances with values differing are not equal."""
    u1 = USD(12.3456)
    u2 = USD(12.3457)
    assert u1 != u2


def test_credits_equality_after_arithmetic_operations():
    """Test Credits equality after arithmetic operations."""
    c1 = Credits(1000)
    c2 = Credits(500) + Credits(500)
    assert c1 == c2


def test_usd_equality_after_arithmetic_operations():
    """Test USD equality after arithmetic operations."""
    u1 = USD(10)
    u2 = USD(5) + USD(5)
    assert u1 == u2


def test_credits_to_usd_conversion_equality():
    """Test that converting Credits to USD and back maintains equality."""
    c = Credits(1500)
    u = c.to_usd()
    c_converted_back = u.to_credits()
    assert c == c_converted_back


def test_usd_to_credits_conversion_equality():
    """Test that converting USD to Credits and back maintains equality."""
    u = USD(15)
    c = u.to_credits()
    u_converted_back = c.to_usd()
    assert u == u_converted_back


def test_credits_comparison_with_non_numeric_type():
    """Test that Credits comparison with a non-numeric, non-related type returns NotImplemented."""
    c = Credits(1000)

    class NonNumeric:
        pass

    nn = NonNumeric()
    assert (c == nn) is False


def test_usd_comparison_with_non_numeric_type():
    """Test that USD comparison with a non-numeric, non-related type returns NotImplemented."""
    u = USD(10)

    class NonNumeric:
        pass

    nn = NonNumeric()
    assert (u == nn) is False
