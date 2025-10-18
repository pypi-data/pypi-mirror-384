# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

# pylint: disable=redefined-outer-name,protected-access

"""
Unit tests for MCP router module.

"""
from unittest.mock import AsyncMock, Mock

import pytest

from qbraid_core.services.mcp.client import MCPWebSocketClient
from qbraid_core.services.mcp.router import MCPRouter


@pytest.fixture
def mock_client():
    """Create a mock MCP WebSocket client."""
    client = Mock(spec=MCPWebSocketClient)
    client.is_connected = True
    client.send = AsyncMock()
    client.connect = AsyncMock()
    client.shutdown = AsyncMock()
    return client


@pytest.fixture
def router():
    """Create an MCPRouter instance."""
    return MCPRouter()


@pytest.fixture
def router_with_backends(router):
    """Create an MCPRouter with mock backends."""
    lab_client = Mock(spec=MCPWebSocketClient)
    lab_client.is_connected = True
    lab_client.send = AsyncMock()
    lab_client.connect = AsyncMock()
    lab_client.shutdown = AsyncMock()

    devices_client = Mock(spec=MCPWebSocketClient)
    devices_client.is_connected = False
    devices_client.send = AsyncMock()
    devices_client.connect = AsyncMock()
    devices_client.shutdown = AsyncMock()

    router.add_backend("lab", lab_client)
    router.add_backend("devices", devices_client)

    return router, lab_client, devices_client


def test_router_initialization():
    """Test MCPRouter initialization."""
    router = MCPRouter()

    assert router.on_message is None
    assert not router._backends
    assert router._is_shutting_down is False


def test_router_initialization_with_callback():
    """Test MCPRouter initialization with message callback."""
    callback_called = []

    def on_message(msg):
        callback_called.append(msg)

    router = MCPRouter(on_message=on_message)
    assert router.on_message is on_message


def test_add_backend(router, mock_client):
    """Test adding a backend to the router."""
    router.add_backend("lab", mock_client)

    assert "lab" in router._backends
    assert router._backends["lab"] == mock_client


@pytest.mark.asyncio
async def test_connect_all_no_backends(router, caplog):
    """Test connecting when no backends are registered."""
    await router.connect_all()

    assert "No backends registered" in caplog.text


@pytest.mark.asyncio
async def test_connect_all_with_backends(router_with_backends):
    """Test connecting to all backends."""
    router, lab_client, devices_client = router_with_backends

    await router.connect_all()

    lab_client.connect.assert_called_once()
    devices_client.connect.assert_called_once()


def test_route_tool_call_valid_pattern(router_with_backends):
    """Test routing a tool call with valid qbraid pattern."""
    router, _, _ = router_with_backends

    # Test routing to lab backend
    backend = router.route_tool_call("qbraid_lab_environment_install")
    assert backend == "lab"

    # Test routing to devices backend
    backend = router.route_tool_call("qbraid_devices_list")
    assert backend == "devices"


def test_route_tool_call_unknown_backend(router_with_backends):
    """Test routing a tool call to an unknown backend."""
    router, _, _ = router_with_backends

    backend = router.route_tool_call("qbraid_unknown_tool")
    assert backend is None


def test_route_tool_call_single_backend(router, mock_client):
    """Test routing when only one backend is available."""
    router.add_backend("lab", mock_client)

    # Tool doesn't follow pattern, but should route to only backend
    backend = router.route_tool_call("ping")
    assert backend == "lab"


def test_route_tool_call_no_pattern_multiple_backends(router_with_backends):
    """Test routing when tool doesn't follow pattern and multiple backends exist."""
    router, _, _ = router_with_backends

    backend = router.route_tool_call("ping")
    assert backend is None


@pytest.mark.asyncio
async def test_send_to_backend_success(router_with_backends):
    """Test sending a message to a specific backend."""
    router, lab_client, _ = router_with_backends

    message = {"method": "test", "params": {}}
    await router.send_to_backend("lab", message)

    lab_client.send.assert_called_once_with(message)


@pytest.mark.asyncio
async def test_send_to_backend_not_found(router_with_backends):
    """Test sending a message to a non-existent backend."""
    router, _, _ = router_with_backends

    message = {"method": "test", "params": {}}

    with pytest.raises(ValueError, match="Backend 'nonexistent' not found"):
        await router.send_to_backend("nonexistent", message)


@pytest.mark.asyncio
async def test_handle_message_tool_call(router_with_backends):
    """Test handling a tool call message."""
    router, lab_client, _ = router_with_backends

    message = {"method": "tools/call", "params": {"name": "qbraid_lab_test_tool"}}

    await router.handle_message(message)

    lab_client.send.assert_called_once_with(message)


@pytest.mark.asyncio
async def test_handle_message_tool_call_no_route(router_with_backends):
    """Test handling a tool call that cannot be routed."""
    router, lab_client, devices_client = router_with_backends

    message = {"method": "tools/call", "params": {"name": "qbraid_unknown_tool"}}

    await router.handle_message(message)

    # Should not send to any backend
    lab_client.send.assert_not_called()
    devices_client.send.assert_not_called()


@pytest.mark.asyncio
async def test_handle_message_tool_call_missing_name(router_with_backends):
    """Test handling a tool call message missing tool name."""
    router, lab_client, devices_client = router_with_backends

    message = {"method": "tools/call", "params": {}}

    await router.handle_message(message)

    # Should not send to any backend
    lab_client.send.assert_not_called()
    devices_client.send.assert_not_called()


@pytest.mark.asyncio
async def test_handle_message_broadcast(router_with_backends):
    """Test broadcasting non-tool-call messages to all backends."""
    router, lab_client, devices_client = router_with_backends

    message = {"method": "initialize", "params": {}}

    await router.handle_message(message)

    lab_client.send.assert_called_once_with(message)
    devices_client.send.assert_called_once_with(message)


@pytest.mark.asyncio
async def test_handle_message_broadcast_with_error(router_with_backends):
    """Test broadcasting when one backend fails."""
    router, lab_client, devices_client = router_with_backends

    # Make lab client raise an error
    lab_client.send.side_effect = Exception("Connection error")

    message = {"method": "initialize", "params": {}}

    # Should not raise, just log the error
    await router.handle_message(message)

    lab_client.send.assert_called_once_with(message)
    devices_client.send.assert_called_once_with(message)


@pytest.mark.asyncio
async def test_handle_message_exception(router_with_backends, monkeypatch):
    """Test handling message when an exception occurs."""
    router, _, _ = router_with_backends

    # Mock route_tool_call to raise an exception
    def mock_route(*args):
        raise Exception("Test error")  # pylint: disable=broad-exception-raised

    monkeypatch.setattr(router, "route_tool_call", mock_route)

    message = {"method": "tools/call", "params": {"name": "test"}}

    # Should not raise, just log the error
    await router.handle_message(message)


@pytest.mark.asyncio
async def test_shutdown_all(router_with_backends):
    """Test shutting down all backends."""
    router, lab_client, devices_client = router_with_backends

    await router.shutdown_all()

    assert router._is_shutting_down is True
    lab_client.shutdown.assert_called_once()
    devices_client.shutdown.assert_called_once()


@pytest.mark.asyncio
async def test_shutdown_all_already_shutting_down(router_with_backends):
    """Test shutting down when already in shutdown state."""
    router, lab_client, devices_client = router_with_backends

    router._is_shutting_down = True

    await router.shutdown_all()

    # Should not call shutdown again
    lab_client.shutdown.assert_not_called()
    devices_client.shutdown.assert_not_called()


def test_get_connected_backends(router_with_backends):
    """Test getting list of connected backends."""
    router, _, _ = router_with_backends

    connected = router.get_connected_backends()

    assert connected == ["lab"]


def test_get_backend_status(router_with_backends):
    """Test getting connection status for all backends."""
    router, _, _ = router_with_backends

    status = router.get_backend_status()

    assert status == {"lab": True, "devices": False}
