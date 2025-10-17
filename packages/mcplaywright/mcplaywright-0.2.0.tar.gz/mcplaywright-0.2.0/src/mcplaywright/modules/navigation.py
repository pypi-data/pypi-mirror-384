"""
Provides page navigation capabilities.
"""

from typing import Dict, Any, Optional
from fastmcp.contrib.mcp_mixin import MCPMixin, mcp_tool
import logging

logger = logging.getLogger(__name__)


class BrowserNavigation(MCPMixin):
    """
    Mixin for browser navigation operations.
    
    Handles URL navigation, history management, and page reloading.
    """
    
    @mcp_tool(
        name="browser_navigate",
        description="Navigate to a URL"
    )
    async def navigate_to_url(self, url: str, wait_until: str = "load") -> Dict[str, Any]:
        """Navigate to a specified URL."""
        try:
            page = await self.get_current_page()
            
            # Navigate to URL
            response = await page.goto(url, wait_until=wait_until)
            
            # Get page info after navigation
            final_url = page.url
            title = await page.title()
            status = response.status if response else None
            
            return {
                "status": "success",
                "url": final_url,
                "title": title,
                "response_status": status
            }
        except Exception as e:
            logger.error(f"Error navigating to {url}: {e}")
            return {
                "status": "error",
                "message": str(e),
                "url": url
            }
    
    @mcp_tool(
        name="browser_navigate_back",
        description="Go back to the previous page in history"
    )
    async def navigate_back(self) -> Dict[str, Any]:
        """Navigate back in browser history."""
        try:
            page = await self.get_current_page()
            
            # Go back
            response = await page.go_back()
            
            # Get updated page info
            url = page.url
            title = await page.title()
            
            return {
                "status": "success",
                "url": url,
                "title": title,
                "had_previous": response is not None
            }
        except Exception as e:
            logger.error(f"Error navigating back: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    @mcp_tool(
        name="browser_navigate_forward",
        description="Go forward to the next page in history"
    )
    async def navigate_forward(self) -> Dict[str, Any]:
        """Navigate forward in browser history."""
        try:
            page = await self.get_current_page()
            
            # Go forward
            response = await page.go_forward()
            
            # Get updated page info
            url = page.url
            title = await page.title()
            
            return {
                "status": "success",
                "url": url,
                "title": title,
                "had_next": response is not None
            }
        except Exception as e:
            logger.error(f"Error navigating forward: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    @mcp_tool(
        name="browser_reload",
        description="Reload the current page"
    )
    async def reload_page(self, wait_until: str = "load") -> Dict[str, Any]:
        """Reload the current page."""
        try:
            page = await self.get_current_page()
            
            # Reload page
            response = await page.reload(wait_until=wait_until)
            
            # Get page info
            url = page.url
            title = await page.title()
            status = response.status if response else None
            
            return {
                "status": "success",
                "url": url,
                "title": title,
                "response_status": status
            }
        except Exception as e:
            logger.error(f"Error reloading page: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    @mcp_tool(
        name="browser_wait_for",
        description="Wait for specific conditions on the page"
    )
    async def wait_for_condition(
        self,
        selector: Optional[str] = None,
        text: Optional[str] = None,
        timeout: int = 30000,
        state: str = "visible"
    ) -> Dict[str, Any]:
        """Wait for specific conditions on the page."""
        try:
            page = await self.get_current_page()
            
            if selector:
                # Wait for selector
                await page.wait_for_selector(selector, state=state, timeout=timeout)
                return {
                    "status": "success",
                    "condition": "selector",
                    "value": selector,
                    "state": state
                }
            elif text:
                # Wait for text
                await page.wait_for_function(
                    f"document.body.innerText.includes('{text}')",
                    timeout=timeout
                )
                return {
                    "status": "success",
                    "condition": "text",
                    "value": text
                }
            else:
                # Just wait for timeout
                await page.wait_for_timeout(timeout)
                return {
                    "status": "success",
                    "condition": "timeout",
                    "value": timeout
                }
                
        except Exception as e:
            logger.error(f"Error waiting for condition: {e}")
            return {
                "status": "error",
                "message": str(e),
                "condition": selector or text or "timeout"
            }
