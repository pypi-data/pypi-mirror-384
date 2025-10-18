"""
SMCP - Secure Model Context Protocol

A security-focused wrapper library for MCP servers providing conditional
security guards that activate only when their required configuration is present.
"""

import logging

from .app_wrapper import FastSMCP
from .decorators import tool, prompt, retrieval

__version__ = "0.1.0"
__all__ = ["FastSMCP", "tool", "prompt", "retrieval"]

# Non-intrusive watermark for community edition
def _show_watermark():
    """Display a subtle watermark message for the community edition."""
    logger = logging.getLogger(__name__)
    logger.info("SMCP Community Edition - For commercial licensing visit: https://smcp.dev/business")

# Show watermark on import (only once)
try:
    if not hasattr(_show_watermark, '_shown'):
        _show_watermark()
        _show_watermark._shown = True
except Exception:
    # Silently fail if logging isn't configured
    pass
