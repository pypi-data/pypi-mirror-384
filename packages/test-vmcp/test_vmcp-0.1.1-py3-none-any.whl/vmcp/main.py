"""
vMCP - Virtual Model Context Protocol
======================================

Main application entry point.
Creates and configures the FastAPI application with MCP server.
"""

import uvicorn
from vmcp.backend.config import settings
from vmcp.backend.utilities.logging import setup_logging, get_logger
from vmcp.backend.proxy_server import create_app

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Create the FastAPI application with MCP server
app = create_app()


def main():
    """Run the vMCP server."""
    logger.info(f"🚀 Starting vMCP server on {settings.HOST}:{settings.PORT}")

    uvicorn.run(
        "vmcp.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.ENV == "development",
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True
    )


if __name__ == "__main__":
    main()
