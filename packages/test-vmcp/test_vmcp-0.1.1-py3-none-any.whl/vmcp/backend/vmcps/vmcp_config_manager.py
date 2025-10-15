#!/usr/bin/env python3
"""
vMCP Configuration Manager - Backward Compatibility Wrapper
===========================================================

This module provides backward compatibility with the old monolithic
vmcp_config_manager.py file by re-exporting the new modular VMCPConfigManager.

All functionality has been refactored into a clean modular architecture under
the config_manager/ package. This file simply re-exports it for compatibility.

For new code, prefer importing from config_manager directly:
    from vmcp.backend.vmcps.config_manager import VMCPConfigManager
"""

# Re-export the new modular VMCPConfigManager
from vmcp.backend.vmcps.config_manager import VMCPConfigManager

# Re-export helper types that may be used by existing code
from vmcp.backend.vmcps.config_manager.helpers import UIWidget

__all__ = ['VMCPConfigManager', 'UIWidget']
