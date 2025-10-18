# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

"""
Unit tests for getting and update environment state files
including state.json and install_status.txt.

"""

import json

from qbraid_core.services.environments.state import update_state_json


def test_update_install_status_creates_file_if_not_exists(tmp_path):
    """Test that the function creates a state.json file if it does not exist."""
    slug_path = tmp_path
    state_json_path = slug_path / "state.json"
    install_complete = 1
    install_success = 1
    message = "Installation completed successfully."

    update_state_json(str(slug_path), install_complete, install_success, message)

    assert state_json_path.exists(), "state.json should exist after function call."
    with open(state_json_path, "r", encoding="utf-8") as file:
        data = json.load(file)
    assert data == {
        "install": {"complete": 1, "success": 1, "message": message}
    }, "Data did not match expected values."


def test_update_install_status_updates_existing_file(tmp_path):
    """Test that the function updates an existing state.json file."""
    slug_path = tmp_path
    state_json_path = slug_path / "state.json"
    initial_data = {"install": {"complete": 0, "success": 0, "message": "Initial state"}}
    with open(state_json_path, "w", encoding="utf-8") as file:
        json.dump(initial_data, file, indent=4)

    update_state_json(str(slug_path), 1, 1, "Update successful")

    with open(state_json_path, "r", encoding="utf-8") as file:
        data = json.load(file)
    assert data == {
        "install": {"complete": 1, "success": 1, "message": "Update successful"}
    }, "Existing data was not updated correctly."


def test_update_state_json_handles_optional_params(tmp_path):
    """Test that the function handles optional parameters correctly."""
    slug_path = tmp_path
    state_json_path = slug_path / "state.json"
    update_state_json(str(slug_path), 1, -1, "Multi\nLine\nMessage")

    with open(state_json_path, "r", encoding="utf-8") as file:
        data = json.load(file)
    expected_data = {
        "install": {"complete": 1, "success": -1, "message": "Multi Line Message"},
    }
    assert data == expected_data, "Function did not handle optional parameters correctly."
