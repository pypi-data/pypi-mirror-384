"""
vMCP Configuration Manager - Modular Architecture
=================================================

This module provides a clean, maintainable architecture for managing vMCP configurations.

Structure:
- manager: Main VMCPConfigManager class (orchestrator)
- core: CRUD operations and capability aggregation
- execution: Tool, resource, and prompt execution routing
- custom_tools: Custom tool execution (prompt/python/http)
- parsing: Variable substitution and template processing
- helpers: Utility functions and type conversions

All modules are composed into the main VMCPConfigManager class for a unified interface.

Usage:
    from vmcp.backend.vmcps.config_manager import VMCPConfigManager

    manager = VMCPConfigManager(user_id=1, vmcp_id="my-vmcp")
    tools = await manager.tools_list()
    result = await manager.call_tool(request)
"""

from .manager import VMCPConfigManager

__all__ = ['VMCPConfigManager']
