"""
MCPlaywright - Python Playwright MCP Server

A comprehensive FastMCP-based server providing browser automation capabilities
with advanced features for video recording, HTTP request monitoring, and UI customization.
"""

__version__ = "0.1.0"
__author__ = "MCPlaywright Team"
__license__ = "Apache-2.0"

from .server import app

__all__ = ["app"]