"""
Storage base class for vMCP OSS version.

Provides a unified interface for database operations with VMCP and MCP server configurations.
This is a simplified version for OSS - single user, no complex authentication.
"""

import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from vmcp.backend.storage.database import SessionLocal
from vmcp.backend.storage.models import (
    User,
    MCPServer,
    VMCP,
    VMCPMCPMapping,
    VMCPEnvironment,
    VMCPStats,
    ThirdPartyOAuthState,
    ApplicationLog,
)
from vmcp.backend.vmcps.models import VMCPConfig

logger = logging.getLogger(__name__)


class StorageBase:
    """
    Storage abstraction layer for vMCP OSS.

    Provides CRUD operations for vMCPs, MCP servers, and related data.
    Always uses user_id=1 (the dummy user) in OSS version.
    """

    def __init__(self, user_id: int = 1):
        """
        Initialize storage handler.

        Args:
            user_id: User ID (always 1 in OSS version)
        """
        self.user_id = user_id
        logger.debug(f"StorageBase initialized for user {user_id}")

    def _get_session(self) -> Session:
        """Get a new database session."""
        return SessionLocal()

    # ========================== MCP SERVER METHODS ==========================

    def get_mcp_servers(self) -> Dict[str, Any]:
        """Get all MCP servers for the user."""
        session = self._get_session()
        try:
            servers = session.query(MCPServer).filter(
                MCPServer.user_id == self.user_id
            ).all()

            servers_dict = {}
            for server in servers:
                servers_dict[server.server_id] = server.mcp_server_config

            logger.debug(f"Found {len(servers_dict)} MCP servers for user {self.user_id}")
            return servers_dict

        except Exception as e:
            logger.error(f"Error getting MCP servers: {e}")
            return {}
        finally:
            session.close()

    def get_mcp_server_ids(self) -> List[str]:
        """Get list of MCP server IDs for the user."""
        session = self._get_session()
        try:
            servers = session.query(MCPServer.server_id).filter(
                MCPServer.user_id == self.user_id
            ).all()

            server_ids = [server.server_id for server in servers]
            logger.debug(f"Found {len(server_ids)} MCP server IDs")
            return server_ids

        except Exception as e:
            logger.error(f"Error getting MCP server IDs: {e}")
            return []
        finally:
            session.close()

    def get_mcp_server(self, server_id: str) -> Dict[str, Any]:
        """Get MCP server configuration by ID."""
        session = self._get_session()
        try:
            server = session.query(MCPServer).filter(
                MCPServer.user_id == self.user_id,
                MCPServer.server_id == server_id
            ).first()

            if not server:
                logger.warning(f"MCP server not found: {server_id}")
                return {}

            return {
                "server_id": server.server_id,
                "name": server.name,
                "description": server.description,
                "mcp_server_config": server.mcp_server_config,
                "oauth_state": server.oauth_state,
            }

        except Exception as e:
            logger.error(f"Error getting MCP server {server_id}: {e}")
            return {}
        finally:
            session.close()

    def save_mcp_server(self, server_id: str, server_config: Dict[str, Any]) -> bool:
        """Save or update MCP server configuration."""
        session = self._get_session()
        try:
            # Check if server exists
            server = session.query(MCPServer).filter(
                MCPServer.user_id == self.user_id,
                MCPServer.server_id == server_id
            ).first()

            if server:
                # Update existing server
                server.name = server_config.get("name", server.name)
                server.description = server_config.get("description")
                server.mcp_server_config = server_config
                logger.info(f"Updated MCP server: {server_id}")
            else:
                # Create new server
                server = MCPServer(
                    id=f"{self.user_id}_{server_id}",
                    user_id=self.user_id,
                    server_id=server_id,
                    name=server_config.get("name", server_id),
                    description=server_config.get("description"),
                    mcp_server_config=server_config,
                )
                session.add(server)
                logger.info(f"Created new MCP server: {server_id}")

            session.commit()
            return True

        except Exception as e:
            logger.error(f"Error saving MCP server {server_id}: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    def delete_mcp_server(self, server_id: str) -> bool:
        """Delete MCP server by ID."""
        session = self._get_session()
        try:
            server = session.query(MCPServer).filter(
                MCPServer.user_id == self.user_id,
                MCPServer.server_id == server_id
            ).first()

            if server:
                session.delete(server)
                session.commit()
                logger.info(f"Deleted MCP server: {server_id}")
                return True
            else:
                logger.warning(f"MCP server not found for deletion: {server_id}")
                return False

        except Exception as e:
            logger.error(f"Error deleting MCP server {server_id}: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    # ========================== VMCP METHODS ==========================

    def save_vmcp(self, vmcp_id: str, vmcp_config: Dict[str, Any]) -> bool:
        """Save or update vMCP configuration."""
        session = self._get_session()
        try:
            # Check if vMCP exists
            vmcp = session.query(VMCP).filter(
                VMCP.user_id == self.user_id,
                VMCP.vmcp_id == vmcp_id
            ).first()

            if vmcp:
                # Update existing vMCP
                vmcp.name = vmcp_config.get("name", vmcp.name)
                vmcp.description = vmcp_config.get("description")
                vmcp.vmcp_config = vmcp_config
                logger.info(f"Updated vMCP: {vmcp_id}")
            else:
                # Create new vMCP
                vmcp = VMCP(
                    id=f"{self.user_id}_{vmcp_id}",
                    user_id=self.user_id,
                    vmcp_id=vmcp_id,
                    name=vmcp_config.get("name", vmcp_id),
                    description=vmcp_config.get("description"),
                    vmcp_config=vmcp_config,
                )
                session.add(vmcp)
                logger.info(f"Created new vMCP: {vmcp_id}")

            session.commit()
            return True

        except Exception as e:
            logger.error(f"Error saving vMCP {vmcp_id}: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    def load_vmcp_config(self, vmcp_id: str) -> Optional[VMCPConfig]:
        """Load vMCP configuration by ID."""
        session = self._get_session()
        try:
            vmcp = session.query(VMCP).filter(
                VMCP.user_id == self.user_id,
                VMCP.vmcp_id == vmcp_id
            ).first()

            if not vmcp:
                logger.warning(f"vMCP not found: {vmcp_id}")
                return None

            # Load environment variables
            env = session.query(VMCPEnvironment).filter(
                VMCPEnvironment.user_id == self.user_id,
                VMCPEnvironment.vmcp_id == vmcp.id
            ).first()

            vmcp_dict = vmcp.vmcp_config.copy()
            if env and env.environment_vars:
                vmcp_dict["environment_variables"] = env.environment_vars

            # Convert dict to VMCPConfig object
            config = VMCPConfig.from_dict(vmcp_dict)

            logger.debug(f"Loaded vMCP config: {vmcp_id}")
            return config

        except Exception as e:
            logger.error(f"Error loading vMCP {vmcp_id}: {e}")
            return None
        finally:
            session.close()

    def list_vmcps(self) -> List[Dict[str, Any]]:
        """List all vMCP configurations for the user."""
        session = self._get_session()
        try:
            vmcps = session.query(VMCP).filter(
                VMCP.user_id == self.user_id,
                VMCP.vmcp_id.isnot(None)  # Only include records with valid vmcp_id
            ).all()

            vmcp_list = []
            for vmcp in vmcps:
                # Skip if vmcp_id is None (safety check)
                if not vmcp.vmcp_id:
                    logger.warning(f"Skipping vMCP with None vmcp_id: {vmcp.id}")
                    continue

                config = vmcp.vmcp_config or {}
                vmcp_list.append({
                    "id": vmcp.vmcp_id,
                    "vmcp_id": vmcp.vmcp_id,
                    "name": vmcp.name or "Unnamed vMCP",
                    "description": vmcp.description,
                    "total_tools": config.get("total_tools", 0),
                    "total_resources": config.get("total_resources", 0),
                    "total_resource_templates": config.get("total_resource_templates", 0),
                    "total_prompts": config.get("total_prompts", 0),
                    "created_at": vmcp.created_at.isoformat() if vmcp.created_at else None,
                    "updated_at": vmcp.updated_at.isoformat() if vmcp.updated_at else None,
                })

            logger.debug(f"Found {len(vmcp_list)} vMCPs for user {self.user_id}")
            return vmcp_list

        except Exception as e:
            logger.error(f"Error listing vMCPs: {e}")
            return []
        finally:
            session.close()

    def delete_vmcp(self, vmcp_id: str) -> bool:
        """Delete vMCP by ID."""
        session = self._get_session()
        try:
            vmcp = session.query(VMCP).filter(
                VMCP.user_id == self.user_id,
                VMCP.vmcp_id == vmcp_id
            ).first()

            if vmcp:
                session.delete(vmcp)
                session.commit()
                logger.info(f"Deleted vMCP: {vmcp_id}")
                return True
            else:
                logger.warning(f"vMCP not found for deletion: {vmcp_id}")
                return False

        except Exception as e:
            logger.error(f"Error deleting vMCP {vmcp_id}: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    def update_vmcp(self, vmcp_config: VMCPConfig) -> bool:
        """Update an existing VMCP configuration."""
        from datetime import datetime

        # Update the updated_at timestamp
        vmcp_config.updated_at = datetime.now()

        # Save the updated configuration using save_vmcp
        success = self.save_vmcp(vmcp_config.id, vmcp_config.to_dict())

        if success:
            logger.info(f"Successfully updated vMCP: {vmcp_config.id}")
        else:
            logger.error(f"Failed to update vMCP: {vmcp_config.id}")

        return success

    # ========================== VMCP ENVIRONMENT METHODS ==========================

    def save_vmcp_environment(self, vmcp_id: str, environment_vars: Dict[str, str]) -> bool:
        """Save environment variables for a vMCP."""
        session = self._get_session()
        try:
            # Get vMCP internal ID
            vmcp = session.query(VMCP).filter(
                VMCP.user_id == self.user_id,
                VMCP.vmcp_id == vmcp_id
            ).first()

            if not vmcp:
                logger.error(f"vMCP not found: {vmcp_id}")
                return False

            # Check if environment exists
            env = session.query(VMCPEnvironment).filter(
                VMCPEnvironment.user_id == self.user_id,
                VMCPEnvironment.vmcp_id == vmcp.id
            ).first()

            if env:
                # Update existing environment
                env.environment_vars = environment_vars
                logger.info(f"Updated environment for vMCP: {vmcp_id}")
            else:
                # Create new environment
                env = VMCPEnvironment(
                    id=f"{self.user_id}_{vmcp_id}_env",
                    user_id=self.user_id,
                    vmcp_id=vmcp.id,
                    environment_vars=environment_vars,
                )
                session.add(env)
                logger.info(f"Created environment for vMCP: {vmcp_id}")

            session.commit()
            return True

        except Exception as e:
            logger.error(f"Error saving vMCP environment {vmcp_id}: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    def load_vmcp_environment(self, vmcp_id: str) -> Dict[str, str]:
        """Load environment variables for a vMCP."""
        session = self._get_session()
        try:
            # Get vMCP internal ID
            vmcp = session.query(VMCP).filter(
                VMCP.user_id == self.user_id,
                VMCP.vmcp_id == vmcp_id
            ).first()

            if not vmcp:
                logger.warning(f"vMCP not found: {vmcp_id}")
                return {}

            env = session.query(VMCPEnvironment).filter(
                VMCPEnvironment.user_id == self.user_id,
                VMCPEnvironment.vmcp_id == vmcp.id
            ).first()

            if not env:
                logger.debug(f"No environment found for vMCP: {vmcp_id}")
                return {}

            return env.environment_vars or {}

        except Exception as e:
            logger.error(f"Error loading vMCP environment {vmcp_id}: {e}")
            return {}
        finally:
            session.close()

    # ========================== OAUTH STATE METHODS ==========================

    def save_third_party_oauth_state(self, state: str, state_data: Dict[str, Any]) -> bool:
        """Save third-party OAuth state."""
        session = self._get_session()
        try:
            from datetime import datetime, timezone, timedelta

            # Check if state exists
            oauth_state = session.query(ThirdPartyOAuthState).filter(
                ThirdPartyOAuthState.state == state
            ).first()

            expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

            if oauth_state:
                # Update existing state
                oauth_state.state_data = state_data
                oauth_state.expires_at = expires_at
                logger.info(f"Updated OAuth state: {state[:8]}...")
            else:
                # Create new state
                oauth_state = ThirdPartyOAuthState(
                    state=state,
                    state_data=state_data,
                    expires_at=expires_at,
                )
                session.add(oauth_state)
                logger.info(f"Created OAuth state: {state[:8]}...")

            session.commit()
            return True

        except Exception as e:
            logger.error(f"Error saving OAuth state: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    def get_third_party_oauth_state(self, state: str) -> Optional[Dict[str, Any]]:
        """Get third-party OAuth state."""
        session = self._get_session()
        try:
            from datetime import datetime, timezone

            oauth_state = session.query(ThirdPartyOAuthState).filter(
                ThirdPartyOAuthState.state == state
            ).first()

            if not oauth_state:
                logger.warning(f"OAuth state not found: {state[:8]}...")
                return None

            # Check if expired
            if oauth_state.expires_at < datetime.now(timezone.utc):
                logger.warning(f"OAuth state expired: {state[:8]}...")
                session.delete(oauth_state)
                session.commit()
                return None

            return oauth_state.state_data

        except Exception as e:
            logger.error(f"Error getting OAuth state: {e}")
            return None
        finally:
            session.close()

    def delete_third_party_oauth_state(self, state: str) -> bool:
        """Delete third-party OAuth state."""
        session = self._get_session()
        try:
            oauth_state = session.query(ThirdPartyOAuthState).filter(
                ThirdPartyOAuthState.state == state
            ).first()

            if oauth_state:
                session.delete(oauth_state)
                session.commit()
                logger.info(f"Deleted OAuth state: {state[:8]}...")
                return True
            else:
                logger.warning(f"OAuth state not found for deletion: {state[:8]}...")
                return False

        except Exception as e:
            logger.error(f"Error deleting OAuth state: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    # ========================== STATS & LOGGING METHODS ==========================

    def save_vmcp_stats(self, vmcp_id: str, operation_type: str, operation_name: str,
                       success: bool, duration_ms: Optional[int] = None,
                       error_message: Optional[str] = None,
                       operation_metadata: Optional[Dict[str, Any]] = None,
                       mcp_server_id: Optional[str] = None) -> bool:
        """Save vMCP operation statistics."""
        session = self._get_session()
        try:
            # Get vMCP internal ID
            vmcp = session.query(VMCP).filter(
                VMCP.user_id == self.user_id,
                VMCP.vmcp_id == vmcp_id
            ).first()

            if not vmcp:
                logger.error(f"vMCP not found for stats: {vmcp_id}")
                return False

            stats = VMCPStats(
                vmcp_id=vmcp.id,
                operation_type=operation_type,
                operation_name=operation_name,
                mcp_server_id=mcp_server_id,
                success=success,
                error_message=error_message,
                duration_ms=duration_ms,
                operation_metadata=operation_metadata,
            )
            session.add(stats)
            session.commit()

            logger.debug(f"Saved stats for vMCP {vmcp_id}: {operation_type}:{operation_name}")
            return True

        except Exception as e:
            logger.error(f"Error saving vMCP stats: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    def save_application_log(self, level: str, logger_name: str, message: str,
                            vmcp_id: Optional[str] = None,
                            mcp_server_id: Optional[str] = None,
                            log_metadata: Optional[Dict[str, Any]] = None,
                            traceback: Optional[str] = None) -> bool:
        """Save application log entry."""
        session = self._get_session()
        try:
            log = ApplicationLog(
                level=level,
                logger_name=logger_name,
                message=message,
                vmcp_id=vmcp_id,
                mcp_server_id=mcp_server_id,
                log_metadata=log_metadata,
                traceback=traceback,
            )
            session.add(log)
            session.commit()

            logger.debug(f"Saved application log: {level} - {logger_name}")
            return True

        except Exception as e:
            logger.error(f"Error saving application log: {e}")
            session.rollback()
            return False
        finally:
            session.close()
