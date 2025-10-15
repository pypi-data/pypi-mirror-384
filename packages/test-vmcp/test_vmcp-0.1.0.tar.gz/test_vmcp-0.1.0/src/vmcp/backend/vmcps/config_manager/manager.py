"""
vMCP Configuration Manager - Main Orchestrator
==============================================

This is the main VMCPConfigManager class that composes all submodules into a unified interface.

The manager delegates all operations to specialized modules:
- core: CRUD and capability aggregation
- execution: Tool/resource/prompt routing and execution
- custom_tools: Custom tool execution (prompt/python/http)
- parsing: Variable substitution and template processing

This provides a clean, maintainable architecture while maintaining backward compatibility
with the original monolithic implementation.
"""

import logging
from typing import Dict, List, Any, Optional
from jinja2 import Environment, DictLoader

from mcp.types import Tool, Resource, ResourceTemplate, Prompt

from vmcp.backend.storage.base import StorageBase
from vmcp.backend.mcps.mcp_config_manager import MCPConfigManager
from vmcp.backend.mcps.mcp_client import MCPClientManager
from vmcp.backend.vmcps.models import VMCPConfig, VMCPToolCallRequest, VMCPResourceRequest
from vmcp.backend.mcps.models import MCPServerConfig

from .core import CoreOperations
from .execution import ExecutionManager
from .custom_tools import CustomToolsManager
from .parsing import ParsingEngine

logger = logging.getLogger("vmcp.config_manager")


class VMCPConfigManager:
    """
    Main vMCP Configuration Manager - orchestrates all operations.

    A vMCP (Virtual MCP) aggregates multiple MCP servers into a unified interface,
    providing combined tools, resources, and prompts with support for:
    - Custom tools (prompt-based, Python, HTTP)
    - Custom prompts and resources
    - Environment variables
    - File uploads
    - Widget support for OpenAI Apps SDK
    - Variable substitution with @param, @config, @tool, @resource, @prompt
    - Jinja2 templating

    Architecture:
    This class composes specialized modules for different concerns:
    - core: CRUD operations and capability aggregation
    - execution: Routing and execution of operations
    - custom_tools: Custom tool handlers
    - parsing: Variable substitution engine

    All public methods delegate to the appropriate module, maintaining a clean
    separation of concerns while providing a unified interface.
    """

    def __init__(
        self,
        user_id: int = 1,
        vmcp_id: Optional[str] = None,
        logging_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize VMCPConfigManager.

        Args:
            user_id: User ID (always 1 in OSS version)
            vmcp_id: Optional vMCP ID to work with
            logging_config: Optional logging configuration
        """
        # Core dependencies
        self.storage = StorageBase(user_id)
        self.user_id = user_id
        self.vmcp_id = vmcp_id
        self.mcp_config_manager = MCPConfigManager(user_id)
        self.mcp_client_manager = MCPClientManager(self.mcp_config_manager)
        self.logging_config = logging_config or {
            "agent_name": "vmcp_client",
            "agent_id": "vmcp_client",
            "client_id": "vmcp_client"
        }

        # Initialize Jinja2 environment for template preprocessing
        self.jinja_env = Environment(
            loader=DictLoader({}),
            variable_start_string='{{',
            variable_end_string='}}',
            block_start_string='{%',
            block_end_string='%}',
            comment_start_string='{#',
            comment_end_string='#}'
        )

        # Initialize submodules
        self.core = CoreOperations(self)
        self.execution = ExecutionManager(self)
        self.custom_tools = CustomToolsManager(self)
        self.parsing = ParsingEngine(self)

        logger.info(f"VMCPConfigManager initialized for user {user_id}, vmcp_id: {vmcp_id}")

    # ============================================================================
    # CRUD Operations (delegated to core module)
    # ============================================================================

    def load_vmcp_config(self, specific_vmcp_id: Optional[str] = None) -> Optional[VMCPConfig]:
        """Load vMCP configuration from storage."""
        return self.core.load_vmcp_config(specific_vmcp_id)

    def list_available_vmcps(self) -> List[Dict[str, Any]]:
        """List all available vMCP configurations."""
        return self.core.list_available_vmcps()

    def save_vmcp_config(self, vmcp_config: VMCPConfig) -> bool:
        """Save a vMCP configuration."""
        return self.core.save_vmcp_config(vmcp_config)

    def create_vmcp_config(
        self,
        name: str,
        description: Optional[str] = None,
        system_prompt: Optional[Dict[str, Any]] = None,
        vmcp_config: Optional[Dict[str, Any]] = None,
        custom_prompts: Optional[List[Dict[str, Any]]] = None,
        custom_tools: Optional[List[Dict[str, Any]]] = None,
        custom_context: Optional[List[str]] = None,
        custom_resources: Optional[List[Dict[str, Any]]] = None,
        custom_resource_templates: Optional[List[Dict[str, Any]]] = None,
        custom_resource_uris: Optional[List[str]] = None,
        environment_variables: Optional[List[Dict[str, Any]]] = None,
        uploaded_files: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[str]:
        """Create a new vMCP configuration."""
        return self.core.create_vmcp_config(
            name=name,
            description=description,
            system_prompt=system_prompt,
            vmcp_config=vmcp_config,
            custom_prompts=custom_prompts,
            custom_tools=custom_tools,
            custom_context=custom_context,
            custom_resources=custom_resources,
            custom_resource_templates=custom_resource_templates,
            custom_resource_uris=custom_resource_uris,
            environment_variables=environment_variables,
            uploaded_files=uploaded_files
        )

    def update_vmcp_config(
        self,
        vmcp_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        system_prompt: Optional[Dict[str, Any]] = None,
        vmcp_config: Optional[Dict[str, Any]] = None,
        custom_prompts: Optional[List[Dict[str, Any]]] = None,
        custom_tools: Optional[List[Dict[str, Any]]] = None,
        custom_context: Optional[List[str]] = None,
        custom_resources: Optional[List[Dict[str, Any]]] = None,
        custom_resource_templates: Optional[List[Dict[str, Any]]] = None,
        custom_resource_uris: Optional[List[str]] = None,
        environment_variables: Optional[List[Dict[str, Any]]] = None,
        uploaded_files: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """Update an existing vMCP configuration."""
        return self.core.update_vmcp_config(
            vmcp_id=vmcp_id,
            name=name,
            description=description,
            system_prompt=system_prompt,
            vmcp_config=vmcp_config,
            custom_prompts=custom_prompts,
            custom_tools=custom_tools,
            custom_context=custom_context,
            custom_resources=custom_resources,
            custom_resource_templates=custom_resource_templates,
            custom_resource_uris=custom_resource_uris,
            environment_variables=environment_variables,
            uploaded_files=uploaded_files
        )

    def delete_vmcp(self, vmcp_id: str) -> Dict[str, Any]:
        """Delete a vMCP configuration."""
        return self.core.delete_vmcp(vmcp_id)

    # Resource management
    def add_resource(self, vmcp_id: str, resource_data: Dict[str, Any]) -> bool:
        """Add a resource to the vMCP."""
        return self.core.add_resource(vmcp_id, resource_data)

    def update_resource(self, vmcp_id: str, resource_data: Dict[str, Any]) -> bool:
        """Update a resource in the vMCP."""
        return self.core.update_resource(vmcp_id, resource_data)

    def delete_resource(self, vmcp_id: str, resource_data: Dict[str, Any]) -> bool:
        """Delete a resource from the vMCP."""
        return self.core.delete_resource(vmcp_id, resource_data)

    # ============================================================================
    # Capability Aggregation (delegated to core module)
    # ============================================================================

    async def tools_list(self) -> List[Tool]:
        """List all tools from the vMCP's selected servers and custom tools."""
        return await self.core.tools_list()

    async def resources_list(self) -> List[Resource]:
        """List all resources from the vMCP's selected servers."""
        return await self.core.resources_list()

    async def resource_templates_list(self) -> List[ResourceTemplate]:
        """List all resource templates from the vMCP's selected servers."""
        return await self.core.resource_templates_list()

    async def prompts_list(self) -> List[Prompt]:
        """List all prompts from the vMCP's selected servers and custom prompts."""
        return await self.core.prompts_list()

    # ============================================================================
    # Execution Operations (delegated to execution module)
    # ============================================================================

    async def call_tool(
        self,
        vmcp_tool_call_request: VMCPToolCallRequest,
        connect_if_needed: bool = True,
        return_metadata: bool = False
    ) -> Dict[str, Any]:
        """Execute a tool call."""
        return await self.execution.call_tool(
            vmcp_tool_call_request,
            connect_if_needed,
            return_metadata
        )

    async def get_resource(self, resource_id: str, connect_if_needed: bool = True):
        """Get a specific resource."""
        return await self.execution.get_resource(resource_id, connect_if_needed)

    async def get_prompt(self, prompt_id: str, arguments: Optional[Dict[str, Any]] = None):
        """Get a prompt."""
        return await self.execution.get_prompt(prompt_id, arguments)

    async def get_system_prompt(self, arguments: Optional[Dict[str, Any]] = None):
        """Get the system prompt with variable substitution."""
        return await self.execution.get_system_prompt(arguments)

    async def get_custom_prompt(self, prompt_id: str, arguments: Optional[Dict[str, Any]] = None):
        """Get a custom prompt with variable substitution."""
        return await self.execution.get_custom_prompt(prompt_id, arguments)

    async def get_resource_template(self, request: VMCPResourceRequest):
        """Get a resource template with parameter substitution."""
        return await self.execution.get_resource_template(request)

    async def call_custom_resource(self, resource_id: str):
        """Fetch a custom resource from the vMCP's uploaded files."""
        return await self.execution.call_custom_resource(resource_id)

    # Server configuration
    def update_vmcp_server(self, vmcp_id: str, server_config: MCPServerConfig) -> bool:
        """Update the server configuration for a vMCP."""
        return self.execution.update_vmcp_server(vmcp_id, server_config)

    # Background logging
    async def log_vmcp_operation(
        self,
        operation_type: str,
        operation_id: str,
        arguments: Optional[Dict[str, Any]],
        result: Optional[Any],
        metadata: Optional[Dict[str, Any]]
    ) -> None:
        """Background task to log vMCP operations."""
        return await self.execution.log_vmcp_operation(
            operation_type,
            operation_id,
            arguments,
            result,
            metadata
        )

    # ============================================================================
    # Custom Tools (delegated to custom_tools module)
    # ============================================================================

    async def call_custom_tool(
        self,
        tool_id: str,
        arguments: Optional[Dict[str, Any]] = None,
        tool_as_prompt: bool = False
    ):
        """Execute a custom tool."""
        return await self.custom_tools.call_custom_tool(tool_id, arguments, tool_as_prompt)

    # ============================================================================
    # Parsing Engine (delegated to parsing module)
    # ============================================================================

    async def parse_vmcp_text(
        self,
        text: str,
        config_item: dict,
        arguments: Dict[str, Any],
        environment_variables: Dict[str, Any],
        is_prompt: bool = False
    ):
        """Parse vMCP text with full variable substitution."""
        return await self.parsing.parse_vmcp_text(
            text,
            config_item,
            arguments,
            environment_variables,
            is_prompt
        )
