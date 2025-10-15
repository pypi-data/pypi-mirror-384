"""
MCP Configuration Manager for vMCP OSS.

Handles MCP server configuration persistence using the database.
"""

from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from vmcp.backend.utilities.logging import get_logger
from vmcp.backend.utilities.tracing import trace_async
from vmcp.backend.mcps.models import MCPServerConfig, MCPTransportType, MCPAuthConfig, MCPConnectionStatus
from vmcp.backend.storage.models import MCPServer
from vmcp.backend.storage.database import get_db

logger = get_logger(__name__)


class MCPConfigManager:
    """Manages MCP server configurations with database persistence."""

    def __init__(self, user_id: int = 1):
        """
        Initialize MCP config manager.

        Args:
            user_id: User ID (always 1 in OSS mode)
        """
        self.user_id = user_id
        self._servers: Dict[str, MCPServerConfig] = {}
        self.load_servers()
        logger.info(f"MCPConfigManager initialized with {len(self._servers)} servers")

    def load_servers(self) -> None:
        """Load all MCP servers from database."""
        db = next(get_db())
        try:
            servers = db.query(MCPServer).filter(
                MCPServer.user_id == self.user_id
            ).all()

            self._servers = {}
            for server in servers:
                try:
                    config_dict = server.mcp_server_config
                    config = MCPServerConfig.from_dict(config_dict)
                    config.server_id = server.server_id
                    self._servers[server.server_id] = config
                    logger.debug(f"Loaded server: {server.name}")
                except Exception as e:
                    logger.error(f"Failed to load server {server.id}: {e}")

            logger.info(f"Loaded {len(self._servers)} MCP servers")
        finally:
            db.close()

    def add_server(self, config: MCPServerConfig) -> bool:
        """
        Add a new MCP server.

        Args:
            config: Server configuration

        Returns:
            True if successful, False otherwise
        """
        db = next(get_db())
        try:
            # Check if server already exists
            composite_id = f"{self.user_id}:{config.server_id}"
            existing_server = db.query(MCPServer).filter(
                MCPServer.id == composite_id
            ).first()

            if existing_server:
                logger.info(f"Server already exists: {config.name} ({config.server_id}), skipping creation")
                # Update memory cache with existing server
                self._servers[config.server_id] = config
                return True

            # Create database record
            server = MCPServer(
                id=composite_id,
                user_id=self.user_id,
                server_id=config.server_id,
                name=config.name,
                description=config.description,
                mcp_server_config=config.to_dict(),
                oauth_state=None  # Will be set during OAuth if needed
            )

            db.add(server)
            db.commit()

            # Add to memory cache
            self._servers[config.server_id] = config

            logger.info(f"Added MCP server: {config.name} ({config.server_id})")
            return True

        except Exception as e:
            logger.error(f"Failed to add server {config.name}: {e}")
            db.rollback()
            return False
        finally:
            db.close()

    def update_server_config(self, server_id: str, config: MCPServerConfig) -> bool:
        """
        Update an existing MCP server configuration.

        Args:
            server_id: Server ID
            config: Updated configuration

        Returns:
            True if successful, False otherwise
        """
        db = next(get_db())
        try:
            server = db.query(MCPServer).filter(
                MCPServer.server_id == server_id,
                MCPServer.user_id == self.user_id
            ).first()

            if not server:
                logger.warning(f"Server {server_id} not found")
                return False

            # Update database record
            server.name = config.name
            server.description = config.description
            server.mcp_server_config = config.to_dict()
            server.updated_at = datetime.utcnow()

            db.commit()

            # Update memory cache
            self._servers[server_id] = config

            logger.info(f"Updated MCP server: {config.name}")
            return True

        except Exception as e:
            logger.error(f"Failed to update server {server_id}: {e}")
            db.rollback()
            return False
        finally:
            db.close()

    def update_server_session(self, server_id: str, session_id: str) -> bool:
        """
        Update server's session ID.

        Args:
            server_id: Server ID
            session_id: New session ID

        Returns:
            True if successful, False otherwise
        """
        if server_id not in self._servers:
            logger.warning(f"Server {server_id} not found in cache")
            return False

        config = self._servers[server_id]
        config.session_id = session_id

        return self.update_server_config(server_id, config)

    def update_server_oauth(self, server_id: str, oauth_state: Dict) -> bool:
        """
        Update server's OAuth state.

        Args:
            server_id: Server ID
            oauth_state: OAuth state data (tokens, expiry, etc.)

        Returns:
            True if successful, False otherwise
        """
        db = next(get_db())
        try:
            server = db.query(MCPServer).filter(
                MCPServer.server_id == server_id,
                MCPServer.user_id == self.user_id
            ).first()

            if not server:
                logger.warning(f"Server {server_id} not found")
                return False

            server.oauth_state = oauth_state
            server.updated_at = datetime.utcnow()
            db.commit()

            logger.info(f"Updated OAuth state for server: {server_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to update OAuth state: {e}")
            db.rollback()
            return False
        finally:
            db.close()

    def remove_server(self, server_id: str) -> bool:
        """
        Remove an MCP server.

        Args:
            server_id: Server ID

        Returns:
            True if successful, False otherwise
        """
        db = next(get_db())
        try:
            server = db.query(MCPServer).filter(
                MCPServer.server_id == server_id,
                MCPServer.user_id == self.user_id
            ).first()

            if not server:
                logger.warning(f"Server {server_id} not found")
                return False

            db.delete(server)
            db.commit()

            # Remove from memory cache
            if server_id in self._servers:
                del self._servers[server_id]

            logger.info(f"Removed MCP server: {server_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to remove server {server_id}: {e}")
            db.rollback()
            return False
        finally:
            db.close()

    def get_server(self, server_id: str) -> Optional[MCPServerConfig]:
        """
        Get server configuration by ID.

        Args:
            server_id: Server ID or name

        Returns:
            Server configuration or None if not found
        """
        # Try by ID first
        if server_id in self._servers:
            return self._servers[server_id]

        # Try by name
        return self.get_server_by_name(server_id)

    def get_server_by_name(self, name: str) -> Optional[MCPServerConfig]:
        """
        Get server configuration by name.

        Args:
            name: Server name

        Returns:
            Server configuration or None if not found
        """
        for config in self._servers.values():
            if config.name == name:
                return config
        return None

    def list_servers(self) -> List[MCPServerConfig]:
        """
        Get all server configurations.

        Returns:
            List of all server configurations
        """
        return list(self._servers.values())

    def server_exists(self, server_id: str) -> bool:
        """
        Check if a server exists.

        Args:
            server_id: Server ID

        Returns:
            True if server exists, False otherwise
        """
        return server_id in self._servers
