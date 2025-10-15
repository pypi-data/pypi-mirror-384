"""VMCP (Virtual MCP) module for aggregating multiple MCP servers."""

from vmcp.backend.vmcps.models import (
    VMCPCreateRequest,
    VMCPUpdateRequest,
    VMCPInfo,
    VMCPToolCallRequest,
    VMCPResourceRequest,
    VMCPPromptRequest,
)

__all__ = [
    "VMCPCreateRequest",
    "VMCPUpdateRequest",
    "VMCPInfo",
    "VMCPToolCallRequest",
    "VMCPResourceRequest",
    "VMCPPromptRequest",
]
