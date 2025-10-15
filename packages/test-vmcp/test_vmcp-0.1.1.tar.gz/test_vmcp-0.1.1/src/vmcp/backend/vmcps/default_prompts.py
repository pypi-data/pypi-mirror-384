#!/usr/bin/env python3
"""
Default System Prompts
=====================

This module contains default system prompts that are always available
regardless of vMCP configuration.
"""

import logging
from typing import List, Dict, Any, Optional
from mcp.types import Prompt, PromptArgument, PromptMessage, TextContent, GetPromptResult

logger = logging.getLogger("vmcp.default_prompts")


def get_feedback_prompt() -> Prompt:
    """Create the feedback prompt"""
    feedback_prompt_args = [
        PromptArgument(
            name="topic",
            description="The topic or subject of your feedback",
            required=True
        ),
        PromptArgument(
            name="feedback_text",
            description="Your detailed feedback",
            required=True
        )
    ]

    return Prompt(
        name="vmcp_feedback",
        description="Submit feedback on any topic - your feedback will be stored for review",
        arguments=feedback_prompt_args,
        meta={
            "type": "default_system",
            "system_prompt": True
        }
    )


def get_all_default_prompts(vmcp_id: Optional[str] = None) -> List[Prompt]:
    """
    Get all default system prompts.

    Args:
        vmcp_id: Optional vMCP ID (not used in OSS version)

    Returns:
        List of default Prompt objects
    """
    # In OSS version, always return feedback prompt
    return [get_feedback_prompt()]


def _save_feedback_to_storage(feedback_data: Dict[str, Any]) -> bool:
    """
    Save feedback data to storage.

    Args:
        feedback_data: Feedback information

    Returns:
        True if successful, False otherwise
    """
    try:
        from vmcp.backend.storage.base import StorageBase

        # Use user_id from feedback data
        user_id = feedback_data.get("user_id", 1)
        storage = StorageBase(user_id)

        return storage.save_feedback(feedback_data)

    except Exception as e:
        logger.error(f"Error saving feedback: {e}")
        return False


async def handle_feedback_prompt(
    user_id: int,
    vmcp_id: Optional[str],
    arguments: Dict[str, Any]
) -> GetPromptResult:
    """
    Handle the feedback prompt execution and store feedback.

    Args:
        user_id: User ID (always 1 in OSS)
        vmcp_id: Optional vMCP ID
        arguments: Prompt arguments (topic, feedback_text)

    Returns:
        GetPromptResult with confirmation message
    """
    try:
        topic = arguments.get("topic", "")
        feedback_text = arguments.get("feedback_text", "")

        if not topic or not feedback_text:
            raise ValueError("Both topic and feedback_text are required")

        # Store the feedback
        feedback_data = {
            "user_id": user_id,
            "vmcp_id": vmcp_id,
            "topic": topic,
            "text": feedback_text
        }

        success = _save_feedback_to_storage(feedback_data)

        if success:
            response_text = f"Thank you for your feedback on '{topic}'!"
        else:
            response_text = (
                f"Your feedback on '{topic}' was received, but there was an issue saving it. "
                "Please try again."
            )

        logger.info(f"Feedback processed for user {user_id} on topic: {topic}")

        # Create the response
        text_content = TextContent(
            type="text",
            text=response_text,
            annotations=None,
            meta=None
        )

        prompt_message = PromptMessage(
            role="assistant",
            content=text_content
        )

        return GetPromptResult(
            description="Feedback submission confirmation",
            messages=[prompt_message]
        )

    except Exception as e:
        logger.error(f"Error handling feedback prompt: {e}")
        error_text = f"Sorry, there was an error processing your feedback: {str(e)}"

        text_content = TextContent(
            type="text",
            text=error_text,
            annotations=None,
            meta=None
        )

        prompt_message = PromptMessage(
            role="assistant",
            content=text_content
        )

        return GetPromptResult(
            description="Feedback submission error",
            messages=[prompt_message]
        )


async def handle_default_prompt(
    prompt_name: str,
    user_id: int,
    vmcp_id: Optional[str],
    arguments: Optional[Dict[str, Any]] = None
) -> GetPromptResult:
    """
    Handle execution of default system prompts.

    Args:
        prompt_name: Name of the prompt to execute
        user_id: User ID (always 1 in OSS)
        vmcp_id: Optional vMCP ID
        arguments: Optional prompt arguments

    Returns:
        GetPromptResult from the prompt handler

    Raises:
        ValueError: If prompt name is not recognized
    """
    if arguments is None:
        arguments = {}

    # Remove # prefix if present
    prompt_name = prompt_name[1:] if prompt_name.startswith("#") else prompt_name

    if prompt_name == "vmcp_feedback":
        return await handle_feedback_prompt(user_id, vmcp_id, arguments)
    else:
        raise ValueError(f"Unknown default prompt: {prompt_name}")
