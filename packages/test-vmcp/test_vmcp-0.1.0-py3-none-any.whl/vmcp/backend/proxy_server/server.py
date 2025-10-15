"""
vMCP Proxy Server - MCP Protocol Implementation
================================================

This module implements the MCP protocol server using FastMCP.
It serves vMCPs as MCP endpoints with authentication.
"""

from mcp.server.fastmcp import FastMCP
from mcp.server.lowlevel import NotificationOptions
from typing import List, Dict, Any, Optional
from mcp.types import (
    Prompt, Tool, Resource, ResourceTemplate,
    CallToolRequest, ReadResourceRequest, ServerResult
)
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import asyncio
import logging

from vmcp.backend.config import settings
from vmcp.backend.utilities.logging import get_logger
from vmcp.backend.utilities.tracing import trace_method, add_tracing_middleware
from vmcp.backend.vmcps.config_manager import VMCPConfigManager
from vmcp.backend.vmcps.models import VMCPToolCallRequest
from vmcp.backend.storage.dummy_user import get_user_context, UserContext
from vmcp.backend.mcps.router import router as mcp_router
from vmcp.backend.vmcps.router import router as vmcp_router

logger = get_logger(__name__)


class ProxyServer(FastMCP):
    """
    MCP Proxy Server that serves vMCPs as MCP endpoints.

    This server is stateless - all managers are created per request.
    """

    def __init__(self, name: str):
        """Initialize the MCP proxy server."""
        logger.info(f"🚀 Initializing ProxyServer: {name}")

        # Configure streamable HTTP path
        super().__init__(
            name,
            streamable_http_path="/mcp",
            instructions="vMCP - Virtual MCP Server"
        )

        self._mcp_server.create_initialization_options(
            notification_options=NotificationOptions(
                prompts_changed=True,
                resources_changed=True,
                tools_changed=True
            ),
            experimental_capabilities={"vmcp": {"version": "0.1.0"}}
        )

        logger.info("✅ ProxyServer initialization complete (stateless)")

    async def get_user_context_from_request(self) -> Optional[UserContext]:
        """
        Get user context from the current request.

        In OSS version, this always returns the dummy user context.
        """
        try:
            # In OSS, we always use the dummy user (user_id=1)
            # But we still extract vmcp info from headers for routing
            from vmcp.backend.proxy_server.dependencies import get_http_request

            request = get_http_request()
            vmcp_name = request.headers.get('vmcp-name', 'default')
            vmcp_username = request.headers.get('vmcp-username')

            # Create dummy user context
            user_context = UserContext(
                user_id=1,  # Always dummy user in OSS
                vmcp_name_header=vmcp_name,
                vmcp_username_header=vmcp_username
            )

            return user_context

        except Exception as e:
            logger.error(f"❌ Error getting user context: {e}")
            return None

    def _setup_handlers(self) -> None:
        """Set up MCP protocol handlers."""
        logger.info("🔌 Setting up MCP protocol handlers...")

        self._mcp_server.list_tools()(self.proxy_list_tools)
        logger.debug("   ✅ list_tools handler registered")

        self._mcp_server.request_handlers[CallToolRequest] = self.root_proxy_call_tool
        logger.debug("   ✅ call_tool handler registered")

        self._mcp_server.list_resources()(self.proxy_list_resources)
        logger.debug("   ✅ list_resources handler registered")

        self._mcp_server.request_handlers[ReadResourceRequest] = self.proxy_read_resource
        logger.debug("   ✅ read_resource handler registered")

        self._mcp_server.list_prompts()(self.proxy_list_prompts)
        logger.debug("   ✅ list_prompts handler registered")

        self._mcp_server.get_prompt()(self.proxy_get_prompt)
        logger.debug("   ✅ get_prompt handler registered")

        self._mcp_server.list_resource_templates()(self.proxy_list_resource_templates)
        logger.debug("   ✅ list_resource_templates handler registered")

        logger.info("🎉 All MCP protocol handlers registered successfully")

    @trace_method("ProxyServer.list_tools")
    async def proxy_list_tools(self) -> List[Tool]:
        """List all tools from the vMCP."""
        logger.info("🔍 MCP: proxy_list_tools called")

        user_context = await self.get_user_context_from_request()
        if not user_context:
            logger.warning("🔍 No user context - returning empty tools list")
            return []

        vmcp_id = user_context.vmcp_name_header
        logger.info(f"🔍 MCP: Listing tools for vMCP: {vmcp_id}")

        # Get vMCP config manager
        manager = VMCPConfigManager(
            user_id=user_context.user_id,
            vmcp_id=vmcp_id
        )

        tools = await manager.tools_list()
        logger.info(f"🔍 MCP: Found {len(tools)} tools")

        return tools

    @trace_method("ProxyServer.list_resources")
    async def proxy_list_resources(self) -> List[Resource]:
        """List all resources from the vMCP."""
        logger.info("🔍 MCP: proxy_list_resources called")

        user_context = await self.get_user_context_from_request()
        if not user_context:
            logger.warning("🔍 No user context - returning empty resources list")
            return []

        vmcp_id = user_context.vmcp_name_header
        logger.info(f"🔍 MCP: Listing resources for vMCP: {vmcp_id}")

        manager = VMCPConfigManager(
            user_id=user_context.user_id,
            vmcp_id=vmcp_id
        )

        resources = await manager.resources_list()
        logger.info(f"🔍 MCP: Found {len(resources)} resources")

        return resources

    @trace_method("ProxyServer.list_resource_templates")
    async def proxy_list_resource_templates(self) -> List[ResourceTemplate]:
        """List all resource templates from the vMCP."""
        logger.info("🔍 MCP: proxy_list_resource_templates called")

        user_context = await self.get_user_context_from_request()
        if not user_context:
            logger.warning("🔍 No user context - returning empty templates list")
            return []

        vmcp_id = user_context.vmcp_name_header
        logger.info(f"🔍 MCP: Listing resource templates for vMCP: {vmcp_id}")

        manager = VMCPConfigManager(
            user_id=user_context.user_id,
            vmcp_id=vmcp_id
        )

        templates = await manager.resource_templates_list()
        logger.info(f"🔍 MCP: Found {len(templates)} resource templates")

        return templates

    @trace_method("ProxyServer.list_prompts")
    async def proxy_list_prompts(self) -> List[Prompt]:
        """List all prompts from the vMCP."""
        logger.info("🔍 MCP: proxy_list_prompts called")

        user_context = await self.get_user_context_from_request()
        if not user_context:
            logger.warning("🔍 No user context - returning empty prompts list")
            return []

        vmcp_id = user_context.vmcp_name_header
        logger.info(f"🔍 MCP: Listing prompts for vMCP: {vmcp_id}")

        manager = VMCPConfigManager(
            user_id=user_context.user_id,
            vmcp_id=vmcp_id
        )

        prompts = await manager.prompts_list()
        logger.info(f"🔍 MCP: Found {len(prompts)} prompts")

        return prompts

    @trace_method("ProxyServer.root_proxy_call_tool")
    async def root_proxy_call_tool(self, req: CallToolRequest):
        """Root handler for tool calls."""
        tool_name = req.params.name
        arguments = req.params.arguments or {}
        result = await self.proxy_call_tool(tool_name, arguments)
        return result

    @trace_method("ProxyServer.call_tool")
    async def proxy_call_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a tool call."""
        logger.info(f"🛠️  MCP: Tool call requested: {name}")
        logger.debug(f"   Arguments: {arguments}")

        user_context = await self.get_user_context_from_request()
        if not user_context:
            logger.error("🔍 No user context - cannot call tool")
            raise Exception("Tool calls require user context")

        vmcp_id = user_context.vmcp_name_header
        logger.info(f"🛠️  MCP: Executing tool '{name}' for vMCP: {vmcp_id}")

        manager = VMCPConfigManager(
            user_id=user_context.user_id,
            vmcp_id=vmcp_id
        )

        result = await manager.call_tool(
            VMCPToolCallRequest(tool_name=name, arguments=arguments)
        )

        logger.info(f"✅ MCP: Tool '{name}' executed successfully")
        return result

    @trace_method("ProxyServer.get_prompt")
    async def proxy_get_prompt(
        self,
        name: str,
        arguments: Optional[Dict[str, Any]] = None
    ) -> Any:
        """Get a prompt."""
        logger.info(f"📝 MCP: Get prompt requested: {name}")

        user_context = await self.get_user_context_from_request()
        if not user_context:
            logger.error("🔍 No user context - cannot get prompt")
            raise Exception("Prompt requests require user context")

        vmcp_id = user_context.vmcp_name_header
        logger.info(f"📝 MCP: Getting prompt '{name}' for vMCP: {vmcp_id}")

        manager = VMCPConfigManager(
            user_id=user_context.user_id,
            vmcp_id=vmcp_id
        )

        prompt = await manager.get_prompt(name, arguments or {})
        logger.info(f"✅ MCP: Prompt '{name}' retrieved successfully")

        return prompt

    @trace_method("ProxyServer.read_resource")
    async def proxy_read_resource(self, req: ReadResourceRequest) -> ServerResult:
        """Read a resource."""
        uri = req.params.uri
        logger.info(f"📦 MCP: Resource read requested: {uri}")

        user_context = await self.get_user_context_from_request()
        if not user_context:
            logger.error("🔍 No user context - cannot read resource")
            raise Exception("Resource read requires user context")

        vmcp_id = user_context.vmcp_name_header
        logger.info(f"📦 MCP: Reading resource '{uri}' for vMCP: {vmcp_id}")

        manager = VMCPConfigManager(
            user_id=user_context.user_id,
            vmcp_id=vmcp_id
        )

        resource_result = await manager.get_resource(uri)

        if resource_result:
            logger.info(f"✅ MCP: Resource read successful: {uri}")
            return ServerResult(resource_result)
        else:
            logger.warning(f"⚠️  Resource '{uri}' not found")
            raise ValueError(f"Resource '{uri}' not found")


def create_app() -> FastAPI:
    """
    Create the FastAPI application with MCP server mounted.

    Returns:
        FastAPI application
    """
    logger.info("🎬 Creating vMCP Proxy Server...")

    # Create MCP server
    mcp = ProxyServer("vMCP Proxy")

    # Create FastMCP HTTP app
    logger.info("🔧 Creating FastMCP streamable HTTP app...")
    mcp_http_app = mcp.streamable_http_app()

    # Lifespan context manager
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Manage MCP session manager lifecycle and database initialization."""
        # Initialize database tables on startup
        try:
            from vmcp.backend.storage.database import init_db
            from vmcp.backend.storage.dummy_user import ensure_dummy_user
            logger.info("📊 Initializing database...")
            init_db()
            ensure_dummy_user()
            logger.info("✅ Database initialized")
        except Exception as e:
            logger.warning(f"⚠️  Database initialization warning: {e}")

        logger.info("🚀 Starting MCP session manager...")

        shutdown_event = asyncio.Event()
        session_task = None

        async def run_session_manager():
            try:
                async with mcp.session_manager.run():
                    await shutdown_event.wait()
            except asyncio.CancelledError:
                logger.info("🛑 MCP session manager cancelled")
            except Exception as e:
                logger.error(f"❌ MCP session manager error: {e}")

        session_task = asyncio.create_task(run_session_manager())

        try:
            logger.info("✅ MCP session manager started")
            yield
        finally:
            logger.info("🛑 Shutting down MCP session manager...")
            shutdown_event.set()

            if session_task:
                try:
                    await asyncio.wait_for(session_task, timeout=3.0)
                except asyncio.TimeoutError:
                    logger.warning("⚠️ Session manager shutdown timeout")
                    session_task.cancel()

            logger.info("✅ MCP session manager shutdown complete")

    # Create FastAPI app
    app = FastAPI(
        title="vMCP Proxy Server",
        description="MCP proxy server for vMCP endpoints",
        version="0.1.0",
        lifespan=lifespan,
        redirect_slashes=False
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add tracing middleware
    add_tracing_middleware(
        app,
        "vmcp-proxy-server",
        excluded_paths={"/health", "/docs", "/openapi.json", "/redoc"},
        excluded_prefixes={"/static/", "/assets/"}
    )

    # Simple authentication middleware (dummy user in OSS)
    @app.middleware("http")
    async def simple_auth_middleware(request: Request, call_next):
        """
        Simple authentication for OSS version.

        In OSS, we just check for any bearer token presence.
        No actual validation since we use dummy user (user_id=1).
        """
        # Skip auth for non-MCP endpoints
        if not request.url.path.startswith("/vmcp/mcp"):
            return await call_next(request)

        # Handle CORS preflight
        if request.method == "OPTIONS":
            from fastapi.responses import Response
            return Response(
                status_code=204,
                headers={
                    "Access-Control-Allow-Origin": "*",
                    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
                    "Access-Control-Allow-Headers": "Authorization, Content-Type, vmcp-name, vmcp-username",
                }
            )

        # Check for authorization header (but don't validate in OSS)
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return JSONResponse(
                status_code=401,
                content={
                    "error": "unauthorized",
                    "message": "Missing or invalid Authorization header"
                }
            )

        # In OSS, we accept any bearer token and use dummy user
        return await call_next(request)

    # Root endpoint - redirect to /app
    @app.get("/")
    async def root():
        """Root endpoint - redirects to /app."""
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/app")

    # # Commented out JSON response for now
    # @app.get("/")
    # async def root():
    #     """Root endpoint with server information."""
    #     return {
    #         "service": "vMCP Proxy Server",
    #         "version": "0.1.0",
    #         "description": "MCP proxy server for vMCP endpoints",
    #         "endpoints": {
    #             "mcp": "/vmcp/mcp",
    #             "api": "/api",
    #             "health": "/health",
    #         }
    #     }

    @app.get("/health")
    async def health():
        """Health check endpoint."""
        return {"status": "ok"}

    # Mount API routers
    logger.info("📌 Mounting API routes...")
    app.include_router(mcp_router)
    app.include_router(vmcp_router)

    # Mount MCP server
    logger.info("📌 Mounting MCP server...")
    app.mount("/vmcp/", mcp_http_app, name="vmcp_mcp_server")
    logger.info("✅ MCP server mounted at /vmcp/mcp")

    # Mount documentation (if available)
    # Docs is at vmcp/docs/build (sibling to backend)
    docs_dir = Path(__file__).parent.parent.parent / "docs" / "build"
    if docs_dir.exists() and docs_dir.is_dir():
        logger.info(f"📌 Mounting documentation from {docs_dir}")
        app.mount(
            "/documentation",
            StaticFiles(directory=str(docs_dir), html=True),
            name="documentation"
        )
        logger.info("✅ Documentation mounted at /documentation")

        # Add redirect for /documention -> /documentation (typo fix)
        @app.get("/documentation/{path:path}")
        @app.get("/documentation")
        async def redirect_documention(path: str = ""):
            """Redirect /documentation to /documentation."""
            from fastapi.responses import RedirectResponse
            redirect_path = f"/documentation/{path}" if path else "/documentation/"
            return RedirectResponse(url=redirect_path, status_code=301)
    else:
        logger.warning(f"⚠️  Documentation directory not found: {docs_dir}")
        logger.info("   Documentation will not be served. Run 'npm run build' in docs/ first.")

    # Mount frontend static files (if available)
    # Frontend is at vmcp/frontend/build (sibling to backend)
    frontend_dir = Path(__file__).parent.parent.parent / "frontend" / "build"
    if frontend_dir.exists() and frontend_dir.is_dir():
        logger.info(f"📌 Mounting frontend from {frontend_dir}")

        # Serve static assets (JS, CSS, images, etc.)
        app.mount(
            "/assets",
            StaticFiles(directory=str(frontend_dir / "assets")),
            name="frontend-assets"
        )

        # Serve other static files at root (like vite.svg, favicon, etc.)
        @app.get("/{file_path:path}")
        async def serve_frontend_files(file_path: str):
            """Serve frontend static files and SPA routing."""
            # Skip API routes and documentation
            if file_path.startswith(("api/", "vmcp/", "docs", "documentation/", "openapi.json", "health")):
                return None

            # Try to serve the requested file
            file = frontend_dir / file_path
            if file.is_file():
                return FileResponse(str(file))

            # For /app/* paths, serve index.html (SPA routing)
            if file_path.startswith("app"):
                index_file = frontend_dir / "index.html"
                if index_file.exists():
                    return FileResponse(str(index_file))

            # For other paths, don't serve frontend (let other routes handle)

            return {
                "service": "vMCP",
                "version": "0.1.0",
                "message": "Frontend not built yet. Use /api for API",
                "endpoints": {
                    "api": "/api",
                    "mcp": "/vmcp/mcp",
                    "docs": "/docs"
                }
            }

        logger.info("✅ Frontend mounted at /")
    else:
        logger.warning(f"⚠️  Frontend directory not found: {frontend_dir}")
        logger.info("   Frontend will not be served. Run frontend build first.")

    return app
