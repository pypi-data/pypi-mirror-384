"""
MCP Server models and schemas.

Defines data structures for MCP server configuration, authentication, and status.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from enum import Enum
from dataclasses import dataclass, asdict, field
from datetime import datetime


class MCPTransportType(Enum):
    """MCP transport protocol types."""
    STDIO = "stdio"
    HTTP = "http"
    SSE = "sse"


class MCPConnectionStatus(Enum):
    """MCP connection status."""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    AUTH_REQUIRED = "auth_required"
    ERROR = "error"
    UNKNOWN = "unknown"
    NOT_FOUND = "not_found"


class MCPInstallRequest(BaseModel):
    """Request model for installing/adding a new MCP server."""

    name: str = Field(..., description="Unique name for the MCP server")
    mode: str = Field(..., description="Transport mode: stdio, http, or sse")
    description: Optional[str] = Field(None, description="Server description")

    # For stdio servers
    command: Optional[str] = Field(None, description="Command to run for stdio server")
    args: Optional[List[str]] = Field(None, description="Command arguments")
    env: Optional[Dict[str, str]] = Field(None, description="Environment variables")

    # For HTTP/SSE servers
    url: Optional[str] = Field(None, description="Server URL for http/sse mode")
    headers: Optional[Dict[str, str]] = Field(None, description="HTTP headers")

    # Authentication
    auth_type: Optional[str] = Field("none", description="Auth type: none, oauth, bearer, basic")
    client_id: Optional[str] = Field(None, description="OAuth client ID")
    client_secret: Optional[str] = Field(None, description="OAuth client secret")
    auth_url: Optional[str] = Field(None, description="OAuth authorization URL")
    token_url: Optional[str] = Field(None, description="OAuth token URL")
    scope: Optional[str] = Field(None, description="OAuth scope")
    access_token: Optional[str] = Field(None, description="Bearer token")

    # Settings
    auto_connect: bool = Field(True, description="Auto-connect on startup")
    enabled: bool = Field(True, description="Server enabled")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "filesystem-server",
                "mode": "stdio",
                "command": "npx",
                "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"],
                "description": "MCP server for filesystem operations",
                "auto_connect": True,
                "enabled": True
            }
        }


class MCPUpdateRequest(BaseModel):
    """Request model for updating MCP server configuration."""

    name: Optional[str] = Field(None, description="New name for the server")
    description: Optional[str] = Field(None, description="New description")
    enabled: Optional[bool] = Field(None, description="Enable/disable server")
    auto_connect: Optional[bool] = Field(None, description="Auto-connect on startup")

    # Transport settings
    command: Optional[str] = Field(None, description="Command (stdio only)")
    args: Optional[List[str]] = Field(None, description="Arguments (stdio only)")
    env: Optional[Dict[str, str]] = Field(None, description="Environment variables")
    url: Optional[str] = Field(None, description="Server URL (http/sse only)")
    headers: Optional[Dict[str, str]] = Field(None, description="HTTP headers")


class MCPServerInfo(BaseModel):
    """Information about an MCP server."""

    name: str
    server_id: str
    transport_type: str
    status: str
    description: Optional[str] = None
    url: Optional[str] = None
    command: Optional[str] = None
    last_connected: Optional[str] = None
    last_error: Optional[str] = None
    capabilities: Optional[Dict[str, Any]] = None
    tools: Optional[List[str]] = None
    resources: Optional[List[str]] = None
    prompts: Optional[List[str]] = None
    auto_connect: bool = True
    enabled: bool = True


class MCPToolCallRequest(BaseModel):
    """Request for calling an MCP tool."""

    tool_name: str = Field(..., description="Name of the tool to call")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Tool arguments")


class MCPResourceRequest(BaseModel):
    """Request for reading an MCP resource."""

    uri: str = Field(..., description="Resource URI")


class MCPPromptRequest(BaseModel):
    """Request for getting an MCP prompt."""

    prompt_name: str = Field(..., description="Name of the prompt")
    arguments: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Prompt arguments")


class RenameServerRequest(BaseModel):
    """Request for renaming an MCP server."""

    new_name: str = Field(..., description="New name for the server")


@dataclass
class MCPAuthConfig:
    """MCP Authentication configuration."""

    type: str  # "oauth", "bearer", "basic", "none"
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    auth_url: Optional[str] = None
    token_url: Optional[str] = None
    scope: Optional[str] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        if self.expires_at:
            data['expires_at'] = self.expires_at.isoformat()
        return data


@dataclass
class MCPServerConfig:
    """Complete MCP Server configuration."""

    name: str
    transport_type: MCPTransportType
    description: Optional[str] = None
    server_id: Optional[str] = None
    favicon_url: Optional[str] = None

    # For stdio servers
    command: Optional[str] = None
    args: Optional[List[str]] = None
    env: Optional[Dict[str, str]] = None

    # For HTTP/SSE servers
    url: Optional[str] = None
    headers: Optional[Dict[str, str]] = None

    # Authentication
    auth: Optional[MCPAuthConfig] = None

    # Session ID for persistence
    session_id: Optional[str] = None

    # Status and metadata
    status: MCPConnectionStatus = MCPConnectionStatus.UNKNOWN
    last_connected: Optional[datetime] = None
    last_error: Optional[str] = None

    # Capabilities from server
    capabilities: Optional[Dict[str, Any]] = field(default_factory=dict)
    tools: Optional[List[str]] = field(default_factory=list)
    tool_details: Optional[List[Any]] = field(default_factory=list)  # Full Tool objects with schemas
    resources: Optional[List[str]] = field(default_factory=list)  # Resource URIs for backward compatibility
    resource_details: Optional[List[Any]] = field(default_factory=list)  # Full Resource objects with metadata
    resource_templates: Optional[List[str]] = field(default_factory=list)  # Resource template names
    resource_template_details: Optional[List[Any]] = field(default_factory=list)  # Full ResourceTemplate objects
    prompts: Optional[List[str]] = field(default_factory=list)  # Prompt names for backward compatibility
    prompt_details: Optional[List[Any]] = field(default_factory=list)  # Full Prompt objects with schemas

    # Settings
    auto_connect: bool = True
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        data = asdict(self)
        data['transport_type'] = self.transport_type.value
        data['status'] = self.status.value

        if self.auth:
            data['auth'] = self.auth.to_dict()

        if self.last_connected:
            data['last_connected'] = self.last_connected.isoformat()

        # Handle MCP type objects serialization (Tool, Resource, Prompt, etc.)
        if self.tool_details:
            data['tool_details'] = [self._serialize_mcp_object(tool) for tool in self.tool_details]

        if self.resource_details:
            data['resource_details'] = [self._serialize_mcp_object(resource) for resource in self.resource_details]

        if self.resource_template_details:
            data['resource_template_details'] = [self._serialize_mcp_object(template) for template in self.resource_template_details]

        if self.prompt_details:
            data['prompt_details'] = [self._serialize_mcp_object(prompt) for prompt in self.prompt_details]

        return data

    def _serialize_mcp_object(self, obj) -> Dict[str, Any]:
        """Serialize MCP objects (Tool, Resource, etc.) to dictionary"""
        if hasattr(obj, 'model_dump'):
            # Pydantic model
            return obj.model_dump(mode='json')
        elif hasattr(obj, '__dataclass_fields__'):
            # Dataclass (like MCP Tool, Resource, etc.)
            return asdict(obj)
        else:
            # Fallback - try to convert to dict
            return obj if isinstance(obj, dict) else str(obj)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MCPServerConfig':
        """Create from dictionary (JSON deserialization)"""
        # Handle enum deserialization
        data['transport_type'] = MCPTransportType(data['transport_type'])
        data['status'] = MCPConnectionStatus(data['status'])

        # Handle datetime deserialization
        if data.get('last_connected'):
            data['last_connected'] = datetime.fromisoformat(data['last_connected'])

        # Handle auth object
        if data.get('auth'):
            auth_data = data['auth']
            if auth_data.get('expires_at'):
                auth_data['expires_at'] = datetime.fromisoformat(auth_data['expires_at'])
            data['auth'] = MCPAuthConfig(**auth_data)

        # Handle null values for list fields - convert to empty lists
        list_fields = [
            'args', 'tools', 'tool_details', 'resources', 'resource_details',
            'resource_templates', 'resource_template_details', 'prompts', 'prompt_details'
        ]
        for field in list_fields:
            if data.get(field) is None:
                data[field] = []

        # Handle null values for dict fields - convert to empty dicts
        # Also handle string values (might be serialized JSON)
        dict_fields = ['env', 'headers', 'capabilities']
        for field in dict_fields:
            value = data.get(field)
            if value is None:
                data[field] = {}
            elif isinstance(value, str):
                # If it's a string, try to parse as JSON, otherwise use empty dict
                try:
                    import json
                    data[field] = json.loads(value) if value else {}
                except (json.JSONDecodeError, ValueError):
                    data[field] = {}
            elif not isinstance(value, dict):
                # If it's not None, string, or dict, use empty dict
                data[field] = {}

        return cls(**data)

    def to_dict_for_vmcp(self) -> Dict[str, Any]:
        """Convert to dictionary for vMCP usage, excluding auth and session_id fields"""
        data = self.to_dict()

        # Remove auth and session_id fields for vMCP usage
        data.pop('auth', None)
        data.pop('session_id', None)

        return data

    def generate_server_id(self) -> str:
        """Generate a unique server ID based on configuration."""
        import hashlib
        import json

        # Create a deterministic hash based on server configuration
        config_str = json.dumps({
            'name': self.name,
            'transport_type': self.transport_type.value,
            'command': self.command,
            'url': self.url,
        }, sort_keys=True)

        return hashlib.sha256(config_str.encode()).hexdigest()[:16]
