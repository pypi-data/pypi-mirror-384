"""
MCPlaywright Modules for FastMCP

Modular components that provide specific browser automation capabilities.
Each module can be composed to create a full-featured MCP server.
"""

from .browser import BrowserCore
from .screenshots import BrowserScreenshots
from .navigation import BrowserNavigation
from .interaction import BrowserInteraction
# from .debugging import ClientIdentification  # TODO: update class name
# from .extensions import ExtensionManagement   # TODO: update class name
# from .coordinates import CoordinateInteraction # TODO: update class name
# from .media import MediaStreamMixin            # TODO: update class name
# from .system import SystemControlMixin         # TODO: update class name

__all__ = [
    "BrowserCore",
    "BrowserScreenshots",
    "BrowserNavigation",
    "BrowserInteraction",
    # "ClientIdentification",
    # "ExtensionManagement",
    # "CoordinateInteraction",
    # "MediaStreamMixin",
    # "SystemControlMixin",
]