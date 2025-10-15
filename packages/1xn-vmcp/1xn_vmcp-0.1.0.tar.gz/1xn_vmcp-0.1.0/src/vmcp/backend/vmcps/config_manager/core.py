"""
Core Operations Module
=====================

Handles CRUD operations and capability aggregation for vMCP configurations.

Responsibilities:
- vMCP configuration management (create, read, update, delete)
- Resource management (add, update, delete)
- Capability aggregation (tools, resources, prompts from multiple servers)
- Widget integration for OpenAI Apps SDK
"""

import asyncio
import logging
import urllib.parse
from typing import List, Dict, Any, Optional
from datetime import datetime

from mcp.types import Tool, Resource, ResourceTemplate, Prompt, PromptArgument

from vmcp.backend.utilities.tracing import trace_method, log_to_span
from vmcp.backend.vmcps.models import VMCPConfig
from vmcp.backend.vmcps.default_prompts import get_all_default_prompts
from vmcp.backend.config import settings
from .helpers import UIWidget, tool_meta as _tool_meta

logger = logging.getLogger("vmcp.config_manager.core")


class CoreOperations:
    """Core CRUD and aggregation operations for vMCP management."""

    def __init__(self, manager):
        """
        Initialize core operations.

        Args:
            manager: Parent VMCPConfigManager instance
        """
        self.manager = manager
        self.storage = manager.storage
        self.user_id = manager.user_id
        self.vmcp_id = manager.vmcp_id
        self.mcp_config_manager = manager.mcp_config_manager

    # ============================================================================
    # CRUD Operations
    # ============================================================================

    @trace_method("CoreOperations.load_vmcp_config")
    def load_vmcp_config(self, specific_vmcp_id: Optional[str] = None) -> Optional[VMCPConfig]:
        """
        Load vMCP configuration from storage.

        Args:
            specific_vmcp_id: Optional specific vMCP ID to load

        Returns:
            VMCPConfig if found, None otherwise
        """
        vmcp_id_to_load = specific_vmcp_id or self.vmcp_id

        log_to_span(
            f"Loading vMCP config: {vmcp_id_to_load}",
            operation_type="config_load",
            vmcp_id=vmcp_id_to_load
        )

        result = self.storage.load_vmcp_config(vmcp_id_to_load)

        if result:
            log_to_span(
                f"Loaded vMCP config: {result.name}",
                operation_type="config_load",
                vmcp_id=vmcp_id_to_load,
                total_tools=result.total_tools
            )
        else:
            log_to_span(
                f"vMCP config not found: {vmcp_id_to_load}",
                operation_type="config_load",
                vmcp_id=vmcp_id_to_load
            )

        return result

    @trace_method("CoreOperations.list_available_vmcps")
    def list_available_vmcps(self) -> List[Dict[str, Any]]:
        """List all available vMCP configurations for the user."""
        return self.storage.list_vmcps()

    @trace_method("CoreOperations.save_vmcp_config")
    def save_vmcp_config(self, vmcp_config: VMCPConfig) -> bool:
        """Save a vMCP configuration to storage."""
        return self.storage.save_vmcp(vmcp_config)

    def create_vmcp_config(
        self,
        name: str,
        description: Optional[str] = None,
        system_prompt: Optional[Dict[str, Any]] = None,
        vmcp_config: Optional[Dict[str, Any]] = None,
        custom_prompts: Optional[List[Dict[str, Any]]] = None,
        custom_tools: Optional[List[Dict[str, Any]]] = None,
        custom_context: Optional[List[str]] = None,
        custom_resources: Optional[List[Dict[str, Any]]] = None,
        custom_resource_templates: Optional[List[Dict[str, Any]]] = None,
        custom_resource_uris: Optional[List[str]] = None,
        environment_variables: Optional[List[Dict[str, Any]]] = None,
        uploaded_files: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[str]:
        """
        Create a new vMCP configuration.

        Args:
            name: vMCP name
            description: Optional description
            system_prompt: System prompt configuration
            vmcp_config: vMCP configuration with selected servers, tools, resources, prompts
            custom_prompts: Custom prompts
            custom_tools: Custom tools (prompt/python/http)
            custom_context: Custom context strings
            custom_resources: Custom resources
            custom_resource_templates: Custom resource templates
            custom_resource_uris: Custom resource URIs
            environment_variables: Environment variables
            uploaded_files: Uploaded files

        Returns:
            vMCP ID if successful, None otherwise
        """
        try:
            import uuid
            vmcp_id = str(uuid.uuid4())

            # Convert string system prompt to object format if needed
            if isinstance(system_prompt, str):
                system_prompt = {
                    "text": system_prompt,
                    "variables": []
                }

            # Calculate totals
            vmcp_cfg = vmcp_config or {}
            total_tools = len(custom_tools or []) + sum(
                len(x) for x in vmcp_cfg.get('selected_tools', {}).values()
            )
            total_resources = len(custom_resources or []) + sum(
                len(x) for x in vmcp_cfg.get('selected_resources', {}).values()
            )
            total_resource_templates = len(custom_resource_templates or []) + sum(
                len(x) for x in vmcp_cfg.get('selected_resource_templates', {}).values()
            )
            total_prompts = len(custom_prompts or []) + sum(
                len(x) for x in vmcp_cfg.get('selected_prompts', {}).values()
            )

            # Create vMCP configuration
            config = VMCPConfig(
                id=vmcp_id,
                name=name,
                user_id=self.user_id,
                description=description,
                system_prompt=system_prompt,
                vmcp_config=vmcp_cfg,
                custom_prompts=custom_prompts or [],
                custom_tools=custom_tools or [],
                custom_context=custom_context or [],
                custom_resources=custom_resources or [],
                custom_resource_templates=custom_resource_templates or [],
                environment_variables=environment_variables or [],
                uploaded_files=uploaded_files or [],
                custom_resource_uris=custom_resource_uris or [],
                total_tools=total_tools,
                total_resources=total_resources,
                total_resource_templates=total_resource_templates,
                total_prompts=total_prompts,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

            # Save to storage
            success = self.storage.save_vmcp(vmcp_id, config.to_dict())
            if success:
                logger.info(f"Created vMCP config: {name} (ID: {vmcp_id})")
                return vmcp_id
            else:
                logger.error(f"Failed to save vMCP config: {name}")
                return None

        except Exception as e:
            logger.error(f"Error creating vMCP config: {e}")
            return None

    @trace_method("CoreOperations.update_vmcp_config")
    def update_vmcp_config(
        self,
        vmcp_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        system_prompt: Optional[Dict[str, Any]] = None,
        vmcp_config: Optional[Dict[str, Any]] = None,
        custom_prompts: Optional[List[Dict[str, Any]]] = None,
        custom_tools: Optional[List[Dict[str, Any]]] = None,
        custom_context: Optional[List[str]] = None,
        custom_resources: Optional[List[Dict[str, Any]]] = None,
        custom_resource_templates: Optional[List[Dict[str, Any]]] = None,
        custom_resource_uris: Optional[List[str]] = None,
        environment_variables: Optional[List[Dict[str, Any]]] = None,
        uploaded_files: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """Update an existing vMCP configuration."""
        try:
            # Load existing config
            existing_config = self.storage.load_vmcp_config(vmcp_id)
            if not existing_config:
                logger.error(f"vMCP config not found: {vmcp_id}")
                return False

            # Update fields if provided
            if name is not None:
                existing_config.name = name
            if description is not None:
                existing_config.description = description
            if system_prompt is not None:
                existing_config.system_prompt = system_prompt
            if vmcp_config is not None:
                existing_config.vmcp_config = vmcp_config
            if custom_prompts is not None:
                existing_config.custom_prompts = custom_prompts
            if custom_tools is not None:
                existing_config.custom_tools = custom_tools
            if custom_context is not None:
                existing_config.custom_context = custom_context
            if custom_resources is not None:
                existing_config.custom_resources = custom_resources
            if custom_resource_templates is not None:
                existing_config.custom_resource_templates = custom_resource_templates
            if custom_resource_uris is not None:
                existing_config.custom_resource_uris = custom_resource_uris
            if environment_variables is not None:
                existing_config.environment_variables = environment_variables
            if uploaded_files is not None:
                existing_config.uploaded_files = uploaded_files

            # Recalculate totals
            existing_vmcp_config = existing_config.vmcp_config or {}
            selected_tools = existing_vmcp_config.get('selected_tools', {}) or {}
            selected_resources = existing_vmcp_config.get('selected_resources', {}) or {}
            selected_resource_templates = existing_vmcp_config.get('selected_resource_templates', {}) or {}
            selected_prompts = existing_vmcp_config.get('selected_prompts', {}) or {}

            total_tools = len(existing_config.custom_tools or []) + sum(
                len(x) for x in selected_tools.values() if isinstance(x, list)
            )
            total_resources = len(existing_config.custom_resources or []) + sum(
                len(x) for x in selected_resources.values() if isinstance(x, list)
            )
            total_resource_templates = len(existing_config.custom_resource_templates or []) + sum(
                len(x) for x in selected_resource_templates.values() if isinstance(x, list)
            )
            total_prompts = len(existing_config.custom_prompts or []) + sum(
                len(x) for x in selected_prompts.values() if isinstance(x, list)
            )

            existing_config.total_tools = total_tools
            existing_config.total_resources = total_resources
            existing_config.total_resource_templates = total_resource_templates
            existing_config.total_prompts = total_prompts
            existing_config.updated_at = datetime.utcnow()

            # Save updated config
            success = self.storage.update_vmcp(existing_config)
            if success:
                logger.info(f"Updated vMCP config: {existing_config.name} (ID: {vmcp_id})")
            else:
                logger.error(f"Failed to update vMCP config: {vmcp_id}")

            return success

        except Exception as e:
            logger.error(f"Error updating vMCP config {vmcp_id}: {e}")
            return False

    @trace_method("CoreOperations.delete_vmcp")
    def delete_vmcp(self, vmcp_id: str) -> Dict[str, Any]:
        """Delete a vMCP configuration and handle all cleanup."""
        try:
            self.storage.delete_vmcp(vmcp_id)
            return {
                "success": True,
                "message": f"Successfully deleted {vmcp_id}"
            }

        except Exception as e:
            logger.error(f"Error deleting vMCP {vmcp_id}: {e}")
            return {
                "success": False,
                "message": f"Failed to delete vMCP: {str(e)}"
            }

    # ============================================================================
    # Resource Management
    # ============================================================================

    @trace_method("CoreOperations.add_resource")
    def add_resource(self, vmcp_id: str, resource_data: Dict[str, Any]) -> bool:
        """Add a resource to the vMCP."""
        logger.info(f"Adding resource to vMCP: {vmcp_id}")
        try:
            vmcp_config = self.storage.load_vmcp_config(vmcp_id)
            if not vmcp_config:
                return False

            vmcp_config.uploaded_files.append(resource_data)
            vmcp_config.custom_resources.append(resource_data)
            vmcp_config.updated_at = datetime.now()
            return self.storage.update_vmcp(vmcp_config)
        except Exception as e:
            logger.error(f"Error adding resource to vMCP {vmcp_id}: {e}")
            return False

    @trace_method("CoreOperations.update_resource")
    def update_resource(self, vmcp_id: str, resource_data: Dict[str, Any]) -> bool:
        """Update a resource in the vMCP."""
        logger.info(f"Updating resource in vMCP: {vmcp_id}")
        try:
            vmcp_config = self.storage.load_vmcp_config(vmcp_id)
            if not vmcp_config:
                return False

            # Remove old version
            vmcp_config.uploaded_files = [
                r for r in vmcp_config.uploaded_files
                if r.get('id') != resource_data.get('id')
            ]
            vmcp_config.custom_resources = [
                r for r in vmcp_config.custom_resources
                if r.get('id') != resource_data.get('id')
            ]
            # Add new version
            vmcp_config.uploaded_files.append(resource_data)
            vmcp_config.custom_resources.append(resource_data)
            vmcp_config.updated_at = datetime.now()
            return self.storage.update_vmcp(vmcp_config)
        except Exception as e:
            logger.error(f"Error updating resource in vMCP {vmcp_id}: {e}")
            return False

    @trace_method("CoreOperations.delete_resource")
    def delete_resource(self, vmcp_id: str, resource_data: Dict[str, Any]) -> bool:
        """Delete a resource from the vMCP."""
        logger.info(f"Deleting resource from vMCP: {vmcp_id}")
        try:
            vmcp_config = self.storage.load_vmcp_config(vmcp_id)
            if not vmcp_config:
                return False

            vmcp_config.uploaded_files = [
                r for r in vmcp_config.uploaded_files
                if r.get('id') != resource_data.get('id')
            ]
            vmcp_config.custom_resources = [
                r for r in vmcp_config.custom_resources
                if r.get('id') != resource_data.get('id')
            ]
            vmcp_config.updated_at = datetime.now()
            return self.storage.update_vmcp(vmcp_config)
        except Exception as e:
            logger.error(f"Error deleting resource from vMCP {vmcp_id}: {e}")
            return False

    # ============================================================================
    # Capability Aggregation - List Operations
    # ============================================================================

    @trace_method("CoreOperations.tools_list")
    async def tools_list(self) -> List[Tool]:
        """
        List all tools from the vMCP's selected servers and custom tools.

        Aggregates tools from:
        - Selected MCP servers (with filtering if configured)
        - Custom tools (prompt/python/http types)
        - Tool overrides and renaming
        - Widget attachments for OpenAI Apps SDK

        Returns:
            List of Tool objects
        """
        if not self.vmcp_id:
            log_to_span(
                operation_type="tools_list",
                operation_id="tools_list_no_vmcp_id",
                result={"success": False, "error": "No vmcp_id provided"},
                level="warning"
            )
            return []

        vmcp_config = self.storage.load_vmcp_config(self.vmcp_id)
        if not vmcp_config:
            log_to_span(
                operation_type="tools_list",
                operation_id=f"tools_list_{self.vmcp_id}",
                result={"success": False, "error": "VMCP config not found"},
                level="warning"
            )
            return []

        vmcp_servers = vmcp_config.vmcp_config.get('selected_servers', [])
        vmcp_selected_tools = vmcp_config.vmcp_config.get('selected_tools', {})
        vmcp_selected_tool_overrides = vmcp_config.vmcp_config.get('selected_tool_overrides', {})
        all_tools = []

        # Aggregate tools from servers
        for server in vmcp_servers:
            server_id = server.get('server_id')
            server_name = server.get('name')
            server_tools = self.mcp_config_manager.tools_list(server_id)

            # Filter to selected tools if configured
            if server_id in vmcp_selected_tools:
                selected_tools = vmcp_selected_tools.get(server_id, [])
                server_tools = [tool for tool in server_tools if tool.name in selected_tools]

            selected_tool_overrides = {}
            if server_id in vmcp_selected_tool_overrides:
                selected_tool_overrides = vmcp_selected_tool_overrides.get(server_id, {})

            for tool in server_tools:
                # Get tool overrides (name, description, widget)
                tool_override = selected_tool_overrides.get(tool.name, {})
                _tool_name = tool_override.get("name", tool.name)
                _tool_description = tool_override.get("description", tool.description)

                # Build tool meta including widget information if attached
                tool_meta_dict = {
                    **(tool.meta or {}),
                    "original_name": tool.name,
                    "server": server_name,
                    "vmcp_id": self.vmcp_id,
                    "server_id": server_id
                }

                widget_meta = {}
                # Add widget metadata if widget is attached to this tool
                if "widget_id" in tool_override and tool_override["widget_id"]:
                    widget_id = tool_override["widget_id"]

                    # Load widget from database
                    from vmcp.backend.storage.models import Widget, Blob
                    from vmcp.backend.storage.database import get_db

                    db = next(get_db())
                    try:
                        widgets = db.query(Widget).filter(
                            Widget.widget_id == widget_id
                        ).all()
                        widget = [widget.to_dict() for widget in widgets]
                        if widget:
                            widget = widget[0]

                        invoking_message = "Loading"
                        invoked_message = "Loaded"
                        widget_metadata = tool_override.get("widget_metadata", {})
                        if widget_metadata.get("invoking_message"):
                            invoking_message = widget_metadata["invoking_message"]
                        if widget_metadata.get("invoked_message"):
                            invoked_message = widget_metadata["invoked_message"]

                        blob = ""
                        # Widget HTML can be loaded from blob storage if needed
                        uiwidget = UIWidget(
                            identifier=widget.get("name"),
                            title=widget.get("name"),
                            template_uri=widget.get("template_uri"),
                            invoking=invoking_message,
                            invoked=invoked_message,
                            html=blob,
                            response_text=f"Rendered a widget for {tool.name}",
                        )
                        widget_meta = _tool_meta(uiwidget)
                        logger.info(f"Loaded {len(widgets)} widgets for vMCP: {self.vmcp_id}")
                    except Exception as e:
                        logger.error(f"Failed to load widgets: {e}")
                    finally:
                        db.close()

                tool_meta_dict.update(widget_meta)

                # Create tool with server-prefixed name
                vmcp_tool = Tool(
                    name=f"{server_name.replace('_', '')}_{_tool_name}",
                    description=_tool_description,
                    inputSchema=tool.inputSchema,
                    outputSchema=tool.outputSchema,
                    annotations=tool.annotations,
                    meta=tool_meta_dict
                )
                all_tools.append(vmcp_tool)

        # Add custom tools
        for custom_tool in vmcp_config.custom_tools:
            tool_type = custom_tool.get('tool_type', 'prompt')

            if tool_type == 'python':
                # For Python tools, parse the function to extract parameters
                tool_input_schema = self.manager.custom_tools.parse_python_function_schema(custom_tool)
            else:
                # For prompt and HTTP tools, use the existing logic
                tool_input_variables = custom_tool.get("variables", [])
                tool_input_schema = {
                    "type": "object",
                    "properties": {
                        var.get("name"): {
                            "type": "string",
                            "description": var.get("description")
                        }
                        for var in tool_input_variables
                    },
                    "required": [var.get("name") for var in tool_input_variables if var.get("required")],
                    "additionalProperties": False,
                    "$schema": "http://json-schema.org/draft-07/schema#"
                }

            # Get keywords from custom tool config and append to description
            keywords = custom_tool.get("keywords", [])
            description = custom_tool.get("description", "")

            # Append keywords to description if they exist
            if keywords:
                keywords_str = ", ".join(keywords) if isinstance(keywords, list) else str(keywords)
                description = f"{description} [Keywords: {keywords_str}]"

            title = custom_tool.get('name')

            custom_tool_obj = Tool(
                name=custom_tool.get("name"),
                description=description,
                inputSchema=tool_input_schema,
                title=title,
                meta={
                    "type": "custom",
                    "tool_type": tool_type,
                    "vmcp_id": self.vmcp_id
                }
            )
            all_tools.append(custom_tool_obj)

        # Background logging
        if self.user_id:
            asyncio.create_task(
                self.manager.execution.log_vmcp_operation(
                    operation_type="tool_list",
                    operation_id=self.vmcp_id,
                    arguments=None,
                    result=all_tools,
                    metadata={"server": "vmcp", "tool": "all_tools", "server_id": self.vmcp_id}
                )
            )

        # Log success to span
        log_to_span(
            operation_type="tools_list",
            operation_id=f"tools_list_{self.vmcp_id}",
            result={
                "success": True,
                "tool_count": len(all_tools),
                "tools": [tool.name for tool in all_tools[:5]]
            },
            level="info"
        )

        return all_tools

    @trace_method("CoreOperations.resources_list")
    async def resources_list(self) -> List[Resource]:
        """
        List all resources from the vMCP's selected servers.

        Aggregates resources from:
        - Selected MCP servers
        - Custom resources (uploaded files)
        - Widget resources (for OpenAI Apps SDK)

        Returns:
            List of Resource objects
        """
        if not self.vmcp_id:
            return []

        logger.info(f"Fetching resources for vMCP: {self.vmcp_id}")
        vmcp_config = self.storage.load_vmcp_config(self.vmcp_id)
        vmcp_name = vmcp_config.name
        if not vmcp_config:
            return []

        # Load widgets from database for this vMCP
        from vmcp.backend.storage.models import Widget
        from vmcp.backend.storage.database import get_db

        db = next(get_db())
        try:
            widgets = db.query(Widget).filter(
                Widget.user_id == self.user_id,
                Widget.vmcp_id == self.vmcp_id
            ).all()
            vmcp_config.custom_widgets = [widget.to_dict() for widget in widgets]
            logger.info(f"Loaded {len(widgets)} widgets for vMCP: {self.vmcp_id}")
        except Exception as e:
            logger.error(f"Failed to load widgets: {e}")
            vmcp_config.custom_widgets = []
        finally:
            db.close()

        vmcp_servers = vmcp_config.vmcp_config.get('selected_servers', [])
        vmcp_selected_resources = vmcp_config.vmcp_config.get('selected_resources', {})
        all_resources = []

        # Aggregate resources from servers
        for server in vmcp_servers:
            server_name = server.get('name')
            server_id = server.get('server_id')
            server_resources = self.mcp_config_manager.resources_list(server_id)

            # Filter to selected resources if configured
            if server_id in vmcp_selected_resources:
                selected_resources = vmcp_selected_resources.get(server_id, [])
                server_resources = [
                    resource for resource in server_resources
                    if str(resource.uri) in selected_resources
                ]

            for resource in server_resources:
                vmcp_resource = Resource(
                    name=f"{server_name.replace('_', '')}_{resource.name}",
                    uri=f"{server_name.replace('_', '')}:{resource.uri}",
                    description=resource.description,
                    mimeType=resource.mimeType,
                    size=resource.size,
                    annotations=resource.annotations,
                    meta={
                        **(resource.meta or {}),
                        "original_name": resource.name,
                        "server": server_name,
                        "vmcp_id": self.vmcp_id,
                        "server_id": server_id
                    }
                )
                all_resources.append(vmcp_resource)

        # Add custom resources (uploaded files)
        custom_resources = vmcp_config.custom_resources
        for file in custom_resources:
            # Create a valid URI by using a proper scheme and URL-encoding the filename
            original_filename = file.get('original_filename', 'unknown_file')
            encoded_filename = urllib.parse.quote(original_filename, safe='')
            vmcp_scheme = f"vmcp-{vmcp_name.replace('_', '-')}"

            vmcp_resource = Resource(
                name=original_filename,
                title=original_filename,
                uri=f"custom:{vmcp_scheme}://{encoded_filename}",
                mimeType=file.get('content_type'),
                size=file.get('size'),
                meta={
                    "original_name": original_filename,
                    "server": "vmcp",
                    "vmcp_id": self.vmcp_id
                }
            )
            all_resources.append(vmcp_resource)

        # Add widget resources
        custom_widgets = vmcp_config.custom_widgets or []
        for widget in custom_widgets:
            # Only include built widgets
            if widget.get('build_status') == 'built':
                widget_id = widget.get('id')
                widget_name = widget.get('name', 'Unnamed Widget')
                widget_description = widget.get('description', '')
                template_uri = widget.get('template_uri', f'ui://widget/{widget_id}')

                # Widget serving URLs
                widget_js_uri = f"{settings.BASE_URL}/widgets/{widget_id}/serve/js"
                widget_css_uri = f"{settings.BASE_URL}/widgets/{widget_id}/serve/css"

                vmcp_resource = Resource(
                    name=widget_name,
                    title=widget_name,
                    uri=template_uri,
                    description=widget_description,
                    mimeType="text/html+skybridge",
                    meta={
                        "original_name": widget_name,
                        "server": "vmcp",
                        "vmcp_id": self.vmcp_id,
                        "widget_id": widget_id,
                        "widget_js_uri": widget_js_uri,
                        "widget_css_uri": widget_css_uri,
                        "template_uri": template_uri,
                        "resource_type": "widget"
                    }
                )
                all_resources.append(vmcp_resource)

        # Background logging
        if self.user_id:
            asyncio.create_task(
                self.manager.execution.log_vmcp_operation(
                    operation_type="resource_list",
                    operation_id=self.vmcp_id,
                    arguments=None,
                    result=all_resources,
                    metadata={"server": "vmcp", "resource": "all_resources", "server_id": self.vmcp_id}
                )
            )

        return all_resources

    @trace_method("CoreOperations.resource_templates_list")
    async def resource_templates_list(self) -> List[ResourceTemplate]:
        """List all resource templates from the vMCP's selected servers."""
        if not self.vmcp_id:
            return []

        vmcp_config = self.storage.load_vmcp_config(self.vmcp_id)
        if not vmcp_config:
            return []

        vmcp_servers = vmcp_config.vmcp_config.get('selected_servers', [])
        vmcp_selected_resource_templates = vmcp_config.vmcp_config.get('selected_resource_templates', {})
        all_resource_templates = []

        for server in vmcp_servers:
            server_name = server.get('name')
            server_id = server.get('server_id')
            server_resource_templates = self.mcp_config_manager.resource_templates_list(server_id)

            # Filter to selected resource templates if configured
            if server_id in vmcp_selected_resource_templates:
                selected_resource_templates = vmcp_selected_resource_templates.get(server_id, [])
                server_resource_templates = [
                    template for template in server_resource_templates
                    if template.name in selected_resource_templates
                ]

            for template in server_resource_templates:
                # Create a new ResourceTemplate object with vMCP-specific naming
                vmcp_template = ResourceTemplate(
                    name=f"{server_name.replace('_', '')}_{template.name}",
                    uriTemplate=template.uriTemplate,
                    description=template.description,
                    mimeType=template.mimeType,
                    annotations=template.annotations,
                    meta={
                        **(template.meta or {}),
                        "original_name": template.name,
                        "server": server_name,
                        "vmcp_id": self.vmcp_id,
                        "server_id": server_id
                    }
                )
                all_resource_templates.append(vmcp_template)

        # Background logging
        if self.user_id:
            asyncio.create_task(
                self.manager.execution.log_vmcp_operation(
                    operation_type="resource_template_list",
                    operation_id=self.vmcp_id,
                    arguments=None,
                    result=all_resource_templates,
                    metadata={"server": "vmcp", "resource_template": "all_resource_templates", "server_id": self.vmcp_id}
                )
            )

        return all_resource_templates

    @trace_method("CoreOperations.prompts_list")
    async def prompts_list(self) -> List[Prompt]:
        """
        List all prompts from the vMCP's selected servers and custom prompts.

        Aggregates prompts from:
        - Selected MCP servers
        - Custom prompts
        - Custom tools (can be used as prompts)
        - Default system prompts

        Returns:
            List of Prompt objects
        """
        if not self.vmcp_id:
            # Return default system prompts even without vMCP
            return get_all_default_prompts()

        vmcp_config = self.storage.load_vmcp_config(self.vmcp_id)
        if not vmcp_config:
            return []

        vmcp_servers = vmcp_config.vmcp_config.get('selected_servers', [])
        vmcp_selected_prompts = vmcp_config.vmcp_config.get('selected_prompts', {})
        all_prompts = []

        logger.info(f"Collecting prompts from {len(vmcp_servers)} servers...")

        # Add prompts from attached servers
        for server in vmcp_servers:
            server_name = server.get('name')
            server_id = server.get('server_id')
            server_prompts = self.mcp_config_manager.prompts_list(server_id)

            # Filter to selected prompts if configured
            if server_id in vmcp_selected_prompts:
                selected_prompts = vmcp_selected_prompts.get(server_id, [])
                server_prompts = [
                    prompt for prompt in server_prompts
                    if prompt.name in selected_prompts
                ]
            logger.info(f"Collected {len(server_prompts)} prompts from {server_name}")

            for prompt in server_prompts:
                # Create a new Prompt object with vMCP-specific naming
                vmcp_prompt = Prompt(
                    name=f"{server_name.replace('_', '')}_{prompt.name}",
                    title=f"#{server_name.replace('_', '')}_{prompt.name}",
                    description=prompt.description,
                    arguments=prompt.arguments,
                    meta={
                        **(prompt.meta or {}),
                        "original_name": prompt.name,
                        "server": server_name,
                        "vmcp_id": self.vmcp_id,
                        "server_id": server_id
                    }
                )
                all_prompts.append(vmcp_prompt)

        # Add custom prompts from vMCP config
        for custom_prompt in vmcp_config.custom_prompts:
            # Convert custom prompt variables to PromptArgument objects
            prompt_arguments = []

            # Add variables from custom prompt
            if custom_prompt.get('variables'):
                for var in custom_prompt['variables']:
                    prompt_arg = PromptArgument(
                        name=var.get('name'),
                        description=var.get('description', f"Variable: {var.get('name')}"),
                        required=var.get('required', False)
                    )
                    prompt_arguments.append(prompt_arg)

            # Create a new Prompt object for custom prompt
            custom_prompt_obj = Prompt(
                name=f"{custom_prompt.get('name')}",
                title=f"#{custom_prompt.get('name')}",
                description=custom_prompt.get("description", ""),
                arguments=prompt_arguments,
                meta={
                    "type": "custom",
                    "vmcp_id": self.vmcp_id,
                    "custom_prompt_id": custom_prompt.get("id")
                }
            )
            all_prompts.append(custom_prompt_obj)

        # Add custom tools as prompts too
        for custom_tool in vmcp_config.custom_tools:
            # Convert custom tool variables to PromptArgument objects
            prompt_arguments = []

            # Add variables from custom tool
            if custom_tool.get('variables'):
                for var in custom_tool['variables']:
                    prompt_arg = PromptArgument(
                        name=var.get('name'),
                        description=var.get('description', f"Variable: {var.get('name')}"),
                        required=var.get('required', False)
                    )
                    prompt_arguments.append(prompt_arg)

            # Create a new Prompt object for custom tool
            custom_prompt_obj = Prompt(
                name=f"{custom_tool.get('name')}",
                title=f"#{custom_tool.get('name')}",
                description=custom_tool.get("description", ""),
                arguments=prompt_arguments,
                meta={
                    "type": "custom",
                    "vmcp_id": self.vmcp_id,
                    "custom_tool_id": custom_tool.get("id")
                }
            )
            all_prompts.append(custom_prompt_obj)

        # Add default system prompts
        default_prompts = get_all_default_prompts(self.vmcp_id)
        all_prompts.extend(default_prompts)

        # Background logging
        if self.user_id:
            asyncio.create_task(
                self.manager.execution.log_vmcp_operation(
                    operation_type="prompt_list",
                    operation_id=self.vmcp_id,
                    arguments=None,
                    result=all_prompts,
                    metadata={"server": "vmcp", "prompt": "all_prompts", "server_id": self.vmcp_id}
                )
            )

        return all_prompts
