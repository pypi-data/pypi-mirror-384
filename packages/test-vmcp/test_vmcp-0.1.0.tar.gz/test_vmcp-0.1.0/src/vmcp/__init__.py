"""
vMCP - Virtual Model Context Protocol

An open-source tool for aggregating and managing multiple MCP servers
with a unified interface.
"""

__version__ = "0.1.0"
__author__ = "vMCP Team"
__license__ = "MIT"

from vmcp.backend.config import settings

__all__ = ["settings", "__version__"]
