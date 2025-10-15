"""
Tests to verify compatibility with MCP SDK v1.17.0 features.

These tests ensure mcp-commons works correctly with the new SDK version
and validate that v1.17.0 features are available even if not yet exposed
in the mcp-commons public API.
"""

import pytest
from mcp.server.fastmcp import FastMCP
from mcp.shared.memory import create_connected_server_and_client_session


class TestMCPSDKv117Compatibility:
    """Test compatibility with MCP SDK v1.17.0 features"""

    def test_fastmcp_has_remove_tool_method(self):
        """Verify that FastMCP has the remove_tool method from v1.17.0"""
        mcp = FastMCP("test-server")

        # Add a test tool
        @mcp.tool()
        def test_tool() -> str:
            """A test tool"""
            return "test"

        # Verify remove_tool method exists
        assert hasattr(mcp, "remove_tool"), "FastMCP should have remove_tool method"
        assert callable(mcp.remove_tool), "remove_tool should be callable"

        # Test removal works
        mcp.remove_tool("test_tool")

    def test_tool_removal_raises_on_nonexistent_tool(self):
        """Verify that removing non-existent tool raises appropriate error"""
        mcp = FastMCP("test-server")

        # Attempting to remove non-existent tool should raise an exception
        # The specific exception type may vary, so we catch the base Exception
        with pytest.raises(Exception):  # noqa: B017
            mcp.remove_tool("nonexistent_tool")

    @pytest.mark.asyncio
    async def test_in_memory_transport_available(self):
        """Verify that create_connected_server_and_client_session is available"""

        # Create a simple server
        server = FastMCP("test-server")

        @server.tool()
        def simple_tool() -> str:
            """A simple test tool"""
            return "Hello from test"

        # Verify we can create connected session (returns ClientSession)
        async with create_connected_server_and_client_session(server) as client_session:
            assert client_session is not None
            # Verify it's a ClientSession with expected attributes
            assert hasattr(client_session, "call_tool")


class TestBackwardCompatibility:
    """Ensure v1.17.0 doesn't break existing mcp-commons functionality"""

    def test_bulk_registration_still_works(self):
        """Verify bulk_register_tools works with v1.17.0"""
        from mcp_commons import bulk_register_tools

        mcp = FastMCP("test-server")

        def tool1() -> str:
            return "tool1"

        def tool2() -> str:
            return "tool2"

        tools_config = {
            "tool1": {"function": tool1, "description": "First tool"},
            "tool2": {"function": tool2, "description": "Second tool"},
        }

        # Should work without errors
        registered = bulk_register_tools(mcp, tools_config)

        assert len(registered) == 2
        assert ("tool1", "First tool") in registered
        assert ("tool2", "Second tool") in registered

    def test_mcp_adapter_still_works(self):
        """Verify create_mcp_adapter works with v1.17.0"""
        from mcp_commons import UseCaseResult, create_mcp_adapter

        async def sample_use_case() -> UseCaseResult:
            return UseCaseResult.success_with_data({"message": "test"})

        # Should create adapter without errors
        adapted = create_mcp_adapter(sample_use_case)

        assert callable(adapted)
        assert adapted.__name__ == sample_use_case.__name__
