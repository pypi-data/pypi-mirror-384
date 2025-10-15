"""
Tests for tool removal features (Phase 2 - v1.2.0)

Tests the new bulk removal, replacement, and conditional removal functions
that leverage MCP SDK v1.17.0's remove_tool() capability.
"""

import pytest
from mcp.server.fastmcp import FastMCP

from mcp_commons.bulk_registration import (
    bulk_register_tools,
    bulk_remove_tools,
    bulk_replace_tools,
    conditional_remove_tools,
    count_tools,
    get_registered_tools,
    tool_exists,
)


# Test fixtures
@pytest.fixture
def mcp_server():
    """Create a fresh FastMCP server for each test."""
    return FastMCP("test-server")


@pytest.fixture
def sample_tools():
    """Sample tool functions for testing."""

    def tool1():
        """Test tool 1"""
        return "result1"

    def tool2():
        """Test tool 2"""
        return "result2"

    def tool3():
        """Test tool 3"""
        return "result3"

    def deprecated_tool():
        """Deprecated test tool"""
        return "deprecated"

    return {
        "tool1": tool1,
        "tool2": tool2,
        "tool3": tool3,
        "deprecated_tool": deprecated_tool,
    }


# ============================================================================
# Helper Function Tests
# ============================================================================


def test_get_registered_tools_empty_server(mcp_server):
    """Test getting tools from empty server."""
    tools = get_registered_tools(mcp_server)
    assert tools == []


def test_get_registered_tools_with_tools(mcp_server, sample_tools):
    """Test getting tools from server with registered tools."""
    # Register some tools
    tools_config = {
        "tool1": {"function": sample_tools["tool1"], "description": "Tool 1"},
        "tool2": {"function": sample_tools["tool2"], "description": "Tool 2"},
    }
    bulk_register_tools(mcp_server, tools_config)

    # Get registered tools
    tools = get_registered_tools(mcp_server)
    assert len(tools) == 2
    assert "tool1" in tools
    assert "tool2" in tools


def test_tool_exists(mcp_server, sample_tools):
    """Test checking if tool exists."""
    # Initially should not exist
    assert not tool_exists(mcp_server, "tool1")

    # Register tool
    tools_config = {
        "tool1": {"function": sample_tools["tool1"], "description": "Tool 1"}
    }
    bulk_register_tools(mcp_server, tools_config)

    # Now should exist
    assert tool_exists(mcp_server, "tool1")
    assert not tool_exists(mcp_server, "nonexistent")


def test_count_tools(mcp_server, sample_tools):
    """Test counting registered tools."""
    # Empty server
    assert count_tools(mcp_server) == 0

    # Register tools
    tools_config = {
        "tool1": {"function": sample_tools["tool1"], "description": "Tool 1"},
        "tool2": {"function": sample_tools["tool2"], "description": "Tool 2"},
        "tool3": {"function": sample_tools["tool3"], "description": "Tool 3"},
    }
    bulk_register_tools(mcp_server, tools_config)

    # Count should match
    assert count_tools(mcp_server) == 3


# ============================================================================
# bulk_remove_tools() Tests
# ============================================================================


def test_bulk_remove_tools_success(mcp_server, sample_tools):
    """Test successful removal of multiple tools."""
    # Register tools
    tools_config = {
        "tool1": {"function": sample_tools["tool1"], "description": "Tool 1"},
        "tool2": {"function": sample_tools["tool2"], "description": "Tool 2"},
        "tool3": {"function": sample_tools["tool3"], "description": "Tool 3"},
    }
    bulk_register_tools(mcp_server, tools_config)
    assert count_tools(mcp_server) == 3

    # Remove tools
    result = bulk_remove_tools(mcp_server, ["tool1", "tool2"])

    # Verify result structure
    assert "removed" in result
    assert "failed" in result
    assert "success_rate" in result

    # Verify successful removal
    assert len(result["removed"]) == 2
    assert "tool1" in result["removed"]
    assert "tool2" in result["removed"]
    assert len(result["failed"]) == 0
    assert result["success_rate"] == 100.0

    # Verify tools are actually removed
    assert count_tools(mcp_server) == 1
    assert not tool_exists(mcp_server, "tool1")
    assert not tool_exists(mcp_server, "tool2")
    assert tool_exists(mcp_server, "tool3")


def test_bulk_remove_tools_partial_failure(mcp_server, sample_tools):
    """Test bulk removal with some failures."""
    # Register tools
    tools_config = {
        "tool1": {"function": sample_tools["tool1"], "description": "Tool 1"},
        "tool2": {"function": sample_tools["tool2"], "description": "Tool 2"},
    }
    bulk_register_tools(mcp_server, tools_config)

    # Try to remove existing and non-existent tools
    result = bulk_remove_tools(mcp_server, ["tool1", "nonexistent", "tool2"])

    # Should have 2 successful, 1 failed
    assert len(result["removed"]) == 2
    assert len(result["failed"]) == 1
    assert result["success_rate"] == pytest.approx(66.67, rel=0.01)

    # Check failed entry
    failed_tool_names = [name for name, _ in result["failed"]]
    assert "nonexistent" in failed_tool_names


def test_bulk_remove_tools_empty_list(mcp_server):
    """Test bulk removal with empty list."""
    result = bulk_remove_tools(mcp_server, [])

    assert result["removed"] == []
    assert result["failed"] == []
    assert result["success_rate"] == 0.0


def test_bulk_remove_tools_all_fail(mcp_server):
    """Test bulk removal where all tools fail to remove."""
    # Try to remove non-existent tools
    result = bulk_remove_tools(mcp_server, ["nonexistent1", "nonexistent2"])

    assert len(result["removed"]) == 0
    assert len(result["failed"]) == 2
    assert result["success_rate"] == 0.0


# ============================================================================
# bulk_replace_tools() Tests
# ============================================================================


def test_bulk_replace_tools_success(mcp_server, sample_tools):
    """Test successful tool replacement."""
    # Register initial tools
    old_tools = {
        "old_tool1": {"function": sample_tools["tool1"], "description": "Old Tool 1"},
        "old_tool2": {"function": sample_tools["tool2"], "description": "Old Tool 2"},
    }
    bulk_register_tools(mcp_server, old_tools)
    assert count_tools(mcp_server) == 2

    # Replace with new tools
    new_tools = {
        "new_tool1": {"function": sample_tools["tool3"], "description": "New Tool 1"},
    }
    result = bulk_replace_tools(mcp_server, ["old_tool1", "old_tool2"], new_tools)

    # Verify result structure
    assert "removed" in result
    assert "added" in result
    assert "removal_failed" in result
    assert "addition_failed" in result
    assert "errors" in result

    # Verify successful replacement
    assert len(result["removed"]) == 2
    assert len(result["added"]) == 1
    assert not result["addition_failed"]
    assert len(result["errors"]) == 0

    # Verify tool state
    assert count_tools(mcp_server) == 1
    assert not tool_exists(mcp_server, "old_tool1")
    assert not tool_exists(mcp_server, "old_tool2")
    assert tool_exists(mcp_server, "new_tool1")


def test_bulk_replace_tools_removal_failure(mcp_server, sample_tools):
    """Test replacement when some removals fail."""
    # Register one tool
    old_tools = {
        "old_tool1": {"function": sample_tools["tool1"], "description": "Old Tool 1"}
    }
    bulk_register_tools(mcp_server, old_tools)

    # Try to remove existing and non-existent, then add new
    new_tools = {
        "new_tool1": {"function": sample_tools["tool2"], "description": "New Tool 1"}
    }
    result = bulk_replace_tools(mcp_server, ["old_tool1", "nonexistent"], new_tools)

    # Should have partial removal, successful addition
    assert len(result["removed"]) == 1
    assert len(result["removal_failed"]) == 1
    assert len(result["added"]) == 1
    assert not result["addition_failed"]
    assert len(result["errors"]) > 0  # Should have error from failed removal


def test_bulk_replace_tools_addition_failure(mcp_server, sample_tools):
    """Test replacement when addition fails."""
    # Register tools
    old_tools = {
        "old_tool1": {"function": sample_tools["tool1"], "description": "Old Tool 1"}
    }
    bulk_register_tools(mcp_server, old_tools)

    # Try to add invalid tools (missing function)
    new_tools = {"new_tool1": {"description": "New Tool 1"}}  # Missing function!

    result = bulk_replace_tools(mcp_server, ["old_tool1"], new_tools)

    # Removal should succeed, addition should fail
    assert len(result["removed"]) == 1
    assert result["addition_failed"]
    assert len(result["errors"]) > 0


def test_bulk_replace_tools_empty_lists(mcp_server):
    """Test replacement with empty lists."""
    result = bulk_replace_tools(mcp_server, [], {})

    assert result["removed"] == []
    assert result["added"] == []
    assert not result["addition_failed"]


# ============================================================================
# conditional_remove_tools() Tests
# ============================================================================


def test_conditional_remove_tools_by_prefix(mcp_server, sample_tools):
    """Test conditional removal by prefix."""
    # Register tools with different prefixes
    tools_config = {
        "test_tool1": {"function": sample_tools["tool1"], "description": "Test Tool 1"},
        "test_tool2": {"function": sample_tools["tool2"], "description": "Test Tool 2"},
        "prod_tool1": {"function": sample_tools["tool3"], "description": "Prod Tool 1"},
    }
    bulk_register_tools(mcp_server, tools_config)
    assert count_tools(mcp_server) == 3

    # Remove all test_ tools
    removed = conditional_remove_tools(
        mcp_server, lambda name: name.startswith("test_")
    )

    # Verify removal
    assert len(removed) == 2
    assert "test_tool1" in removed
    assert "test_tool2" in removed
    assert count_tools(mcp_server) == 1
    assert tool_exists(mcp_server, "prod_tool1")


def test_conditional_remove_tools_by_keyword(mcp_server, sample_tools):
    """Test conditional removal by keyword in name."""
    # Register tools
    tools_config = {
        "tool1": {"function": sample_tools["tool1"], "description": "Tool 1"},
        "deprecated_tool": {
            "function": sample_tools["deprecated_tool"],
            "description": "Deprecated Tool",
        },
        "tool2": {"function": sample_tools["tool2"], "description": "Tool 2"},
    }
    bulk_register_tools(mcp_server, tools_config)

    # Remove deprecated tools
    removed = conditional_remove_tools(
        mcp_server, lambda name: "deprecated" in name.lower()
    )

    # Verify removal
    assert len(removed) == 1
    assert "deprecated_tool" in removed
    assert count_tools(mcp_server) == 2


def test_conditional_remove_tools_no_matches(mcp_server, sample_tools):
    """Test conditional removal when no tools match."""
    # Register tools
    tools_config = {
        "tool1": {"function": sample_tools["tool1"], "description": "Tool 1"},
        "tool2": {"function": sample_tools["tool2"], "description": "Tool 2"},
    }
    bulk_register_tools(mcp_server, tools_config)

    # Try to remove with non-matching condition
    removed = conditional_remove_tools(
        mcp_server, lambda name: name.startswith("nonexistent_")
    )

    # No tools should be removed
    assert removed == []
    assert count_tools(mcp_server) == 2


def test_conditional_remove_tools_all_match(mcp_server, sample_tools):
    """Test conditional removal when all tools match."""
    # Register tools
    tools_config = {
        "tool1": {"function": sample_tools["tool1"], "description": "Tool 1"},
        "tool2": {"function": sample_tools["tool2"], "description": "Tool 2"},
        "tool3": {"function": sample_tools["tool3"], "description": "Tool 3"},
    }
    bulk_register_tools(mcp_server, tools_config)

    # Remove all tools (condition always True)
    removed = conditional_remove_tools(mcp_server, lambda name: True)

    # All tools should be removed
    assert len(removed) == 3
    assert count_tools(mcp_server) == 0


def test_conditional_remove_tools_complex_condition(mcp_server, sample_tools):
    """Test conditional removal with complex condition."""
    # Register tools
    tools_config = {
        "api_v1_get": {"function": sample_tools["tool1"], "description": "API v1 Get"},
        "api_v1_post": {
            "function": sample_tools["tool2"],
            "description": "API v1 Post",
        },
        "api_v2_get": {"function": sample_tools["tool3"], "description": "API v2 Get"},
    }
    bulk_register_tools(mcp_server, tools_config)

    # Remove v1 API tools only
    removed = conditional_remove_tools(mcp_server, lambda name: "api_v1" in name)

    # Verify removal
    assert len(removed) == 2
    assert "api_v1_get" in removed
    assert "api_v1_post" in removed
    assert count_tools(mcp_server) == 1
    assert tool_exists(mcp_server, "api_v2_get")


# ============================================================================
# Integration Tests
# ============================================================================


def test_full_lifecycle_workflow(mcp_server, sample_tools):
    """Test complete tool lifecycle: register, check, remove, verify."""
    # Phase 1: Register initial tools
    initial_tools = {
        "tool1": {"function": sample_tools["tool1"], "description": "Tool 1"},
        "tool2": {"function": sample_tools["tool2"], "description": "Tool 2"},
    }
    bulk_register_tools(mcp_server, initial_tools)

    # Verify registration
    assert count_tools(mcp_server) == 2
    assert tool_exists(mcp_server, "tool1")
    assert tool_exists(mcp_server, "tool2")

    # Phase 2: Add more tools
    additional_tools = {
        "tool3": {"function": sample_tools["tool3"], "description": "Tool 3"}
    }
    bulk_register_tools(mcp_server, additional_tools)
    assert count_tools(mcp_server) == 3

    # Phase 3: Remove one tool
    result = bulk_remove_tools(mcp_server, ["tool1"])
    assert len(result["removed"]) == 1
    assert count_tools(mcp_server) == 2

    # Phase 4: Replace remaining tools
    new_tools = {
        "new_tool": {"function": sample_tools["tool1"], "description": "New Tool"}
    }
    result = bulk_replace_tools(mcp_server, ["tool2", "tool3"], new_tools)
    assert len(result["removed"]) == 2
    assert len(result["added"]) == 1
    assert count_tools(mcp_server) == 1
    assert tool_exists(mcp_server, "new_tool")


def test_error_handling_consistency(mcp_server):
    """Test that error handling is consistent across functions."""
    # Test removing non-existent tool
    result1 = bulk_remove_tools(mcp_server, ["nonexistent"])
    assert len(result1["failed"]) == 1
    assert result1["success_rate"] == 0.0

    # Test replacing with non-existent removal
    result2 = bulk_replace_tools(mcp_server, ["nonexistent"], {})
    assert len(result2["removal_failed"]) == 1
    assert len(result2["errors"]) > 0

    # Test conditional removal with no matches
    removed = conditional_remove_tools(mcp_server, lambda name: False)
    assert removed == []
