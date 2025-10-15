"""
Database models for vMCP OSS version.

Simplified models without authentication - uses a single dummy user for all operations.
Only includes essential tables: User (dummy), MCP servers, VMCPs, stats, and logs.
"""

import json
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Text, Boolean, Index, TypeDecorator
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


# SQLite-compatible JSON type
class JSONType(TypeDecorator):
    """Platform-independent JSON type.

    Uses JSON for PostgreSQL, Text for SQLite.
    """
    impl = Text
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value)
        return value

    def process_result_value(self, value, dialect):
        if value is not None:
            return json.loads(value)
        return value


class User(Base):
    """
    Dummy user model for OSS version.

    In OSS, there's always a single local user. This simplifies the codebase
    while keeping the API structure consistent for future auth extensions.
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    mcp_servers = relationship("MCPServer", back_populates="user", cascade="all, delete-orphan")
    vmcps = relationship("VMCP", back_populates="user", cascade="all, delete-orphan")
    vmcp_environments = relationship("VMCPEnvironment", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}')>"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"


class MCPServer(Base):
    """
    MCP Server configuration model.

    Stores individual MCP servers that can be connected to and used.
    Each server has its own configuration, transport type, and authentication settings.
    """
    __tablename__ = "mcp_servers"

    # Primary identifier (composite of user_id and server_id)
    id = Column(String(255), primary_key=True, index=True)

    # User relationship (always the dummy user in OSS)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # MCP server identification
    server_id = Column(String(255), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Configuration stored as JSON
    # Contains: transport_type, command/url, args, env, auth_config, etc.
    mcp_server_config = Column(JSONType, nullable=False)

    # OAuth state for MCP server authentication
    # Stores access tokens and refresh tokens for OAuth-enabled MCP servers
    oauth_state = Column(JSONType, nullable=True)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="mcp_servers")
    vmcp_mappings = relationship("VMCPMCPMapping", back_populates="mcp_server", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<MCPServer(id='{self.id}', server_id='{self.server_id}', name='{self.name}')>"


class VMCP(Base):
    """
    Virtual MCP (vMCP) configuration model.

    A vMCP aggregates multiple MCP servers into a single unified interface.
    It provides a consolidated view of tools, resources, and prompts from multiple servers.
    """
    __tablename__ = "vmcps"

    # Primary identifier (composite of user_id and vmcp_id)
    id = Column(String(255), primary_key=True, index=True)

    # User relationship (always the dummy user in OSS)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # vMCP identification
    vmcp_id = Column(String(255), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Configuration stored as JSON
    # Contains: list of mcp_server_ids, tool mappings, resource mappings, etc.
    vmcp_config = Column(JSONType, nullable=False)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="vmcps")
    mcp_mappings = relationship("VMCPMCPMapping", back_populates="vmcp", cascade="all, delete-orphan")
    environments = relationship("VMCPEnvironment", back_populates="vmcp", cascade="all, delete-orphan")
    stats = relationship("VMCPStats", back_populates="vmcp", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<VMCP(id='{self.id}', vmcp_id='{self.vmcp_id}', name='{self.name}')>"


class VMCPMCPMapping(Base):
    """
    Mapping between VMCPs and MCP Servers.

    Defines which MCP servers are included in each vMCP and their configuration.
    """
    __tablename__ = "vmcp_mcp_mappings"

    id = Column(Integer, primary_key=True, index=True)

    # Foreign keys
    vmcp_id = Column(String(255), ForeignKey("vmcps.id"), nullable=False, index=True)
    mcp_server_id = Column(String(255), ForeignKey("mcp_servers.id"), nullable=False, index=True)

    # Mapping configuration (tool filters, resource filters, etc.)
    mapping_config = Column(JSONType, nullable=True)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    # Relationships
    vmcp = relationship("VMCP", back_populates="mcp_mappings")
    mcp_server = relationship("MCPServer", back_populates="vmcp_mappings")

    # Unique constraint
    __table_args__ = (
        Index('idx_vmcp_mcp_unique', 'vmcp_id', 'mcp_server_id', unique=True),
    )

    def __repr__(self):
        return f"<VMCPMCPMapping(vmcp_id='{self.vmcp_id}', mcp_server_id='{self.mcp_server_id}')>"


class VMCPEnvironment(Base):
    """
    Environment variables for VMCPs.

    Stores environment variables that are injected when executing tools
    from MCP servers within a vMCP.
    """
    __tablename__ = "vmcp_environments"

    id = Column(String(255), primary_key=True, index=True)

    # Foreign keys
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    vmcp_id = Column(String(255), ForeignKey("vmcps.id"), nullable=False, index=True)

    # Environment variables as JSON
    environment_vars = Column(JSONType, nullable=False, default={})

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="vmcp_environments")
    vmcp = relationship("VMCP", back_populates="environments")

    def __repr__(self):
        return f"<VMCPEnvironment(vmcp_id='{self.vmcp_id}')>"


class VMCPStats(Base):
    """
    Usage statistics for VMCPs.

    Tracks tool calls, resource reads, prompt usage, and errors for analytics.
    """
    __tablename__ = "vmcp_stats"

    id = Column(Integer, primary_key=True, index=True)

    # Foreign key
    vmcp_id = Column(String(255), ForeignKey("vmcps.id"), nullable=False, index=True)

    # Operation details
    operation_type = Column(String(50), nullable=False, index=True)  # tool_call, resource_read, prompt_get
    operation_name = Column(String(255), nullable=False)  # Name of tool/resource/prompt
    mcp_server_id = Column(String(255), nullable=True, index=True)  # Which MCP server was used

    # Success/failure
    success = Column(Boolean, nullable=False, default=True)
    error_message = Column(Text, nullable=True)

    # Timing
    duration_ms = Column(Integer, nullable=True)  # Operation duration in milliseconds

    # Additional metadata
    operation_metadata = Column(JSONType, nullable=True)  # Additional operation metadata

    # Timestamp
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)

    # Relationships
    vmcp = relationship("VMCP", back_populates="stats")

    # Indexes for querying
    __table_args__ = (
        Index('idx_stats_vmcp_created', 'vmcp_id', 'created_at'),
        Index('idx_stats_operation_type', 'vmcp_id', 'operation_type'),
    )

    def __repr__(self):
        return f"<VMCPStats(vmcp_id='{self.vmcp_id}', operation='{self.operation_type}:{self.operation_name}', success={self.success})>"


class ThirdPartyOAuthState(Base):
    """
    OAuth state for third-party MCP server authentication.

    Stores OAuth state data during the OAuth flow for MCP servers
    that require OAuth authentication.
    """
    __tablename__ = "third_party_oauth_states"

    id = Column(Integer, primary_key=True, index=True)
    state = Column(String(255), unique=True, nullable=False, index=True)
    state_data = Column(JSONType, nullable=False)

    # Expiration
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)

    def __repr__(self):
        return f"<ThirdPartyOAuthState(state='{self.state}')>"


class ApplicationLog(Base):
    """
    Application logs for debugging and monitoring.

    Stores important application events, errors, and debug information.
    """
    __tablename__ = "application_logs"

    id = Column(Integer, primary_key=True, index=True)

    # Log details
    level = Column(String(20), nullable=False, index=True)  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    logger_name = Column(String(255), nullable=False, index=True)
    message = Column(Text, nullable=False)

    # Context
    vmcp_id = Column(String(255), nullable=True, index=True)
    mcp_server_id = Column(String(255), nullable=True, index=True)

    # Additional data
    log_metadata = Column(JSONType, nullable=True)
    traceback = Column(Text, nullable=True)

    # Timestamp
    created_at = Column(DateTime, server_default=func.now(), nullable=False, index=True)

    # Indexes
    __table_args__ = (
        Index('idx_logs_level_created', 'level', 'created_at'),
        Index('idx_logs_vmcp_created', 'vmcp_id', 'created_at'),
    )

    def __repr__(self):
        return f"<ApplicationLog(level='{self.level}', logger='{self.logger_name}', message='{self.message[:50]}...')>"


class GlobalMCPServerRegistry(Base):
    """
    Global MCP Server Registry - preconfigured public MCP servers.

    This table stores publicly available MCP servers that users can add to their configurations.
    Updated from the preconfigured-servers.json file.
    """
    __tablename__ = "global_mcp_server_registry"

    # Primary identifier
    id = Column(Integer, primary_key=True, index=True)

    # Server identification
    server_id = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Server configuration
    transport_type = Column(String(50), nullable=False)  # http, sse, stdio
    url = Column(String(512), nullable=True)
    headers = Column(JSONType, nullable=True)  # For HTTP/SSE servers

    # Display information
    favicon_url = Column(String(512), nullable=True)
    category = Column(String(100), nullable=True)
    icon = Column(String(20), nullable=True)

    # Authentication
    requires_auth = Column(Boolean, default=False, nullable=False)
    env_vars = Column(Text, nullable=True)  # Environment variables needed

    # Metadata
    note = Column(Text, nullable=True)  # Additional notes or instructions
    enabled = Column(Boolean, default=True, nullable=False)
    status = Column(String(50), default='unknown', nullable=False)  # unknown, available, unavailable

    # Timestamps
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

    # Indexes
    __table_args__ = (
        Index('idx_registry_category', 'category'),
        Index('idx_registry_enabled', 'enabled'),
    )

    def __repr__(self):
        return f"<GlobalMCPServerRegistry(server_id='{self.server_id}', name='{self.name}')>"
