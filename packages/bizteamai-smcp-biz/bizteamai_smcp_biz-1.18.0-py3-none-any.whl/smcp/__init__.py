"""
SMCP Business Edition - Secure Model Context Protocol

Professional secure MCP server implementation with core-based licensing.
"""

import logging
import atexit
import os

from .license import verify_license, get_licensed_cores
from .enforce import start_enforcement

# Import core SMCP functionality
from .app_wrapper import FastSMCP
from .decorators import tool, prompt, retrieval

__version__ = "0.1.0"
__all__ = ["FastSMCP", "tool", "prompt", "retrieval"]

# Initialize licensing system
logger = logging.getLogger(__name__)

def _initialize_licensing():
    """Initialize the licensing system on module import."""
    try:
        # Check if we're in development/testing mode
        if os.getenv('BIZTEAM_DEV_MODE') == '1':
            logger.info("SMCP Business Edition - Development mode (license checking disabled)")
            return
        
        # Verify license on import
        license_info = verify_license()
        if license_info:
            licensed_cores = get_licensed_cores()
            logger.info(f"SMCP Business Edition - Licensed for {licensed_cores} cores")
            
            # Start enforcement monitoring
            start_enforcement()
        else:
            logger.error("SMCP Business Edition - Invalid or missing license")
            raise RuntimeError("Valid license required for SMCP Business Edition")
            
    except Exception as e:
        logger.error(f"License initialization failed: {e}")
        if os.getenv('BIZTEAM_DEV_MODE') != '1':
            raise

# Initialize on import
_initialize_licensing()

# Clean up on exit
atexit.register(lambda: logger.debug("SMCP Business Edition - Shutting down"))
