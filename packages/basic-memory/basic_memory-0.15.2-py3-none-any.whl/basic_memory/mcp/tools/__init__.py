"""MCP tools for Basic Memory.

This package provides the complete set of tools for interacting with
Basic Memory through the MCP protocol. Importing this module registers
all tools with the MCP server.
"""

# Import tools to register them with MCP
from basic_memory.mcp.tools.delete_note import delete_note
from basic_memory.mcp.tools.read_content import read_content
from basic_memory.mcp.tools.build_context import build_context
from basic_memory.mcp.tools.recent_activity import recent_activity
from basic_memory.mcp.tools.read_note import read_note
from basic_memory.mcp.tools.view_note import view_note
from basic_memory.mcp.tools.write_note import write_note
from basic_memory.mcp.tools.search import search_notes
from basic_memory.mcp.tools.canvas import canvas
from basic_memory.mcp.tools.list_directory import list_directory
from basic_memory.mcp.tools.edit_note import edit_note
from basic_memory.mcp.tools.move_note import move_note
from basic_memory.mcp.tools.sync_status import sync_status
from basic_memory.mcp.tools.project_management import (
    list_memory_projects,
    create_memory_project,
    delete_project,
)

# ChatGPT-compatible tools
from basic_memory.mcp.tools.chatgpt_tools import search, fetch

__all__ = [
    "build_context",
    "canvas",
    "create_memory_project",
    "delete_note",
    "delete_project",
    "edit_note",
    "fetch",
    "list_directory",
    "list_memory_projects",
    "move_note",
    "read_content",
    "read_note",
    "recent_activity",
    "search",
    "search_notes",
    "sync_status",
    "view_note",
    "write_note",
]
