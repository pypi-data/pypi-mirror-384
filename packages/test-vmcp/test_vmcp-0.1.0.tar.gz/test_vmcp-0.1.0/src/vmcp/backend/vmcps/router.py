"""
vMCP Router - REST API endpoints for Virtual MCP management.

Provides endpoints for creating, managing, and using virtual MCPs that aggregate
multiple MCP servers.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, status
from pydantic import BaseModel

from vmcp.backend.utilities.logging import get_logger
from vmcp.backend.utilities.tracing import trace_async
from vmcp.backend.vmcps.config_manager import VMCPConfigManager
from vmcp.backend.vmcps.models import (
    VMCPConfig, VMCPToolCallRequest, VMCPResourceRequest
)
from vmcp.backend.storage.dummy_user import UserContext, get_user_context
from mcp.types import Tool, Resource, ResourceTemplate, Prompt

logger = get_logger(__name__)

router = APIRouter(prefix="/api/vmcps", tags=["vMCPs"])


# ============================================================================
# Request/Response Models
# ============================================================================

class CreateVMCPRequest(BaseModel):
    """Request to create a new vMCP."""
    name: str
    description: Optional[str] = None
    system_prompt: Optional[Dict[str, Any]] = None
    vmcp_config: Optional[Dict[str, Any]] = None
    custom_prompts: Optional[List[Dict[str, Any]]] = None
    custom_tools: Optional[List[Dict[str, Any]]] = None
    custom_context: Optional[List[str]] = None
    custom_resources: Optional[List[Dict[str, Any]]] = None
    custom_resource_templates: Optional[List[Dict[str, Any]]] = None
    custom_resource_uris: Optional[List[str]] = None
    environment_variables: Optional[List[Dict[str, Any]]] = None
    uploaded_files: Optional[List[Dict[str, Any]]] = None


class UpdateVMCPRequest(BaseModel):
    """Request to update an existing vMCP."""
    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[Dict[str, Any]] = None
    vmcp_config: Optional[Dict[str, Any]] = None
    custom_prompts: Optional[List[Dict[str, Any]]] = None
    custom_tools: Optional[List[Dict[str, Any]]] = None
    custom_context: Optional[List[str]] = None
    custom_resources: Optional[List[Dict[str, Any]]] = None
    custom_resource_templates: Optional[List[Dict[str, Any]]] = None
    custom_resource_uris: Optional[List[str]] = None
    environment_variables: Optional[List[Dict[str, Any]]] = None
    uploaded_files: Optional[List[Dict[str, Any]]] = None


class VMCPResponse(BaseModel):
    """Response containing vMCP information."""
    id: str
    name: str
    description: Optional[str] = None
    system_prompt: Optional[Dict[str, Any]] = None
    vmcp_config: Optional[Dict[str, Any]] = None
    custom_prompts: Optional[List[Dict[str, Any]]] = None
    custom_tools: Optional[List[Dict[str, Any]]] = None
    custom_context: Optional[List[str]] = None
    custom_resources: Optional[List[Dict[str, Any]]] = None
    custom_resource_uris: Optional[List[str]] = None
    environment_variables: Optional[List[Dict[str, Any]]] = None
    uploaded_files: Optional[List[Dict[str, Any]]] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    is_public: bool = False


class VMCPSummaryResponse(BaseModel):
    """Summary response for vMCP in lists."""
    id: str
    vmcp_id: str
    name: str
    description: Optional[str] = None
    total_tools: int = 0
    total_resources: int = 0
    total_resource_templates: int = 0
    total_prompts: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class VMCPListResponse(BaseModel):
    """Response containing list of vMCPs."""
    vmcps: List[VMCPSummaryResponse]
    total: int


class VMCPCreateResponse(BaseModel):
    """Response for vMCP creation (matches main app format)."""
    success: bool = True
    vMCP: VMCPResponse


# ============================================================================
# Dependencies
# ============================================================================

def get_vmcp_manager(
    user_context: UserContext = Depends(get_user_context),
    vmcp_id: Optional[str] = None
) -> VMCPConfigManager:
    """Dependency to get vMCP config manager."""
    return VMCPConfigManager(user_id=user_context.user_id, vmcp_id=vmcp_id)


# ============================================================================
# Health & Info Endpoints
# ============================================================================

@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "vMCP - Virtual MCP Management"
    }


@router.get("/info")
async def get_info():
    """Get vMCP service information."""
    return {
        "service": "vMCP",
        "version": "0.1.0",
        "description": "Virtual MCP - Aggregate multiple MCP servers",
        "capabilities": {
            "custom_tools": ["prompt", "python", "http"],
            "variable_substitution": ["@param", "@config", "@tool", "@resource", "@prompt"],
            "templates": ["jinja2"],
            "widgets": True,
            "authentication": ["bearer", "apikey", "basic", "custom"]
        }
    }


# ============================================================================
# vMCP CRUD Endpoints
# ============================================================================

@router.get("/", response_model=VMCPListResponse)
@trace_async("vmcp.list")
async def list_vmcps(
    manager: VMCPConfigManager = Depends(get_vmcp_manager)
):
    """
    List all vMCPs for the current user.

    Returns:
        List of vMCP configurations
    """
    logger.info("Listing vMCPs")

    try:
        vmcps = manager.list_available_vmcps()

        vmcp_responses = [
            VMCPSummaryResponse(
                id=vmcp.get("id"),
                vmcp_id=vmcp.get("vmcp_id"),
                name=vmcp.get("name"),
                description=vmcp.get("description"),
                total_tools=vmcp.get("total_tools", 0),
                total_resources=vmcp.get("total_resources", 0),
                total_resource_templates=vmcp.get("total_resource_templates", 0),
                total_prompts=vmcp.get("total_prompts", 0),
                created_at=vmcp.get("created_at"),
                updated_at=vmcp.get("updated_at")
            )
            for vmcp in vmcps
        ]

        return VMCPListResponse(vmcps=vmcp_responses, total=len(vmcp_responses))

    except Exception as e:
        logger.error(f"Failed to list vMCPs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list vMCPs: {str(e)}"
        )


@router.get("/{vmcp_id}", response_model=VMCPResponse)
@trace_async("vmcp.get")
async def get_vmcp(
    vmcp_id: str,
    manager: VMCPConfigManager = Depends(get_vmcp_manager)
):
    """
    Get a specific vMCP by ID.

    Args:
        vmcp_id: vMCP identifier

    Returns:
        vMCP configuration
    """
    logger.info(f"Getting vMCP: {vmcp_id}")

    try:
        vmcp_config = manager.load_vmcp_config(vmcp_id)

        if not vmcp_config:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"vMCP not found: {vmcp_id}"
            )

        return VMCPResponse(
            id=vmcp_config.id,
            name=vmcp_config.name,
            description=vmcp_config.description,
            system_prompt=vmcp_config.system_prompt,
            vmcp_config=vmcp_config.vmcp_config,
            custom_prompts=vmcp_config.custom_prompts,
            custom_tools=vmcp_config.custom_tools,
            custom_context=vmcp_config.custom_context,
            custom_resources=vmcp_config.custom_resources,
            custom_resource_uris=vmcp_config.custom_resource_uris,
            environment_variables=vmcp_config.environment_variables,
            uploaded_files=vmcp_config.uploaded_files,
            created_at=vmcp_config.created_at.isoformat() if vmcp_config.created_at else None,
            updated_at=vmcp_config.updated_at.isoformat() if vmcp_config.updated_at else None,
            is_public=vmcp_config.is_public
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get vMCP {vmcp_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get vMCP: {str(e)}"
        )


@router.post("/", response_model=VMCPCreateResponse, status_code=status.HTTP_201_CREATED)
@trace_async("vmcp.create")
async def create_vmcp(
    request: CreateVMCPRequest,
    manager: VMCPConfigManager = Depends(get_vmcp_manager)
):
    """
    Create a new vMCP.

    Args:
        request: vMCP creation request

    Returns:
        Created vMCP configuration wrapped in success response
    """
    logger.info(f"Creating vMCP: {request.name}")

    try:
        vmcp_id = manager.create_vmcp_config(
            name=request.name,
            description=request.description,
            system_prompt=request.system_prompt,
            vmcp_config=request.vmcp_config,
            custom_prompts=request.custom_prompts,
            custom_tools=request.custom_tools,
            custom_context=request.custom_context,
            custom_resources=request.custom_resources,
            custom_resource_templates=request.custom_resource_templates,
            custom_resource_uris=request.custom_resource_uris,
            environment_variables=request.environment_variables,
            uploaded_files=request.uploaded_files
        )

        if not vmcp_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create vMCP"
            )

        # Load and return created vMCP
        vmcp_config = manager.load_vmcp_config(vmcp_id)

        vmcp_response = VMCPResponse(
            id=vmcp_config.id,
            name=vmcp_config.name,
            description=vmcp_config.description,
            system_prompt=vmcp_config.system_prompt,
            vmcp_config=vmcp_config.vmcp_config,
            custom_prompts=vmcp_config.custom_prompts,
            custom_tools=vmcp_config.custom_tools,
            custom_context=vmcp_config.custom_context,
            custom_resources=vmcp_config.custom_resources,
            custom_resource_uris=vmcp_config.custom_resource_uris,
            environment_variables=vmcp_config.environment_variables,
            uploaded_files=vmcp_config.uploaded_files,
            created_at=vmcp_config.created_at.isoformat() if vmcp_config.created_at else None,
            updated_at=vmcp_config.updated_at.isoformat() if vmcp_config.updated_at else None,
            is_public=vmcp_config.is_public
        )

        # Wrap in success response to match main app format
        return VMCPCreateResponse(success=True, vMCP=vmcp_response)

    except Exception as e:
        logger.error(f"Failed to create vMCP: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create vMCP: {str(e)}"
        )


@router.put("/{vmcp_id}", response_model=VMCPResponse)
@trace_async("vmcp.update")
async def update_vmcp(
    vmcp_id: str,
    request: UpdateVMCPRequest,
    manager: VMCPConfigManager = Depends(get_vmcp_manager)
):
    """
    Update an existing vMCP.

    Args:
        vmcp_id: vMCP identifier
        request: vMCP update request

    Returns:
        Updated vMCP configuration
    """
    logger.info(f"Updating vMCP: {vmcp_id}")

    try:
        success = manager.update_vmcp_config(
            vmcp_id=vmcp_id,
            name=request.name,
            description=request.description,
            system_prompt=request.system_prompt,
            vmcp_config=request.vmcp_config,
            custom_prompts=request.custom_prompts,
            custom_tools=request.custom_tools,
            custom_context=request.custom_context,
            custom_resources=request.custom_resources,
            custom_resource_templates=request.custom_resource_templates,
            custom_resource_uris=request.custom_resource_uris,
            environment_variables=request.environment_variables,
            uploaded_files=request.uploaded_files
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"vMCP not found or update failed: {vmcp_id}"
            )

        # Load and return updated vMCP
        vmcp_config = manager.load_vmcp_config(vmcp_id)

        return VMCPResponse(
            id=vmcp_config.id,
            name=vmcp_config.name,
            description=vmcp_config.description,
            system_prompt=vmcp_config.system_prompt,
            vmcp_config=vmcp_config.vmcp_config,
            custom_prompts=vmcp_config.custom_prompts,
            custom_tools=vmcp_config.custom_tools,
            custom_context=vmcp_config.custom_context,
            custom_resources=vmcp_config.custom_resources,
            custom_resource_uris=vmcp_config.custom_resource_uris,
            environment_variables=vmcp_config.environment_variables,
            uploaded_files=vmcp_config.uploaded_files,
            created_at=vmcp_config.created_at.isoformat() if vmcp_config.created_at else None,
            updated_at=vmcp_config.updated_at.isoformat() if vmcp_config.updated_at else None,
            is_public=vmcp_config.is_public
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update vMCP {vmcp_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update vMCP: {str(e)}"
        )


@router.delete("/{vmcp_id}")
@trace_async("vmcp.delete")
async def delete_vmcp(
    vmcp_id: str,
    manager: VMCPConfigManager = Depends(get_vmcp_manager)
):
    """
    Delete a vMCP.

    Args:
        vmcp_id: vMCP identifier

    Returns:
        Deletion status
    """
    logger.info(f"Deleting vMCP: {vmcp_id}")

    try:
        result = manager.delete_vmcp(vmcp_id)

        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.get("message", f"Failed to delete vMCP: {vmcp_id}")
            )

        return {
            "success": True,
            "message": f"vMCP {vmcp_id} deleted successfully"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete vMCP {vmcp_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete vMCP: {str(e)}"
        )


# ============================================================================
# Server Management Endpoints
# ============================================================================

@router.post("/{vmcp_id}/add-server")
@trace_async("vmcp.servers.add")
async def add_server_to_vmcp(
    vmcp_id: str,
    request: dict,
    user_context: UserContext = Depends(get_user_context)
):
    """
    Add an MCP server to a vMCP configuration.

    This endpoint accepts server data from the registry or custom server forms,
    creates the MCP server if it doesn't exist, and adds it to the vMCP.
    """
    logger.info(f"📋 Add server to vMCP endpoint called for vmcp_id: {vmcp_id}")
    logger.info(f"   📝 Request data: {request}")

    try:
        from vmcp.backend.mcps.mcp_config_manager import MCPConfigManager
        from vmcp.backend.mcps.models import MCPServerConfig, MCPTransportType, MCPConnectionStatus

        # Get managers
        config_manager = MCPConfigManager(user_context.user_id)
        vmcp_manager = VMCPConfigManager(user_context.user_id, vmcp_id)

        # Load vMCP config
        vmcp_config = vmcp_manager.load_vmcp_config()
        if not vmcp_config:
            raise HTTPException(status_code=404, detail=f"vMCP '{vmcp_id}' not found")

        server_data = request.get('server_data', {})
        if server_data.get("mcp_server_config"):
            server_data = server_data.get("mcp_server_config")

        server_id = server_data.get('id') or server_data.get('server_id')
        server_name = server_data.get('name')

        if not server_id and not server_name:
            raise HTTPException(status_code=400, detail="Either server id or server name is required")

        # Check if server already exists
        existing_server = config_manager.get_server_by_id(server_id) if server_id else None

        server_to_add = None

        if existing_server:
            logger.info(f"   ✅ Found existing server: {existing_server.name} ({existing_server.server_id})")
            server_to_add = existing_server
            server_id = server_to_add.server_id
        else:
            # Create new server from server_data
            logger.info(f"   🔧 Creating new server from data: {server_name}")

            # Map transport type
            transport_type = MCPTransportType(server_data.get('transport', 'http'))

            # Create server config
            server_config = MCPServerConfig(
                name=server_data.get('name', ''),
                transport_type=transport_type,
                description=server_data.get('description', ''),
                url=server_data.get('url'),
                command=server_data.get('command'),
                args=server_data.get('args'),
                env=server_data.get('env'),
                headers=server_data.get('headers'),
                auto_connect=server_data.get('auto_connect', True),
                enabled=server_data.get('enabled', True),
                status=MCPConnectionStatus.DISCONNECTED,
                favicon_url=server_data.get('favicon_url')
            )

            # Generate server ID if not already set
            if not server_config.server_id:
                server_config.server_id = server_config.generate_server_id()

            server_id = server_config.server_id

            # Add server to backend
            success = config_manager.add_server(server_config)
            if not success:
                raise HTTPException(status_code=500, detail="Failed to create server")

            server_to_add = server_config
            logger.info(f"   ✅ Created new server: {server_config.name} ({server_id})")

        # Try to connect and discover capabilities (matching main app logic)
        from vmcp.backend.mcps.mcp_client import MCPClientManager, AuthenticationError

        try:
            logger.info(f"   🔗 Attempting to connect to server: {server_name}")
            client_manager = MCPClientManager(config_manager)
            mcp_server = config_manager.get_server(server_id)

            if mcp_server:
                # Ping the server to get current status
                try:
                    current_status = await client_manager.ping_server(mcp_server.server_id)
                    logger.info(f"   🔍 Server {mcp_server.server_id}: ping result = {current_status.value}")
                except AuthenticationError as e:
                    import traceback
                    logger.error(f"   ❌ Traceback: {traceback.format_exc()}")
                    logger.error(f"   ❌ Authentication error for server {mcp_server.server_id}: {e}")
                    current_status = MCPConnectionStatus.AUTH_REQUIRED
                except asyncio.CancelledError as e:
                    logger.warning(f"   ⚠️ Connection to server {mcp_server.server_id} was cancelled")
                    current_status = MCPConnectionStatus.ERROR
                except ExceptionGroup as e:
                    logger.error(f"   ❌ ExceptionGroup while pinging server {mcp_server.server_id}: {len(e.exceptions)} sub-exceptions")
                    current_status = MCPConnectionStatus.ERROR
                except Exception as e:
                    import traceback
                    logger.error(f"   ❌ Traceback: {traceback.format_exc()}")
                    logger.error(f"   ❌ Error pinging server {mcp_server.server_id}: {e}")
                    current_status = MCPConnectionStatus.UNKNOWN

                mcp_server.status = current_status

                # Discover capabilities
                try:
                    capabilities = await client_manager.discover_capabilities(mcp_server.server_id)
                except Exception as e:
                    import traceback
                    logger.error(f"   ❌ Traceback: {traceback.format_exc()}")
                    logger.error(f"   ❌ Error discovering capabilities for server {mcp_server.server_id}: {e}")
                    capabilities = None

                if capabilities:
                    # Update server config with discovered capabilities
                    if capabilities.get('tools',[]):
                        mcp_server.tools = capabilities.get('tools', [])
                    if capabilities.get('resources',[]):
                        mcp_server.resources = capabilities.get('resources', [])
                    if capabilities.get('prompts',[]):
                        mcp_server.prompts = capabilities.get('prompts', [])
                    if capabilities.get('tool_details',[]):
                        mcp_server.tool_details = capabilities.get('tool_details', [])
                    if capabilities.get('resource_details',[]):
                        mcp_server.resource_details = capabilities.get('resource_details', [])
                    if capabilities.get('resource_templates',[]):
                        mcp_server.resource_templates = capabilities.get('resource_templates', [])
                    if capabilities.get('resource_template_details',[]):
                        mcp_server.resource_template_details = capabilities.get('resource_template_details', [])
                    if capabilities.get('prompt_details',[]):
                        mcp_server.prompt_details = capabilities.get('prompt_details', [])

                    mcp_server.capabilities = {
                        "tools": bool(mcp_server.tools and len(mcp_server.tools) > 0),
                        "resources": bool(mcp_server.resources and len(mcp_server.resources) > 0),
                        "prompts": bool(mcp_server.prompts and len(mcp_server.prompts) > 0)
                    }

                    # Save updated config with capabilities
                    config_manager.update_server_config(server_id, mcp_server)
                    logger.info(f"   ✅ Updated server config with discovered capabilities")

                # Update server_to_add with the latest data
                server_to_add = mcp_server

        except Exception as e:
            import traceback
            logger.error(f"   ❌ Error during server connection/capability discovery: {e}")
            logger.error(f"   ❌ Traceback: {traceback.format_exc()}")
            # Continue even if connection fails - server can be added and connected later

        # Add server to vMCP configuration
        server_for_vmcp = server_to_add.to_dict_for_vmcp()

        # Update vMCP config
        updated_vmcp_config = vmcp_config.vmcp_config.copy() if vmcp_config.vmcp_config else {}

        # Add server to selected_servers
        selected_servers = updated_vmcp_config.get('selected_servers', [])
        if not any(s.get('server_id') == server_for_vmcp.get('server_id') for s in selected_servers):
            selected_servers.append(server_for_vmcp)
            updated_vmcp_config['selected_servers'] = selected_servers

        # Auto-select all tools, prompts, and resources
        selected_tools = updated_vmcp_config.get('selected_tools', {})
        selected_prompts = updated_vmcp_config.get('selected_prompts', {})
        selected_resources = updated_vmcp_config.get('selected_resources', {})

        selected_tools[server_for_vmcp.get('server_id')] = []
        selected_prompts[server_for_vmcp.get('server_id')] = []
        selected_resources[server_for_vmcp.get('server_id')] = []

        updated_vmcp_config['selected_tools'] = selected_tools
        updated_vmcp_config['selected_prompts'] = selected_prompts
        updated_vmcp_config['selected_resources'] = selected_resources

        # Save updated vMCP config
        save_success = vmcp_manager.update_vmcp_config(
            vmcp_id=vmcp_id,
            vmcp_config=updated_vmcp_config
        )

        if not save_success:
            raise HTTPException(status_code=500, detail="Failed to update vMCP configuration")

        # Reload updated vMCP config
        updated_vmcp = vmcp_manager.load_vmcp_config()

        logger.info(f"✅ Successfully added server {server_to_add.name} to vMCP {vmcp_id}")

        return {
            "success": True,
            "message": f"Server '{server_to_add.name}' added to vMCP successfully",
            "vmcp_config": updated_vmcp,
            "server": server_for_vmcp
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"   ❌ Error adding server to vMCP '{vmcp_id}': {e}")
        logger.error(f"   ❌ Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to add server to vMCP: {str(e)}")


@router.delete("/{vmcp_id}/remove-server")
@trace_async("vmcp.servers.remove")
async def remove_server_from_vmcp(
    vmcp_id: str,
    server_id: str,
    user_context: UserContext = Depends(get_user_context)
):
    """Remove a server from a vMCP configuration"""
    logger.info(f"📋 Remove server from vMCP endpoint called for vmcp_id: {vmcp_id}")

    try:
        vmcp_manager = VMCPConfigManager(user_context.user_id, vmcp_id)

        # Load vMCP config
        vmcp_config = vmcp_manager.load_vmcp_config()
        if not vmcp_config:
            raise HTTPException(status_code=404, detail=f"vMCP '{vmcp_id}' not found")

        # Update vMCP config
        updated_vmcp_config = vmcp_config.vmcp_config.copy() if vmcp_config.vmcp_config else {}

        # Remove server from selected_servers
        selected_servers = updated_vmcp_config.get('selected_servers', [])
        updated_vmcp_config['selected_servers'] = [s for s in selected_servers if s.get('server_id') != server_id]

        # Remove from selections
        selected_tools = updated_vmcp_config.get('selected_tools', {})
        selected_prompts = updated_vmcp_config.get('selected_prompts', {})
        selected_resources = updated_vmcp_config.get('selected_resources', {})

        selected_tools.pop(server_id, None)
        selected_prompts.pop(server_id, None)
        selected_resources.pop(server_id, None)

        # Save updated vMCP config
        save_success = vmcp_manager.update_vmcp_config(
            vmcp_id=vmcp_id,
            vmcp_config=updated_vmcp_config
        )

        if not save_success:
            raise HTTPException(status_code=500, detail="Failed to update vMCP configuration")

        # Reload updated vMCP config
        updated_vmcp = vmcp_manager.load_vmcp_config()

        logger.info(f"✅ Successfully removed server {server_id} from vMCP {vmcp_id}")

        return {
            "success": True,
            "message": f"Server removed from vMCP successfully",
            "vmcp_config": updated_vmcp,
            "server": None
        }

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        logger.error(f"   ❌ Error removing server from vMCP '{vmcp_id}': {e}")
        logger.error(f"   ❌ Full traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to remove server from vMCP: {str(e)}")


# ============================================================================
# Capability Endpoints (Tools, Resources, Prompts)
# ============================================================================

@router.get("/{vmcp_id}/tools")
@trace_async("vmcp.tools.list")
async def list_tools(
    vmcp_id: str,
    user_context: UserContext = Depends(get_user_context)
):
    """
    List all tools available in a vMCP.

    Args:
        vmcp_id: vMCP identifier

    Returns:
        List of tools from all servers and custom tools
    """
    logger.info(f"Listing tools for vMCP: {vmcp_id}")

    try:
        manager = VMCPConfigManager(user_id=user_context.user_id, vmcp_id=vmcp_id)
        tools = await manager.tools_list()

        return {
            "tools": [tool.model_dump(mode="json") for tool in tools],
            "total": len(tools)
        }

    except Exception as e:
        logger.error(f"Failed to list tools for vMCP {vmcp_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list tools: {str(e)}"
        )


@router.get("/{vmcp_id}/resources")
@trace_async("vmcp.resources.list")
async def list_resources(
    vmcp_id: str,
    user_context: UserContext = Depends(get_user_context)
):
    """
    List all resources available in a vMCP.

    Args:
        vmcp_id: vMCP identifier

    Returns:
        List of resources from all servers and custom resources
    """
    logger.info(f"Listing resources for vMCP: {vmcp_id}")

    try:
        manager = VMCPConfigManager(user_id=user_context.user_id, vmcp_id=vmcp_id)
        resources = await manager.resources_list()

        return {
            "resources": [resource.model_dump(mode="json") for resource in resources],
            "total": len(resources)
        }

    except Exception as e:
        logger.error(f"Failed to list resources for vMCP {vmcp_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list resources: {str(e)}"
        )


@router.get("/{vmcp_id}/resource-templates")
@trace_async("vmcp.resource_templates.list")
async def list_resource_templates(
    vmcp_id: str,
    user_context: UserContext = Depends(get_user_context)
):
    """
    List all resource templates available in a vMCP.

    Args:
        vmcp_id: vMCP identifier

    Returns:
        List of resource templates
    """
    logger.info(f"Listing resource templates for vMCP: {vmcp_id}")

    try:
        manager = VMCPConfigManager(user_id=user_context.user_id, vmcp_id=vmcp_id)
        templates = await manager.resource_templates_list()

        return {
            "resource_templates": [template.model_dump(mode="json") for template in templates],
            "total": len(templates)
        }

    except Exception as e:
        logger.error(f"Failed to list resource templates for vMCP {vmcp_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list resource templates: {str(e)}"
        )


@router.get("/{vmcp_id}/prompts")
@trace_async("vmcp.prompts.list")
async def list_prompts(
    vmcp_id: str,
    user_context: UserContext = Depends(get_user_context)
):
    """
    List all prompts available in a vMCP.

    Args:
        vmcp_id: vMCP identifier

    Returns:
        List of prompts from all servers and custom prompts
    """
    logger.info(f"Listing prompts for vMCP: {vmcp_id}")

    try:
        manager = VMCPConfigManager(user_id=user_context.user_id, vmcp_id=vmcp_id)
        prompts = await manager.prompts_list()

        return {
            "prompts": [prompt.model_dump(mode="json") for prompt in prompts],
            "total": len(prompts)
        }

    except Exception as e:
        logger.error(f"Failed to list prompts for vMCP {vmcp_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list prompts: {str(e)}"
        )


# ============================================================================
# Execution Endpoints (Call Tool, Get Resource, Get Prompt)
# ============================================================================

@router.post("/{vmcp_id}/tools/call")
@trace_async("vmcp.tools.call")
async def call_tool(
    vmcp_id: str,
    request: VMCPToolCallRequest,
    user_context: UserContext = Depends(get_user_context)
):
    """
    Execute a tool in a vMCP.

    Args:
        vmcp_id: vMCP identifier
        request: Tool call request with tool name and arguments

    Returns:
        Tool execution result
    """
    logger.info(f"Calling tool {request.tool_name} in vMCP {vmcp_id}")

    try:
        manager = VMCPConfigManager(user_id=user_context.user_id, vmcp_id=vmcp_id)
        result = await manager.call_tool(request)

        return {
            "success": True,
            "result": result.model_dump(mode="json") if hasattr(result, 'model_dump') else result
        }

    except Exception as e:
        logger.error(f"Failed to call tool {request.tool_name} in vMCP {vmcp_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to call tool: {str(e)}"
        )


@router.post("/{vmcp_id}/resources/get")
@trace_async("vmcp.resources.get")
async def get_resource(
    vmcp_id: str,
    request: VMCPResourceRequest,
    user_context: UserContext = Depends(get_user_context)
):
    """
    Get a resource from a vMCP.

    Args:
        vmcp_id: vMCP identifier
        request: Resource request with resource URI

    Returns:
        Resource contents
    """
    logger.info(f"Getting resource {request.uri} in vMCP {vmcp_id}")

    try:
        manager = VMCPConfigManager(user_id=user_context.user_id, vmcp_id=vmcp_id)
        result = await manager.get_resource(request.uri)

        return {
            "success": True,
            "result": result.model_dump(mode="json") if hasattr(result, 'model_dump') else result
        }

    except Exception as e:
        logger.error(f"Failed to get resource {request.uri} in vMCP {vmcp_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get resource: {str(e)}"
        )


@router.post("/{vmcp_id}/prompts/get")
@trace_async("vmcp.prompts.get")
async def get_prompt(
    vmcp_id: str,
    prompt_id: str,
    arguments: Optional[Dict[str, Any]] = None,
    user_context: UserContext = Depends(get_user_context)
):
    """
    Get a prompt from a vMCP.

    Args:
        vmcp_id: vMCP identifier
        prompt_id: Prompt identifier
        arguments: Optional prompt arguments

    Returns:
        Prompt result
    """
    logger.info(f"Getting prompt {prompt_id} in vMCP {vmcp_id}")

    try:
        manager = VMCPConfigManager(user_id=user_context.user_id, vmcp_id=vmcp_id)
        result = await manager.get_prompt(prompt_id, arguments or {})

        return {
            "success": True,
            "result": result.model_dump(mode="json") if hasattr(result, 'model_dump') else result
        }

    except Exception as e:
        logger.error(f"Failed to get prompt {prompt_id} in vMCP {vmcp_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get prompt: {str(e)}"
        )


@router.get("/{vmcp_id}/prompts/system")
@trace_async("vmcp.prompts.system")
async def get_system_prompt(
    vmcp_id: str,
    arguments: Optional[Dict[str, Any]] = None,
    user_context: UserContext = Depends(get_user_context)
):
    """
    Get the system prompt for a vMCP.

    Args:
        vmcp_id: vMCP identifier
        arguments: Optional arguments for variable substitution

    Returns:
        System prompt result
    """
    logger.info(f"Getting system prompt for vMCP {vmcp_id}")

    try:
        manager = VMCPConfigManager(user_id=user_context.user_id, vmcp_id=vmcp_id)
        result = await manager.get_system_prompt(arguments or {})

        return {
            "success": True,
            "result": result.model_dump(mode="json") if hasattr(result, 'model_dump') else result
        }

    except Exception as e:
        logger.error(f"Failed to get system prompt for vMCP {vmcp_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system prompt: {str(e)}"
        )
