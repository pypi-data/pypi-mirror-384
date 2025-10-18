# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

# pylint: disable=redefined-outer-name

"""
Unit tests for qir-runner Python simulator wrapper.

"""
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from qbraid_core.services.quantum.runner import Simulator

RESOURCE_DIR = Path(__file__).parent / "resources"


def load_resource(file_name: str, **kwargs):
    """Helper function to read content from a file."""
    mode = "rb" if file_name.endswith(".bc") else "r"
    file_path = RESOURCE_DIR / file_name

    try:
        with open(file_path, mode, **kwargs) as file:
            return file.read()
    except FileNotFoundError as err:
        raise FileNotFoundError(f"Resource file not found: {file_path}") from err


@pytest.fixture
def mock_runner_data():
    """Load QIR test program and expected stdout from resources."""
    bitcode = load_resource("qir_program.bc")
    stdout = load_resource("qir_runner_stdout.txt")

    shots = 10
    num_qubits = 5
    basis_0 = [0] * num_qubits
    basis_1 = [1] * num_qubits

    qubit_res = [0, 1, 1, 0, 0, 0, 0, 1, 0, 1]
    parsed = {f"q{i}": qubit_res for i in range(num_qubits)}
    measurements = [basis_0 if value == 0 else basis_1 for value in qubit_res]

    key_0 = "0" * num_qubits
    key_1 = "1" * num_qubits

    counts = {
        key_0: qubit_res.count(0),
        key_1: qubit_res.count(1),
    }

    data = {
        "shots": shots,
        "num_qubits": num_qubits,
        "parsed": parsed,
        "measurements": measurements,
        "counts": counts,
        "bitcode": bitcode,
        "stdout": stdout,
        "stderr": "",
        "returncode": 0,
    }

    yield data


def test_run_qir_simulator(mock_runner_data):
    """Test qir-runner sparse simulator python wrapper(s)."""
    simulator = Simulator()
    simulator._qir_runner = "qir-runner"

    shots = mock_runner_data["shots"]
    bitcode = mock_runner_data["bitcode"]

    with patch("subprocess.run") as mock_run:
        mock_completed_process = MagicMock()
        mock_completed_process.stdout = mock_runner_data["stdout"]
        mock_completed_process.stderr = mock_runner_data["stderr"]
        mock_completed_process.returncode = mock_runner_data["returncode"]
        mock_run.return_value = mock_completed_process

        job_data = simulator.run(bitcode, shots=shots)
        measurements = job_data.get("measurements")
        counts = job_data.get("measurementCounts")
        time_stamps = job_data.get("timeStamps", {})
        execution_duration = time_stamps.get("executionDuration")

        assert isinstance(measurements, list)
        assert isinstance(counts, dict)
        assert isinstance(execution_duration, int)

        assert len(counts) == 2
        assert sum(counts.values()) == shots


def test_process_qir_simulator_results(mock_runner_data):
    """Test post-processing of qir runner results."""
    stdout = mock_runner_data["stdout"]
    parsed_data = Simulator._parse_results(stdout)
    measurements = Simulator._data_to_measurements(parsed_data)
    counts = Simulator._measurements_to_counts(measurements)

    assert parsed_data == mock_runner_data["parsed"]
    assert measurements == mock_runner_data["measurements"]
    assert counts == mock_runner_data["counts"]


@pytest.mark.parametrize("numpy", [True, False])
def test_data_to_measurements(numpy):
    """Test the data to measurements conversion function with and without numpy."""
    parsed_data = {"a": [1, 2, 3], "b": [4, 5, 6]}
    expected_output = [[1, 4], [2, 5], [3, 6]]

    output = Simulator._data_to_measurements(parsed_data, numpy=numpy)
    assert output == expected_output
