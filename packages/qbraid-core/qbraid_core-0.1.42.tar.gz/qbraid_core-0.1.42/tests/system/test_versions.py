# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

"""
Unit tests for qBraid core helper functions related to package versions.

"""
import sys
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

from qbraid_core.exceptions import QbraidChainedException, QbraidException
from qbraid_core.system.exceptions import InvalidVersionError, VersionNotFoundError
from qbraid_core.system.versions import (
    _simple_toml_version_extractor,
    bump_version,
    compare_versions,
    extract_version,
    find_largest_version,
    get_bumped_version,
    get_latest_package_version,
    get_local_package_version,
    get_prelease_version,
    is_valid_semantic_version,
    package_has_match_on_pypi,
    update_version_in_pyproject,
)

try:
    if sys.version_info >= (3, 11):
        import tomllib  # pylint: disable=unused-import # noqa: F401
    else:
        import toml  # pylint: disable=unused-import # noqa: F401
    TOML_AVAILABLE = True
except ImportError:
    TOML_AVAILABLE = False


@pytest.mark.parametrize(
    "version_str, expected",
    [
        ("1.0.0", True),
        ("0.1.2", True),
        ("2.0.0-rc.1", True),
        ("1.0.0-alpha+001", True),
        ("1.2.3+meta-valid", True),
        ("+invalid", False),  # no major, minor or patch version
        ("-invalid", False),  # no major, minor or patch version
        ("1.0.0-", False),  # pre-release info cannot be empty if hyphen is present
        ("1.0.0+", False),  # build metadata cannot be empty if plus is present
        ("1.0.0+meta/valid", False),  # build metadata contains invalid characters
        ("1.0.0-alpha", True),
        ("1.1.2+meta-123", True),
        ("1.1.2+meta.123", True),
    ],
)
def test_is_valid_semantic_version(version_str, expected):
    """Test the is_valid_semantic_version function correctly parses version."""
    assert is_valid_semantic_version(version_str) == expected


def test_extract_version_from_package_json():
    """Test the extract_version function correctly extracts version from package.json."""
    mock_file_content = '{"version": "1.0.0-alpha.1"}'
    with patch("builtins.open", mock_open(read_data=mock_file_content)):
        with patch("json.load", return_value={"version": "1.0.0-alpha.1"}):
            assert extract_version("package.json", shorten_prerelease=True) == "1.0.0a1"


@pytest.mark.skipif(not TOML_AVAILABLE, reason="Requires the toml or tomllib package")
def test_extract_version_from_pyproject_toml():
    """Test the extract_version function correctly extracts version from pyproject.toml."""
    mock_file_content = 'project = { version = "1.0.0-beta.2" }'
    with patch("builtins.open", mock_open(read_data=mock_file_content)):
        with patch("tomllib.load", return_value={"project": {"version": "1.0.0-beta.2"}}):
            assert extract_version("pyproject.toml") == "1.0.0-beta.2"


def test_unsupported_file_type():
    """Test the extract_version function raises ValueError for unsupported file type."""
    with pytest.raises(ValueError, match="Unsupported file type"):
        extract_version("setup.cfg")


def test_file_not_found_error():
    """Test the extract_version function raises VersionNotFoundError when file is not found."""
    with patch("builtins.open", side_effect=FileNotFoundError):
        with pytest.raises(VersionNotFoundError, match="Unable to find or read"):
            extract_version("nonexistent.json")


def test_missing_version_key_error():
    """Test the extract_version function raises VersionNotFoundError when
    version key is missing."""
    with patch("builtins.open", mock_open(read_data="{}")):
        with patch("json.load", return_value={}):
            with pytest.raises(VersionNotFoundError, match="Unable to find or read"):
                extract_version("package.json")


def test_io_error_on_file_read():
    """Test the extract_version function raises VersionNotFoundError when file cannot be read."""
    with patch("builtins.open", side_effect=IOError):
        with pytest.raises(VersionNotFoundError, match="Unable to find or read"):
            extract_version("package.json")


@pytest.mark.skipif(not TOML_AVAILABLE, reason="Requires the toml or tomllib package")
def test_invalid_version_error():
    """Test the extract_version function raises InvalidVersionError for invalid semantic version."""
    mock_file_content = 'project = { version = "helloWorld" }'
    with patch("builtins.open", mock_open(read_data=mock_file_content)):
        with patch("tomllib.load", return_value={"project": {"version": "helloWorld"}}):
            with pytest.raises(InvalidVersionError, match="Invalid semantic version"):
                extract_version("pyproject.toml", check=True)


def test_simple_toml_version_extractor_success():
    """Test the _simple_toml_version_extractor function successfully extracts version."""
    mock_toml_content = '[project]\nversion = "1.2.3"\n'
    with patch("builtins.open", mock_open(read_data=mock_toml_content)):
        version = _simple_toml_version_extractor("pyproject.toml")
        assert version == "1.2.3", "The version should be extracted successfully."


def test_simple_toml_version_extractor_no_version_key():
    """Test the _simple_toml_version_extractor function raises ValueError
    when version key is not found."""
    mock_toml_content = '[project]\nname = "example"\n'
    with patch("builtins.open", mock_open(read_data=mock_toml_content)):
        with pytest.raises(ValueError, match="Version key not found in the TOML content."):
            _simple_toml_version_extractor("pyproject.toml")


def test_simple_toml_version_extractor_file_not_found():
    """Test the _simple_toml_version_extractor function raises VersionNotFoundError
    when file is not found."""
    with patch("builtins.open", side_effect=FileNotFoundError):
        with pytest.raises(VersionNotFoundError, match="The specified TOML file does not exist."):
            _simple_toml_version_extractor("pyproject.toml")


def test_simple_toml_version_extractor_io_error():
    """Test the _simple_toml_version_extractor function raises VersionNotFoundError
    when file cannot be read."""
    with patch("builtins.open", side_effect=IOError):
        with pytest.raises(
            VersionNotFoundError, match="An error occurred while reading the TOML file."
        ):
            _simple_toml_version_extractor("pyproject.toml")


def test_get_latest_version_raises():
    """Test the _get_latest_version function when an error occurs."""
    with pytest.raises(VersionNotFoundError):
        get_latest_package_version("nonexistent_package")


@pytest.mark.parametrize(
    "package,python_path", [("not_a_package", None), ("not_a_package", sys.executable)]
)
def test_get_local_version_raises_for_bad_package(package, python_path):
    """Test the _get_local_version function when an error occurs."""
    with pytest.raises(QbraidException) as exc_info:
        get_local_package_version(package, python_path=python_path)
    assert f"{package} not found in the current environment." in str(exc_info)


def test_get_local_version_raises_for_():
    """Test the _get_local_version function when an error occurs."""
    package = "pytest"  # valid package guaranteed to be installed
    python_path = "/bad/python/path"  # invalid python path
    with pytest.raises(QbraidException) as exc_info:
        get_local_package_version(package, python_path=python_path)
    assert f"Python executable not found at {python_path}." in str(exc_info)


@pytest.mark.parametrize("python_path", [None, Path(sys.executable), sys.executable])
def test_get_local_package_version_alt_python(python_path):
    """Test the get_latest_package_version function with an alternative Python path."""
    python_path = Path(sys.executable)
    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(stdout="2.31.0\n")
        assert get_local_package_version("requests", python_path=python_path) == "2.31.0"


def test_bump_local_version_greater():
    """Test that a local version greater than latest bumps to new pre-release."""
    assert get_bumped_version("1.0.0", "1.1.0") == "1.1.0-a.0"


def test_bump_higher_prerelease_number():
    """Test that a higher local prerelease version raises an error."""
    with pytest.raises(InvalidVersionError):
        get_bumped_version("1.0.0-a.1", "1.0.0-a.2")


def test_bump_different_prerelease_types():
    """Test bumping when prerelease types differ, expecting incremented higher type."""
    assert get_bumped_version("1.0.0-a.1", "1.0.0-b.0") == "1.0.0-b.0"


def test_bump_latest_prerelease_local_not():
    """Test error when the latest is prerelease but local is not."""
    with pytest.raises(InvalidVersionError):
        get_bumped_version("1.0.0-a.1", "1.0.0")


def test_bump_local_is_prerelease_no_latest_prerelease():
    """Test bumping when local is prerelease but latest is not, should start a new prerelease."""
    assert get_bumped_version("1.0.0", "1.0.0-a.1") == "1.0.0-a.0"


def test_bump_same_version_without_prerelease():
    """Test bumping when both versions are the same and without prerelease,
    starting a new prerelease."""
    assert get_bumped_version("1.0.0", "1.0.0") == "1.0.0-a.0"


def test_bump_latest_version_greater_base_error():
    """Test error when the latest base version is greater than the local version."""
    with pytest.raises(InvalidVersionError):
        get_bumped_version("1.1.0", "1.0.0")


def test_bump_prerelease_when_local_equals_latest():
    """Test bumping prerelease correctly when both local and latest versions are the same."""
    assert get_bumped_version("1.0.0-a.1", "1.0.0-a.1") == "1.0.0-a.2"


def test_bump_prerelease_with_local_type_less_than_latest():
    """Test correct bumping of prerelease when local type is less significant than latest."""
    assert get_bumped_version("1.0.0-b.1", "1.0.0-a.1") == "1.0.0-b.2"


@pytest.mark.parametrize(
    "version1, version2, expected",
    [
        (None, None, ValueError),
        (None, "1.2.3", "1.2.3"),
        ("1.2.3", None, "1.2.3"),
        ("2.0.0", "1.0.0", "2.0.0"),
        ("1.0.0", "2.0.0", "2.0.0"),
        ("1.0.0", "1.0.0", "1.0.0"),
        ("1.0.0-alpha", "1.0.0-beta", "1.0.0-beta"),
    ],
)
def test_compare_versions(version1, version2, expected):
    """Test cases for comparing semantic version strings."""
    if expected is ValueError:
        with pytest.raises(ValueError):
            compare_versions(version1, version2)
    else:
        assert compare_versions(version1, version2) == expected


@patch("qbraid_core.system.versions.extract_version")
@patch("qbraid_core.system.versions.get_latest_package_version")
@patch("qbraid_core.system.versions.compare_versions")
@patch("qbraid_core.system.versions.get_bumped_version")
def test_get_prerelease_version_success(
    mock_get_bumped_version,
    mock_compare_versions,
    mock_get_latest_package_version,
    mock_extract_version,
):
    """
    Test get_prerelease_version with successful extraction.
    """
    mock_extract_version.return_value = "1.2.3"
    mock_get_latest_package_version.side_effect = ["1.2.3-beta", "1.2.3"]
    mock_compare_versions.return_value = "1.2.3"
    mock_get_bumped_version.return_value = "1.2.3-beta.1"

    package_name = "qbraid_core"
    project_root = Path(__file__).parent.parent.parent.resolve()
    assert get_prelease_version(project_root, package_name) == "1.2.3-beta.1"


def test_get_prerelease_version_missing_pyproject_toml():
    """
    Test get_prerelease_version when pyproject.toml is missing.
    """
    with patch("qbraid_core.system.versions.pathlib.Path.exists", return_value=False):
        project_root = "/path/to/missing"
        package_name = "missing_package"
        with pytest.raises(FileNotFoundError):
            get_prelease_version(project_root, package_name)


def test_get_prerelease_version_invalid_shorten_argument():
    """
    Test get_prerelease_version with invalid shorten argument.
    """
    package_name = "qbraid_core"
    project_root = Path(__file__).parent.parent.parent.resolve()
    with pytest.raises(TypeError):
        get_prelease_version(project_root, package_name, shorten="invalid")


def test_get_prelease_version_success_package_json():
    """
    Test get_prelease_version successfully extracts the version from `package.json`.
    """
    project_root = Path("/fake/path")
    package_name = "testpackage"
    expected_version = "1.0.1-pre"

    with patch("pathlib.Path.exists", MagicMock(side_effect=[True, False])):
        with patch("qbraid_core.system.versions.extract_version", return_value="1.0.0"):
            with patch(
                "qbraid_core.system.versions.get_latest_package_version", return_value="1.0.1"
            ):
                with patch("qbraid_core.system.versions.compare_versions", return_value="1.0.1"):
                    with patch(
                        "qbraid_core.system.versions.get_bumped_version",
                        return_value=expected_version,
                    ):
                        result = get_prelease_version(project_root, package_name)
                        assert result == expected_version


def test_get_prelease_version_fallback_to_pyproject():
    """
    Test get_prelease_version fallbacks to `pyproject.toml` when `package.json` fails.
    """
    project_root = Path("/fake/path")
    package_name = "testpackage"
    expected_version = "1.0.1-a0"

    with patch("pathlib.Path.exists", MagicMock(side_effect=[True, True])):
        with patch(
            "qbraid_core.system.versions.extract_version",
            side_effect=[VersionNotFoundError(), "1.0.0"],
        ):
            with patch(
                "qbraid_core.system.versions.get_latest_package_version", return_value="1.0.1"
            ):
                with patch("qbraid_core.system.versions.compare_versions", return_value="1.0.1"):
                    with patch(
                        "qbraid_core.system.versions.get_bumped_version",
                        return_value=expected_version,
                    ):
                        result = get_prelease_version(project_root, package_name)
                        assert result == expected_version


def test_get_prelease_version_no_metadata_file():
    """
    Test get_prelease_version raises FileNotFoundError when no metadata file is found.
    """
    project_root = Path("/fake/path")
    package_name = "testpackage"

    with patch("pathlib.Path.exists", return_value=False):
        with pytest.raises(FileNotFoundError):
            get_prelease_version(project_root, package_name)


def test_get_prelease_version_error_chaining():
    """
    Test get_prelease_version raises QbraidChainedException when
    both files exist but extraction fails.
    """
    project_root = Path("/fake/path")
    package_name = "testpackage"

    with patch("pathlib.Path.exists", MagicMock(side_effect=[True, True])):
        with patch(
            "qbraid_core.system.versions.extract_version", side_effect=VersionNotFoundError()
        ):
            with pytest.raises(QbraidChainedException) as exc_info:
                get_prelease_version(project_root, package_name)
            assert len(exc_info.value.exceptions) == 2


@pytest.mark.parametrize(
    "version, bump_type, expected",
    [
        ("1.2.3", "major", "2.0.0"),
        ("1.2.3", "minor", "1.3.0"),
        ("1.2.3", "patch", "1.2.4"),
        ("1.2.3", "prerelease", "1.2.3-a.0"),
        ("1.2.3-alpha.1", "prerelease", "1.2.3-a.2"),
        ("1.2.3-rc.100", "prerelease", "1.2.3-rc.101"),
        ("1.0.0", "major", "2.0.0"),
        ("2.1.1", "minor", "2.2.0"),
        ("0.1.9", "patch", "0.1.10"),
    ],
)
def test_bump_version_success(version, bump_type, expected):
    """
    Test that bump_version correctly bumps the version based on the specified bump type.
    """
    assert bump_version(version, bump_type) == expected


@pytest.mark.parametrize(
    "version, bump_type", [("1.2.3", "invalid"), ("1.2.3", ""), ("1.2.3", None)]
)
def test_bump_version_invalid_type(version, bump_type):
    """
    Test that bump_version raises a ValueError when an invalid bump type is specified.
    """
    with pytest.raises(ValueError):
        bump_version(version, bump_type)


def test_update_version_in_pyproject_file_not_found():
    """
    Test that the function raises a FileNotFoundError when the pyproject.toml file does not exist.
    """
    file_path = "pyproject.toml"
    new_version = "0.2.0"

    with patch("pathlib.Path.exists", return_value=False):
        with pytest.raises(FileNotFoundError):
            update_version_in_pyproject(file_path, new_version)


def test_find_largest_version():
    """
    Test that the function correctly finds the largest version from a list of versions.
    """
    versions = ["0.1.0", "0.1.1", "0.1.2", "0.1.17a0", "0.1.3", "0.1.4"]
    assert find_largest_version(versions) == "0.1.17a0"


def test_package_exists():
    """Test package_has_match_on_pypi with a package that exists."""
    assert package_has_match_on_pypi("numpy")


def test_package_with_specific_version():
    """Test package_has_match_on_pypi with a package that exists and a specific version."""
    assert package_has_match_on_pypi("numpy", "==", "1.21.0")


def test_package_with_greater_than_version():
    """Test package_has_match_on_pypi with a package that exists and a greater than version."""
    assert package_has_match_on_pypi("numpy", ">", "1.20.0")


def test_package_with_less_than_version():
    """Test package_has_match_on_pypi with a package that exists and a less than version."""
    assert package_has_match_on_pypi("numpy", "<", "2.0.0")


def test_package_with_compatible_release():
    """Test package_has_match_on_pypi with a package that exists and a compatible release."""
    assert package_has_match_on_pypi("numpy", "~=", "1.21.0")


def test_nonexistent_package():
    """Test package_has_match_on_pypi with a package that does not exist."""
    assert not package_has_match_on_pypi("nonexistent_package_12345")


def test_invalid_operator():
    """Test package_has_match_on_pypi with an invalid operator."""
    with pytest.raises(ValueError, match="Unsupported operator: !="):
        package_has_match_on_pypi("numpy", "!=", "1.21.0")


def test_missing_version_with_operator():
    """Test package_has_match_on_pypi with an operator but no version."""
    with pytest.raises(ValueError, match="Version must be provided when operator is specified."):
        package_has_match_on_pypi("numpy", "==")


@patch("requests.get")
def test_network_error(mock_get):
    """Test package_has_match_on_pypi with a network error."""
    mock_get.side_effect = Exception("Network error")
    assert not package_has_match_on_pypi("numpy")


@patch("requests.get")
def test_non_200_response(mock_get):
    """Test package_has_match_on_pypi with a non-200 response."""
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response
    assert not package_has_match_on_pypi("numpy")


@patch("requests.get")
def test_partial_version(mock_get):
    """Test package_has_match_on_pypi with a partial version."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"releases": {"1.21.0": [], "1.21.1": [], "1.22.0": []}}
    mock_get.return_value = mock_response

    assert package_has_match_on_pypi("numpy", version="1.21")
    assert not package_has_match_on_pypi("numpy", version="1.23")
