"""
MCP Client Manager for vMCP OSS.

Handles connections to MCP servers via stdio, HTTP, or SSE transports.
Manages tool calls, resource reads, and prompt operations.
"""

import asyncio
import traceback
from typing import Dict, List, Optional, Any
from datetime import datetime

import httpx
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.client.sse import sse_client
from mcp.client.streamable_http import streamablehttp_client
from mcp.types import (
    Tool, Resource, Prompt, ResourceTemplate,
    CallToolResult, GetPromptResult, ReadResourceResult
)

from vmcp.backend.utilities.logging import get_logger
from vmcp.backend.utilities.tracing import trace_async
from vmcp.backend.mcps.models import (
    MCPServerConfig, MCPTransportType, MCPConnectionStatus
)

logger = get_logger(__name__)


# Custom exceptions
class AuthenticationError(Exception):
    """Raised when MCP server authentication fails."""
    pass


class MCPOperationError(Exception):
    """Raised when an MCP operation fails."""
    pass


class InvalidSessionIdError(Exception):
    """Raised when session ID is invalid."""
    pass


def safe_extract_response_info(response):
    """Safely extract status code and text from an HTTP response."""
    status_code = None
    error_text = None

    try:
        if hasattr(response, 'status_code'):
            status_code = response.status_code

        if hasattr(response, 'text'):
            try:
                error_text = response.text
            except httpx.ResponseNotRead:
                error_text = f"[Streaming response - status: {status_code}]"
        elif hasattr(response, 'content'):
            try:
                content = response.content
                if hasattr(content, 'decode'):
                    error_text = content.decode('utf-8', errors='ignore')
                else:
                    error_text = str(content)
            except Exception:
                error_text = f"[Unable to read response content - status: {status_code}]"
        else:
            error_text = f"[No content available - status: {status_code}]"

    except Exception as e:
        error_text = f"[Error extracting response info: {e}]"

    return status_code, error_text


def mcp_operation(func):
    """Decorator for MCP operations that handles connection management."""
    async def wrapper(self, server_config: MCPServerConfig, *args, **kwargs):
        # Construct headers
        headers = server_config.headers or {}
        headers["mcp-protocol-version"] = "2025-06-18"

        # Add authentication headers
        if server_config.auth and server_config.auth.access_token:
            headers['Authorization'] = f'Bearer {server_config.auth.access_token}'

        # Add session ID if available
        if server_config.session_id:
            headers['mcp-session-id'] = server_config.session_id

        logger.debug(f"Connecting to {server_config.name} with headers: {list(headers.keys())}")

        session = None
        context = None
        session_entered = False
        context_entered = False

        try:
            # Handle different transport types
            if server_config.transport_type == MCPTransportType.SSE:
                context = sse_client(server_config.url, headers)
                read_stream, write_stream = await context.__aenter__()
                context_entered = True
                session = ClientSession(read_stream, write_stream)
                await session.__aenter__()
                session_entered = True
                result = await session.initialize()
                logger.info(f"Initialized SSE session for {server_config.name}")
                self.connections[server_config.name] = session
                return await func(self, server_config, *args, **kwargs)

            elif server_config.transport_type == MCPTransportType.HTTP:
                context = streamablehttp_client(
                    server_config.url,
                    headers=headers,
                    terminate_on_close=False
                )
                read_stream, write_stream, get_session_id = await context.__aenter__()
                context_entered = True
                session = ClientSession(read_stream, write_stream)
                await session.__aenter__()
                session_entered = True

                if not headers.get('mcp-session-id'):
                    result = await session.initialize()
                    session_id = get_session_id()
                    server_config.session_id = session_id

                    # Save session ID
                    if self.config_manager:
                        self.config_manager.update_server_session(
                            server_config.server_id,
                            session_id
                        )
                    logger.info(f"Created new HTTP session for {server_config.name}: {session_id}")
                else:
                    logger.debug(f"Using existing session ID for {server_config.name}")

                self.connections[server_config.name] = session
                return await func(self, server_config, *args, **kwargs)

            elif server_config.transport_type == MCPTransportType.STDIO:
                # Create server parameters
                server_params = StdioServerParameters(
                    command=server_config.command,
                    args=server_config.args or [],
                    env=server_config.env
                )
                context = stdio_client(server_params)
                read_stream, write_stream = await context.__aenter__()
                context_entered = True
                session = ClientSession(read_stream, write_stream)
                await session.__aenter__()
                session_entered = True
                result = await session.initialize()
                logger.info(f"Initialized stdio session for {server_config.name}")
                self.connections[server_config.name] = session
                return await func(self, server_config, *args, **kwargs)

            else:
                logger.error(f"Invalid transport type: {server_config.transport_type}")
                raise MCPOperationError(f"Invalid transport type: {server_config.transport_type}")

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                logger.error(f"Authentication failed for {server_config.name}: 401 Unauthorized")
                raise AuthenticationError(f"Authentication required for {server_config.name}")
            else:
                status_code, error_text = safe_extract_response_info(e.response)
                logger.error(f"HTTP error for {server_config.name}: {status_code}")
                raise MCPOperationError(f"HTTP {status_code}: {error_text}")

        except asyncio.CancelledError:
            logger.warning(f"Operation cancelled for {server_config.name}")
            raise

        except asyncio.TimeoutError:
            logger.error(f"Operation timed out for {server_config.name}")
            raise

        except Exception as e:
            logger.error(f"Failed to connect to {server_config.name}: {e}")
            logger.debug(traceback.format_exc())

            # Handle ExceptionGroup for nested errors
            if isinstance(e, ExceptionGroup):
                for sub_exception in e.exceptions:
                    if hasattr(sub_exception, 'status_code') and sub_exception.status_code == 401:
                        raise AuthenticationError(f"Authentication required for {server_config.name}")

            raise MCPOperationError(f"Connection failed: {str(e)}")

        finally:
            # Cleanup
            try:
                if session_entered and session:
                    await session.__aexit__(None, None, None)
                if context_entered and context:
                    await context.__aexit__(None, None, None)
                if server_config.name in self.connections:
                    del self.connections[server_config.name]
            except Exception as cleanup_error:
                logger.warning(f"Cleanup error for {server_config.name}: {cleanup_error}")

    return wrapper


class MCPClientManager:
    """Manages multiple MCP server connections."""

    def __init__(self, config_manager=None):
        """
        Initialize MCP client manager.

        Args:
            config_manager: MCPConfigManager instance for persisting configs
        """
        self.config_manager = config_manager
        self.connections: Dict[str, ClientSession] = {}
        logger.info("MCPClientManager initialized")

    @mcp_operation
    @trace_async("mcp.list_tools")
    async def tools_list(
        self,
        server_config: MCPServerConfig,
        *args,
        **kwargs
    ) -> Dict[str, Tool]:
        """
        List available tools from the MCP server.

        Args:
            server_config: Server configuration

        Returns:
            Dictionary of tool name to Tool object
        """
        session = self.connections[server_config.name]
        try:
            result = await session.list_tools()
            tool_details = {tool.name: tool for tool in result.tools}
            logger.info(f"Retrieved {len(tool_details)} tools from {server_config.name}")
            return tool_details
        except Exception as e:
            logger.error(f"Failed to list tools from {server_config.name}: {e}")
            raise MCPOperationError(f"Failed to list tools: {e}")

    @mcp_operation
    @trace_async("mcp.list_prompts")
    async def prompts_list(
        self,
        server_config: MCPServerConfig,
        *args,
        **kwargs
    ) -> Dict[str, Prompt]:
        """
        List available prompts from the MCP server.

        Args:
            server_config: Server configuration

        Returns:
            Dictionary of prompt name to Prompt object
        """
        session = self.connections[server_config.name]
        try:
            result = await session.list_prompts()
            prompt_details = {prompt.name: prompt for prompt in result.prompts}
            logger.info(f"Retrieved {len(prompt_details)} prompts from {server_config.name}")
            return prompt_details
        except Exception as e:
            logger.error(f"Failed to list prompts from {server_config.name}: {e}")
            raise MCPOperationError(f"Failed to list prompts: {e}")

    @mcp_operation
    @trace_async("mcp.list_resources")
    async def resources_list(
        self,
        server_config: MCPServerConfig,
        *args,
        **kwargs
    ) -> Dict[str, Resource]:
        """
        List available resources from the MCP server.

        Args:
            server_config: Server configuration

        Returns:
            Dictionary of resource URI to Resource object
        """
        session = self.connections[server_config.name]
        try:
            result = await session.list_resources()
            resource_details = {str(resource.uri): resource for resource in result.resources}
            logger.info(f"Retrieved {len(resource_details)} resources from {server_config.name}")
            return resource_details
        except Exception as e:
            logger.error(f"Failed to list resources from {server_config.name}: {e}")
            raise MCPOperationError(f"Failed to list resources: {e}")

    @mcp_operation
    @trace_async("mcp.list_resource_templates")
    async def resource_templates_list(
        self,
        server_config: MCPServerConfig,
        *args,
        **kwargs
    ) -> Dict[str, ResourceTemplate]:
        """
        List available resource templates from the MCP server.

        Args:
            server_config: Server configuration

        Returns:
            Dictionary of template name to ResourceTemplate object
        """
        session = self.connections[server_config.name]
        try:
            result = await session.list_resource_templates()
            template_details = {
                template.name: template
                for template in result.resourceTemplates
            }
            logger.info(f"Retrieved {len(template_details)} resource templates from {server_config.name}")
            return template_details
        except Exception as e:
            logger.error(f"Failed to list resource templates from {server_config.name}: {e}")
            raise MCPOperationError(f"Failed to list resource templates: {e}")

    @mcp_operation
    @trace_async("mcp.call_tool")
    async def call_tool(
        self,
        server_config: MCPServerConfig,
        tool_name: str,
        arguments: Dict[str, Any],
        *args,
        **kwargs
    ) -> CallToolResult:
        """
        Call a tool on the MCP server.

        Args:
            server_config: Server configuration
            tool_name: Name of the tool to call
            arguments: Tool arguments

        Returns:
            Tool call result
        """
        session = self.connections[server_config.name]
        try:
            logger.info(f"Calling tool {tool_name} on {server_config.name}")
            result = await session.call_tool(tool_name, arguments)
            logger.info(f"Tool {tool_name} executed successfully")
            return result
        except Exception as e:
            logger.error(f"Failed to call tool {tool_name}: {e}")
            raise MCPOperationError(f"Tool call failed: {e}")

    @mcp_operation
    @trace_async("mcp.read_resource")
    async def read_resource(
        self,
        server_config: MCPServerConfig,
        uri: str,
        *args,
        **kwargs
    ) -> ReadResourceResult:
        """
        Read a resource from the MCP server.

        Args:
            server_config: Server configuration
            uri: Resource URI

        Returns:
            Resource read result
        """
        session = self.connections[server_config.name]
        try:
            logger.info(f"Reading resource {uri} from {server_config.name}")
            result = await session.read_resource(uri)
            logger.info(f"Resource {uri} read successfully")
            return result
        except Exception as e:
            logger.error(f"Failed to read resource {uri}: {e}")
            raise MCPOperationError(f"Resource read failed: {e}")

    @mcp_operation
    @trace_async("mcp.get_prompt")
    async def get_prompt(
        self,
        server_config: MCPServerConfig,
        prompt_name: str,
        arguments: Optional[Dict[str, Any]] = None,
        *args,
        **kwargs
    ) -> GetPromptResult:
        """
        Get a prompt from the MCP server.

        Args:
            server_config: Server configuration
            prompt_name: Name of the prompt
            arguments: Optional prompt arguments

        Returns:
            Prompt result
        """
        session = self.connections[server_config.name]
        try:
            logger.info(f"Getting prompt {prompt_name} from {server_config.name}")
            result = await session.get_prompt(prompt_name, arguments or {})
            logger.info(f"Prompt {prompt_name} retrieved successfully")
            return result
        except Exception as e:
            logger.error(f"Failed to get prompt {prompt_name}: {e}")
            raise MCPOperationError(f"Prompt get failed: {e}")

    async def ping_server(self, server_name: str) -> MCPConnectionStatus:
        """
        Ping an MCP server to check if it's reachable.

        Args:
            server_name: Name or ID of the server

        Returns:
            MCPConnectionStatus enum value
        """
        try:
            if not self.config_manager:
                logger.error("Config manager not available")
                return MCPConnectionStatus.ERROR

            server_config = self.config_manager.get_server(server_name)
            if not server_config:
                logger.error(f"Server {server_name} not found")
                return MCPConnectionStatus.ERROR

            # Try to list tools as a ping - pass server_config, not server_name
            await self.tools_list(server_config)
            logger.info(f"✅ Pinged server {server_name}")

            # Update the server config status to CONNECTED
            if self.config_manager:
                server_config.status = MCPConnectionStatus.CONNECTED
                self.config_manager.update_server_config(server_config.server_id, server_config)

            return MCPConnectionStatus.CONNECTED

        except AuthenticationError as e:
            logger.warning(f"Server {server_name} requires authentication: {e}")
            return MCPConnectionStatus.AUTH_REQUIRED
        except Exception as e:
            logger.warning(f"Server {server_name} ping failed: {e}")
            return MCPConnectionStatus.ERROR

    async def discover_capabilities(self, server_name: str) -> Dict[str, Any]:
        """
        Discover capabilities of the MCP server.

        Args:
            server_name: Name or ID of the server

        Returns:
            Dictionary containing server capabilities (tools, resources, prompts, etc.)
        """
        capabilities = {}
        errors_if_any = {}

        try:
            if not self.config_manager:
                logger.error("Config manager not available")
                return capabilities

            server_config = self.config_manager.get_server(server_name)
            if not server_config:
                logger.error(f"Server {server_name} not found")
                return capabilities

            # Discover tools
            try:
                tools_result = await self.tools_list(server_config)
                # Add server metadata to each tool
                for tool_name, tool in tools_result.items():
                    if hasattr(tool, 'meta'):
                        _orig_meta = tool.meta or {}
                    else:
                        _orig_meta = {}
                    _orig_meta['server_name'] = server_config.name
                    if hasattr(tool, 'meta'):
                        tool.meta = _orig_meta.copy()

                logger.info(f"✅ Added metadata to {server_config.name} tools")
                capabilities['tools'] = list(tools_result.keys())
                capabilities['tool_details'] = list(tools_result.values())
            except Exception as e:
                logger.error(f"Failed to discover tools from server: {e}")
                errors_if_any['tools'] = str(e)
                capabilities['tools'] = []
                capabilities['tool_details'] = []

            # Discover resources
            try:
                resources_result = await self.resources_list(server_config)
                capabilities['resources'] = list(resources_result.keys())
                capabilities['resource_details'] = list(resources_result.values())
            except Exception as e:
                logger.error(f"Failed to discover resources from server: {e}")
                errors_if_any['resources'] = str(e)
                capabilities['resources'] = []
                capabilities['resource_details'] = []

            # Discover resource templates (may not be supported by all servers)
            try:
                # Not all servers support resource templates, so we catch any errors
                templates = []
                template_details = []
                # Store empty lists for now - can be enhanced later
                capabilities['resource_templates'] = templates
                capabilities['resource_template_details'] = template_details
            except Exception as e:
                logger.debug(f"Resource templates not supported by server: {e}")
                capabilities['resource_templates'] = []
                capabilities['resource_template_details'] = []

            # Discover prompts
            try:
                prompts_result = await self.prompts_list(server_config)
                capabilities['prompts'] = list(prompts_result.keys())
                capabilities['prompt_details'] = list(prompts_result.values())
            except Exception as e:
                logger.error(f"Failed to discover prompts from server: {e}")
                errors_if_any['prompts'] = str(e)
                capabilities['prompts'] = []
                capabilities['prompt_details'] = []

            if errors_if_any:
                logger.warning(f"✅ Retrieved capabilities from server [ERRORS_IF_ANY: {errors_if_any}]")
            else:
                logger.info(f"✅ Retrieved all capabilities from server {server_name}")

            return capabilities

        except Exception as e:
            logger.error(f"Failed to discover capabilities for {server_name}: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return capabilities

    def is_connected(self, server_name: str) -> bool:
        """
        Check if a server is currently connected.

        Args:
            server_name: Name of the server

        Returns:
            True if connected, False otherwise
        """
        return server_name in self.connections

    async def disconnect(self, server_name: str) -> None:
        """
        Disconnect from a server.

        Args:
            server_name: Name of the server
        """
        if server_name in self.connections:
            try:
                session = self.connections[server_name]
                await session.__aexit__(None, None, None)
                del self.connections[server_name]
                logger.info(f"Disconnected from {server_name}")
            except Exception as e:
                logger.error(f"Error disconnecting from {server_name}: {e}")

    async def disconnect_all(self) -> None:
        """Disconnect from all servers."""
        server_names = list(self.connections.keys())
        for server_name in server_names:
            await self.disconnect(server_name)
        logger.info("Disconnected from all servers")
