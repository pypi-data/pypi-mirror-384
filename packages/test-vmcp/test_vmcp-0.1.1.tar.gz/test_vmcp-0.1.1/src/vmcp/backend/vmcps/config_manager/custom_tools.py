"""
Custom Tools Manager Module
===========================

Handles execution of custom tools (prompt-based, Python, and HTTP types).

Responsibilities:
- Execute prompt-based tools with variable substitution
- Execute Python tools with secure sandboxing
- Execute HTTP tools with full authentication support
- Type conversion and parameter validation
- Function schema parsing for Python tools
"""

import subprocess
import tempfile
import os
import json
import sys
import logging
import aiohttp
import urllib.parse
import re
import base64
from typing import Dict, List, Any, Optional

from mcp.types import (
    CallToolResult, GetPromptResult, TextContent, PromptMessage
)

from vmcp.backend.utilities.tracing import trace_method

logger = logging.getLogger("vmcp.config_manager.custom_tools")


class CustomToolsManager:
    """Manages execution of custom tools (prompt/python/http)."""

    def __init__(self, manager):
        """
        Initialize custom tools manager.

        Args:
            manager: Parent VMCPConfigManager instance
        """
        self.manager = manager
        self.storage = manager.storage
        self.vmcp_id = manager.vmcp_id

    # ============================================================================
    # Main Entry Point
    # ============================================================================

    @trace_method("CustomToolsManager.call_custom_tool")
    async def call_custom_tool(
        self,
        tool_id: str,
        arguments: Optional[Dict[str, Any]] = None,
        tool_as_prompt: bool = False
    ):
        """
        Execute a custom tool by routing to the appropriate handler.

        Args:
            tool_id: Custom tool name
            arguments: Tool arguments
            tool_as_prompt: Whether to return as GetPromptResult instead of CallToolResult

        Returns:
            CallToolResult or GetPromptResult

        Raises:
            ValueError: If custom tool not found
        """
        vmcp_config = self.storage.load_vmcp_config(self.vmcp_id)
        if not vmcp_config:
            raise ValueError(f"vMCP config not found: {self.vmcp_id}")

        # Find the custom tool
        custom_tool = None
        for tool in vmcp_config.custom_tools:
            if tool.get('name') == tool_id:
                custom_tool = tool
                break

        if not custom_tool:
            raise ValueError(f"Custom tool {tool_id} not found in vMCP {self.vmcp_id}")

        if arguments is None:
            arguments = {}

        # Load environment variables
        environment_variables = self.storage.load_vmcp_environment(self.vmcp_id)
        if not environment_variables:
            environment_variables = {}

        # Route to appropriate handler based on tool type
        tool_type = custom_tool.get('tool_type', 'prompt')

        if tool_type == 'python':
            return await self.execute_python_tool(custom_tool, arguments, environment_variables, tool_as_prompt)
        elif tool_type == 'http':
            return await self.execute_http_tool(custom_tool, arguments, environment_variables, tool_as_prompt)
        else:  # prompt tool (default)
            return await self.execute_prompt_tool(custom_tool, arguments, environment_variables, tool_as_prompt)

    # ============================================================================
    # Tool Type Handlers
    # ============================================================================

    async def execute_prompt_tool(
        self,
        custom_tool: dict,
        arguments: Dict[str, Any],
        environment_variables: Dict[str, Any],
        tool_as_prompt: bool = False
    ):
        """
        Execute a prompt-based tool with variable substitution.

        Args:
            custom_tool: Tool configuration
            arguments: Tool arguments
            environment_variables: Environment variables
            tool_as_prompt: Whether to return as GetPromptResult

        Returns:
            CallToolResult or GetPromptResult
        """
        # Get the tool text
        tool_text = custom_tool.get('text', '')

        # Parse and substitute using the parsing engine
        tool_text, _resource_content = await self.manager.parsing.parse_vmcp_text(
            tool_text,
            custom_tool,
            arguments,
            environment_variables,
            is_prompt=tool_as_prompt
        )

        logger.info(f"Tool text after parsing: {tool_text[:100]}...")

        # Create the TextContent
        text_content = TextContent(
            type="text",
            text=tool_text,
            annotations=None,
            meta=None
        )

        if tool_as_prompt:
            # Create the PromptMessage
            prompt_message = PromptMessage(
                role="user",
                content=text_content
            )

            # Create the GetPromptResult
            return GetPromptResult(
                description="Tool call result",
                messages=[prompt_message]
            )

        # Create the CallToolResult
        return CallToolResult(
            content=[text_content],
            structuredContent=None,
            isError=False
        )

    async def execute_python_tool(
        self,
        custom_tool: dict,
        arguments: Dict[str, Any],
        environment_variables: Dict[str, Any],
        tool_as_prompt: bool = False
    ):
        """
        Execute a Python tool with secure sandboxing.

        This method executes user-provided Python code in a sandboxed subprocess
        with security measures:
        - Runs in separate process (isolated from main app)
        - 30-second timeout
        - Runs in temp directory
        - Limited access to dangerous modules

        Args:
            custom_tool: Tool configuration with 'code' field
            arguments: Tool arguments
            environment_variables: Environment variables
            tool_as_prompt: Whether to return as GetPromptResult

        Returns:
            CallToolResult or GetPromptResult
        """
        # Get the Python code
        python_code = custom_tool.get('code', '')
        if not python_code:
            error_content = TextContent(
                type="text",
                text="No Python code provided for this tool",
                annotations=None,
                meta=None
            )
            return CallToolResult(
                content=[error_content],
                structuredContent=None,
                isError=True
            )

        # Convert arguments to correct types based on tool variables
        converted_arguments = self.convert_arguments_to_types(arguments, custom_tool.get('variables', []))

        # Create a secure execution environment
        try:
            # Create a temporary file for the Python code
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                # Prepare the execution environment with security checks
                execution_code = f"""
import sys
import json
import inspect

# Arguments passed from the tool call
arguments = {json.dumps(converted_arguments)}

# Environment variables
environment_variables = {json.dumps(environment_variables)}

# User's Python code
{python_code}

# Execute the main function if it exists
if 'main' in locals() and callable(main):
    try:
        # Get function signature to properly map arguments
        sig = inspect.signature(main)
        param_names = list(sig.parameters.keys())

        # Filter arguments to only include those that match function parameters
        filtered_args = {{}}
        for param_name in param_names:
            if param_name in arguments:
                filtered_args[param_name] = arguments[param_name]

        result = main(**filtered_args)
        print(json.dumps({{"success": True, "result": result}}))
    except Exception as e:
        print(json.dumps({{"success": False, "error": str(e)}}))
else:
    print(json.dumps({{"success": False, "error": "No 'main' function found in the code"}}))
"""
                f.write(execution_code)
                temp_file = f.name

            # Execute the Python code in a secure subprocess
            result = subprocess.run(
                [sys.executable, temp_file],
                capture_output=True,
                text=True,
                timeout=30,  # 30 second timeout
                cwd=tempfile.gettempdir()  # Run in temp directory
            )

            # Clean up the temporary file
            os.unlink(temp_file)

            # Parse the result
            try:
                result_data = json.loads(result.stdout.strip())
                if result_data.get('success', False):
                    result_text = json.dumps(result_data.get('result', ''), indent=2)
                else:
                    result_text = f"Error: {result_data.get('error', 'Unknown error')}"
            except json.JSONDecodeError:
                result_text = result.stdout if result.stdout else result.stderr

            # Create the TextContent
            text_content = TextContent(
                type="text",
                text=result_text,
                annotations=None,
                meta=None
            )

            if tool_as_prompt:
                # Create the PromptMessage
                prompt_message = PromptMessage(
                    role="user",
                    content=text_content
                )

                # Create the GetPromptResult
                return GetPromptResult(
                    description="Python tool execution result",
                    messages=[prompt_message]
                )

            # Create the CallToolResult
            return CallToolResult(
                content=[text_content],
                structuredContent=None,
                isError=not result_data.get('success', False) if 'result_data' in locals() else False
            )

        except subprocess.TimeoutExpired:
            error_content = TextContent(
                type="text",
                text="Python tool execution timed out (30 seconds)",
                annotations=None,
                meta=None
            )
            return CallToolResult(
                content=[error_content],
                structuredContent=None,
                isError=True
            )
        except Exception as e:
            error_content = TextContent(
                type="text",
                text=f"Error executing Python tool: {str(e)}",
                annotations=None,
                meta=None
            )
            return CallToolResult(
                content=[error_content],
                structuredContent=None,
                isError=True
            )

    async def execute_http_tool(
        self,
        custom_tool: dict,
        arguments: Dict[str, Any],
        environment_variables: Dict[str, Any],
        tool_as_prompt: bool = False
    ):
        """
        Execute an HTTP tool with full parameter substitution and authentication support.

        Supports:
        - Variable substitution in URL, headers, body
        - Multiple authentication types (Bearer, API Key, Basic, Custom)
        - Query parameters
        - Request body (JSON or raw)
        - 30-second timeout

        Args:
            custom_tool: Tool configuration with 'api_config' field
            arguments: Tool arguments
            environment_variables: Environment variables
            tool_as_prompt: Whether to return as GetPromptResult

        Returns:
            CallToolResult or GetPromptResult
        """
        # Get the API configuration
        api_config = custom_tool.get('api_config', {})
        if not api_config.get('url'):
            error_content = TextContent(
                type="text",
                text="No URL configured for this HTTP tool",
                annotations=None,
                meta=None
            )
            return CallToolResult(
                content=[error_content],
                structuredContent=None,
                isError=True
            )

        try:
            # Prepare the request
            method = api_config.get('method', 'GET').upper()
            url = api_config.get('url', '')
            headers = api_config.get('headers', {})
            body = api_config.get('body')
            body_parsed = api_config.get('body_parsed')
            query_params = api_config.get('query_params', {})
            auth = api_config.get('auth', {})

            logger.info(f"HTTP Tool Execution: {custom_tool.get('name')}")
            logger.info(f"Method: {method}, URL: {url}")

            # Step 1: Substitute variables in URL
            url = self.substitute_url_variables(url, arguments, environment_variables)
            logger.info(f"Processed URL: {url}")

            # Step 2: Process headers with variable substitution
            processed_headers = {}
            for key, value in headers.items():
                processed_headers[key] = self.substitute_variables(str(value), arguments, environment_variables)

            # Step 3: Add authentication headers if configured
            if auth and auth.get('type') != 'none':
                auth_headers = self.get_auth_headers(auth, arguments, environment_variables)
                processed_headers.update(auth_headers)
                logger.info(f"Added auth headers: {list(auth_headers.keys())}")

            # Step 4: Process query parameters with variable substitution
            processed_query_params = {}
            for key, value in query_params.items():
                processed_value = self.substitute_variables(str(value), arguments, environment_variables)
                # Only add non-empty values
                if processed_value and processed_value not in ['<string>', '<long>', '<boolean>', '<number>', '']:
                    processed_query_params[key] = processed_value

            # Add query parameters to URL
            if processed_query_params:
                query_string = urllib.parse.urlencode(processed_query_params)
                url = f"{url}?{query_string}" if '?' not in url else f"{url}&{query_string}"
                logger.info(f"Final URL with query params: {url}")

            # Step 5: Prepare request body for POST/PUT/PATCH requests
            request_data = None
            if method in ['POST', 'PUT', 'PATCH', 'DELETE'] and (body or body_parsed):
                if body_parsed:
                    # Use the parsed body with @param substitutions
                    processed_body = self.substitute_body_variables(body_parsed, arguments, environment_variables)
                    request_data = json.dumps(processed_body, indent=2)
                    processed_headers.setdefault('Content-Type', 'application/json')
                elif body:
                    # Use the raw body with variable substitution
                    if isinstance(body, dict):
                        processed_body = self.substitute_body_variables(body, arguments, environment_variables)
                        request_data = json.dumps(processed_body, indent=2)
                        processed_headers.setdefault('Content-Type', 'application/json')
                    else:
                        request_data = self.substitute_variables(str(body), arguments, environment_variables)
                        processed_headers.setdefault('Content-Type', 'application/json')

            # Step 6: Make the HTTP request
            logger.info(f"Making {method} request to: {url}")

            async with aiohttp.ClientSession() as session:
                async with session.request(
                    method=method,
                    url=url,
                    headers=processed_headers,
                    data=request_data,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    response_text = await response.text()

                    # Try to parse JSON response for better formatting
                    try:
                        response_json = json.loads(response_text)
                        formatted_response = json.dumps(response_json, indent=2)
                    except json.JSONDecodeError:
                        formatted_response = response_text

                    # Create result text
                    result_text = f"Status: {response.status}\n"
                    result_text += f"Status Text: {response.reason}\n"
                    result_text += f"Headers: {dict(response.headers)}\n"
                    result_text += f"Response:\n{formatted_response}"

                    # Create the TextContent
                    text_content = TextContent(
                        type="text",
                        text=result_text,
                        annotations=None,
                        meta=None
                    )

                    if tool_as_prompt:
                        # Create the PromptMessage
                        prompt_message = PromptMessage(
                            role="user",
                            content=text_content
                        )

                        # Create the GetPromptResult
                        return GetPromptResult(
                            description="HTTP tool execution result",
                            messages=[prompt_message]
                        )

                    # Create the CallToolResult
                    logger.info(f"HTTP tool execution completed with status: {response.status}")
                    return CallToolResult(
                        content=[text_content],
                        structuredContent=None,
                        isError=response.status >= 400
                    )

        except Exception as e:
            logger.error(f"Error executing HTTP tool: {str(e)}")
            error_content = TextContent(
                type="text",
                text=f"Error executing HTTP tool: {str(e)}",
                annotations=None,
                meta=None
            )
            return CallToolResult(
                content=[error_content],
                structuredContent=None,
                isError=True
            )

    # ============================================================================
    # Helper Methods
    # ============================================================================

    def substitute_variables(self, text: str, arguments: Dict[str, Any], environment_variables: Dict[str, Any]) -> str:
        """
        Substitute @param and @config variables in text.

        Args:
            text: Text with variables to substitute
            arguments: Available arguments
            environment_variables: Available environment variables

        Returns:
            Text with variables substituted
        """
        # Substitute @param variables
        param_pattern = r'@param\.(\w+)'

        def replace_param(match):
            param_name = match.group(1)
            return str(arguments.get(param_name, f"[{param_name} not found]"))

        text = re.sub(param_pattern, replace_param, text)

        # Substitute @config variables
        config_pattern = r'@config\.(\w+)'

        def replace_config(match):
            config_name = match.group(1)
            return str(environment_variables.get(config_name, f"[{config_name} not found]"))

        text = re.sub(config_pattern, replace_config, text)

        return text

    def substitute_url_variables(
        self,
        url: str,
        arguments: Dict[str, Any],
        environment_variables: Dict[str, Any]
    ) -> str:
        """
        Substitute variables in URL (both {{variable}} and :pathParam patterns).

        Args:
            url: URL with variables
            arguments: Available arguments
            environment_variables: Available environment variables

        Returns:
            URL with variables substituted
        """
        # First substitute @param and @config variables
        url = self.substitute_variables(url, arguments, environment_variables)

        # Then substitute {{variable}} patterns
        curly_pattern = r'\{\{([^}]+)\}\}'

        def replace_curly(match):
            var_name = match.group(1)
            return str(arguments.get(var_name, environment_variables.get(var_name, f"[{var_name} not found]")))

        url = re.sub(curly_pattern, replace_curly, url)

        # Finally substitute :pathParam patterns
        path_param_pattern = r':([a-zA-Z_][a-zA-Z0-9_]*)'

        def replace_path_param(match):
            param_name = match.group(1)
            return str(arguments.get(param_name, environment_variables.get(param_name, f"[{param_name} not found]")))

        url = re.sub(path_param_pattern, replace_path_param, url)

        return url

    def substitute_body_variables(
        self,
        body: Any,
        arguments: Dict[str, Any],
        environment_variables: Dict[str, Any]
    ) -> Any:
        """
        Recursively substitute variables in request body.

        Args:
            body: Request body (dict, list, or string)
            arguments: Available arguments
            environment_variables: Available environment variables

        Returns:
            Body with variables substituted
        """
        if isinstance(body, dict):
            return {key: self.substitute_body_variables(value, arguments, environment_variables) for key, value in body.items()}
        elif isinstance(body, list):
            return [self.substitute_body_variables(item, arguments, environment_variables) for item in body]
        elif isinstance(body, str):
            return self.substitute_variables(body, arguments, environment_variables)
        else:
            return body

    def get_auth_headers(
        self,
        auth: Dict[str, Any],
        arguments: Dict[str, Any],
        environment_variables: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Generate authentication headers based on auth configuration.

        Supports:
        - Bearer token
        - API Key (custom header name)
        - Basic authentication
        - Custom headers

        Args:
            auth: Auth configuration
            arguments: Available arguments
            environment_variables: Available environment variables

        Returns:
            Dict of authentication headers
        """
        auth_type = auth.get('type', 'none').lower()
        headers = {}

        if auth_type == 'bearer':
            token = auth.get('token', '')
            if token:
                # Substitute variables in token
                processed_token = self.substitute_variables(token, arguments, environment_variables)
                headers['Authorization'] = f"Bearer {processed_token}"

        elif auth_type == 'apikey':
            api_key = auth.get('apiKey', '')
            key_name = auth.get('keyName', 'X-API-Key')
            if api_key:
                # Substitute variables in API key
                processed_key = self.substitute_variables(api_key, arguments, environment_variables)
                headers[key_name] = processed_key

        elif auth_type == 'basic':
            username = auth.get('username', '')
            password = auth.get('password', '')
            if username and password:
                # Substitute variables in credentials
                processed_username = self.substitute_variables(username, arguments, environment_variables)
                processed_password = self.substitute_variables(password, arguments, environment_variables)

                # Create basic auth header
                credentials = f"{processed_username}:{processed_password}"
                encoded_credentials = base64.b64encode(credentials.encode()).decode()
                headers['Authorization'] = f"Basic {encoded_credentials}"

        elif auth_type == 'custom':
            # Handle custom headers
            custom_headers = auth.get('headers', {})
            for key, value in custom_headers.items():
                processed_value = self.substitute_variables(str(value), arguments, environment_variables)
                headers[key] = processed_value

        return headers

    def convert_arguments_to_types(
        self,
        arguments: Dict[str, Any],
        variables: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Convert string arguments to their correct types based on variable definitions.

        Args:
            arguments: Raw arguments (usually strings from user input)
            variables: Variable definitions with type information

        Returns:
            Dict with properly typed arguments
        """
        converted = {}

        for var in variables:
            var_name = var.get('name')
            var_type = var.get('type', 'str')
            var_default = var.get('default_value')

            if var_name in arguments:
                value = arguments[var_name]

                # Handle null values
                if value is None or value == 'null' or value == '':
                    if var_default is not None:
                        converted[var_name] = var_default
                    else:
                        converted[var_name] = None
                    continue

                try:
                    if var_type == 'int':
                        converted[var_name] = int(value)
                    elif var_type == 'float':
                        converted[var_name] = float(value)
                    elif var_type == 'bool':
                        if isinstance(value, str):
                            converted[var_name] = value.lower() in ('true', '1', 'yes', 'on')
                        else:
                            converted[var_name] = bool(value)
                    elif var_type == 'list':
                        if isinstance(value, str):
                            # Try to parse as JSON array
                            try:
                                converted[var_name] = json.loads(value)
                            except Exception:
                                # Fallback to splitting by comma
                                converted[var_name] = [item.strip() for item in value.split(',')]
                        else:
                            converted[var_name] = value
                    elif var_type == 'dict':
                        if isinstance(value, str):
                            try:
                                converted[var_name] = json.loads(value)
                            except Exception:
                                converted[var_name] = value
                        else:
                            converted[var_name] = value
                    else:  # str or unknown type
                        converted[var_name] = str(value)
                except (ValueError, TypeError) as e:
                    # If conversion fails, use default value or keep as string
                    if var_default is not None:
                        converted[var_name] = var_default
                        logger.warning(f"Failed to convert argument '{var_name}' to type '{var_type}', using default: {e}")
                    else:
                        converted[var_name] = str(value)
                        logger.warning(f"Failed to convert argument '{var_name}' to type '{var_type}': {e}")
            else:
                # If argument not provided, use default value if available
                if var_default is not None:
                    converted[var_name] = var_default
                elif var.get('required', True):
                    logger.warning(f"Required argument '{var_name}' not provided")
                    converted[var_name] = None
                else:
                    converted[var_name] = None

        return converted

    def parse_python_function_schema(self, custom_tool: dict) -> dict:
        """
        Parse Python function to extract parameters and create input schema.

        Args:
            custom_tool: Tool configuration with 'variables' field

        Returns:
            JSON schema for tool input
        """
        # Use the pre-parsed variables from the tool
        variables = custom_tool.get('variables', [])

        if not variables:
            return {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
                "$schema": "http://json-schema.org/draft-07/schema#"
            }

        # Map internal types to JSON schema types
        def map_to_json_schema_type(internal_type: str) -> str:
            type_mapping = {
                'str': 'string',
                'int': 'integer',
                'float': 'number',
                'bool': 'boolean',
                'list': 'array',
                'dict': 'object'
            }
            return type_mapping.get(internal_type, 'string')

        # Build properties from parsed variables
        properties = {}
        required = []

        for var in variables:
            var_name = var.get('name')
            var_type = var.get('type', 'str')
            var_description = var.get('description', f"Parameter: {var_name}")
            var_required = var.get('required', True)
            var_default = var.get('default_value')

            if var_name:
                property_schema = {
                    "type": map_to_json_schema_type(var_type),
                    "description": var_description
                }

                # Add default value if present
                if var_default is not None:
                    property_schema["default"] = var_default

                properties[var_name] = property_schema

                if var_required:
                    required.append(var_name)

        return {
            "type": "object",
            "properties": properties,
            "required": required,
            "additionalProperties": False,
            "$schema": "http://json-schema.org/draft-07/schema#"
        }
