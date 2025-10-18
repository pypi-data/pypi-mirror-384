# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

# pylint: disable=redefined-outer-name

"""
Unit tests for ChatClient class.

"""

from unittest.mock import MagicMock

import pytest

from qbraid_core.exceptions import RequestsApiError
from qbraid_core.services.chat.client import ChatClient
from qbraid_core.services.chat.exceptions import ChatServiceRequestError


@pytest.fixture
def mock_chat_client():
    """Fixture to create a mock ChatClient instance."""
    client = ChatClient()
    client._session = MagicMock()
    return client


def test_chat_success(mock_chat_client):
    """Test the `chat` method when the response is successful."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"content": "Hello, world!"}
    mock_chat_client.session.post.return_value = mock_response

    prompt = "Hello"
    model = "gpt-4o-mini"

    result = mock_chat_client.chat(prompt, model)
    assert result == "Hello, world!"
    mock_chat_client.session.post.assert_called_once_with(
        "/chat", json={"prompt": prompt, "stream": False, "model": model}, stream=False
    )


def test_chat_failure(mock_chat_client):
    """Test the `chat` method when a request fails."""
    mock_chat_client.session.post.side_effect = RequestsApiError("Request failed")

    with pytest.raises(
        ChatServiceRequestError, match="Failed to get chat response: Request failed"
    ):
        mock_chat_client.chat("Hello", "gpt-4o-mini")


def test_chat_stream_success(mock_chat_client):
    """Test the `chat_stream` method when the response is streamed successfully."""
    mock_response = MagicMock()
    mock_response.iter_content.return_value = iter(["chunk1", "chunk2", "chunk3"])
    mock_chat_client.session.post.return_value = mock_response

    prompt = "Stream test"
    model = "gpt-4o-mini"

    chunks = list(mock_chat_client.chat_stream(prompt, model))
    assert chunks == ["chunk1", "chunk2", "chunk3"]
    mock_chat_client.session.post.assert_called_once_with(
        "/chat", json={"prompt": prompt, "stream": True, "model": model}, stream=True
    )


def test_chat_stream_failure(mock_chat_client):
    """Test the `chat_stream` method when a request fails."""
    mock_chat_client.session.post.side_effect = RequestsApiError("Stream request failed")

    with pytest.raises(
        ChatServiceRequestError, match="Failed to get chat response: Stream request failed"
    ):
        list(mock_chat_client.chat_stream("Stream test", "gpt-4o-mini"))
