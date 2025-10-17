"""
Browser Management Mixin for MCPlaywright

Provides core browser lifecycle management capabilities.
"""

from typing import Dict, Any, Optional, List
from fastmcp.contrib.mcp_mixin import MCPMixin, mcp_tool
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
import logging

logger = logging.getLogger(__name__)


class BrowserCore(MCPMixin):
    """
    Mixin for browser management operations.
    
    Handles browser lifecycle, context creation, and page management.
    """
    
    def __init__(self):
        super().__init__()
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._current_page: Optional[Page] = None
        self._pages: List[Page] = []
        self._browser_type = "chromium"
        self._headless = True
        self._viewport = {"width": 1280, "height": 720}
        
    async def ensure_browser_context(self) -> BrowserContext:
        """Ensure browser context is initialized."""
        if not self._context:
            await self._create_browser_context()
        return self._context
    
    async def _create_browser_context(self):
        """Create a new browser context with current configuration."""
        if not self._playwright:
            self._playwright = await async_playwright().start()
        
        # Close existing browser if any
        if self._browser:
            await self._browser.close()
        
        # Launch browser based on type
        browser_launcher = getattr(self._playwright, self._browser_type)
        self._browser = await browser_launcher.launch(
            headless=self._headless,
            args=["--no-sandbox", "--disable-setuid-sandbox"] if self._headless else []
        )
        
        # Create context with viewport
        self._context = await self._browser.new_context(
            viewport=self._viewport,
            user_agent="MCPlaywright/1.0 (FastMCP)"
        )
        
        # Create initial page
        self._current_page = await self._context.new_page()
        self._pages = [self._current_page]
        
        logger.info(f"Browser context created: {self._browser_type}, headless={self._headless}")
    
    async def get_current_page(self) -> Page:
        """Get the current active page."""
        if not self._current_page:
            await self.ensure_browser_context()
        return self._current_page
    
    @mcp_tool(
        name="browser_close",
        description="Close the browser and clean up resources"
    )
    async def close_browser(self) -> Dict[str, Any]:
        """Close browser and cleanup resources."""
        try:
            if self._context:
                await self._context.close()
                self._context = None
            
            if self._browser:
                await self._browser.close()
                self._browser = None
            
            if self._playwright:
                await self._playwright.stop()
                self._playwright = None
            
            self._current_page = None
            self._pages = []
            
            return {
                "status": "success",
                "message": "Browser closed successfully"
            }
        except Exception as e:
            logger.error(f"Error closing browser: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    @mcp_tool(
        name="browser_configure",
        description="Configure browser settings (headless mode, viewport, browser type)"
    )
    async def configure_browser(
        self,
        browser_type: Optional[str] = None,
        headless: Optional[bool] = None,
        viewport: Optional[Dict[str, int]] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """Configure browser settings and restart with new configuration."""
        try:
            # Update configuration
            if browser_type and browser_type in ["chromium", "firefox", "webkit"]:
                self._browser_type = browser_type
            
            if headless is not None:
                self._headless = headless
            
            if viewport:
                self._viewport = viewport
            
            # Restart browser with new configuration
            await self.close_browser()
            await self.ensure_browser_context()
            
            return {
                "status": "success",
                "configuration": {
                    "browser_type": self._browser_type,
                    "headless": self._headless,
                    "viewport": self._viewport
                }
            }
        except Exception as e:
            logger.error(f"Error configuring browser: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    @mcp_tool(
        name="browser_snapshot",
        description="Get a complete accessibility snapshot of the current page",
        annotations={"readOnlyHint": True}
    )
    async def get_page_snapshot(self) -> Dict[str, Any]:
        """Get accessibility snapshot of current page."""
        try:
            page = await self.get_current_page()
            
            # Get page info
            url = page.url
            title = await page.title()
            
            # Get accessibility tree
            accessibility_tree = await page.accessibility.snapshot()
            
            return {
                "status": "success",
                "url": url,
                "title": title,
                "snapshot": accessibility_tree
            }
        except Exception as e:
            logger.error(f"Error getting page snapshot: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    @mcp_tool(
        name="browser_console_messages",
        description="Get all console messages from the current page",
        annotations={"readOnlyHint": True}
    )
    async def get_console_messages(self) -> Dict[str, Any]:
        """Get console messages from the current page."""
        try:
            page = await self.get_current_page()
            
            # Set up console message listener if not already done
            console_messages = []
            
            def handle_console(msg):
                console_messages.append({
                    "type": msg.type,
                    "text": msg.text,
                    "location": msg.location
                })
            
            page.on("console", handle_console)
            
            return {
                "status": "success",
                "messages": console_messages,
                "count": len(console_messages)
            }
        except Exception as e:
            logger.error(f"Error getting console messages: {e}")
            return {
                "status": "error",
                "message": str(e)
            }