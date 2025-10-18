# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

"""
Unit tests related to setting, updating, and verifying
custom user configurations and required run-command pre-sets.

"""
import os

import pytest

from qbraid_core.config import load_config, save_config
from qbraid_core.exceptions import AuthError, RequestsApiError, UserNotFoundError
from qbraid_core.sessions import STATUS_FORCELIST, PostForcelistRetry, QbraidSession, Session

qbraid_refresh_token = os.getenv("REFRESH")
qbraid_api_key = os.getenv("QBRAID_API_KEY")
qbraid_user = os.getenv("JUPYTERHUB_USER")

skip_remote_tests: bool = os.getenv("QBRAID_RUN_REMOTE_TESTS", "False").lower() != "true"
REASON = "QBRAID_RUN_REMOTE_TESTS not set (requires configuration of qBraid storage)"

CURRENT_CONFIG = load_config()


def reset_config():
    """Reset the current configuration to the default."""
    save_config(CURRENT_CONFIG)


def test_api_error():
    """Test raising error when making invalid API request."""
    with pytest.raises(RequestsApiError):
        session = QbraidSession()
        session.request("POST", "not a url")


def test_qbraid_session_from_args():
    """Test initializing QbraidSession with attributes set from user-provided values."""
    refresh_token = "test123"
    session = QbraidSession(refresh_token=refresh_token)
    assert session.refresh_token == refresh_token
    del session


def test_qbraid_config_overwrite_with_id_token():
    """Test setting/saving id-token and then test overwritting config value"""
    dummy_api_key = "alice123"
    dummy_api_key_overwrite = "bob456"
    session = QbraidSession(refresh_token=dummy_api_key)
    assert session.refresh_token == dummy_api_key

    try:
        session.save_config(verify=not skip_remote_tests)
        assert session.get_config("refresh-token") == dummy_api_key
        session.save_config(refresh_token=dummy_api_key_overwrite)
        assert session.get_config("refresh-token") == dummy_api_key_overwrite
    finally:
        reset_config()


def test_qbraid_session_api_key():
    """Test initializing QbraidSession without args and then saving config."""
    session = QbraidSession()
    try:
        session.save_config(
            api_key=qbraid_api_key, user_email=qbraid_user, verify=not skip_remote_tests
        )
        assert session.get_config("api-key") == qbraid_api_key
    finally:
        reset_config()


def test_qbraid_session_save_config():
    """Test initializing QbraidSession without args and then saving config."""
    session = QbraidSession()
    try:
        session.save_config(
            user_email=qbraid_user, refresh_token=qbraid_refresh_token, verify=not skip_remote_tests
        )
        assert session.get_config("email") == qbraid_user
        assert session.get_config("refresh-token") == qbraid_refresh_token
    finally:
        reset_config()


def test_qbraid_session_credential_mismatch_error():
    """Test initializing QbraidSession with mismatched email and apiKey."""
    session = QbraidSession(api_key=qbraid_api_key, user_email="fakeuser@email.com")
    try:
        with pytest.raises(AuthError):
            session.save_config()
    finally:
        reset_config()


def test_qbraid_session_invalid_workspace():
    """Test initializing QbraidSession with invalid workspace."""
    session = QbraidSession(api_key=qbraid_api_key, user_email="fakeuser@email.com")
    try:
        with pytest.raises(ValueError):
            session.save_config(workspace="invalid_workspace")
    finally:
        reset_config()


def test_save_config_bad_url():
    """Test that passing bad base_url to save_config raises exception."""
    session = QbraidSession()
    try:
        with pytest.raises(UserNotFoundError):
            session.save_config(base_url="bad_url")
    finally:
        reset_config()


def test_get_session_values():
    """Test function that retrieves session values."""
    fake_user_email = "test@email.com"
    fake_refresh_token = "2030dksc2lkjlkjll"
    session = QbraidSession(user_email=fake_user_email, refresh_token=fake_refresh_token)
    assert session.user_email == fake_user_email
    assert session.refresh_token == fake_refresh_token


@pytest.mark.parametrize(
    "retry_data", [("POST", 200, False, 8), ("GET", 500, True, 3), ("POST", 502, True, 4)]
)
def test_post_forcelist_retry(retry_data):
    """Test methods for session retry checks and counters"""
    method, code, should_retry, init_retries = retry_data
    retry = PostForcelistRetry(
        total=init_retries,
        status_forcelist=STATUS_FORCELIST,
    )
    assert retry.is_retry(method, code) == should_retry
    assert retry.increment().total == init_retries - 1


def test_user_agent():
    """Test that the user agent is set correctly."""
    session = Session()
    user_agent = session._user_agent()
    assert user_agent.startswith("QbraidCore")
    assert user_agent in session.headers["User-Agent"]


def test_add_user_agent():
    """Test that adding a new user agent updates the headers correctly."""
    session = Session()
    new_user_agent = "Test/123"
    init_user_agent = session._user_agent()
    session.add_user_agent(init_user_agent)
    assert session.headers["User-Agent"] == init_user_agent
    session.add_user_agent(new_user_agent)
    assert session.headers["User-Agent"] == f"{init_user_agent} {new_user_agent}"
