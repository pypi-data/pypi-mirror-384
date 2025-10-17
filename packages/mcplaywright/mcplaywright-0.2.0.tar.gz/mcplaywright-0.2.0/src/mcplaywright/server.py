"""
MCPlaywright Clean Server

Simple, clean FastMCP server using modular components.
"""

from fastmcp import FastMCP
from typing import Dict, Any
import logging

# Import core modules
from .modules.browser import BrowserCore
from .modules.navigation import BrowserNavigation
from .modules.interaction import BrowserInteraction
from .modules.screenshots import BrowserScreenshots

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MCPlaywright(
    BrowserCore,
    BrowserNavigation,
    BrowserInteraction,
    BrowserScreenshots
):
    """
    Clean MCPlaywright server with core functionality.

    Includes:
    - Browser management and lifecycle
    - Navigation and page control
    - Element interactions (click, type, etc.)
    - Screenshots and visual capture
    """

    def __init__(self):
        """Initialize all modules."""
        super().__init__()
        logger.info("MCPlaywright server initialized")


# Create FastMCP app and server instance
app = FastMCP("MCPlaywright")
server = MCPlaywright()

# Register all tools from modules
server.register_all(app)

logger.info("MCPlaywright server ready with clean module architecture")


def main():
    """Run the MCPlaywright server via stdio."""
    app.run()


if __name__ == "__main__":
    main()
