"""
Execution Manager Module
========================

Handles routing and execution of tool, resource, and prompt operations.

Responsibilities:
- Route tool/resource/prompt calls to appropriate servers or custom handlers
- Manage widget metadata for OpenAI Apps SDK
- Background operation logging
- Server configuration updates
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from mcp.types import (
    CallToolResult, ReadResourceResult, GetPromptResult,
    TextContent, PromptMessage, Resource, TextResourceContents,
    BlobResourceContents
)

from vmcp.backend.utilities.tracing import trace_method, add_event, log_to_span
from vmcp.backend.vmcps.models import VMCPToolCallRequest, VMCPResourceRequest
from vmcp.backend.vmcps.default_prompts import handle_default_prompt
from vmcp.backend.vmcps.utilities import convert_openxml_to_csv, get_mime_type
from vmcp.backend.mcps.models import MCPServerConfig
from .helpers import UIWidget, embedded_widget_resource as _embedded_widget_resource

logger = logging.getLogger("vmcp.config_manager.execution")


class ExecutionManager:
    """Manages execution and routing of tool, resource, and prompt operations."""

    def __init__(self, manager):
        """
        Initialize execution manager.

        Args:
            manager: Parent VMCPConfigManager instance
        """
        self.manager = manager
        self.storage = manager.storage
        self.user_id = manager.user_id
        self.vmcp_id = manager.vmcp_id
        self.mcp_client_manager = manager.mcp_client_manager
        self.logging_config = manager.logging_config

    # ============================================================================
    # Tool Execution
    # ============================================================================

    @trace_method("ExecutionManager.call_tool")
    async def call_tool(
        self,
        vmcp_tool_call_request: VMCPToolCallRequest,
        connect_if_needed: bool = True,
        return_metadata: bool = False
    ) -> Dict[str, Any]:
        """
        Execute a tool call by routing to the appropriate server or custom handler.

        Args:
            vmcp_tool_call_request: Tool call request with tool name and arguments
            connect_if_needed: Whether to connect to server if not connected
            return_metadata: Whether to return metadata along with result

        Returns:
            CallToolResult (and optionally metadata dict)

        Raises:
            ValueError: If tool not found or vMCP config not found
        """
        logger.info(f"call_tool called for '{vmcp_tool_call_request.tool_name}'")
        add_event(
            f"call_tool called for '{vmcp_tool_call_request.tool_name}'",
            metadata={"server": "vmcp", "tool": vmcp_tool_call_request.tool_name, "server_id": self.vmcp_id}
        )

        vmcp_config = self.storage.load_vmcp_config(self.vmcp_id)
        if not vmcp_config:
            raise ValueError(f"vMCP config not found: {self.vmcp_id}")

        # Check if it's a custom tool first
        custom_tools = vmcp_config.custom_tools
        for tool in custom_tools:
            if tool.get('name') == vmcp_tool_call_request.tool_name:
                result = await self.manager.custom_tools.call_custom_tool(
                    vmcp_tool_call_request.tool_name,
                    vmcp_tool_call_request.arguments
                )
                if return_metadata:
                    return result, {"server": "custom_tool", "tool": vmcp_tool_call_request.tool_name}
                else:
                    return result

        # Parse tool name to extract server and original tool name
        # Format: servername_toolname
        tool_server_name = vmcp_tool_call_request.tool_name.split('_')[0]
        tool_original_name = "_".join(vmcp_tool_call_request.tool_name.split('_')[1:])

        logger.info(f"Parsed tool name - server: '{tool_server_name}', original: '{tool_original_name}'")

        vmcp_servers = vmcp_config.vmcp_config.get('selected_servers', [])
        vmcp_selected_tool_overrides = vmcp_config.vmcp_config.get('selected_tool_overrides', {})

        # Find the matching server
        for server in vmcp_servers:
            server_name = server.get('name')
            server_id = server.get('server_id')
            server_name_clean = server_name.replace('_', '')

            logger.info(f"Checking server '{server_name}' (clean: '{server_name_clean}') against '{tool_server_name}'")

            if server_name_clean == tool_server_name:
                logger.info(f"Found matching server '{server_name}' for tool '{vmcp_tool_call_request.tool_name}'")

                # Initialize widget_meta to None
                widget_meta = None

                # Check for tool overrides and widget attachments
                if vmcp_selected_tool_overrides.get(server_id, {}):
                    server_tool_overrides = vmcp_selected_tool_overrides.get(server_id, {})

                    # Find the original tool name if it was renamed
                    for _original_tool in server_tool_overrides:
                        if server_tool_overrides.get(_original_tool).get("name") == tool_original_name:
                            tool_original_name = _original_tool
                            break

                    # Check for widget attachment
                    tool_override_data = server_tool_overrides.get(tool_original_name, {})
                    if "widget_id" in tool_override_data and tool_override_data["widget_id"]:
                        logger.info(f"Widget tool override {tool_override_data}")
                        widget_id = tool_override_data["widget_id"]

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
                            widget_metadata = tool_override_data.get("widget_metadata", {})
                            if widget_metadata.get("invoking_message"):
                                invoking_message = widget_metadata["invoking_message"]
                            if widget_metadata.get("invoked_message"):
                                invoked_message = widget_metadata["invoked_message"]

                            # Load widget HTML from blob storage
                            blob = ""
                            built_files = widget.get("built_files", None)
                            if built_files and built_files.get("html"):
                                blob_obj = db.query(Blob).filter(
                                    Blob.blob_id == built_files.get("html")
                                ).first()

                                if blob_obj and blob_obj.file_data:
                                    # file_data is stored as bytes, decode to string
                                    if isinstance(blob_obj.file_data, bytes):
                                        blob = blob_obj.file_data.decode('utf-8')
                                    else:
                                        blob = str(blob_obj.file_data)
                                    logger.info(f"Fetched blob HTML data, length: {len(blob)}")

                            # Ensure blob is never None
                            if not blob:
                                blob = ""
                                logger.warning("No HTML data found for widget, using empty string")

                            # Create widget object
                            uiwidget = UIWidget(
                                identifier=widget.get("name"),
                                title=widget.get("name"),
                                template_uri=widget.get("template_uri"),
                                invoking=invoking_message,
                                invoked=invoked_message,
                                html=blob,
                                response_text=f"Rendered a widget for {tool_original_name}",
                            )
                            widget_resource = _embedded_widget_resource(uiwidget)
                            widget_meta = {
                                "openai.com/widget": widget_resource.model_dump(mode="json"),
                                "openai/outputTemplate": uiwidget.template_uri,
                                "openai/toolInvocation/invoking": uiwidget.invoking,
                                "openai/toolInvocation/invoked": uiwidget.invoked,
                                "openai/widgetAccessible": True,
                                "openai/resultCanProduceWidget": True,
                            }
                            logger.info(f"Loaded {len(widgets)} widgets for vMCP: {self.vmcp_id}")
                        except Exception as e:
                            logger.error(f"Failed to load widgets: {e}")
                        finally:
                            db.close()

                # Call the tool on the server
                result = await self.mcp_client_manager.call_tool(
                    server_id,
                    tool_original_name,
                    vmcp_tool_call_request.arguments
                )

                logger.info(f"Tool call successful, result type: {type(result)}")

                # Background logging
                if self.user_id:
                    asyncio.create_task(
                        self.log_vmcp_operation(
                            operation_type="tool_call",
                            operation_id=vmcp_tool_call_request.tool_name,
                            arguments=vmcp_tool_call_request.arguments,
                            result=result,
                            metadata={"server": server_name, "tool": tool_original_name, "server_id": server_id}
                        )
                    )

                # Attach widget metadata if present
                if widget_meta:
                    result = CallToolResult(
                        content=result.content,
                        structuredContent=result.structuredContent,
                        _meta=widget_meta,
                    )

                if return_metadata:
                    return result, {"server": server_name, "tool": tool_original_name, "server_id": server_id}
                else:
                    return result

        # If we get here, the tool was not found in any server
        logger.error(f"Tool '{vmcp_tool_call_request.tool_name}' not found in any server")
        logger.error(f"Searched servers: {[s.get('name') for s in vmcp_servers]}")
        raise ValueError(f"Tool {vmcp_tool_call_request.tool_name} not found in vMCP {self.vmcp_id}")

    # ============================================================================
    # Resource Execution
    # ============================================================================

    @trace_method("ExecutionManager.get_resource")
    async def get_resource(self, resource_id: str, connect_if_needed: bool = True) -> ReadResourceResult:
        """
        Get a specific resource by routing to the appropriate server or custom handler.

        Args:
            resource_id: Resource URI/ID
            connect_if_needed: Whether to connect to server if not connected

        Returns:
            ReadResourceResult with resource contents

        Raises:
            ValueError: If resource not found or vMCP config not found
        """
        # Convert resource_id to string if it's a Pydantic AnyUrl or other object
        resource_id_str = str(resource_id)
        logger.info(f"Searching for resource '{resource_id_str}' in vMCP '{self.vmcp_id}'")

        vmcp_config = self.storage.load_vmcp_config(self.vmcp_id)
        if not vmcp_config:
            raise ValueError(f"vMCP config not found: {self.vmcp_id}")

        # Check if it's a custom resource (custom: scheme)
        if resource_id_str.startswith('custom:'):
            return await self.call_custom_resource(resource_id_str)

        # Check if it's a widget resource (ui://widget/ or template_uri)
        from vmcp.backend.storage.models import Widget
        from vmcp.backend.storage.database import get_db

        db = next(get_db())
        try:
            # Try to find widget by template_uri
            widget = db.query(Widget).filter(
                Widget.user_id == self.user_id,
                Widget.vmcp_id == self.vmcp_id,
                Widget.template_uri == resource_id_str
            ).first()

            if widget:
                logger.info(f"Found widget resource: {resource_id_str}")
                widget_dict = widget.to_dict()

                # Get built HTML from blob storage
                from vmcp.backend.storage.models import Blob
                built_files = widget_dict.get("built_files", {})
                html_blob_id = built_files.get("html")

                if html_blob_id:
                    blob = db.query(Blob).filter(Blob.blob_id == html_blob_id).first()
                    if blob and blob.file_data:
                        if isinstance(blob.file_data, bytes):
                            html_content = blob.file_data.decode('utf-8')
                        else:
                            html_content = str(blob.file_data)

                        return ReadResourceResult(
                            contents=[
                                TextResourceContents(
                                    uri=resource_id_str,
                                    mimeType="text/html+skybridge",
                                    text=html_content
                                )
                            ]
                        )

                # Fallback if no HTML found
                return ReadResourceResult(
                    contents=[
                        TextResourceContents(
                            uri=resource_id_str,
                            mimeType="text/plain",
                            text=f"Widget: {widget_dict.get('name', 'Unnamed Widget')}"
                        )
                    ]
                )
        finally:
            db.close()

        # Parse resource ID to extract server and original resource name
        # Format: servername:resource_uri
        if ':' in resource_id_str:
            parts = resource_id_str.split(':', 1)
            resource_server_name = parts[0]
            resource_original_uri = parts[1]
        else:
            # No server prefix, search all servers
            resource_server_name = None
            resource_original_uri = resource_id_str

        logger.info(f"Parsed resource - server: '{resource_server_name}', uri: '{resource_original_uri}'")

        vmcp_servers = vmcp_config.vmcp_config.get('selected_servers', [])

        # Find the matching server
        for server in vmcp_servers:
            server_name = server.get('name')
            server_id = server.get('server_id')
            server_name_clean = server_name.replace('_', '')

            # If server name specified, match it; otherwise try all servers
            if resource_server_name and server_name_clean != resource_server_name:
                continue

            logger.info(f"Checking server '{server_name}' for resource '{resource_original_uri}'")

            try:
                result = await self.mcp_client_manager.read_resource(
                    server_id,
                    resource_original_uri
                )

                logger.info(f"Resource read successful from server '{server_name}'")

                # Background logging
                if self.user_id:
                    asyncio.create_task(
                        self.log_vmcp_operation(
                            operation_type="resource_read",
                            operation_id=resource_id_str,
                            arguments=None,
                            result=result,
                            metadata={"server": server_name, "resource": resource_original_uri, "server_id": server_id}
                        )
                    )

                return result

            except Exception as e:
                logger.debug(f"Resource not found on server '{server_name}': {e}")
                continue

        # If we get here, the resource was not found
        logger.error(f"Resource '{resource_id_str}' not found in any server")
        raise ValueError(f"Resource {resource_id_str} not found in vMCP {self.vmcp_id}")

    @trace_method("ExecutionManager.call_custom_resource")
    async def call_custom_resource(self, resource_id: str) -> ReadResourceResult:
        """
        Fetch a custom resource from the vMCP's uploaded files.

        Args:
            resource_id: Custom resource URI (custom:vmcp-name://filename)

        Returns:
            ReadResourceResult with resource contents

        Raises:
            ValueError: If resource not found
        """
        import urllib.parse

        logger.info(f"Fetching custom resource: {resource_id}")

        vmcp_config = self.storage.load_vmcp_config(self.vmcp_id)
        if not vmcp_config:
            raise ValueError(f"vMCP config not found: {self.vmcp_id}")

        # Parse the custom resource URI
        # Format: custom:vmcp-name://encoded_filename
        if not resource_id.startswith('custom:'):
            raise ValueError(f"Invalid custom resource URI: {resource_id}")

        # Extract filename from URI
        uri_parts = resource_id.split('://')
        if len(uri_parts) != 2:
            raise ValueError(f"Invalid custom resource URI format: {resource_id}")

        encoded_filename = uri_parts[1]
        decoded_filename = urllib.parse.unquote(encoded_filename)

        logger.info(f"Looking for custom resource file: {decoded_filename}")

        # Search in custom resources
        for resource in vmcp_config.custom_resources:
            if resource.get('original_filename') == decoded_filename:
                logger.info(f"Found custom resource: {decoded_filename}")

                # Load content from blob storage
                from vmcp.backend.storage.models import Blob
                from vmcp.backend.storage.database import get_db

                blob_id = resource.get('blob_id')
                if not blob_id:
                    raise ValueError(f"No blob_id found for resource: {decoded_filename}")

                db = next(get_db())
                try:
                    blob = db.query(Blob).filter(Blob.blob_id == blob_id).first()
                    if not blob:
                        raise ValueError(f"Blob not found for resource: {decoded_filename}")

                    file_data = blob.file_data
                    content_type = resource.get('content_type', 'application/octet-stream')

                    # Handle Excel files - convert to CSV
                    if decoded_filename.endswith('.xlsx') or content_type == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
                        try:
                            csv_content, csv_mime = convert_openxml_to_csv(file_data, decoded_filename)
                            return ReadResourceResult(
                                contents=[
                                    TextResourceContents(
                                        uri=resource_id,
                                        mimeType=csv_mime,
                                        text=csv_content
                                    )
                                ]
                            )
                        except Exception as e:
                            logger.warning(f"Failed to convert Excel to CSV: {e}, returning as binary")

                    # Check if content is text or binary
                    if content_type.startswith('text/') or content_type in ['application/json', 'application/xml']:
                        # Text content
                        if isinstance(file_data, bytes):
                            text_content = file_data.decode('utf-8', errors='replace')
                        else:
                            text_content = str(file_data)

                        return ReadResourceResult(
                            contents=[
                                TextResourceContents(
                                    uri=resource_id,
                                    mimeType=content_type,
                                    text=text_content
                                )
                            ]
                        )
                    else:
                        # Binary content
                        import base64
                        if isinstance(file_data, bytes):
                            blob_data = base64.b64encode(file_data).decode('utf-8')
                        else:
                            blob_data = base64.b64encode(file_data.encode()).decode('utf-8')

                        return ReadResourceResult(
                            contents=[
                                BlobResourceContents(
                                    uri=resource_id,
                                    mimeType=content_type,
                                    blob=blob_data
                                )
                            ]
                        )
                finally:
                    db.close()

        raise ValueError(f"Custom resource not found: {decoded_filename}")

    # ============================================================================
    # Prompt Execution
    # ============================================================================

    @trace_method("ExecutionManager.get_prompt")
    async def get_prompt(
        self,
        prompt_id: str,
        arguments: Optional[Dict[str, Any]] = None
    ) -> GetPromptResult:
        """
        Get a prompt by routing to the appropriate server or custom handler.

        Args:
            prompt_id: Prompt name/ID
            arguments: Optional prompt arguments

        Returns:
            GetPromptResult with prompt messages

        Raises:
            ValueError: If prompt not found or vMCP config not found
        """
        logger.info(f"get_prompt called for '{prompt_id}'")

        if arguments is None:
            arguments = {}

        vmcp_config = self.storage.load_vmcp_config(self.vmcp_id)
        if not vmcp_config:
            raise ValueError(f"vMCP config not found: {self.vmcp_id}")

        # Check if it's a default system prompt (starts with # or vmcp_)
        if prompt_id.startswith('#') or prompt_id.startswith('vmcp_'):
            clean_prompt_id = prompt_id[1:] if prompt_id.startswith('#') else prompt_id
            return await handle_default_prompt(clean_prompt_id, self.user_id, self.vmcp_id, arguments)

        # Check if it's a custom prompt
        for custom_prompt in vmcp_config.custom_prompts:
            if custom_prompt.get('name') == prompt_id:
                logger.info(f"Found custom prompt: {prompt_id}")
                return await self.get_custom_prompt(prompt_id, arguments)

        # Check if it's a custom tool used as a prompt
        for custom_tool in vmcp_config.custom_tools:
            if custom_tool.get('name') == prompt_id:
                logger.info(f"Found custom tool as prompt: {prompt_id}")
                result = await self.manager.custom_tools.call_custom_tool(
                    prompt_id,
                    arguments,
                    tool_as_prompt=True
                )
                # Background logging
                if self.user_id:
                    asyncio.create_task(
                        self.log_vmcp_operation(
                            operation_type="prompt_get",
                            operation_id=prompt_id,
                            arguments=arguments,
                            result=result,
                            metadata={"server": "custom_tool", "tool": prompt_id, "server_id": "custom_tool"}
                        )
                    )
                return result

        # Parse prompt ID to extract server and original prompt name
        # Format: servername_promptname
        prompt_server_name = prompt_id.split('_')[0]
        prompt_original_name = "_".join(prompt_id.split('_')[1:])

        logger.info(f"Parsed prompt name - server: '{prompt_server_name}', original: '{prompt_original_name}'")

        vmcp_servers = vmcp_config.vmcp_config.get('selected_servers', [])

        # Find the matching server
        for server in vmcp_servers:
            server_name = server.get('name')
            server_id = server.get('server_id')
            server_name_clean = server_name.replace('_', '')

            if server_name_clean == prompt_server_name:
                logger.info(f"Found matching server '{server_name}' for prompt '{prompt_id}'")

                result = await self.mcp_client_manager.get_prompt(
                    server_id,
                    prompt_original_name,
                    arguments
                )

                logger.info(f"Prompt get successful from server '{server_name}'")

                # Background logging
                if self.user_id:
                    asyncio.create_task(
                        self.log_vmcp_operation(
                            operation_type="prompt_get",
                            operation_id=prompt_id,
                            arguments=arguments,
                            result=result,
                            metadata={"server": server_name, "prompt": prompt_original_name, "server_id": server_id}
                        )
                    )

                return result

        # If we get here, the prompt was not found
        logger.error(f"Prompt '{prompt_id}' not found in vMCP '{self.vmcp_id}'")
        raise ValueError(f"Prompt {prompt_id} not found in vMCP {self.vmcp_id}")

    @trace_method("ExecutionManager.get_system_prompt")
    async def get_system_prompt(self, arguments: Optional[Dict[str, Any]] = None) -> GetPromptResult:
        """
        Get the system prompt with variable substitution.

        Args:
            arguments: Optional arguments for variable substitution

        Returns:
            GetPromptResult with system prompt

        Raises:
            ValueError: If system prompt not found
        """
        vmcp_config = self.storage.load_vmcp_config(self.vmcp_id)
        if not vmcp_config:
            raise ValueError(f"vMCP config not found: {self.vmcp_id}")

        system_prompt = vmcp_config.system_prompt
        if not system_prompt:
            raise ValueError(f"System prompt not found in vMCP {self.vmcp_id}")

        # Get the prompt text
        prompt_text = system_prompt.get('text', '')

        # Load environment variables
        environment_variables = self.storage.load_vmcp_environment(self.vmcp_id)

        # Save environment variables from arguments if provided
        if arguments:
            for env_var in environment_variables:
                if env_var in arguments:
                    environment_variables[env_var] = arguments[env_var]
            self.storage.save_vmcp_environment(self.vmcp_id, environment_variables)

        # Parse and substitute using the parsing engine
        prompt_text, _resource_content = await self.manager.parsing.parse_vmcp_text(
            prompt_text,
            system_prompt,
            arguments or {},
            environment_variables,
            is_prompt=True
        )

        # Create the response
        text_content = TextContent(
            type="text",
            text=prompt_text,
            annotations=None,
            meta=None
        )

        prompt_message = PromptMessage(
            role="user",
            content=text_content
        )

        return GetPromptResult(
            description=system_prompt.get('description'),
            messages=[prompt_message]
        )

    @trace_method("ExecutionManager.get_custom_prompt")
    async def get_custom_prompt(
        self,
        prompt_id: str,
        arguments: Optional[Dict[str, Any]] = None
    ) -> GetPromptResult:
        """
        Get a custom prompt with variable substitution.

        Args:
            prompt_id: Custom prompt name
            arguments: Optional arguments for variable substitution

        Returns:
            GetPromptResult with custom prompt

        Raises:
            ValueError: If custom prompt not found
        """
        vmcp_config = self.storage.load_vmcp_config(self.vmcp_id)
        if not vmcp_config:
            raise ValueError(f"vMCP config not found: {self.vmcp_id}")

        # Find the custom prompt
        custom_prompt = None
        for prompt in vmcp_config.custom_prompts:
            if prompt.get('name') == prompt_id:
                custom_prompt = prompt
                break

        if not custom_prompt:
            raise ValueError(f"Custom prompt {prompt_id} not found in vMCP {self.vmcp_id}")

        # Get the prompt text
        prompt_text = custom_prompt.get('text', '')
        if arguments is None:
            arguments = {}

        # Load environment variables
        environment_variables = self.storage.load_vmcp_environment(self.vmcp_id)
        if not environment_variables:
            environment_variables = {}

        # Parse and substitute using the parsing engine
        prompt_text, _resource_content = await self.manager.parsing.parse_vmcp_text(
            prompt_text,
            custom_prompt,
            arguments,
            environment_variables,
            is_prompt=True
        )

        # Create the response
        text_content = TextContent(
            type="text",
            text=prompt_text,
            annotations=None,
            meta=None
        )

        prompt_message = PromptMessage(
            role="user",
            content=text_content
        )

        return GetPromptResult(
            description=custom_prompt.get('description'),
            messages=[prompt_message]
        )

    @trace_method("ExecutionManager.get_resource_template")
    async def get_resource_template(self, request: VMCPResourceRequest) -> Resource:
        """
        Get a resource template with parameter substitution.

        Args:
            request: Resource template request with template name and parameters

        Returns:
            Resource object with processed URI

        Raises:
            ValueError: If resource template not found
        """
        if not self.vmcp_id:
            raise ValueError("No vMCP ID specified")

        vmcp_config = self.storage.load_vmcp_config(self.vmcp_id)
        if not vmcp_config:
            raise ValueError(f"vMCP config not found: {self.vmcp_id}")

        template_name = request.uri  # Using uri field for template name
        parameters = request.arguments or {}

        vmcp_servers = vmcp_config.vmcp_config.get('selected_servers', [])
        vmcp_selected_resource_templates = vmcp_config.vmcp_config.get('selected_resource_templates', {})

        # Try to find the resource template in the servers
        for server in vmcp_servers:
            if template_name in vmcp_selected_resource_templates.get(server.get('name'), []):
                try:
                    # Get the resource template details
                    template_detail = await self.mcp_client_manager.get_resource_template_detail(
                        server.get('name'),
                        template_name,
                        connect_if_needed=True
                    )
                    if template_detail:
                        # Process the URI template with parameters
                        uri_template = template_detail.uriTemplate
                        processed_uri = uri_template
                        for param_name, param_value in parameters.items():
                            placeholder = f"{{{param_name}}}"
                            processed_uri = processed_uri.replace(placeholder, str(param_value))

                        # Create a resource from the template
                        return Resource(
                            uri=processed_uri,
                            name=template_name,
                            description=template_detail.description,
                            mimeType=template_detail.mimeType,
                            annotations=template_detail.annotations
                        )
                except Exception as e:
                    logger.error(f"Failed to get resource template {template_name} from server {server.get('name')}: {e}")
                    continue

        # Check custom resource templates
        for template in vmcp_config.custom_resource_templates:
            if template.get('name') == template_name:
                # Process custom resource template
                uri_template = template.get('uri_template', '')
                processed_uri = uri_template
                for param_name, param_value in parameters.items():
                    placeholder = f"{{{param_name}}}"
                    processed_uri = processed_uri.replace(placeholder, str(param_value))

                # Create a resource from the custom template
                return Resource(
                    uri=processed_uri,
                    name=template_name,
                    description=template.get('description', f"Custom resource template: {template_name}"),
                    mimeType=template.get('mime_type'),
                    annotations=template.get('annotations')
                )

        raise ValueError(f"Resource template {template_name} not found in vMCP {self.vmcp_id}")

    # ============================================================================
    # Background Operations
    # ============================================================================

    async def log_vmcp_operation(
        self,
        operation_type: str,
        operation_id: str,
        arguments: Optional[Dict[str, Any]],
        result: Optional[Any],
        metadata: Optional[Dict[str, Any]]
    ) -> None:
        """
        Background task to log vMCP operations.

        Args:
            operation_type: Type of operation (tool_call, resource_read, prompt_get, etc.)
            operation_id: Operation identifier
            arguments: Operation arguments
            result: Operation result
            metadata: Additional metadata
        """
        try:
            vmcp_id = self.vmcp_id
            vmcp_config = self.manager.core.load_vmcp_config(vmcp_id)

            # Log to current span if available
            log_to_span(
                operation_type=operation_type,
                operation_id=operation_id,
                arguments=arguments,
                result={"type": type(result).__name__} if result else None,
                metadata=metadata
            )

            # File logging as fallback/backup
            total_tools = vmcp_config.total_tools if vmcp_config else 0
            total_resources = vmcp_config.total_resources if vmcp_config else 0
            total_resource_templates = vmcp_config.total_resource_templates if vmcp_config else 0
            total_prompts = vmcp_config.total_prompts if vmcp_config else 0

            # Log the operation
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "method": operation_type,
                "agent_name": self.logging_config.get("agent_name", "unknown"),
                "agent_id": self.logging_config.get("agent_id", "unknown"),
                "user_id": self.user_id,
                "client_id": self.logging_config.get("client_id", "unknown"),
                "operation_id": operation_id,
                "mcp_server": metadata.get("server") if metadata else None,
                "mcp_method": operation_type,
                "original_name": metadata.get("tool") if operation_type == "tool_call" else
                               metadata.get("prompt") if operation_type == "prompt_get" else
                               metadata.get("resource"),
                "arguments": arguments,
                "result": result.to_dict() if hasattr(result, 'to_dict') else str(result),
                "vmcp_id": vmcp_id,
                "vmcp_name": vmcp_config.name if vmcp_config else None,
                "total_tools": total_tools,
                "total_resources": total_resources,
                "total_resource_templates": total_resource_templates,
                "total_prompts": total_prompts
            }

            # Save to log file
            self.storage.save_user_vmcp_logs(log_entry)
            logger.info(f"Successfully logged {operation_type} for user {self.user_id}")
        except Exception as e:
            # Silently fail for logging - don't affect the main request
            logger.error(f"Could not log {operation_type} for user {self.user_id}: {e}")

    def update_vmcp_server(self, vmcp_id: str, server_config: MCPServerConfig) -> bool:
        """
        Update the server configuration for a vMCP.

        Args:
            vmcp_id: vMCP ID
            server_config: Updated server configuration

        Returns:
            True if successful, False otherwise
        """
        vmcp_config = self.manager.core.load_vmcp_config(vmcp_id)
        server_id = server_config.server_id

        if vmcp_config:
            selected_servers = vmcp_config.vmcp_config.get('selected_servers', [])
            if selected_servers:
                for idx, server in enumerate(selected_servers):
                    if server.get('server_id') == server_id:
                        server_config_dict = server_config.to_dict()
                        vmcp_config.vmcp_config['selected_servers'][idx] = server_config_dict

                        # Update selected tools/resources/prompts if not already set
                        selected_tools = vmcp_config.vmcp_config.get('selected_tools', {})
                        selected_resources = vmcp_config.vmcp_config.get('selected_resources', {})
                        selected_prompts = vmcp_config.vmcp_config.get('selected_prompts', {})

                        if not selected_tools.get(server_id, []):
                            selected_tools[server_id] = server_config_dict.get('tools', [])
                            vmcp_config.vmcp_config['selected_tools'] = selected_tools
                            vmcp_config.total_tools = sum(len(x) for x in selected_tools.values())

                        if not selected_resources.get(server_id, []):
                            selected_resources[server_id] = server_config_dict.get('resources', []).copy()
                            vmcp_config.vmcp_config['selected_resources'] = selected_resources.copy()
                            vmcp_config.total_resources = sum(len(x) for x in selected_resources.values())

                        if not selected_prompts.get(server_id, []):
                            selected_prompts[server_id] = server_config_dict.get('prompts', []).copy()
                            vmcp_config.vmcp_config['selected_prompts'] = selected_prompts
                            vmcp_config.total_prompts = sum(len(x) for x in selected_prompts.values())

                        self.manager.core.update_vmcp_config(vmcp_id, vmcp_config=vmcp_config.vmcp_config)
                        return True

        return False
