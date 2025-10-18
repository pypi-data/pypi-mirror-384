# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

"""
Unit tests for MCP __init__ module.

"""
from qbraid_core.services.mcp import MCPRouter, MCPWebSocketClient, discover_mcp_servers


def test_imports():
    """Test that all exports are accessible."""
    assert MCPWebSocketClient is not None
    assert discover_mcp_servers is not None
    assert MCPRouter is not None


def test_mcp_websocket_client_class():
    """Test MCPWebSocketClient is a class."""
    assert callable(MCPWebSocketClient)


def test_discover_mcp_servers_function():
    """Test discover_mcp_servers is a function."""
    assert callable(discover_mcp_servers)


def test_mcp_router_class():
    """Test MCPRouter is a class."""
    assert callable(MCPRouter)
