"""
MCP Commons - Shared infrastructure for MCP servers.

This library provides reusable components for building MCP (Model Context Protocol) servers,
eliminating boilerplate and ensuring consistency across server implementations.
"""

from .adapters import AdapterStats, create_mcp_adapter, validate_use_case_result
from .base import BaseUseCase, UseCaseResult
from .bulk_registration import (
    BulkRegistrationError,
    bulk_register_tools,
    bulk_register_tuple_format,
    bulk_register_with_adapter_pattern,
    bulk_remove_tools,
    bulk_replace_tools,
    conditional_remove_tools,
    count_tools,
    get_registered_tools,
    log_registration_summary,
    register_tools,
    tool_exists,
    validate_tools_config,
)
from .config import ConfigurationError, MCPConfig, create_config, load_dotenv_file
from .exceptions import AdapterError, McpCommonsError, UseCaseError
from .server import (
    MCPServerBuilder,
    create_mcp_app,
    print_mcp_help,
    run_mcp_server,
    setup_logging,
)

__version__ = "1.2.2"
__all__ = [
    # Core adapter functionality
    "create_mcp_adapter",
    "validate_use_case_result",
    "AdapterStats",
    # Base classes
    "UseCaseResult",
    "BaseUseCase",
    # Bulk registration functionality
    "bulk_register_tools",
    "bulk_register_with_adapter_pattern",
    "bulk_register_tuple_format",
    "log_registration_summary",
    "validate_tools_config",
    "register_tools",
    "BulkRegistrationError",
    # Tool removal functionality (Phase 2 - v1.2.0)
    "bulk_remove_tools",
    "bulk_replace_tools",
    "conditional_remove_tools",
    "get_registered_tools",
    "tool_exists",
    "count_tools",
    # Server utilities
    "MCPServerBuilder",
    "setup_logging",
    "run_mcp_server",
    "create_mcp_app",
    "print_mcp_help",
    # Configuration management
    "MCPConfig",
    "ConfigurationError",
    "create_config",
    "load_dotenv_file",
    # Exceptions
    "McpCommonsError",
    "UseCaseError",
    "AdapterError",
]
