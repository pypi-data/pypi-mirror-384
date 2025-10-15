"""
VMCP models and schemas.

Defines data structures for Virtual MCP configuration and operations.
A VMCP aggregates multiple MCP servers into a unified interface.
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime


class VMCPInfo(BaseModel):
    """Information about a Virtual MCP."""
    id: str
    name: str
    description: Optional[str] = None
    mcp_server_ids: List[str] = Field(default_factory=list, description="List of MCP server IDs in this vMCP")
    total_tools: int = 0
    total_resources: int = 0
    total_prompts: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class VMCPCreateRequest(BaseModel):
    """Request model for creating a new vMCP."""
    name: str = Field(..., description="vMCP name")
    description: Optional[str] = Field(None, description="vMCP description")
    mcp_server_ids: List[str] = Field(default_factory=list, description="List of MCP server IDs to include")
    environment_variables: Optional[Dict[str, str]] = Field(default_factory=dict, description="Environment variables")


class VMCPUpdateRequest(BaseModel):
    """Request model for updating a vMCP."""
    name: Optional[str] = Field(None, description="New vMCP name")
    description: Optional[str] = Field(None, description="New description")
    mcp_server_ids: Optional[List[str]] = Field(None, description="Updated list of MCP server IDs")
    environment_variables: Optional[Dict[str, str]] = Field(None, description="Updated environment variables")


class VMCPToolCallRequest(BaseModel):
    """Request for calling a tool through vMCP."""
    tool_name: str = Field(..., description="Name of the tool to call")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Tool arguments")


class VMCPResourceRequest(BaseModel):
    """Request for reading a resource through vMCP."""
    uri: str = Field(..., description="Resource URI")


class VMCPPromptRequest(BaseModel):
    """Request for getting a prompt through vMCP."""
    prompt_name: str = Field(..., description="Name of the prompt")
    arguments: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Prompt arguments")


class StatsFilterRequest(BaseModel):
    """Request for filtering stats."""
    vmcp_id: Optional[str] = None
    operation_type: Optional[str] = None  # tool_call, resource_read, prompt_get
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    limit: int = Field(default=100, le=1000)


class StatsSummary(BaseModel):
    """Summary statistics for a vMCP."""
    vmcp_id: str
    total_operations: int
    successful_operations: int
    failed_operations: int
    avg_duration_ms: Optional[float] = None
    operations_by_type: Dict[str, int] = Field(default_factory=dict)
    operations_by_server: Dict[str, int] = Field(default_factory=dict)


class LogEntry(BaseModel):
    """Log entry for vMCP operations."""
    id: int
    vmcp_id: str
    operation_type: str
    operation_name: str
    mcp_server_id: Optional[str] = None
    success: bool
    error_message: Optional[str] = None
    duration_ms: Optional[int] = None
    created_at: str


class StatsResponse(BaseModel):
    """Response containing stats data."""
    summary: StatsSummary
    recent_logs: List[LogEntry] = Field(default_factory=list)


@dataclass
class VMCPConfig:
    """
    Complete vMCP configuration.

    A vMCP aggregates multiple MCP servers and provides a unified interface
    to their tools, resources, and prompts.
    """
    id: str
    name: str
    user_id: str  # Changed from int to str to match main app
    description: Optional[str] = None

    # System prompt configuration
    system_prompt: Optional[Dict[str, Any]] = None

    # vMCP configuration with selected servers, tools, resources, prompts
    vmcp_config: Optional[Dict[str, Any]] = field(default_factory=dict)

    # Custom configurations
    custom_prompts: List[Dict[str, Any]] = field(default_factory=list)
    custom_tools: List[Dict[str, Any]] = field(default_factory=list)
    custom_context: List[str] = field(default_factory=list)
    custom_resources: List[Dict[str, Any]] = field(default_factory=list)
    custom_resource_templates: List[Dict[str, Any]] = field(default_factory=list)
    custom_widgets: List[Dict[str, Any]] = field(default_factory=list)  # Added from main app
    custom_resource_uris: List[str] = field(default_factory=list)
    uploaded_files: List[Dict[str, Any]] = field(default_factory=list)

    # MCP server configuration (legacy compatibility)
    mcp_server_ids: List[str] = field(default_factory=list)

    # Environment variables for this vMCP
    environment_variables: List[Dict[str, Any]] = field(default_factory=list)

    # Cached capabilities (updated when servers are queried)
    total_tools: Optional[int] = None  # Changed from int = 0 to Optional[int] = None
    total_resources: Optional[int] = None
    total_resource_templates: Optional[int] = None
    total_prompts: Optional[int] = None

    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    creator_id: Optional[str] = None  # Added from main app
    creator_username: Optional[str] = None  # Added from main app

    # Sharing fields (for future compatibility)
    is_public: bool = False
    public_tags: List[str] = field(default_factory=list)
    public_at: Optional[str] = None
    is_wellknown: bool = False
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Set default timestamps if not provided."""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

    def to_dict(self, include_environment_variables: bool = True) -> Dict[str, Any]:
        """Convert VMCPConfig to dictionary for JSON serialization."""
        vmcp_dict = {
            "id": self.id,
            "name": self.name,
            "user_id": self.user_id,
            "description": self.description,
            "system_prompt": self.system_prompt,
            "vmcp_config": self.vmcp_config,
            "custom_prompts": self.custom_prompts,
            "custom_tools": self.custom_tools,
            "custom_context": self.custom_context,
            "custom_resources": self.custom_resources,
            "custom_resource_templates": self.custom_resource_templates,
            "custom_widgets": self.custom_widgets,
            "uploaded_files": self.uploaded_files,
            "custom_resource_uris": self.custom_resource_uris,
            "total_tools": self.total_tools,
            "total_resources": self.total_resources,
            "total_resource_templates": self.total_resource_templates,
            "total_prompts": self.total_prompts,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "creator_id": self.creator_id,
            "creator_username": self.creator_username,
            # Sharing fields
            "is_public": self.is_public,
            "public_tags": self.public_tags,
            "public_at": self.public_at,
            "metadata": self.metadata
        }

        # Conditionally include environment variables (for backward compatibility)
        if include_environment_variables:
            vmcp_dict["environment_variables"] = self.environment_variables

        # Handle any enum serialization in the data
        vmcp_dict = self._serialize_enums(vmcp_dict)

        return vmcp_dict

    def _serialize_enums(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively serialize enums in the data dictionary."""
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                if hasattr(value, 'value'):  # Check if it's an enum
                    result[key] = value.value
                elif isinstance(value, dict):
                    result[key] = self._serialize_enums(value)
                elif isinstance(value, list):
                    result[key] = [self._serialize_enums(item) if isinstance(item, dict) else (item.value if hasattr(item, 'value') else item) for item in value]
                else:
                    result[key] = value
            return result
        elif isinstance(data, list):
            return [self._serialize_enums(item) if isinstance(item, dict) else (item.value if hasattr(item, 'value') else item) for item in data]
        else:
            return data.value if hasattr(data, 'value') else data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VMCPConfig':
        """Create VMCPConfig from dictionary."""
        # Handle datetime string conversion
        processed_data = data.copy()

        # Remove legacy/unknown fields that are no longer part of the model
        # This handles backward compatibility with old database records
        legacy_fields = {'agent_config'}  # Add more legacy fields here if needed
        for field_name in legacy_fields:
            processed_data.pop(field_name, None)

        # Convert string timestamps to datetime objects if they exist
        if 'created_at' in processed_data and isinstance(processed_data['created_at'], str):
            try:
                processed_data['created_at'] = datetime.fromisoformat(processed_data['created_at'].replace('Z', '+00:00'))
            except (ValueError, TypeError):
                processed_data['created_at'] = None

        if 'updated_at' in processed_data and isinstance(processed_data['updated_at'], str):
            try:
                processed_data['updated_at'] = datetime.fromisoformat(processed_data['updated_at'].replace('Z', '+00:00'))
            except (ValueError, TypeError):
                processed_data['updated_at'] = None

        return cls(**processed_data)


@dataclass
class AggregatedCapabilities:
    """
    Aggregated capabilities from multiple MCP servers.

    Provides a unified view of all tools, resources, and prompts
    available through a vMCP.
    """
    tools: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    resources: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    prompts: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    # Mapping of capability name to source server
    tool_to_server: Dict[str, str] = field(default_factory=dict)
    resource_to_server: Dict[str, str] = field(default_factory=dict)
    prompt_to_server: Dict[str, str] = field(default_factory=dict)

    def add_tool(self, tool_name: str, tool_data: Dict[str, Any], server_id: str):
        """Add a tool from an MCP server."""
        self.tools[tool_name] = tool_data
        self.tool_to_server[tool_name] = server_id

    def add_resource(self, resource_uri: str, resource_data: Dict[str, Any], server_id: str):
        """Add a resource from an MCP server."""
        self.resources[resource_uri] = resource_data
        self.resource_to_server[resource_uri] = server_id

    def add_prompt(self, prompt_name: str, prompt_data: Dict[str, Any], server_id: str):
        """Add a prompt from an MCP server."""
        self.prompts[prompt_name] = prompt_data
        self.prompt_to_server[prompt_name] = server_id

    def get_tool_server(self, tool_name: str) -> Optional[str]:
        """Get the server ID that provides a tool."""
        return self.tool_to_server.get(tool_name)

    def get_resource_server(self, resource_uri: str) -> Optional[str]:
        """Get the server ID that provides a resource."""
        return self.resource_to_server.get(resource_uri)

    def get_prompt_server(self, prompt_name: str) -> Optional[str]:
        """Get the server ID that provides a prompt."""
        return self.prompt_to_server.get(prompt_name)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'tools': self.tools,
            'resources': self.resources,
            'prompts': self.prompts,
            'tool_to_server': self.tool_to_server,
            'resource_to_server': self.resource_to_server,
            'prompt_to_server': self.prompt_to_server,
            'total_tools': len(self.tools),
            'total_resources': len(self.resources),
            'total_prompts': len(self.prompts),
        }
