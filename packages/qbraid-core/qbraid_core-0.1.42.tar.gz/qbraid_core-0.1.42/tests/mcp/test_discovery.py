# Copyright (c) 2025, qBraid Development Team
# All rights reserved.

# pylint: disable=redefined-outer-name

"""
Unit tests for MCP discovery module.

"""
from qbraid_core.services.mcp.discovery import (
    KNOWN_MCP_ENDPOINTS,
    MCPServerEndpoint,
    discover_mcp_servers,
    get_mcp_endpoint,
)


def test_mcp_server_endpoint_build_url():
    """Test building WebSocket URLs from MCPServerEndpoint."""
    endpoint = MCPServerEndpoint(
        name="lab",
        base_url="https://lab.qbraid.com",
        path_template="/user/{username}/mcp/mcp",
        requires_token=True,
        description="Test endpoint",
    )

    # Test with token
    url = endpoint.build_url("user@example.com", "abc123")
    assert url == "wss://lab.qbraid.com/user/user@example.com/mcp/mcp?token=abc123"

    # Test without token
    url_no_token = endpoint.build_url("user@example.com")
    assert url_no_token == "wss://lab.qbraid.com/user/user@example.com/mcp/mcp"


def test_mcp_server_endpoint_build_url_http():
    """Test building WebSocket URLs from HTTP base URL."""
    endpoint = MCPServerEndpoint(
        name="test",
        base_url="http://localhost:8000",
        path_template="/mcp",
        requires_token=False,
    )

    url = endpoint.build_url("testuser")
    assert url == "ws://localhost:8000/mcp"


def test_mcp_server_endpoint_build_url_ws():
    """Test building WebSocket URLs when base URL is already WebSocket."""
    endpoint = MCPServerEndpoint(
        name="test",
        base_url="wss://example.com",
        path_template="/mcp",
        requires_token=False,
    )

    url = endpoint.build_url("testuser")
    assert url == "wss://example.com/mcp"


def test_discover_mcp_servers_lab():
    """Test discovering MCP servers for lab workspace."""
    endpoints = discover_mcp_servers(workspace="lab", include_staging=False)

    assert len(endpoints) > 0
    assert all(endpoint.name.startswith("lab") for endpoint in endpoints)
    assert all("staging" not in endpoint.name for endpoint in endpoints)


def test_discover_mcp_servers_lab_staging():
    """Test discovering MCP servers for lab staging workspace."""
    endpoints = discover_mcp_servers(workspace="lab", include_staging=True)

    assert len(endpoints) > 0
    assert all(endpoint.name.startswith("lab") for endpoint in endpoints)
    assert all("staging" in endpoint.name for endpoint in endpoints)


def test_discover_mcp_servers_no_match():
    """Test discovering MCP servers with no matching workspace."""
    endpoints = discover_mcp_servers(workspace="nonexistent", include_staging=False)

    assert len(endpoints) == 0


def test_get_mcp_endpoint_found():
    """Test getting a specific MCP endpoint by name."""
    # Get the first known endpoint name
    if KNOWN_MCP_ENDPOINTS:
        known_name = KNOWN_MCP_ENDPOINTS[0].name
        endpoint = get_mcp_endpoint(known_name)

        assert endpoint is not None
        assert endpoint.name == known_name


def test_get_mcp_endpoint_not_found():
    """Test getting a non-existent MCP endpoint."""
    endpoint = get_mcp_endpoint("nonexistent-endpoint")

    assert endpoint is None


def test_known_mcp_endpoints_structure():
    """Test that KNOWN_MCP_ENDPOINTS has correct structure."""
    assert isinstance(KNOWN_MCP_ENDPOINTS, list)
    assert len(KNOWN_MCP_ENDPOINTS) > 0

    for endpoint in KNOWN_MCP_ENDPOINTS:
        assert isinstance(endpoint, MCPServerEndpoint)
        assert hasattr(endpoint, "name")
        assert hasattr(endpoint, "base_url")
        assert hasattr(endpoint, "path_template")
        assert hasattr(endpoint, "requires_token")
