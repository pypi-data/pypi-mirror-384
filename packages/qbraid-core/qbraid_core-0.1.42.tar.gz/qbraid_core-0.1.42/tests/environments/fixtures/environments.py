# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

"""
Module containing environment fixtures for unit tests.

"""
import os

import pytest

from qbraid_core.sessions import QbraidSession

qbraid_refresh_token = os.getenv("REFRESH")
qbraid_api_key = os.getenv("QBRAID_API_KEY")
qbraid_user = os.getenv("JUPYTERHUB_USER")


@pytest.fixture
def qbraid_environments():
    """Returns a list of all qBraid environments."""
    session = QbraidSession(
        user_email=qbraid_user, refresh_token=qbraid_refresh_token, api_key=qbraid_api_key
    )
    envs = session.get("/environments").json()
    yield envs
