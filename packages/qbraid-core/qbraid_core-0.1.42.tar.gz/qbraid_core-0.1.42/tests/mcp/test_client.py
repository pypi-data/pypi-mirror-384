# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

# pylint: disable=redefined-outer-name,protected-access

"""
Unit tests for MCP WebSocket client module.

"""
import asyncio
import json
from unittest.mock import AsyncMock, Mock

import pytest

from qbraid_core.services.mcp.client import MCPWebSocketClient


@pytest.fixture
def mock_websocket():
    """Create a mock WebSocket connection."""
    mock_ws = AsyncMock()
    mock_ws.send = AsyncMock()
    mock_ws.ping = AsyncMock()
    mock_ws.close = AsyncMock()
    mock_ws.__aiter__ = Mock(return_value=iter([]))
    return mock_ws


@pytest.fixture
def client():
    """Create an MCPWebSocketClient instance."""
    return MCPWebSocketClient(
        websocket_url="wss://test.example.com/mcp", on_message=None, name="test"
    )


@pytest.fixture
def client_with_callback():
    """Create an MCPWebSocketClient with a message callback."""
    callback = Mock()
    return (
        MCPWebSocketClient(
            websocket_url="wss://test.example.com/mcp", on_message=callback, name="test"
        ),
        callback,
    )


def test_client_initialization():
    """Test MCPWebSocketClient initialization."""
    url = "wss://test.example.com/mcp"
    name = "test-client"

    client = MCPWebSocketClient(websocket_url=url, name=name)

    assert client.websocket_url == url
    assert client.name == name
    assert client.on_message is None
    assert client._ws is None
    assert client._is_connected is False
    assert client._is_shutting_down is False
    assert not client._message_queue
    assert client._heartbeat_task is None
    assert client._reconnect_task is None
    assert client._receive_task is None


def test_client_initialization_with_callback():
    """Test MCPWebSocketClient initialization with callback."""

    def callback(msg):  # pylint: disable=unused-argument
        pass

    client = MCPWebSocketClient(
        websocket_url="wss://test.example.com/mcp", on_message=callback, name="test"
    )

    assert client.on_message is callback


def test_is_connected_property(client):
    """Test is_connected property."""
    assert client.is_connected is False

    client._is_connected = True
    client._ws = None
    assert client.is_connected is False

    client._ws = "mock_ws"
    assert client.is_connected is True


@pytest.mark.asyncio
async def test_connect_success(client, mock_websocket, monkeypatch):
    """Test successful WebSocket connection."""
    import qbraid_core.services.mcp.client as client_module  # pylint: disable=import-outside-toplevel

    async def mock_wait_for(coro, timeout):  # pylint: disable=unused-argument
        return mock_websocket

    monkeypatch.setattr(client_module.asyncio, "wait_for", mock_wait_for)
    monkeypatch.setattr(
        client_module, "websockets", Mock(connect=AsyncMock(return_value=mock_websocket))
    )

    await client.connect()

    assert client._is_connected is True
    assert client._ws == mock_websocket
    assert client._heartbeat_task is not None
    assert client._receive_task is not None


@pytest.mark.asyncio
async def test_connect_with_queued_messages(client, mock_websocket, monkeypatch):
    """Test connection sends queued messages."""
    import qbraid_core.services.mcp.client as client_module  # pylint: disable=import-outside-toplevel

    async def mock_wait_for(coro, timeout):  # pylint: disable=unused-argument
        return mock_websocket

    monkeypatch.setattr(client_module.asyncio, "wait_for", mock_wait_for)
    monkeypatch.setattr(
        client_module, "websockets", Mock(connect=AsyncMock(return_value=mock_websocket))
    )

    # Queue some messages
    client._message_queue = ['{"method": "test1"}', '{"method": "test2"}']

    await client.connect()

    assert not client._message_queue
    assert mock_websocket.send.call_count == 2


@pytest.mark.asyncio
async def test_connect_timeout(client, monkeypatch):
    """Test connection timeout handling."""
    import qbraid_core.services.mcp.client as client_module  # pylint: disable=import-outside-toplevel

    async def mock_wait_for(coro, timeout):  # pylint: disable=unused-argument
        raise asyncio.TimeoutError()

    monkeypatch.setattr(client_module.asyncio, "wait_for", mock_wait_for)
    monkeypatch.setattr(client_module, "websockets", Mock(connect=AsyncMock()))

    schedule_reconnect_mock = AsyncMock()
    monkeypatch.setattr(client, "_schedule_reconnect", schedule_reconnect_mock)

    await client.connect()

    assert client._is_connected is False
    schedule_reconnect_mock.assert_called_once()


@pytest.mark.asyncio
async def test_connect_exception(client, monkeypatch):
    """Test connection exception handling."""
    import qbraid_core.services.mcp.client as client_module  # pylint: disable=import-outside-toplevel

    async def mock_wait_for(coro, timeout):  # pylint: disable=unused-argument
        raise Exception("Connection failed")  # pylint: disable=broad-exception-raised

    monkeypatch.setattr(client_module.asyncio, "wait_for", mock_wait_for)
    monkeypatch.setattr(client_module, "websockets", Mock(connect=AsyncMock()))

    schedule_reconnect_mock = AsyncMock()
    monkeypatch.setattr(client, "_schedule_reconnect", schedule_reconnect_mock)

    await client.connect()

    assert client._is_connected is False
    schedule_reconnect_mock.assert_called_once()


@pytest.mark.asyncio
async def test_connect_when_shutting_down(client):
    """Test connect does nothing when shutting down."""
    client._is_shutting_down = True

    await client.connect()

    assert client._ws is None
    assert client._is_connected is False


@pytest.mark.asyncio
async def test_connect_websockets_not_available(client, monkeypatch):
    """Test connect raises ImportError when websockets not available."""
    import qbraid_core.services.mcp.client as client_module  # pylint: disable=import-outside-toplevel

    monkeypatch.setattr(client_module, "WEBSOCKETS_AVAILABLE", False)

    with pytest.raises(ImportError, match="MCP WebSocket client requires the 'websockets' package"):
        await client.connect()


@pytest.mark.asyncio
async def test_send_success(client, mock_websocket):
    """Test successful message sending."""
    client._ws = mock_websocket
    client._is_connected = True

    message = {"method": "test", "params": {}}

    await client.send(message)

    mock_websocket.send.assert_called_once()
    call_args = mock_websocket.send.call_args[0][0]
    assert json.loads(call_args) == message


@pytest.mark.asyncio
async def test_send_when_not_connected(client):
    """Test sending message when not connected queues it."""
    client._is_connected = False

    message = {"method": "test", "params": {}}

    await client.send(message)

    assert len(client._message_queue) == 1
    assert json.loads(client._message_queue[0]) == message


@pytest.mark.asyncio
async def test_send_failure_queues_message(client, mock_websocket):
    """Test send failure queues message and raises error."""
    client._ws = mock_websocket
    client._is_connected = True
    mock_websocket.send.side_effect = Exception("Send failed")

    message = {"method": "test", "params": {}}

    with pytest.raises(ConnectionError, match="Failed to send message to test"):
        await client.send(message)

    assert len(client._message_queue) == 1


@pytest.mark.asyncio
async def test_receive_loop_processes_messages(client_with_callback, mock_websocket):
    """Test receive loop processes incoming messages."""
    client, callback = client_with_callback

    # Mock the async iterator
    messages = ['{"method": "test1"}', '{"method": "test2"}']

    async def async_iter():
        for msg in messages:
            yield msg

    mock_websocket.__aiter__ = lambda self: async_iter()  # pylint: disable=unnecessary-lambda
    client._ws = mock_websocket
    client._is_connected = True

    # Run receive loop in background
    task = asyncio.create_task(client._receive_loop())

    # Give it time to process
    await asyncio.sleep(0.1)

    # Cancel the task
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass

    assert callback.call_count == 2


@pytest.mark.asyncio
async def test_receive_loop_json_decode_error(client, mock_websocket, monkeypatch):
    """Test receive loop handles JSON decode errors."""

    async def async_iter():
        yield "invalid json"

    mock_websocket.__aiter__ = lambda self: async_iter()  # pylint: disable=unnecessary-lambda
    client._ws = mock_websocket

    # Patch _schedule_reconnect to prevent actual reconnection
    monkeypatch.setattr(client, "_schedule_reconnect", AsyncMock())

    task = asyncio.create_task(client._receive_loop())
    await asyncio.sleep(0.1)

    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


@pytest.mark.asyncio
async def test_receive_loop_no_callback(client, mock_websocket, monkeypatch):
    """Test receive loop when no callback is registered."""

    async def async_iter():
        yield '{"method": "test"}'

    mock_websocket.__aiter__ = lambda self: async_iter()  # pylint: disable=unnecessary-lambda
    client._ws = mock_websocket

    monkeypatch.setattr(client, "_schedule_reconnect", AsyncMock())

    task = asyncio.create_task(client._receive_loop())
    await asyncio.sleep(0.1)

    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


@pytest.mark.asyncio
async def test_heartbeat_loop(client, mock_websocket):
    """Test heartbeat loop sends pings."""
    client._ws = mock_websocket
    client._is_connected = True

    # Mock the pong awaitable
    pong_future = asyncio.Future()
    pong_future.set_result(None)
    mock_websocket.ping.return_value = pong_future

    # Create heartbeat task
    client._heartbeat_task = asyncio.create_task(client._heartbeat_loop())

    # Wait a bit
    await asyncio.sleep(0.1)

    # Cancel the task
    client._heartbeat_task.cancel()
    try:
        await client._heartbeat_task
    except asyncio.CancelledError:
        pass


@pytest.mark.asyncio
async def test_heartbeat_loop_timeout(client, mock_websocket):
    """Test heartbeat loop handles timeout."""
    client._ws = mock_websocket
    client._is_connected = True

    # Mock ping to timeout
    async def timeout_ping():
        raise asyncio.TimeoutError()

    mock_websocket.ping.side_effect = timeout_ping

    asyncio.create_task(client._heartbeat_loop())
    await asyncio.sleep(0.1)

    # Task should exit due to timeout
    await asyncio.sleep(0.1)


@pytest.mark.asyncio
async def test_schedule_reconnect(client, monkeypatch):
    """Test reconnection scheduling."""
    connect_mock = AsyncMock()
    monkeypatch.setattr(client, "connect", connect_mock)

    await client._schedule_reconnect()

    assert client._reconnect_task is not None

    # Wait for reconnection
    await asyncio.sleep(client.RECONNECT_DELAY + 0.1)

    connect_mock.assert_called_once()


@pytest.mark.asyncio
async def test_schedule_reconnect_when_shutting_down(client):
    """Test reconnection is not scheduled when shutting down."""
    client._is_shutting_down = True

    await client._schedule_reconnect()

    assert client._reconnect_task is None


@pytest.mark.asyncio
async def test_schedule_reconnect_when_already_scheduled(client):
    """Test reconnection is not scheduled if already scheduled."""
    client._reconnect_task = asyncio.create_task(asyncio.sleep(10))

    await client._schedule_reconnect()

    # Should still be the same task
    assert client._reconnect_task is not None


@pytest.mark.asyncio
async def test_cleanup_connection(client, mock_websocket):
    """Test connection cleanup."""
    client._ws = mock_websocket
    client._is_connected = True

    # Create mock tasks
    client._receive_task = asyncio.create_task(asyncio.sleep(10))
    client._heartbeat_task = asyncio.create_task(asyncio.sleep(10))

    await client._cleanup_connection()

    assert client._ws is None
    assert client._is_connected is False
    assert client._receive_task is None
    assert client._heartbeat_task is None


@pytest.mark.asyncio
async def test_cleanup_connection_close_error(client, mock_websocket):
    """Test cleanup handles WebSocket close errors."""
    client._ws = mock_websocket
    mock_websocket.close.side_effect = Exception("Close failed")

    # Should not raise
    await client._cleanup_connection()

    assert client._ws is None


@pytest.mark.asyncio
async def test_shutdown(client, monkeypatch):
    """Test graceful shutdown."""
    cleanup_mock = AsyncMock()
    monkeypatch.setattr(client, "_cleanup_connection", cleanup_mock)

    await client.shutdown()

    assert client._is_shutting_down is True
    cleanup_mock.assert_called_once()


@pytest.mark.asyncio
async def test_shutdown_already_shutting_down(client, monkeypatch):
    """Test shutdown when already shutting down."""
    client._is_shutting_down = True
    cleanup_mock = AsyncMock()
    monkeypatch.setattr(client, "_cleanup_connection", cleanup_mock)

    await client.shutdown()

    cleanup_mock.assert_not_called()


@pytest.mark.asyncio
async def test_shutdown_cancels_reconnect_task(client, monkeypatch):
    """Test shutdown cancels reconnection task."""
    client._reconnect_task = asyncio.create_task(asyncio.sleep(10))
    monkeypatch.setattr(client, "_cleanup_connection", AsyncMock())

    await client.shutdown()

    assert client._reconnect_task.cancelled()
