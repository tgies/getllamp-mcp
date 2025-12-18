"""
getllamp MCP Server - Jericho Z-Machine Interface

A standalone MCP server that wraps Jericho for playing interactive fiction games.
Can be used with Claude Desktop, Gemini CLI, or any MCP-compatible client.
"""

from mcp_server.server import create_server, main

__all__ = ["create_server", "main"]
__version__ = "0.1.0"
