"""
MCP Router - REST API endpoints for MCP server management.

Provides endpoints for installing, connecting, and managing MCP servers.
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel

from vmcp.backend.utilities.logging import get_logger
from vmcp.backend.utilities.tracing import trace_async
from vmcp.backend.mcps.models import (
    MCPInstallRequest, MCPUpdateRequest, MCPServerInfo,
    MCPToolCallRequest, MCPResourceRequest, MCPPromptRequest,
    RenameServerRequest, MCPServerConfig, MCPTransportType,
    MCPConnectionStatus, MCPAuthConfig
)
from vmcp.backend.mcps.mcp_client import MCPClientManager, AuthenticationError, MCPOperationError
from vmcp.backend.mcps.mcp_config_manager import MCPConfigManager
from vmcp.backend.storage.dummy_user import UserContext, get_user_context

logger = get_logger(__name__)

router = APIRouter(prefix="/api/mcps", tags=["MCPs"])


def get_config_manager(user_context: UserContext = Depends(get_user_context)) -> MCPConfigManager:
    """Dependency to get MCP config manager."""
    return MCPConfigManager(user_id=user_context.user_id)


def get_client_manager(config_manager: MCPConfigManager = Depends(get_config_manager)) -> MCPClientManager:
    """Dependency to get MCP client manager."""
    return MCPClientManager(config_manager=config_manager)


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "vMCP - MCP Server Management"
    }


@router.post("/install")
@trace_async("mcp.install")
async def install_mcp_server(
    request: MCPInstallRequest,
    background_tasks: BackgroundTasks,
    config_manager: MCPConfigManager = Depends(get_config_manager)
):
    """
    Install a new MCP server.

    Args:
        request: MCP installation request with server configuration

    Returns:
        Installation status and server info
    """
    logger.info(f"Installing MCP server: {request.name}")

    try:
        # Validate transport mode
        transport_type = MCPTransportType(request.mode.lower())

        # Create auth config if provided
        auth = None
        if request.auth_type and request.auth_type != "none":
            auth = MCPAuthConfig(
                type=request.auth_type,
                client_id=request.client_id,
                client_secret=request.client_secret,
                auth_url=request.auth_url,
                token_url=request.token_url,
                scope=request.scope,
                access_token=request.access_token
            )

        # Create server config
        server_config = MCPServerConfig(
            name=request.name,
            transport_type=transport_type,
            description=request.description,
            command=request.command,
            args=request.args,
            env=request.env,
            url=request.url,
            headers=request.headers,
            auth=auth,
            auto_connect=request.auto_connect,
            enabled=request.enabled,
            status=MCPConnectionStatus.DISCONNECTED
        )

        # Generate server ID
        server_config.server_id = server_config.generate_server_id()

        # Check if server already exists
        if config_manager.server_exists(server_config.server_id):
            raise HTTPException(
                status_code=400,
                detail=f"Server with similar configuration already exists"
            )

        # Save server configuration
        if not config_manager.add_server(server_config):
            raise HTTPException(
                status_code=500,
                detail="Failed to save server configuration"
            )

        logger.info(f"✅ Successfully installed MCP server: {request.name}")

        # Try to connect in background if auto_connect is enabled
        if request.auto_connect:
            background_tasks.add_task(
                try_connect_server,
                config_manager,
                server_config.server_id
            )

        return {
            "success": True,
            "message": f"Server {request.name} installed successfully",
            "server_id": server_config.server_id,
            "server": MCPServerInfo(
                name=server_config.name,
                server_id=server_config.server_id,
                transport_type=server_config.transport_type.value,
                status=server_config.status.value,
                description=server_config.description,
                url=server_config.url,
                command=server_config.command,
                auto_connect=server_config.auto_connect,
                enabled=server_config.enabled
            )
        }

    except ValueError as e:
        logger.error(f"Invalid transport mode: {request.mode}")
        raise HTTPException(status_code=400, detail=f"Invalid transport mode: {request.mode}")
    except Exception as e:
        logger.error(f"Failed to install server: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def try_connect_server(config_manager: MCPConfigManager, server_id: str):
    """Background task to try connecting to a server."""
    try:
        client_manager = MCPClientManager(config_manager)
        await client_manager.ping_server(server_id)
        logger.info(f"Successfully connected to server: {server_id}")
    except Exception as e:
        logger.warning(f"Failed to auto-connect to {server_id}: {e}")


def _list_servers_internal(config_manager: MCPConfigManager) -> List[Dict[str, Any]]:
    """Internal helper to list servers."""
    servers = config_manager.list_servers()

    # Return full server dict with all details (matching main app)
    return [server.to_dict() for server in servers]


@router.get("/")
@trace_async("mcp.list")
async def list_servers_root(
    config_manager: MCPConfigManager = Depends(get_config_manager)
) -> Dict[str, List[Dict[str, Any]]]:
    """
    List all installed MCP servers (root endpoint for frontend compatibility).

    Returns:
        Dict with 'servers' key containing list of server information
    """
    return {"servers": _list_servers_internal(config_manager)}


@router.get("/list")
@trace_async("mcp.list")
async def list_servers(
    config_manager: MCPConfigManager = Depends(get_config_manager)
) -> List[Dict[str, Any]]:
    """
    List all installed MCP servers.

    Returns:
        List of server information with full details
    """
    return _list_servers_internal(config_manager)


@router.get("/{server_id}/info")
@trace_async("mcp.info")
async def get_server_info(
    server_id: str,
    config_manager: MCPConfigManager = Depends(get_config_manager)
) -> MCPServerInfo:
    """Get information about a specific MCP server."""
    server = config_manager.get_server(server_id)

    if not server:
        raise HTTPException(status_code=404, detail=f"Server {server_id} not found")

    return MCPServerInfo(
        name=server.name,
        server_id=server.server_id,
        transport_type=server.transport_type.value,
        status=server.status.value,
        description=server.description,
        url=server.url,
        command=server.command,
        last_connected=server.last_connected.isoformat() if server.last_connected else None,
        last_error=server.last_error,
        capabilities=server.capabilities,
        tools=server.tools,
        resources=server.resources,
        prompts=server.prompts,
        auto_connect=server.auto_connect,
        enabled=server.enabled
    )


@router.post("/{server_id}/connect")
@trace_async("mcp.connect")
async def connect_server(
    server_id: str,
    client_manager: MCPClientManager = Depends(get_client_manager),
    config_manager: MCPConfigManager = Depends(get_config_manager)
):
    """Connect to an MCP server, test the connection, and discover capabilities."""
    server = config_manager.get_server(server_id)

    if not server:
        raise HTTPException(status_code=404, detail=f"Server {server_id} not found")

    try:
        # Try to ping the server
        current_status = await client_manager.ping_server(server_id)
        logger.info(f"🔍 Server {server_id}: ping result = {current_status.value if current_status else 'None'}")

        # Update server status
        server.status = current_status
        server.last_connected = datetime.utcnow()
        server.last_error = None

        # If connected, discover capabilities
        if current_status == MCPConnectionStatus.CONNECTED:
            try:
                capabilities = await client_manager.discover_capabilities(server_id)
                if capabilities:
                    # Update server config with discovered capabilities
                    if capabilities.get('tools', []):
                        server.tools = capabilities.get('tools', [])
                    if capabilities.get('resources', []):
                        server.resources = capabilities.get('resources', [])
                    if capabilities.get('prompts', []):
                        server.prompts = capabilities.get('prompts', [])
                    if capabilities.get('tool_details', []):
                        server.tool_details = capabilities.get('tool_details', [])
                    if capabilities.get('resource_details', []):
                        server.resource_details = capabilities.get('resource_details', [])
                    if capabilities.get('resource_templates', []):
                        server.resource_templates = capabilities.get('resource_templates', [])
                    if capabilities.get('resource_template_details', []):
                        server.resource_template_details = capabilities.get('resource_template_details', [])
                    if capabilities.get('prompt_details', []):
                        server.prompt_details = capabilities.get('prompt_details', [])

                    server.capabilities = {
                        "tools": bool(server.tools and len(server.tools) > 0),
                        "resources": bool(server.resources and len(server.resources) > 0),
                        "prompts": bool(server.prompts and len(server.prompts) > 0)
                    }

                    logger.info(f"✅ Successfully discovered capabilities for server '{server_id}'")
            except Exception as e:
                logger.error(f"❌ Error discovering capabilities for server {server_id}: {e}")
                # Don't fail the connection if capabilities discovery fails

        # Save updated config
        config_manager.update_server_config(server_id, server)

        if current_status == MCPConnectionStatus.CONNECTED:
            return {
                "success": True,
                "message": f"Successfully connected to {server.name}",
                "status": current_status.value
            }
        elif current_status == MCPConnectionStatus.AUTH_REQUIRED:
            raise HTTPException(
                status_code=401,
                detail={
                    "error": "authentication_required",
                    "message": "Authentication required",
                    "server_id": server_id,
                    "auth_url": server.auth.auth_url if server.auth else None
                }
            )
        else:
            raise Exception("Connection test failed")

    except AuthenticationError as e:
        logger.warning(f"Authentication required for {server_id}")
        server.status = MCPConnectionStatus.AUTH_REQUIRED
        server.last_error = str(e)
        config_manager.update_server_config(server_id, server)

        raise HTTPException(
            status_code=401,
            detail={
                "error": "authentication_required",
                "message": str(e),
                "server_id": server_id,
                "auth_url": server.auth.auth_url if server.auth else None
            }
        )
    except HTTPException:
        raise
    except asyncio.CancelledError as e:
        logger.warning(f"Connection to {server_id} was cancelled")
        server.status = MCPConnectionStatus.ERROR
        server.last_error = "Connection cancelled"
        server.session_id = None
        config_manager.update_server_config(server_id, server)
        raise HTTPException(status_code=500, detail="Connection cancelled or timed out")
    except ExceptionGroup as e:
        logger.error(f"ExceptionGroup while connecting to {server_id}: {e.exceptions}")
        server.status = MCPConnectionStatus.ERROR
        server.last_error = f"Multiple errors: {len(e.exceptions)} sub-exceptions"
        server.session_id = None
        config_manager.update_server_config(server_id, server)
        raise HTTPException(status_code=500, detail="Connection failed with multiple errors")
    except Exception as e:
        logger.error(f"Failed to connect to {server_id}: {e}")
        server.status = MCPConnectionStatus.ERROR
        server.last_error = str(e)
        # Clear session_id on error (it may be invalid)
        server.session_id = None
        config_manager.update_server_config(server_id, server)

        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{server_id}/disconnect")
@trace_async("mcp.disconnect")
async def disconnect_server(
    server_id: str,
    client_manager: MCPClientManager = Depends(get_client_manager),
    config_manager: MCPConfigManager = Depends(get_config_manager)
):
    """Disconnect from an MCP server."""
    server = config_manager.get_server(server_id)

    if not server:
        raise HTTPException(status_code=404, detail=f"Server {server_id} not found")

    try:
        await client_manager.disconnect(server.name)

        server.status = MCPConnectionStatus.DISCONNECTED
        config_manager.update_server_config(server_id, server)

        return {
            "success": True,
            "message": f"Disconnected from {server.name}",
            "status": "disconnected"
        }
    except Exception as e:
        logger.error(f"Error disconnecting from {server_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{server_id}/tools")
@trace_async("mcp.list_tools")
async def list_tools(
    server_id: str,
    client_manager: MCPClientManager = Depends(get_client_manager),
    config_manager: MCPConfigManager = Depends(get_config_manager)
) -> Dict[str, Any]:
    """List all tools available from an MCP server."""
    server = config_manager.get_server(server_id)

    if not server:
        raise HTTPException(status_code=404, detail=f"Server {server_id} not found")

    try:
        tools = await client_manager.tools_list(server_id)

        # Update server config with tool list
        server.tools = list(tools.keys())
        server.tool_details = list(tools.values())
        config_manager.update_server_config(server_id, server)

        return {
            "server_id": server_id,
            "server_name": server.name,
            "tools": [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "inputSchema": tool.inputSchema.model_dump() if tool.inputSchema else {}
                }
                for tool in tools.values()
            ]
        }
    except AuthenticationError:
        raise HTTPException(status_code=401, detail="Authentication required")
    except Exception as e:
        logger.error(f"Failed to list tools from {server_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{server_id}/tools/call")
@trace_async("mcp.call_tool")
async def call_tool(
    server_id: str,
    request: MCPToolCallRequest,
    client_manager: MCPClientManager = Depends(get_client_manager),
    config_manager: MCPConfigManager = Depends(get_config_manager)
):
    """Call a tool on an MCP server."""
    server = config_manager.get_server(server_id)

    if not server:
        raise HTTPException(status_code=404, detail=f"Server {server_id} not found")

    try:
        result = await client_manager.call_tool(
            server_id,
            request.tool_name,
            request.arguments
        )

        return {
            "success": True,
            "tool_name": request.tool_name,
            "result": result.model_dump()
        }
    except AuthenticationError:
        raise HTTPException(status_code=401, detail="Authentication required")
    except MCPOperationError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error calling tool: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{server_id}/resources")
@trace_async("mcp.list_resources")
async def list_resources(
    server_id: str,
    client_manager: MCPClientManager = Depends(get_client_manager),
    config_manager: MCPConfigManager = Depends(get_config_manager)
) -> Dict[str, Any]:
    """List all resources available from an MCP server."""
    server = config_manager.get_server(server_id)

    if not server:
        raise HTTPException(status_code=404, detail=f"Server {server_id} not found")

    try:
        resources = await client_manager.resources_list(server_id)

        # Update server config with resource list
        server.resources = list(resources.keys())
        config_manager.update_server_config(server_id, server)

        return {
            "server_id": server_id,
            "server_name": server.name,
            "resources": [
                {
                    "uri": str(resource.uri),
                    "name": resource.name,
                    "description": resource.description,
                    "mimeType": resource.mimeType
                }
                for resource in resources.values()
            ]
        }
    except AuthenticationError:
        raise HTTPException(status_code=401, detail="Authentication required")
    except Exception as e:
        logger.error(f"Failed to list resources from {server_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{server_id}/resources/read")
@trace_async("mcp.read_resource")
async def read_resource(
    server_id: str,
    request: MCPResourceRequest,
    client_manager: MCPClientManager = Depends(get_client_manager),
    config_manager: MCPConfigManager = Depends(get_config_manager)
):
    """Read a resource from an MCP server."""
    server = config_manager.get_server(server_id)

    if not server:
        raise HTTPException(status_code=404, detail=f"Server {server_id} not found")

    try:
        result = await client_manager.read_resource(server_id, request.uri)

        return {
            "success": True,
            "uri": request.uri,
            "result": result.model_dump()
        }
    except AuthenticationError:
        raise HTTPException(status_code=401, detail="Authentication required")
    except MCPOperationError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error reading resource: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{server_id}/prompts")
@trace_async("mcp.list_prompts")
async def list_prompts(
    server_id: str,
    client_manager: MCPClientManager = Depends(get_client_manager),
    config_manager: MCPConfigManager = Depends(get_config_manager)
) -> Dict[str, Any]:
    """List all prompts available from an MCP server."""
    server = config_manager.get_server(server_id)

    if not server:
        raise HTTPException(status_code=404, detail=f"Server {server_id} not found")

    try:
        prompts = await client_manager.prompts_list(server_id)

        # Update server config with prompt list
        server.prompts = list(prompts.keys())
        config_manager.update_server_config(server_id, server)

        return {
            "server_id": server_id,
            "server_name": server.name,
            "prompts": [
                {
                    "name": prompt.name,
                    "description": prompt.description,
                    "arguments": [
                        {
                            "name": arg.name,
                            "description": arg.description,
                            "required": arg.required
                        }
                        for arg in (prompt.arguments or [])
                    ]
                }
                for prompt in prompts.values()
            ]
        }
    except AuthenticationError:
        raise HTTPException(status_code=401, detail="Authentication required")
    except Exception as e:
        logger.error(f"Failed to list prompts from {server_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{server_id}/prompts/get")
@trace_async("mcp.get_prompt")
async def get_prompt(
    server_id: str,
    request: MCPPromptRequest,
    client_manager: MCPClientManager = Depends(get_client_manager),
    config_manager: MCPConfigManager = Depends(get_config_manager)
):
    """Get a prompt from an MCP server."""
    server = config_manager.get_server(server_id)

    if not server:
        raise HTTPException(status_code=404, detail=f"Server {server_id} not found")

    try:
        result = await client_manager.get_prompt(
            server_id,
            request.prompt_name,
            request.arguments
        )

        return {
            "success": True,
            "prompt_name": request.prompt_name,
            "result": result.model_dump()
        }
    except AuthenticationError:
        raise HTTPException(status_code=401, detail="Authentication required")
    except MCPOperationError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error getting prompt: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{server_id}/update")
@trace_async("mcp.update")
async def update_server(
    server_id: str,
    request: MCPUpdateRequest,
    config_manager: MCPConfigManager = Depends(get_config_manager)
):
    """Update MCP server configuration."""
    server = config_manager.get_server(server_id)

    if not server:
        raise HTTPException(status_code=404, detail=f"Server {server_id} not found")

    try:
        # Update fields if provided
        if request.name is not None:
            server.name = request.name
        if request.description is not None:
            server.description = request.description
        if request.enabled is not None:
            server.enabled = request.enabled
        if request.auto_connect is not None:
            server.auto_connect = request.auto_connect
        if request.command is not None:
            server.command = request.command
        if request.args is not None:
            server.args = request.args
        if request.env is not None:
            server.env = request.env
        if request.url is not None:
            server.url = request.url
        if request.headers is not None:
            server.headers = request.headers

        # Save updated config
        if not config_manager.update_server_config(server_id, server):
            raise HTTPException(status_code=500, detail="Failed to update server")

        logger.info(f"✅ Updated MCP server: {server.name}")

        return {
            "success": True,
            "message": f"Server {server.name} updated successfully",
            "server_id": server_id
        }
    except Exception as e:
        logger.error(f"Failed to update server: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{server_id}/uninstall")
@trace_async("mcp.uninstall")
async def uninstall_server(
    server_id: str,
    config_manager: MCPConfigManager = Depends(get_config_manager),
    client_manager: MCPClientManager = Depends(get_client_manager)
):
    """Uninstall an MCP server."""
    server = config_manager.get_server(server_id)

    if not server:
        raise HTTPException(status_code=404, detail=f"Server {server_id} not found")

    try:
        # Disconnect if connected
        if client_manager.is_connected(server.name):
            await client_manager.disconnect(server.name)

        # Remove from config
        if not config_manager.remove_server(server_id):
            raise HTTPException(status_code=500, detail="Failed to remove server")

        logger.info(f"✅ Uninstalled MCP server: {server.name}")

        return {
            "success": True,
            "message": f"Server {server.name} uninstalled successfully"
        }
    except Exception as e:
        logger.error(f"Failed to uninstall server: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Import datetime for timestamps
from datetime import datetime


# ============================================================================
# Global MCP Registry Endpoints
# ============================================================================

@router.get("/registry/servers")
@trace_async("mcp.registry.list")
async def list_global_mcp_servers(
    category: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    user_context: UserContext = Depends(get_user_context)
):
    """
    List all global MCP servers with optional filtering.

    Returns a list of pre-configured MCP servers that are available globally.
    """
    try:
        logger.info(f"📋 Listing global MCP servers for user {user_context.user_id}")

        from vmcp.backend.storage.database import SessionLocal
        from vmcp.backend.storage.models import GlobalMCPServerRegistry
        from sqlalchemy import or_

        # Get database session
        db = SessionLocal()

        try:
            # Build query
            query = db.query(GlobalMCPServerRegistry)

            # Apply filters
            if category:
                query = query.filter(GlobalMCPServerRegistry.category == category)

            if search:
                search_term = f"%{search.lower()}%"
                query = query.filter(
                    or_(
                        GlobalMCPServerRegistry.name.ilike(search_term),
                        GlobalMCPServerRegistry.description.ilike(search_term)
                    )
                )

            # Apply pagination
            total_count = query.count()
            servers = query.offset(offset).limit(limit).all()

            # Convert to response format
            server_list = []
            for server in servers:
                server_data = {
                    "id": server.server_id,
                    "name": server.name,
                    "description": server.description,
                    "transport": server.transport_type,
                    "url": server.url,
                    "favicon_url": server.favicon_url,
                    "category": server.category or "MCP Servers",
                    "icon": server.icon or "🔍",
                    "requiresAuth": server.requires_auth,
                    "env_vars": server.env_vars or "",
                    "note": server.note or "",
                    "mcp_registry_config": {
                        "env": None,
                        "url": server.url,
                        "args": None,
                        "name": server.name
                    },
                    "mcp_server_config": {
                        "env": None,
                        "url": server.url,
                        "args": None,
                        "auth": None,
                        "name": server.name
                    },
                    "stats": {
                        "last_used": None,
                        "usage_count": 0,
                        "success_rate": 0
                    },
                    "created_at": server.created_at.isoformat() if server.created_at else None,
                    "updated_at": server.updated_at.isoformat() if server.updated_at else None
                }
                server_list.append(server_data)

            logger.info(f"✅ Retrieved {len(server_list)} global MCP servers (total: {total_count})")

            return {
                "success": True,
                "servers": server_list,
                "total": total_count,
                "limit": limit,
                "offset": offset
            }
        finally:
            db.close()

    except Exception as e:
        logger.error(f"❌ Error listing global MCP servers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/registry/servers/{server_id}")
@trace_async("mcp.registry.get")
async def get_global_mcp_server(
    server_id: str,
    user_context: UserContext = Depends(get_user_context)
):
    """
    Get a specific global MCP server by ID.
    """
    try:
        logger.info(f"📋 Getting global MCP server {server_id} for user {user_context.user_id}")

        from vmcp.backend.storage.database import SessionLocal
        from vmcp.backend.storage.models import GlobalMCPServerRegistry

        # Get database session
        db = SessionLocal()

        try:
            server = db.query(GlobalMCPServerRegistry).filter(
                GlobalMCPServerRegistry.server_id == server_id
            ).first()

            if not server:
                raise HTTPException(status_code=404, detail=f"Global MCP server not found: {server_id}")

            server_data = {
                "id": server.server_id,
                "name": server.name,
                "description": server.description,
                "transport": server.transport_type,
                "url": server.url,
                "favicon_url": server.favicon_url,
                "category": server.category or "MCP Servers",
                "icon": server.icon or "🔍",
                "requiresAuth": server.requires_auth,
                "env_vars": server.env_vars or "",
                "note": server.note or "",
                "mcp_registry_config": {
                    "env": None,
                    "url": server.url,
                    "args": None,
                    "name": server.name
                },
                "mcp_server_config": {
                    "env": None,
                    "url": server.url,
                    "args": None,
                    "auth": None,
                    "name": server.name
                },
                "stats": {
                    "last_used": None,
                    "usage_count": 0,
                    "success_rate": 0
                },
                "created_at": server.created_at.isoformat() if server.created_at else None,
                "updated_at": server.updated_at.isoformat() if server.updated_at else None
            }

            logger.info(f"✅ Retrieved global MCP server: {server.name}")
            return {
                "success": True,
                "server": server_data
            }
        finally:
            db.close()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error getting global MCP server {server_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
