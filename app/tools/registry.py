#!/usr/bin/env python3
"""
Tool registry system for Budget Cash Envelope MCP Server.
This module provides a scalable way to register and dispatch tools.
"""

import json
from collections.abc import Callable
from typing import Any

import mcp.types as types
from fastmcp import FastMCP

from app.services.envelope_service import EnvelopeService
from app.services.transaction_service import TransactionService
from app.tools import handlers
from app.tools.handlers import HandlerResponse
from app.tools.schemas import get_all_tool_schemas


class ToolRegistry:
    """Registry for managing tool definitions and handlers."""

    def __init__(
        self,
        envelope_service: EnvelopeService,
        transaction_service: TransactionService,
    ):
        self.envelope_service = envelope_service
        self.transaction_service = transaction_service
        self._tools: dict[str, dict[str, Any]] = {}
        self._handlers: dict[str, Callable] = {}
        self._register_all_tools()

    def _register_all_tools(self) -> None:
        """Register all tools with their handlers."""
        schemas = get_all_tool_schemas()

        # Envelope tools
        envelope_tools = [
            "create_envelope",
            "list_envelopes",
            "get_envelope",
            "update_envelope",
            "delete_envelope",
        ]

        for tool_name in envelope_tools:
            self._tools[tool_name] = schemas[tool_name]
            handler_name = f"handle_{tool_name}"
            self._handlers[tool_name] = getattr(handlers, handler_name)

        # Transaction tools
        transaction_tools = [
            "create_transaction",
            "list_transactions",
            "get_transaction",
            "update_transaction",
            "delete_transaction",
        ]

        for tool_name in transaction_tools:
            self._tools[tool_name] = schemas[tool_name]
            handler_name = f"handle_{tool_name}"
            self._handlers[tool_name] = getattr(handlers, handler_name)

        # Utility tools
        utility_tools = [
            "get_envelope_balance",
            "get_budget_summary",
            "get_cloud_status",
            "sync_to_cloud",
            "sync_from_cloud",
        ]

        for tool_name in utility_tools:
            self._tools[tool_name] = schemas[tool_name]
            handler_name = f"handle_{tool_name}"
            self._handlers[tool_name] = getattr(handlers, handler_name)

    def get_tool_list(self) -> list[str]:
        """Get list of all registered tool names."""
        return list(self._tools.keys())

    def get_tool_schema(self, tool_name: str) -> dict[str, Any]:
        """Get schema for a specific tool."""
        if tool_name not in self._tools:
            raise ValueError(f"Unknown tool: {tool_name}")
        return self._tools[tool_name]

    def get_all_tool_schemas(self) -> dict[str, dict[str, Any]]:
        """Get all tool schemas."""
        return self._tools

    async def call_tool(
        self, tool_name: str, arguments: dict[str, Any]
    ) -> HandlerResponse:
        """Call a tool handler."""
        if tool_name not in self._handlers:
            raise ValueError(f"Unknown tool: {tool_name}")

        handler = self._handlers[tool_name]

        # Determine which service to use based on tool category
        if tool_name in [
            "create_envelope",
            "list_envelopes",
            "get_envelope",
            "update_envelope",
            "delete_envelope",
            "get_envelope_balance",
            "get_budget_summary",
            "get_cloud_status",
            "sync_to_cloud",
            "sync_from_cloud",
        ]:
            return await handler(self.envelope_service, arguments)
        else:
            return await handler(self.transaction_service, arguments)


class MCPToolAdapter:
    """Adapter for MCP Python SDK tools."""

    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    def get_mcp_tools(self) -> list[types.Tool]:
        """Get tools in MCP SDK format."""
        mcp_tools = []
        for tool_name, schema in self.registry.get_all_tool_schemas().items():
            tool = types.Tool(
                name=schema["name"],
                description=schema["description"],
                inputSchema=schema["inputSchema"],
            )
            mcp_tools.append(tool)
        return mcp_tools

    async def handle_tool_call(
        self, name: str, arguments: dict[str, Any]
    ) -> list[types.Content]:
        """Handle tool call for MCP SDK."""
        result = await self.registry.call_tool(name, arguments)

        # Format result as MCP content
        if isinstance(result, dict | list):
            text = json.dumps(result, indent=2)
        else:
            text = str(result)

        return [types.TextContent(type="text", text=text)]


class FastMCPToolAdapter:
    """Adapter for FastMCP tools."""

    def __init__(self, registry: ToolRegistry):
        self.registry = registry

    def register_tools_with_fastmcp(self, mcp: FastMCP) -> None:
        """Register all tools with FastMCP server."""

        for tool_name, schema in self.registry.get_all_tool_schemas().items():
            self._register_single_tool(mcp, tool_name, schema)

    def _register_single_tool(
        self, mcp: FastMCP, tool_name: str, schema: dict[str, Any]
    ) -> None:
        """Register a single tool with FastMCP."""

        async def tool_handler(**kwargs: Any) -> str:
            """Generic tool handler for FastMCP."""
            result = await self.registry.call_tool(tool_name, kwargs)

            if isinstance(result, dict | list):
                return json.dumps(result, indent=2)
            return str(result)

        # Register the tool with FastMCP using the correct API
        mcp.tool(
            description=schema["description"],
        )(tool_handler)


def create_tool_registry(
    envelope_service: EnvelopeService,
    transaction_service: TransactionService,
) -> ToolRegistry:
    """Factory function to create a tool registry."""
    return ToolRegistry(envelope_service, transaction_service)


def create_mcp_adapter(registry: ToolRegistry) -> MCPToolAdapter:
    """Factory function to create MCP adapter."""
    return MCPToolAdapter(registry)


def create_fastmcp_adapter(registry: ToolRegistry) -> FastMCPToolAdapter:
    """Factory function to create FastMCP adapter."""
    return FastMCPToolAdapter(registry)
