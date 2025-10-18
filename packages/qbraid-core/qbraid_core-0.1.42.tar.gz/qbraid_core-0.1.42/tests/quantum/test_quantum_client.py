# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

# pylint: disable=redefined-outer-name

"""
Unit tests for QuantumClient.

"""
import base64
import sys
import unittest
from unittest.mock import MagicMock, Mock, patch

import pytest

from qbraid_core.exceptions import RequestsApiError, ResourceNotFoundError
from qbraid_core.services.quantum import QuantumClient, QuantumServiceRequestError


@pytest.fixture
def mock_session():
    """Fixture to provide a mock session object."""
    return Mock()


@pytest.fixture
def quantum_client(mock_session):
    """Fixture to provide a QuantumClient instance with a mocked session."""
    with patch("qbraid_core.QbraidClient.session", new=mock_session):
        client = QuantumClient()
        client.session = mock_session
        yield client


def test_search_devices_success(quantum_client, mock_session):
    """Test successful search of quantum devices."""
    mock_response = Mock()
    mock_response.json.return_value = [{"device_id": "123"}]
    mock_session.get.return_value = mock_response

    query = {"type": "Simulator"}
    response = quantum_client.search_devices(query)

    assert response == [{"device_id": "123"}]
    mock_session.get.assert_called_once_with("/quantum-devices", params=query)


def test_search_jobs_success(quantum_client, mock_session):
    """Test successful search of quantum jobs."""
    mock_response = Mock()
    mock_response.json.return_value = {"jobsArray": [{"job_id": "abc"}]}
    mock_session.get.return_value = mock_response

    query = {"user": "test_user"}
    response = quantum_client.search_jobs(query)

    assert response == [{"job_id": "abc"}]
    mock_session.get.assert_called_once_with("/quantum-jobs", params=query)


def test_create_job_success(quantum_client, mock_session):
    """Test successful creation of a quantum job."""
    mock_response = Mock()
    mock_response.json.return_value = {"job_id": "abc"}
    mock_session.post.return_value = mock_response

    data = {"bitcode": b"sample_bitcode"}
    response = quantum_client.create_job(data)

    assert response == {"job_id": "abc"}
    assert data["bitcode"] == "c2FtcGxlX2JpdGNvZGU="  # base64 encoded value
    mock_session.post.assert_called_once_with("/quantum-jobs", json=data)


def test_estimate_cost_success(quantum_client, mock_session):
    """Test successful calculation of the cost of running a quantum job."""
    mock_response = Mock()
    mock_response.json.return_value = {"estimatedCredits": 10.0}
    mock_session.get.return_value = mock_response

    device_id = "device123"
    shots = 1000
    estimated_minutes = 30.0

    response = quantum_client.estimate_cost(device_id, shots, estimated_minutes)

    assert response["estimatedCredits"] == 10.0
    mock_session.get.assert_called_once_with(
        "/quantum-jobs/cost-estimate",
        params={"qbraidDeviceId": device_id, "shots": shots, "minutes": estimated_minutes},
    )


def test_estimate_cost_failure(quantum_client, mock_session):
    """Test failed calculation of the cost of running a quantum job."""
    mock_session.get.side_effect = RequestsApiError("Error")

    device_id = "device123"
    shots = 1000
    estimated_minutes = 30.0

    with pytest.raises(QuantumServiceRequestError):
        quantum_client.estimate_cost(device_id, shots, estimated_minutes)


def test_estimate_cost_value_error(quantum_client):
    """Test ValueError when invalid arguments are provided to estimate_cost."""
    with pytest.raises(ValueError):
        quantum_client.estimate_cost("device123", None, None)


@pytest.fixture
def client():
    """Fixture to provide a QuantumClient instance."""
    return QuantumClient()


@pytest.fixture
def mock_response():
    """Fixture to provide a mock response object."""
    return MagicMock()


def test_get_job_results_success(client, mock_response):
    """Test successful retrieval of quantum job results."""
    mock_response.json.return_value = {"data": {"result": "success"}, "error": None}

    with patch.object(client.session, "get", return_value=mock_response):
        result = client.get_job_results("test_id")
        assert result == {"result": "success"}


def test_get_job_results_retry_on_failure(client, mock_response):
    """Test successful retrieval of quantum job results after retrying."""
    mock_response.json.return_value = {"data": {"result": "success"}, "error": None}

    with patch.object(client.session, "get", side_effect=[RequestsApiError, mock_response]):
        result = client.get_job_results("test_id", max_retries=2)
        assert result == {"result": "success"}


def test_get_job_results_max_retries_failure(client):
    """Test failure to retrieve quantum job results after max retries."""
    with patch.object(client.session, "get", side_effect=RequestsApiError):
        with pytest.raises(QuantumServiceRequestError):
            client.get_job_results("test_id", max_retries=3)


def test_get_job_results_error_in_response(client, mock_response):
    """Test failure to retrieve quantum job results when an error is present in the response."""
    mock_response.json.return_value = {"error": "Job failed"}

    with patch.object(client.session, "get", return_value=mock_response):
        with pytest.raises(QuantumServiceRequestError, match="Failed to retrieve job results"):
            client.get_job_results("test_id")


def test_get_job_results_no_data_found(client, mock_response):
    """Test failure to retrieve quantum job results when no data is found in the response."""
    mock_response.json.return_value = {"data": None, "error": None}

    with patch.object(client.session, "get", return_value=mock_response):
        with pytest.raises(ResourceNotFoundError):
            client.get_job_results("test_id")


class TestQuantumClient(unittest.TestCase):
    """Test the QuantumClient class."""

    def setUp(self):
        """Set up the QuantumClient instance."""
        self.client = QuantumClient()

    @patch("qbraid_core.services.quantum.client.QuantumClient.session")
    def test_search_devices(self, mock_session):
        """Test the search_devices method."""
        mock_session.get.return_value.json.return_value = [{"id": "device1"}, {"id": "device2"}]
        result = self.client.search_devices({"type": "SIMULATOR"})
        self.assertEqual(result, [{"id": "device1"}, {"id": "device2"}])
        mock_session.get.assert_called_with("/quantum-devices", params={"type": "Simulator"})

    @patch("qbraid_core.services.quantum.client.QuantumClient.session")
    def test_search_jobs(self, mock_session):
        """Test the search_jobs method."""
        mock_session.get.return_value.json.return_value = {
            "jobsArray": [{"id": "job1"}, {"id": "job2"}]
        }
        result = self.client.search_jobs({"maxResults": 2})
        self.assertEqual(result, [{"id": "job1"}, {"id": "job2"}])
        mock_session.get.assert_called_with("/quantum-jobs", params={"resultsPerPage": 2})

    @patch("qbraid_core.services.quantum.client.QuantumClient.search_devices")
    def test_get_device(self, mock_search):
        """Test the get_device method."""
        mock_search.return_value = [{"id": "device1"}]
        result = self.client.get_device(qbraid_id="1234")
        self.assertEqual(result, {"id": "device1"})
        mock_search.assert_called_once_with(query={"qbraid_id": "1234"})

    @patch("qbraid_core.services.quantum.client.QuantumClient.search_jobs")
    def test_get_job(self, mock_search):
        """Test the get_job method."""
        mock_search.return_value = [{"id": "job1"}]
        result = self.client.get_job(qbraid_id="5678")
        self.assertEqual(result, {"id": "job1"})
        mock_search.assert_called_once_with(query={"qbraidJobId": "5678"})

    @patch("qbraid_core.services.quantum.client.QuantumClient.session")
    def test_create_job(self, mock_session):
        """Test the create_job method."""
        mock_session.post.return_value.json.return_value = {"job_id": "1234"}
        result = self.client.create_job({"bitcode": b"example_code"})
        self.assertEqual(result, {"job_id": "1234"})
        mock_session.post.assert_called_once_with(
            "/quantum-jobs", json={"bitcode": base64.b64encode(b"example_code").decode("utf-8")}
        )

    @patch("qbraid_core.services.quantum.client.QuantumClient.get_job")
    @patch("qbraid_core.services.quantum.client.QuantumClient.session")
    def test_cancel_job(self, mock_session, mock_get_job):
        """Test the cancel_job method."""
        job_id = "3F5E4D8A12B6EF991234CABD"
        mock_get_job.return_value = {"_id": job_id}
        mock_session.put.return_value.json.return_value = {"cancelled": True}
        result = self.client.cancel_job(qbraid_id=job_id)
        self.assertEqual(result, {"cancelled": True})
        mock_get_job.assert_called_once_with(qbraid_id=job_id)
        mock_session.put.assert_called_once_with(f"/quantum-jobs/cancel/{job_id}")

    @patch("qbraid_core.services.quantum.client.get_active_python_path")
    @patch("qbraid_core.services.quantum.client.python_paths_equivalent")
    @patch("qbraid_core.services.quantum.client.quantum_lib_proxy_state")
    def test_qbraid_jobs_state(self, mock_proxy_state, mock_path_equiv, mock_active_path):
        """Test the qbraid_jobs_state method."""
        mock_active_path.return_value = "/usr/bin/python"
        mock_path_equiv.return_value = True
        mock_proxy_state.return_value = {"enabled": True}
        result = self.client.qbraid_jobs_state()
        self.assertEqual(result, {"exe": "/usr/bin/python", "libs": {"braket": {"enabled": True}}})
        mock_active_path.assert_called_once()
        mock_path_equiv.assert_called_once_with(sys.executable, "/usr/bin/python")
        mock_proxy_state.assert_called_once_with("braket", is_default_python=True)


if __name__ == "__main__":
    unittest.main()
