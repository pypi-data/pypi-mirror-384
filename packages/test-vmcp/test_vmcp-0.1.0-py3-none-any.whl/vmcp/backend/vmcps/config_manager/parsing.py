"""
Parsing Engine Module
=====================

The heart of the vMCP system - handles all variable substitution and template processing.

Responsibilities:
- @param.variable substitution
- @config.variable substitution
- @resource.server.resource_name fetching and substitution
- @tool.server.tool_name() execution and substitution
- @prompt.server.prompt_name() execution and substitution
- Jinja2 template detection and rendering
- Parameter parsing (AST-based with regex fallback)
"""

import ast
import json
import logging
import re
from typing import Dict, List, Any, Optional, Tuple

from vmcp.backend.utilities.tracing import trace_method
from vmcp.backend.vmcps.models import VMCPToolCallRequest, VMCPResourceRequest

logger = logging.getLogger("vmcp.config_manager.parsing")


class ParsingEngine:
    """
    Manages variable substitution and template processing for vMCP.

    This is the core engine that enables dynamic content generation by:
    - Substituting variables from arguments and environment
    - Fetching and embedding resources
    - Executing tools and prompts inline
    - Processing Jinja2 templates
    """

    def __init__(self, manager):
        """
        Initialize parsing engine.

        Args:
            manager: Parent VMCPConfigManager instance
        """
        self.manager = manager
        self.jinja_env = manager.jinja_env

    # ============================================================================
    # Main Parsing Method - The Core Engine
    # ============================================================================

    @trace_method("ParsingEngine.parse_vmcp_text")
    async def parse_vmcp_text(
        self,
        text: str,
        config_item: dict,
        arguments: Dict[str, Any],
        environment_variables: Dict[str, Any],
        is_prompt: bool = False
    ) -> Tuple[str, Optional[Any]]:
        """
        Parse vMCP text with full variable substitution.

        This is the core parsing engine that processes text with:
        1. @config.VAR_NAME - Environment variable substitution
        2. @param.variable_name - Argument variable substitution
        3. @resource.server.resource_name - Resource fetching and substitution
        4. @tool.server.tool_name(params) - Tool execution and substitution
        5. @prompt.server.prompt_name(params) - Prompt execution and substitution
        6. Jinja2 template detection and rendering

        Args:
            text: Text to parse
            config_item: Configuration item (tool/prompt/resource config)
            arguments: Available arguments
            environment_variables: Available environment variables
            is_prompt: Whether this is being parsed for a prompt (affects resource handling)

        Returns:
            Tuple of (parsed_text, resource_content)
        """
        resource_content = None

        logger.info(f"Parsing VMCP text (length: {len(text)})")
        logger.debug(f"Environment variables: {list(environment_variables.keys())}")
        logger.debug(f"Arguments: {list(arguments.keys())}")
        logger.debug(f"Is prompt: {is_prompt}")

        processed_text = text

        # Step 1: Substitute @config.VAR_NAME (environment variables)
        env_pattern = r'@config\.(\w+)'

        def replace_env(match):
            env_name = match.group(1)
            env_value = environment_variables.get(
                env_name,
                arguments.get(env_name, f"[{env_name} not found]")
            )
            logger.debug(f"Substituting @config.{env_name} with: {env_value}")
            return str(env_value)

        processed_text = re.sub(env_pattern, replace_env, processed_text)

        # Step 2: Substitute @param.variable_name (arguments)
        var_pattern = r'@param\.(\w+)'

        def replace_var(match):
            var_name = match.group(1)
            var_value = arguments.get(var_name, f"[{var_name} not found]")
            logger.debug(f"Substituting @param.{var_name} with: {var_value}")
            return str(var_value)

        processed_text = re.sub(var_pattern, replace_var, processed_text)

        # Step 3: Handle @resource.server.resource_name references
        resource_pattern = r'@resource\.(\w+)\.([\w\/\:\.\-]+)'
        resources_to_fetch = []

        def collect_resource(match):
            server_name = match.group(1)
            resource_name = match.group(2)
            resources_to_fetch.append((server_name, resource_name, match.group(0)))
            return match.group(0)  # Keep original for now, will replace after fetching

        processed_text = re.sub(resource_pattern, collect_resource, processed_text)

        # Fetch resources and substitute
        for server_name, resource_name, original_match in resources_to_fetch:
            try:
                logger.info(f"Fetching resource: {server_name}.{resource_name}")

                # Create the resource name with server prefix
                if server_name == "vmcp":
                    prefixed_resource_name = f"{resource_name}"
                else:
                    prefixed_resource_name = f"{server_name.replace('_', '')}:{resource_name}"

                # Fetch the resource
                resource_result = await self.manager.execution.get_resource(
                    prefixed_resource_name,
                    connect_if_needed=True
                )

                # Convert result to string
                if hasattr(resource_result, 'contents') and resource_result.contents:
                    if len(resource_result.contents) > 1:
                        resource_str = json.dumps(resource_result.contents, indent=2, default=str)
                    else:
                        content = resource_result.contents[0]
                        resource_str = content.text if hasattr(content, 'text') else str(content)
                else:
                    resource_str = str(resource_result)

                # Substitute in text
                processed_text = processed_text.replace(original_match, resource_str)

                logger.info(f"Successfully fetched and substituted resource {server_name}.{resource_name}")

            except Exception as e:
                logger.error(f"Failed to fetch resource {server_name}.{resource_name}: {e}")
                processed_text = processed_text.replace(
                    original_match,
                    f"[Resource fetch failed: {str(e)}]"
                )

        # Step 4: Handle @tool.server.tool_name(params) calls
        tool_pattern = r'@tool\.(\w+)\.(\w+)\(([^)]*)\)'

        async def replace_tool(match):
            server_name = match.group(1)
            tool_name = match.group(2)
            params_str = match.group(3).strip()

            try:
                logger.info(f"Executing tool call: {server_name}.{tool_name}")

                # Parse parameters
                tool_arguments = {}
                if params_str:
                    tool_arguments = self.parse_parameters(params_str, arguments, environment_variables)

                # Create the tool name with server prefix
                if server_name == "vmcp":
                    prefixed_tool_name = f"{tool_name}"
                else:
                    prefixed_tool_name = f"{server_name.replace('_', '')}_{tool_name}"

                # Create tool call request
                tool_request = VMCPToolCallRequest(
                    tool_name=prefixed_tool_name,
                    arguments=tool_arguments
                )

                # Execute the tool call
                tool_result = await self.manager.execution.call_tool(tool_request)

                # Extract result text
                try:
                    if len(tool_result.content) > 1:
                        tool_result_str = json.dumps(tool_result.content, indent=2, default=str)
                    else:
                        tool_result_str = str(tool_result.content[0].text)
                except Exception:
                    if isinstance(tool_result, dict):
                        tool_result_str = json.dumps(tool_result, indent=2, default=str)
                    else:
                        tool_result_str = str(tool_result)

                logger.info(f"Successfully executed tool call {server_name}.{tool_name}")
                return tool_result_str

            except Exception as e:
                logger.error(f"Failed to execute tool call {server_name}.{tool_name}: {e}")
                return f"[Tool call failed: {str(e)}]"

        # Process tool calls sequentially (since they're async)
        while True:
            match = re.search(tool_pattern, processed_text)
            if not match:
                break

            replacement = await replace_tool(match)
            processed_text = processed_text[:match.start()] + replacement + processed_text[match.end():]

        # Step 5: Handle @prompt.server.prompt_name(params) calls
        prompt_pattern = r'@prompt\.(\w+)\.(\w+)\(([^)]*)\)'

        async def replace_prompt(match):
            server_name = match.group(1)
            prompt_name = match.group(2)
            params_str = match.group(3).strip()

            try:
                logger.info(f"Executing prompt call: {server_name}.{prompt_name}")

                # Parse parameters
                prompt_arguments = {}
                if params_str:
                    prompt_arguments = self.parse_parameters(params_str, arguments, environment_variables)

                # Create the prompt name with server prefix
                if server_name == "vmcp":
                    prefixed_prompt_name = f"{prompt_name}"
                else:
                    prefixed_prompt_name = f"{server_name.replace('_', '')}_{prompt_name}"

                # Execute the prompt call
                prompt_result = await self.manager.execution.get_prompt(
                    prefixed_prompt_name,
                    prompt_arguments
                )

                # Extract result text
                try:
                    if hasattr(prompt_result, 'messages') and prompt_result.messages:
                        prompt_result_str = prompt_result.messages[0].content.text
                    else:
                        prompt_result_str = str(prompt_result)
                except Exception:
                    if isinstance(prompt_result, dict):
                        prompt_result_str = json.dumps(prompt_result, indent=2, default=str)
                    else:
                        prompt_result_str = str(prompt_result)

                logger.info(f"Successfully executed prompt call {server_name}.{prompt_name}")
                return prompt_result_str

            except Exception as e:
                logger.error(f"Failed to execute prompt call {server_name}.{prompt_name}: {e}")
                return f"[Prompt call failed: {str(e)}]"

        # Process prompt calls sequentially (since they're async)
        while True:
            match = re.search(prompt_pattern, processed_text)
            if not match:
                break

            replacement = await replace_prompt(match)
            processed_text = processed_text[:match.start()] + replacement + processed_text[match.end():]

        # Step 6: Check if the fully processed text is a Jinja2 template and process it
        if self.is_jinja_template(processed_text):
            logger.info("Detected Jinja2 template after all substitutions")
            processed_text = self.preprocess_jinja_to_regex(processed_text, arguments, environment_variables)

        return processed_text, resource_content

    # ============================================================================
    # Jinja2 Template Support
    # ============================================================================

    def is_jinja_template(self, text: str) -> bool:
        """
        Check if text contains Jinja2 patterns.

        Args:
            text: Text to check

        Returns:
            True if text contains valid Jinja2 syntax
        """
        # Check for Jinja2 patterns
        jinja_patterns = [
            r'\{\{[^}]*\}\}',  # {{ variable }}
            r'\{%[^%]*%\}',    # {% block %}
            r'\{#[^#]*#\}'     # {# comment #}
        ]

        has_jinja_patterns = any(re.search(pattern, text) for pattern in jinja_patterns)

        if not has_jinja_patterns:
            logger.debug("No Jinja2 patterns found in text")
            return False

        # Validate Jinja2 syntax
        try:
            self.jinja_env.parse(text)
            logger.debug("Valid Jinja2 template detected")
            return True
        except Exception as e:
            logger.debug(f"Jinja2 syntax validation failed: {e}")
            return False

    def preprocess_jinja_to_regex(
        self,
        text: str,
        arguments: Dict[str, Any],
        environment_variables: Dict[str, Any]
    ) -> str:
        """
        Render Jinja2 templates to plain text.

        Args:
            text: Text containing Jinja2 template
            arguments: Available arguments
            environment_variables: Available environment variables

        Returns:
            Rendered text
        """
        if not self.is_jinja_template(text):
            logger.debug("Not a Jinja2 template")
            return text

        try:
            # Create Jinja2 template
            template = self.jinja_env.from_string(text)

            # Prepare context
            context = {
                **arguments,
                **environment_variables,
                'param': arguments,
                'config': environment_variables,
            }

            # Render the template to get final text
            rendered_text = template.render(**context)
            logger.info("Jinja2 template rendered successfully")
            return rendered_text

        except Exception as e:
            logger.warning(f"Jinja2 preprocessing failed, using original text: {e}")
            return text

    # ============================================================================
    # Parameter Parsing
    # ============================================================================

    @trace_method("ParsingEngine.parse_parameters")
    def parse_parameters(
        self,
        params_str: str,
        arguments: Dict[str, Any],
        environment_variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Parse parameter string using Python AST.

        Handles function-like syntax with type annotations:
        - param1="value"
        - param2=123
        - param3=@param.var
        - param4=@config.env_var

        Args:
            params_str: Parameter string to parse
            arguments: Available arguments
            environment_variables: Available environment variables

        Returns:
            Dict of parsed parameters
        """
        params = {}
        if not params_str.strip():
            return params

        try:
            # Preprocess the parameter string to handle @var and @env references
            processed_params_str = self.preprocess_parameter_string(
                params_str,
                arguments,
                environment_variables
            )

            # Use Python's AST parser to parse the parameter string
            # We'll create a mock function definition to parse the parameters
            function_def = f"def mock_function({processed_params_str}): pass"

            # Parse the function definition
            tree = ast.parse(function_def)
            func_def = tree.body[0]

            # Extract parameters from the function definition
            for arg in func_def.args.args:
                param_name = arg.arg
                default_value = None

                # Get default value if present
                arg_index = func_def.args.args.index(arg)
                defaults_start = len(func_def.args.args) - len(func_def.args.defaults)
                if arg_index >= defaults_start:
                    default_idx = arg_index - defaults_start
                    default_ast = func_def.args.defaults[default_idx]
                    default_value = self._evaluate_ast_node(default_ast, arguments, environment_variables)

                # If no default value from AST, try to get from arguments
                if default_value is None and param_name in arguments:
                    default_value = arguments[param_name]

                params[param_name] = default_value

        except Exception as e:
            logger.warning(f"Failed to parse parameters with AST, falling back to regex: {e}")
            # Fallback to the original regex-based parsing
            return self.parse_parameters_regex(params_str, arguments, environment_variables)

        return params

    def preprocess_parameter_string(
        self,
        params_str: str,
        arguments: Dict[str, Any],
        environment_variables: Dict[str, Any]
    ) -> str:
        """
        Preprocess parameter string to replace @var and @env references with actual values.

        Args:
            params_str: Parameter string
            arguments: Available arguments
            environment_variables: Available environment variables

        Returns:
            Preprocessed parameter string
        """
        # Replace @param.name references
        var_pattern = r'@param\.(\w+)'

        def replace_var(match):
            var_name = match.group(1)
            var_value = arguments.get(var_name, f"[{var_name} not found]")
            # If it's a string, wrap in quotes
            if isinstance(var_value, str) and not (var_value.startswith('"') and var_value.endswith('"')):
                return f'"{var_value}"'
            return str(var_value)

        processed_str = re.sub(var_pattern, replace_var, params_str)

        # Replace @config.name references
        env_pattern = r'@config\.(\w+)'

        def replace_env(match):
            env_name = match.group(1)
            env_value = environment_variables.get(env_name, f"[{env_name} not found]")
            # If it's a string, wrap in quotes
            if isinstance(env_value, str) and not (env_value.startswith('"') and env_value.endswith('"')):
                return f'"{env_value}"'
            return str(env_value)

        processed_str = re.sub(env_pattern, replace_env, processed_str)

        return processed_str

    def parse_parameters_regex(
        self,
        params_str: str,
        arguments: Dict[str, Any],
        environment_variables: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Fallback regex-based parameter parsing.

        Args:
            params_str: Parameter string
            arguments: Available arguments
            environment_variables: Available environment variables

        Returns:
            Dict of parsed parameters
        """
        params = {}
        if not params_str.strip():
            return params

        # Simple parameter parsing - handles param="value" format
        param_pattern = r'(\w+)\s*=\s*([^,]+?)(?=\s*,\s*\w+\s*=|$)'

        for match in re.finditer(param_pattern, params_str):
            param_name = match.group(1)
            param_value = match.group(2)

            # Remove quotes if present
            if param_value.startswith('"') and param_value.endswith('"'):
                param_value = param_value[1:-1]

            # Substitute any @param.name or @config.name references in the parameter value
            param_value = re.sub(
                r'@param\.(\w+)',
                lambda m: str(arguments.get(m.group(1), f"[{m.group(1)} not found]")),
                param_value
            )
            param_value = re.sub(
                r'@config\.(\w+)',
                lambda m: str(environment_variables.get(m.group(1), f"[{m.group(1)} not found]")),
                param_value
            )

            params[param_name] = param_value

        return params

    # ============================================================================
    # AST Helper Methods
    # ============================================================================

    def _evaluate_ast_node(
        self,
        node: ast.AST,
        arguments: Dict[str, Any],
        environment_variables: Dict[str, Any]
    ) -> Any:
        """
        Evaluate an AST node to get its value.

        Args:
            node: AST node to evaluate
            arguments: Available arguments
            environment_variables: Available environment variables

        Returns:
            Evaluated value
        """
        from .helpers import evaluate_ast_node
        return evaluate_ast_node(node, arguments, environment_variables)
