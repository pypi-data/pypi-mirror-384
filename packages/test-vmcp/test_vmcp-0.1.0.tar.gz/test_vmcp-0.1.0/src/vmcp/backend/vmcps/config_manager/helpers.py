"""
Helper Functions and Utilities
==============================

Provides utility functions, data classes, and helpers for vMCP operations.
Includes widget support for OpenAI Apps SDK.
"""

import ast
import json
import logging
from dataclasses import dataclass
from typing import Dict, Any, Optional

from mcp.types import EmbeddedResource, TextResourceContents

logger = logging.getLogger("vmcp.config_manager.helpers")

# Widget MIME type for OpenAI Apps SDK
MIME_TYPE = "text/html+skybridge"


@dataclass
class ReadResourceContents:
    """Contents returned from a read_resource call."""
    content: str | bytes
    mime_type: str | None = None


@dataclass(frozen=True)
class UIWidget:
    """
    Widget metadata for OpenAI Apps SDK integration.

    Represents a UI widget that can be attached to tools and resources
    to provide rich interactive experiences.
    """
    identifier: str
    title: str
    template_uri: str
    invoking: str
    invoked: str
    html: str
    response_text: str


def resource_description(widget: UIWidget) -> str:
    """Get description for a widget resource."""
    return f"{widget.title} widget markup"


def tool_meta(widget: UIWidget) -> Dict[str, Any]:
    """
    Generate tool metadata for OpenAI Apps SDK widget integration.

    Args:
        widget: UIWidget instance with widget information

    Returns:
        Dict with OpenAI Apps SDK metadata
    """
    return {
        "openai/outputTemplate": widget.template_uri,
        "openai/toolInvocation/invoking": widget.invoking,
        "openai/toolInvocation/invoked": widget.invoked,
        "openai/widgetAccessible": True,
        "openai/resultCanProduceWidget": True,
        "annotations": {
            "destructiveHint": False,
            "openWorldHint": False,
            "readOnlyHint": True,
        }
    }


def embedded_widget_resource(widget: UIWidget) -> EmbeddedResource:
    """
    Create an embedded resource for a widget.

    Args:
        widget: UIWidget instance

    Returns:
        EmbeddedResource with widget HTML content
    """
    return EmbeddedResource(
        type="resource",
        resource=TextResourceContents(
            uri=widget.template_uri,
            mimeType=MIME_TYPE,
            text=widget.html,
            title=widget.title,
        ),
    )


# AST Helper Functions

def ast_to_string(node: ast.AST) -> str:
    """
    Convert AST node to string representation.

    Args:
        node: AST node to convert

    Returns:
        String representation of the node
    """
    if isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Constant):
        return str(node.value)
    elif isinstance(node, ast.Str):  # Python < 3.8 compatibility
        return node.s
    elif isinstance(node, ast.Num):  # Python < 3.8 compatibility
        return str(node.n)
    elif isinstance(node, ast.NameConstant):  # Python < 3.8 compatibility
        return str(node.value)
    else:
        return str(node)


def evaluate_ast_node(
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
    if isinstance(node, ast.Constant):
        return node.value
    elif isinstance(node, ast.Str):  # Python < 3.8 compatibility
        return node.s
    elif isinstance(node, ast.Num):  # Python < 3.8 compatibility
        return node.n
    elif isinstance(node, ast.NameConstant):  # Python < 3.8 compatibility
        return node.value
    elif isinstance(node, ast.Name):
        # Check if it's a variable reference
        var_name = node.id
        if var_name in arguments:
            return arguments[var_name]
        elif var_name in environment_variables:
            return environment_variables[var_name]
        else:
            return f"[{var_name} not found]"
    else:
        # For complex expressions, try to evaluate safely
        try:
            return ast.literal_eval(node)
        except Exception:
            return str(node)


def cast_value_to_type(value: Any, type_str: str) -> Any:
    """
    Cast a value to the specified type.

    Args:
        value: Value to cast
        type_str: Target type as string (str, int, float, bool, list, dict)

    Returns:
        Casted value
    """
    try:
        # Handle common type annotations
        if type_str == "str":
            return str(value)
        elif type_str == "int":
            return int(value)
        elif type_str == "float":
            return float(value)
        elif type_str == "bool":
            if isinstance(value, str):
                return value.lower() in ('true', '1', 'yes', 'on')
            return bool(value)
        elif type_str == "list":
            if isinstance(value, str):
                # Try to parse as JSON list
                try:
                    return json.loads(value)
                except Exception:
                    return [value]
            return list(value) if hasattr(value, '__iter__') else [value]
        elif type_str == "dict":
            if isinstance(value, str):
                # Try to parse as JSON dict
                try:
                    return json.loads(value)
                except Exception:
                    return {"value": value}
            return dict(value) if hasattr(value, 'items') else {"value": value}
        else:
            # For custom types or unknown types, return as-is
            logger.warning(f"Unknown type annotation: {type_str}, returning value as-is")
            return value
    except Exception as e:
        logger.warning(f"Failed to cast {value} to {type_str}: {e}")
        return value
