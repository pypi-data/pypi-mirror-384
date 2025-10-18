# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

"""
Unit tests for quantum job/device data adapter functions.

"""

from typing import Any, Union

import pytest

from qbraid_core.services.quantum.adapter import (
    _device_status_msg,
    _job_status_msg,
    process_job_data,
)


@pytest.mark.parametrize(
    "num_devices, lag, expected",
    [
        (0, 45, "No results matching given criteria"),
        (1, 0, "Device status updated 0 minutes ago"),
        (3, 5, "Device status updated 5 minutes ago"),
        (2, 10, "Device status updated 10 minutes ago"),
        (1, 25, "Device status updated 20 minutes ago"),
        (1, 30, "Device status updated 30 minutes ago"),
        (1, 90, "Device status updated 1 hour ago"),
        (2, 120, "Device status updated 2 hours ago"),
        (1, 61, "Device status updated 1 hour ago"),
    ],
)
def test_device_status_msg(num_devices: int, lag: Union[int, float], expected: str):
    """Test the device status message."""
    assert _device_status_msg(num_devices, lag) == expected


@pytest.mark.parametrize(
    "num_jobs, query, expected",
    [
        (0, {}, "No jobs found submitted by user"),
        (
            0,
            {"status": "pending"},
            "No jobs found matching given criteria",
        ),
        (
            1,
            {"resultsPerPage": 5},
            "Displaying 1/1 jobs matching query",
        ),
        (
            5,
            {"resultsPerPage": 5},
            "Displaying 5 most recent jobs matching query",
        ),
        (
            10,
            {"maxResults": 5, "status": "completed"},
            "Displaying 10 most recent jobs matching query",
        ),
        (
            3,
            {"numResults": 2},
            "Displaying 3 most recent jobs matching query",
        ),
    ],
)
def test_job_status_msg(num_jobs: int, query: dict[str, Any], expected: str):
    """Test the job status message."""
    assert _job_status_msg(num_jobs, query) == expected


device_list = [
    {
        "qbraid_id": "D001",
        "name": "Quantum Processor 1",
        "provider": "QBProvider",
        "statusRefresh": "2023-01-01T12:00:00",
        "status": "Available",
    },
    {
        "qbraid_id": "D002",
        "name": "Quantum Processor 2",
        "provider": "QBProvider",
        "statusRefresh": None,
        "status": "Unavailable",
    },
]

job_list = [
    {"qbraidJobId": "J001", "createdAt": "2023-01-01T12:00:00", "status": "Completed"},
    {
        "_id": "J002",
        "timestamps": {"createdAt": "2023-01-02T12:00:00", "jobStarted": "2023-01-02T12:30:00"},
        "status": "Pending",
    },
]


@pytest.mark.parametrize(
    "jobs, params, expected_output",
    [
        (
            job_list,
            {},
            (
                [
                    ["J001", "2023-01-01T12:00:00", "Completed"],
                    ["J002", "2023-01-02T12:00:00", "Pending"],
                ],
                "Displaying 2/2 jobs matching query",
            ),
        )
    ],
)
def test_process_job_data(jobs, params, expected_output):
    """Test the process_job_data function."""
    assert process_job_data(jobs, params) == expected_output
