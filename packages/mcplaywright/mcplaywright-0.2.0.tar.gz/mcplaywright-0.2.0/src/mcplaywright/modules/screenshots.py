"""
Provides screenshot capture capabilities with various options.
"""

from typing import Dict, Any, Optional
from fastmcp.contrib.mcp_mixin import MCPMixin, mcp_tool
from pathlib import Path
import base64
import logging

logger = logging.getLogger(__name__)


class BrowserScreenshots(MCPMixin):
    """
    Mixin for screenshot operations.
    
    Handles viewport and full-page screenshots with various formats.
    """
    
    def __init__(self):
        super().__init__()
        self.screenshot_dir = Path("/tmp/mcplaywright/screenshots")
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
    
    @mcp_tool(
        name="browser_take_screenshot",
        description="Take a screenshot of the current page",
        annotations={"readOnlyHint": True}
    )
    async def take_screenshot(
        self,
        full_page: bool = False,
        selector: Optional[str] = None,
        filename: Optional[str] = None,
        format: str = "png",
        quality: Optional[int] = None,
        return_base64: bool = False
    ) -> Dict[str, Any]:
        """Take a screenshot of the page or specific element."""
        try:
            page = await self.get_current_page()
            
            # Prepare screenshot options
            options = {
                "type": format,
                "full_page": full_page
            }
            
            if quality and format == "jpeg":
                options["quality"] = quality
            
            # Determine what to screenshot
            if selector:
                # Screenshot specific element
                element = await page.query_selector(selector)
                if not element:
                    return {
                        "status": "error",
                        "message": f"Element not found: {selector}"
                    }
                screenshot_bytes = await element.screenshot(**options)
                target = selector
            else:
                # Screenshot page
                screenshot_bytes = await page.screenshot(**options)
                target = "page"
            
            # Save or return screenshot
            result = {
                "status": "success",
                "target": target,
                "full_page": full_page,
                "format": format
            }
            
            if filename:
                # Save to file
                filepath = self.screenshot_dir / filename
                filepath.write_bytes(screenshot_bytes)
                result["filepath"] = str(filepath)
            
            if return_base64:
                # Return as base64
                result["base64"] = base64.b64encode(screenshot_bytes).decode()
            
            return result
            
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    @mcp_tool(
        name="browser_screenshot_element",
        description="Take a screenshot of a specific element",
        annotations={"readOnlyHint": True}
    )
    async def screenshot_element(
        self,
        selector: str,
        filename: Optional[str] = None,
        format: str = "png",
        quality: Optional[int] = None
    ) -> Dict[str, Any]:
        """Convenience method for element screenshots."""
        return await self.take_screenshot(
            selector=selector,
            filename=filename,
            format=format,
            quality=quality
        )
    
    @mcp_tool(
        name="browser_screenshot_full_page",
        description="Take a full-page screenshot",
        annotations={"readOnlyHint": True}
    )
    async def screenshot_full_page(
        self,
        filename: Optional[str] = None,
        format: str = "png",
        quality: Optional[int] = None
    ) -> Dict[str, Any]:
        """Convenience method for full-page screenshots."""
        return await self.take_screenshot(
            full_page=True,
            filename=filename,
            format=format,
            quality=quality
        )
    
    @mcp_tool(
        name="browser_pdf",
        description="Generate a PDF of the current page",
        annotations={"readOnlyHint": True}
    )
    async def generate_pdf(
        self,
        filename: Optional[str] = None,
        format: str = "A4",
        landscape: bool = False,
        scale: float = 1.0,
        return_base64: bool = False
    ) -> Dict[str, Any]:
        """Generate a PDF of the current page."""
        try:
            page = await self.get_current_page()
            
            # PDF options
            options = {
                "format": format,
                "landscape": landscape,
                "scale": scale,
                "print_background": True
            }
            
            # Generate PDF
            pdf_bytes = await page.pdf(**options)
            
            result = {
                "status": "success",
                "format": format,
                "landscape": landscape,
                "scale": scale
            }
            
            if filename:
                # Save to file
                filepath = self.screenshot_dir / filename
                filepath.write_bytes(pdf_bytes)
                result["filepath"] = str(filepath)
            
            if return_base64:
                # Return as base64
                result["base64"] = base64.b64encode(pdf_bytes).decode()
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating PDF: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
