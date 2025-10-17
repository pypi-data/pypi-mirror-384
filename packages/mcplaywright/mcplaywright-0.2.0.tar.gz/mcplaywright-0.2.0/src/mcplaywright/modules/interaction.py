"""
Provides element interaction capabilities like click, type, hover, etc.
"""

from typing import Dict, Any, Optional, List
from fastmcp.contrib.mcp_mixin import MCPMixin, mcp_tool
import logging

logger = logging.getLogger(__name__)


class BrowserInteraction(MCPMixin):
    """
    Browser interaction operations.

    Handles clicking, typing, hovering, and other element interactions.
    """
    
    @mcp_tool(
        name="browser_click",
        description="Click on an element",
        annotations={"destructiveHint": True}
    )
    async def click_element(
        self,
        selector: str,
        button: str = "left",
        click_count: int = 1,
        delay: int = 0,
        timeout: int = 30000
    ) -> Dict[str, Any]:
        """Click on an element."""
        try:
            page = await self.get_current_page()
            
            # Wait for element and click
            await page.wait_for_selector(selector, timeout=timeout)
            await page.click(
                selector,
                button=button,
                click_count=click_count,
                delay=delay
            )
            
            return {
                "status": "success",
                "selector": selector,
                "button": button,
                "click_count": click_count
            }
        except Exception as e:
            logger.error(f"Error clicking element {selector}: {e}")
            return {
                "status": "error",
                "message": str(e),
                "selector": selector
            }
    
    @mcp_tool(
        name="browser_type",
        description="Type text into an input field",
        annotations={"destructiveHint": True}
    )
    async def type_text(
        self,
        selector: str,
        text: str,
        delay: int = 0,
        clear_first: bool = False,
        timeout: int = 30000
    ) -> Dict[str, Any]:
        """Type text into an input field."""
        try:
            page = await self.get_current_page()
            
            # Wait for element
            await page.wait_for_selector(selector, timeout=timeout)
            
            # Clear field if requested
            if clear_first:
                await page.fill(selector, "")
            
            # Type text
            await page.type(selector, text, delay=delay)
            
            return {
                "status": "success",
                "selector": selector,
                "text_length": len(text),
                "cleared": clear_first
            }
        except Exception as e:
            logger.error(f"Error typing into {selector}: {e}")
            return {
                "status": "error",
                "message": str(e),
                "selector": selector
            }
    
    @mcp_tool(
        name="browser_fill",
        description="Fill an input field with text (faster than typing)",
        annotations={"destructiveHint": True}
    )
    async def fill_input(
        self,
        selector: str,
        value: str,
        timeout: int = 30000
    ) -> Dict[str, Any]:
        """Fill an input field with text."""
        try:
            page = await self.get_current_page()
            
            # Wait for element and fill
            await page.wait_for_selector(selector, timeout=timeout)
            await page.fill(selector, value)
            
            return {
                "status": "success",
                "selector": selector,
                "value_length": len(value)
            }
        except Exception as e:
            logger.error(f"Error filling {selector}: {e}")
            return {
                "status": "error",
                "message": str(e),
                "selector": selector
            }
    
    @mcp_tool(
        name="browser_hover",
        description="Hover over an element"
    )
    async def hover_element(
        self,
        selector: str,
        timeout: int = 30000
    ) -> Dict[str, Any]:
        """Hover over an element."""
        try:
            page = await self.get_current_page()
            
            # Wait for element and hover
            await page.wait_for_selector(selector, timeout=timeout)
            await page.hover(selector)
            
            return {
                "status": "success",
                "selector": selector
            }
        except Exception as e:
            logger.error(f"Error hovering over {selector}: {e}")
            return {
                "status": "error",
                "message": str(e),
                "selector": selector
            }
    
    @mcp_tool(
        name="browser_select_option",
        description="Select an option from a dropdown",
        annotations={"destructiveHint": True}
    )
    async def select_dropdown_option(
        self,
        selector: str,
        value: Optional[str] = None,
        label: Optional[str] = None,
        index: Optional[int] = None,
        timeout: int = 30000
    ) -> Dict[str, Any]:
        """Select an option from a dropdown."""
        try:
            page = await self.get_current_page()
            
            # Wait for element
            await page.wait_for_selector(selector, timeout=timeout)
            
            # Build option selector
            option = None
            if value:
                option = {"value": value}
            elif label:
                option = {"label": label}
            elif index is not None:
                option = {"index": index}
            
            if not option:
                return {
                    "status": "error",
                    "message": "Must provide value, label, or index"
                }
            
            # Select option
            selected = await page.select_option(selector, **option)
            
            return {
                "status": "success",
                "selector": selector,
                "selected": selected,
                "option": option
            }
        except Exception as e:
            logger.error(f"Error selecting option in {selector}: {e}")
            return {
                "status": "error",
                "message": str(e),
                "selector": selector
            }
    
    @mcp_tool(
        name="browser_press_key",
        description="Press a keyboard key or key combination"
    )
    async def press_key(
        self,
        key: str,
        selector: Optional[str] = None,
        timeout: int = 30000
    ) -> Dict[str, Any]:
        """Press a keyboard key."""
        try:
            page = await self.get_current_page()
            
            if selector:
                # Press key on specific element
                await page.wait_for_selector(selector, timeout=timeout)
                await page.press(selector, key)
            else:
                # Press key on page
                await page.keyboard.press(key)
            
            return {
                "status": "success",
                "key": key,
                "selector": selector
            }
        except Exception as e:
            logger.error(f"Error pressing key {key}: {e}")
            return {
                "status": "error",
                "message": str(e),
                "key": key
            }
    
    @mcp_tool(
        name="browser_drag",
        description="Drag from one element to another",
        annotations={"destructiveHint": True}
    )
    async def drag_and_drop(
        self,
        source_selector: str,
        target_selector: str,
        timeout: int = 30000
    ) -> Dict[str, Any]:
        """Drag from source element to target element."""
        try:
            page = await self.get_current_page()
            
            # Wait for both elements
            await page.wait_for_selector(source_selector, timeout=timeout)
            await page.wait_for_selector(target_selector, timeout=timeout)
            
            # Perform drag and drop
            await page.drag_and_drop(source_selector, target_selector)
            
            return {
                "status": "success",
                "source": source_selector,
                "target": target_selector
            }
        except Exception as e:
            logger.error(f"Error dragging from {source_selector} to {target_selector}: {e}")
            return {
                "status": "error",
                "message": str(e),
                "source": source_selector,
                "target": target_selector
            }
    
    @mcp_tool(
        name="browser_check",
        description="Check or uncheck a checkbox",
        annotations={"destructiveHint": True}
    )
    async def toggle_checkbox(
        self,
        selector: str,
        checked: bool = True,
        timeout: int = 30000
    ) -> Dict[str, Any]:
        """Check or uncheck a checkbox."""
        try:
            page = await self.get_current_page()
            
            # Wait for element
            await page.wait_for_selector(selector, timeout=timeout)
            
            # Check or uncheck
            if checked:
                await page.check(selector)
            else:
                await page.uncheck(selector)
            
            # Verify state
            is_checked = await page.is_checked(selector)
            
            return {
                "status": "success",
                "selector": selector,
                "checked": is_checked
            }
        except Exception as e:
            logger.error(f"Error toggling checkbox {selector}: {e}")
            return {
                "status": "error",
                "message": str(e),
                "selector": selector
            }
