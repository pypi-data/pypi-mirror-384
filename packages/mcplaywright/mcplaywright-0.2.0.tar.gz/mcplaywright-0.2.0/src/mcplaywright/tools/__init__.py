"""
MCPlaywright Browser Tools

Collection of FastMCP tools for browser automation with advanced features.
"""

from .browser import *
from .configure import *

__all__ = [
    "browser_navigate",
    "browser_screenshot", 
    "browser_click",
    "browser_configure",
    "browser_close"
]