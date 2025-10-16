# MCP Commons

> A Python library providing reusable infrastructure for building Model Context Protocol (MCP) servers with less boilerplate and consistent patterns.

[![PyPI version](https://badge.fury.io/py/mcp-commons.svg)](https://pypi.org/project/mcp-commons/)
[![Python versions](https://img.shields.io/pypi/pyversions/mcp-commons.svg)](https://pypi.org/project/mcp-commons/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

MCP Commons provides architectural patterns for building maintainable MCP servers:

**Primary Value (90%)**:
- **Adapter Pattern** - Decouple business logic from MCP protocol for multi-interface reuse
- **UseCaseResult** - Consistent error handling pattern across all operations

**Convenience Features (10%)**:
- **Bulk Operations** - Config-driven tool registration with error reporting
- **Tool Lifecycle** - Batch operations over FastMCP's add_tool() and remove_tool()

**Built on FastMCP**: mcp-commons is a thin wrapper over FastMCP's existing methods. It doesn't replace FastMCP's capabilities - it provides architectural patterns and convenience wrappers to make your code more maintainable.

**Current Version**: 1.2.1 | [What's New](#whats-new-in-v121) | [Changelog](CHANGELOG.md)

---

## Why mcp-commons Exists

### The Problem with Decorators

The MCP SDK uses decorators (`@server.tool()`) to register functions as tools. While the goal of making function exposure easy was admirable, **decorators were the wrong mechanism** for this purpose.

**Decorators should add cross-cutting concerns** (caching, authentication, logging) that apply regardless of how a function is used. They should not specify usage contexts (MCP vs REST vs CLI).

```python
# ❌ PROBLEM: Function is now ONLY usable in MCP context
from mcp.server.fastmcp import FastMCP

server = FastMCP("my-server")

@server.tool()
async def search_documents(query: str) -> dict:
    """This function is tied to MCP - can't reuse for REST, CLI, or testing."""
    results = await document_service.search(query)
    return {"results": results}

# Can't use this function in:
# - REST API endpoints
# - CLI commands  
# - GraphQL resolvers
# - Unit tests (without MCP context)
```

### The Solution: Adapter Pattern

**Adapter/wrapper functions** provide the same ease of use while maintaining proper separation of concerns. Your business logic stays pure and framework-agnostic, while thin adapters handle protocol translation.

```python
# ✅ SOLUTION: Pure business logic, reusable everywhere
async def search_documents(query: str) -> List[Document]:
    """Pure function - no MCP coupling, works anywhere."""
    return await document_service.search(query)

# MCP adapter - thin wrapper for protocol translation
@server.tool()
async def mcp_search(query: str) -> dict:
    results = await search_documents(query)
    return {"results": [doc.to_dict() for doc in results]}

# REST API - reuses same logic
@app.get("/api/search")
async def api_search(query: str):
    results = await search_documents(query)
    return {"results": [doc.to_dict() for doc in results]}

# CLI - reuses same logic
@cli.command()
def cli_search(query: str):
    results = asyncio.run(search_documents(query))
    for doc in results:
        print(f"- {doc.title}")

# Testing - pure function, no framework needed
async def test_search():
    results = await search_documents("test query")
    assert len(results) > 0
```

### Architectural Benefits

This adapter pattern enables:

1. **DRY Principle** - One business function, multiple interfaces
2. **Separation of Concerns** - Business logic independent of transport
3. **Framework Independence** - No coupling to MCP SDK, FastAPI, Click, etc.
4. **Easy Testing** - Test pure functions without framework context
5. **Future-Proof** - When MCP SDK v2.0 changes, only adapters need updates

**mcp-commons exists because the MCP SDK got this fundamental design decision wrong.** The adapter pattern isn't "nice to have" - it's essential for proper architecture in any non-trivial application.

---

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Core Features](#core-features)
  - [Tool Adapters](#tool-adapters)
  - [Bulk Registration](#bulk-registration)
  - [Tool Management (v1.2.0)](#tool-management-v120)
- [Advanced Usage](#advanced-usage)
- [API Reference](#api-reference)
- [Contributing](#contributing)
- [License](#license)

---

## Installation

### Requirements

- **Python**: 3.11+ (3.13 recommended)
- **MCP SDK**: 1.17.0+
- **Dependencies**: Pydantic 2.11.9+, PyYAML 6.0.3+

### Install from PyPI

```bash
pip install mcp-commons
```

### Install for Development

```bash
git clone https://github.com/dawsonlp/mcp-commons.git
cd mcp-commons
pip install -e ".[dev]"
```

---

## What FastMCP Provides vs What mcp-commons Adds

| Feature | FastMCP (SDK) | mcp-commons |
|---------|---------------|-------------|
| **Tool registration** | `server.add_tool(func, name, desc)` | Config-driven bulk wrapper |
| **Tool removal** | `server.remove_tool(name)` (v1.17.0+) | Batch wrapper with reporting |
| **Decorators** | `@server.tool()` decorator | ❌ We don't use decorators |
| **Adapter pattern** | ❌ Not provided | ✅ Core feature - decouples logic |
| **UseCaseResult** | ❌ Not provided | ✅ Consistent error handling |
| **Error reporting** | Exceptions on failure | Success/failure batch reports |
| **Tool managers** | ToolManager, ResourceManager, etc. | ✅ We use FastMCP's managers |

**Key Point**: mcp-commons doesn't replace FastMCP - it builds on it. We use FastMCP's `add_tool()` and `remove_tool()` methods internally, adding convenience wrappers and architectural patterns on top.

---

## Quick Start

### 1. Basic Adapter Pattern

Convert your async functions to MCP tools:

```python
from mcp_commons import create_mcp_adapter, UseCaseResult
from mcp.server.fastmcp import FastMCP

# Create MCP server
server = FastMCP("my-server")

# Your business logic
async def search_documents(query: str, limit: int = 10) -> UseCaseResult:
    """Search documents with natural language query."""
    results = await document_service.search(query, limit)
    return UseCaseResult.success_with_data({
        "results": results,
        "count": len(results)
    })

# Register as MCP tool (adapter handles conversion automatically)
@server.tool()
async def search(query: str, limit: int = 10) -> dict:
    adapter = create_mcp_adapter(search_documents)
    return await adapter(query=query, limit=limit)
```

### 2. Bulk Registration

Register multiple tools at once:

```python
from mcp_commons import bulk_register_tools

# Define tool configurations
tools_config = {
    "list_projects": {
        "function": list_projects_handler,
        "description": "List all projects"
    },
    "create_project": {
        "function": create_project_handler,
        "description": "Create a new project"
    },
    "delete_project": {
        "function": delete_project_handler,
        "description": "Delete a project by ID"
    }
}

# Register all at once with consistent error handling
registered = bulk_register_tools(server, tools_config)
print(f"Registered {len(registered)} tools")
```

### 3. Tool Management (v1.2.0)

Dynamically manage tools at runtime:

```python
from mcp_commons import (
    bulk_remove_tools,
    bulk_replace_tools,
    get_registered_tools,
    tool_exists
)

# Check what tools exist
all_tools = get_registered_tools(server)
print(f"Currently registered: {all_tools}")

# Remove deprecated tools
result = bulk_remove_tools(server, ["old_tool1", "old_tool2"])
print(f"Removed {len(result['removed'])} tools")

# Hot-reload: replace tools atomically
result = bulk_replace_tools(
    server,
    tools_to_remove=["v1_search"],
    tools_to_add={
        "v2_search": {
            "function": improved_search,
            "description": "Enhanced search with filters"
        }
    }
)
```

---

## Core Features

### Tool Adapters

The adapter pattern automatically handles the conversion between your business logic and MCP tool format.

#### Basic Usage

```python
from mcp_commons import create_mcp_adapter, UseCaseResult

async def calculate_metrics(dataset_id: str) -> UseCaseResult:
    """Calculate metrics for a dataset."""
    try:
        data = await load_dataset(dataset_id)
        metrics = compute_metrics(data)
        return UseCaseResult.success_with_data(metrics)
    except DatasetNotFoundError as e:
        return UseCaseResult.failure(f"Dataset not found: {e}")
    except Exception as e:
        return UseCaseResult.failure(f"Calculation failed: {e}")

# Create adapter
adapted = create_mcp_adapter(calculate_metrics)

# Use in MCP server
@server.tool()
async def metrics(dataset_id: str) -> dict:
    return await adapted(dataset_id=dataset_id)
```

#### Error Handling

Adapters provide consistent error responses:

```python
# Success response
UseCaseResult.success_with_data({"status": "completed", "value": 42})
# Returns: {"success": True, "data": {...}, "error": None}

# Failure response  
UseCaseResult.failure("Invalid input parameters")
# Returns: {"success": False, "data": None, "error": "Invalid input parameters"}
```

### Bulk Registration

Convenience wrappers over FastMCP's `add_tool()` method for config-driven registration:

**What it actually does**:
```python
# mcp-commons bulk_register_tools() is essentially:
for tool_name, config in tools_config.items():
    server.add_tool(  # ← FastMCP's existing method
        config["function"],
        name=tool_name,
        description=config["description"]
    )
# Plus: error handling, logging, and success/failure reporting
```

**Why use it**: Config-driven API + batch error handling instead of manual loops.

#### Configuration Dictionary

```python
tools_config = {
    "tool_name": {
        "function": async_function,
        "description": "Tool description",
        # Optional metadata
    }
}

registered = bulk_register_tools(server, tools_config)
```

#### Tuple Format (Simple)

```python
from mcp_commons import bulk_register_tuple_format

tools = [
    ("list_items", list_items_function),
    ("get_item", get_item_function),
    ("create_item", create_item_function),
]

bulk_register_tuple_format(server, tools)
```

#### With Adapter Pattern

```python
from mcp_commons import bulk_register_with_adapter_pattern

# All functions return UseCaseResult
use_cases = {
    "validate_data": validate_data_use_case,
    "process_data": process_data_use_case,
    "export_data": export_data_use_case,
}

bulk_register_with_adapter_pattern(
    server,
    use_cases,
    adapter_function=create_mcp_adapter
)
```

### Tool Management (v1.2.0)

New in version 1.2.0: Convenience wrappers for batch tool operations.

**What it actually does**: Loops over FastMCP's `remove_tool()` method (added in SDK v1.17.0) with error reporting:
```python
# mcp-commons bulk_remove_tools() is essentially:
for tool_name in tool_names:
    try:
        server.remove_tool(tool_name)  # ← FastMCP's method (v1.17.0+)
        removed.append(tool_name)
    except Exception as e:
        failed.append((tool_name, str(e)))
# Returns: {"removed": [...], "failed": [...], "success_rate": 66.7}
```

**Why use it**: Batch operations + detailed success/failure reporting instead of manual loops.

#### Remove Tools

```python
from mcp_commons import bulk_remove_tools

# Remove multiple tools
result = bulk_remove_tools(server, ["deprecated_tool1", "deprecated_tool2"])

# Check results
print(f"Removed: {result['removed']}")
print(f"Failed: {result['failed']}")
print(f"Success rate: {result['success_rate']:.1f}%")
```

#### Replace Tools (Hot Reload)

```python
from mcp_commons import bulk_replace_tools

# Atomically swap old tools for new ones
result = bulk_replace_tools(
    server,
    tools_to_remove=["old_search", "old_filter"],
    tools_to_add={
        "new_search": {
            "function": enhanced_search,
            "description": "Improved search with AI"
        },
        "new_filter": {
            "function": enhanced_filter,
            "description": "Advanced filtering"
        }
    }
)
```

#### Conditional Removal

```python
from mcp_commons import conditional_remove_tools

# Remove tools matching a pattern
removed = conditional_remove_tools(
    server,
    lambda name: name.startswith("test_") or "deprecated" in name.lower()
)
print(f"Cleaned up {len(removed)} tools")
```

#### Tool Inspection

```python
from mcp_commons import get_registered_tools, tool_exists, count_tools

# List all tools
tools = get_registered_tools(server)
print(f"Available tools: {tools}")

# Check specific tool
if tool_exists(server, "search_documents"):
    print("Search tool is available")

# Get count
total = count_tools(server)
print(f"Total tools registered: {total}")
```

---

## Advanced Usage

### Custom Error Handlers

```python
from mcp_commons import create_mcp_adapter

def custom_success_handler(result):
    """Custom formatting for successful results."""
    return {
        "status": "success",
        "payload": result.data,
        "timestamp": datetime.now().isoformat()
    }

def custom_error_handler(result):
    """Custom formatting for errors."""
    return {
        "status": "error",
        "message": result.error,
        "timestamp": datetime.now().isoformat()
    }

adapted = create_mcp_adapter(
    my_function,
    success_handler=custom_success_handler,
    error_handler=custom_error_handler
)
```

### Validation and Logging

```python
from mcp_commons import validate_tools_config, log_registration_summary

# Validate before registering
try:
    validate_tools_config(tools_config)
except ValueError as e:
    print(f"Invalid configuration: {e}")
    
# Register with logging
registered = bulk_register_tools(server, tools_config)
log_registration_summary(registered, len(tools_config), "MyServer")
```

### Testing Your Tools

```python
import pytest
from mcp_commons import create_mcp_adapter, UseCaseResult

@pytest.mark.asyncio
async def test_search_tool():
    """Test search tool with adapter."""
    async def mock_search(query: str) -> UseCaseResult:
        return UseCaseResult.success_with_data({"results": ["doc1", "doc2"]})
    
    adapted = create_mcp_adapter(mock_search)
    result = await adapted(query="test")
    
    assert result["success"] is True
    assert len(result["data"]["results"]) == 2
```

---

## API Reference

### Core Functions

#### `create_mcp_adapter()`
Converts an async function to an MCP-compatible tool adapter.

**Parameters:**
- `use_case` (callable): Async function returning `UseCaseResult`
- `success_handler` (callable, optional): Custom success formatter
- `error_handler` (callable, optional): Custom error formatter

**Returns:** Async callable compatible with MCP tools

---

#### `bulk_register_tools()`
Registers multiple tools from a configuration dictionary.

**Parameters:**
- `server` (FastMCP): MCP server instance
- `tools_config` (dict): Tool configurations

**Returns:** List of (tool_name, description) tuples

---

#### `bulk_remove_tools()` *(v1.2.0)*
Removes multiple tools from a running server.

**Parameters:**
- `server` (FastMCP): MCP server instance
- `tool_names` (list[str]): Names of tools to remove

**Returns:** Dictionary with `removed`, `failed`, and `success_rate` keys

---

#### `bulk_replace_tools()` *(v1.2.0)*
Atomically replaces tools for hot-reloading.

**Parameters:**
- `server` (FastMCP): MCP server instance
- `tools_to_remove` (list[str]): Tools to remove
- `tools_to_add` (dict): New tools to add

**Returns:** Dictionary with operation results

---

For complete API documentation, see [API Reference](https://github.com/dawsonlp/mcp-commons/wiki/API-Reference).

---

## What's New in v1.2.1

### Documentation Improvements
- ✅ Professional-grade README with comprehensive examples
- ✅ Complete CONTRIBUTING.md guide for contributors  
- ✅ Enhanced API reference documentation
- ✅ Version badges and professional formatting
- ✅ Clear information hierarchy and navigation

This is a documentation-only release. All v1.2.0 features remain unchanged.

---

## What's New in v1.2.0

### Tool Lifecycle Management
- ✅ `bulk_remove_tools()` - Remove multiple tools with reporting
- ✅ `bulk_replace_tools()` - Atomic tool replacement for hot-reload
- ✅ `conditional_remove_tools()` - Pattern-based tool removal
- ✅ `get_registered_tools()`, `tool_exists()`, `count_tools()` - Tool inspection utilities

### Quality Improvements
- ✅ All 42 tests passing (19 new tests for tool removal)
- ✅ Enhanced testing with MCP SDK v1.17.0 features
- ✅ Comprehensive documentation and examples

### Breaking Changes
None - all features are additive and backward compatible.

See [CHANGELOG.md](CHANGELOG.md) for complete version history.

---

## Roadmap

Future development is planned across multiple phases:

- **Phase 3 (v1.3.0)**: Enhanced error handling and observability
- **Phase 4 (v1.4.0)**: Performance optimization and caching
- **Phase 5 (v1.5.0)**: Advanced features and integrations

See [ROADMAP.md](ROADMAP.md) for detailed plans.

---

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Setup

```bash
# Clone repository
git clone https://github.com/dawsonlp/mcp-commons.git
cd mcp-commons

# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run linting
black src/ tests/
isort src/ tests/
ruff check src/ tests/
```

---

## Support

- 📖 **Documentation**: [GitHub Wiki](https://github.com/dawsonlp/mcp-commons/wiki)
- 🐛 **Issues**: [GitHub Issues](https://github.com/dawsonlp/mcp-commons/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/dawsonlp/mcp-commons/discussions)

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Acknowledgments

Built with the [Model Context Protocol](https://modelcontextprotocol.io/) by Anthropic.
