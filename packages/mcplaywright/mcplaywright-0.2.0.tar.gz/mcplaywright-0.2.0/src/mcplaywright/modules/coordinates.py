"""
Coordinate-Based Interaction

Provides pixel-perfect mouse control for vision-based automation
and legacy UI interaction where accessibility trees fail.
"""

from typing import Dict, Any, Optional, Tuple, List
from fastmcp.contrib.mcp_mixin import MCPMixin, mcp_tool
import logging

logger = logging.getLogger(__name__)


class CoordinateInteraction(MCPMixin):
    """
    Enables vision-based automation with precise pixel control,
    useful for canvas elements, games, and legacy applications.
    """
    
    @mcp_tool(
        name="browser_mouse_click_xy",
        description="Click at specific coordinates on the page"
    )
    async def mouse_click_xy(
        self,
        x: float,
        y: float,
        button: str = "left",
        click_count: int = 1,
        delay: int = 0
    ) -> Dict[str, Any]:
        """Click at specific coordinates."""
        try:
            page = await self.get_current_page()
            
            # Move to position and click
            await page.mouse.click(x, y, button=button, click_count=click_count, delay=delay)
            
            logger.info(f"Clicked at ({x}, {y}) with {button} button")
            
            return {
                "status": "success",
                "coordinates": {"x": x, "y": y},
                "button": button,
                "click_count": click_count
            }
            
        except Exception as e:
            logger.error(f"Error clicking at ({x}, {y}): {e}")
            return {
                "status": "error",
                "message": str(e),
                "coordinates": {"x": x, "y": y}
            }
    
    @mcp_tool(
        name="browser_mouse_drag_xy",
        description="Drag from one coordinate to another"
    )
    async def mouse_drag_xy(
        self,
        start_x: float,
        start_y: float,
        end_x: float,
        end_y: float,
        steps: int = 10,
        button: str = "left"
    ) -> Dict[str, Any]:
        """Drag between two coordinates."""
        try:
            page = await self.get_current_page()
            
            # Move to start position
            await page.mouse.move(start_x, start_y)
            
            # Press button
            await page.mouse.down(button=button)
            
            # Move to end position with steps for smooth animation
            if steps > 1:
                for i in range(1, steps + 1):
                    progress = i / steps
                    current_x = start_x + (end_x - start_x) * progress
                    current_y = start_y + (end_y - start_y) * progress
                    await page.mouse.move(current_x, current_y)
            else:
                await page.mouse.move(end_x, end_y)
            
            # Release button
            await page.mouse.up(button=button)
            
            logger.info(f"Dragged from ({start_x}, {start_y}) to ({end_x}, {end_y})")
            
            return {
                "status": "success",
                "start": {"x": start_x, "y": start_y},
                "end": {"x": end_x, "y": end_y},
                "steps": steps,
                "button": button
            }
            
        except Exception as e:
            logger.error(f"Error dragging: {e}")
            return {
                "status": "error",
                "message": str(e),
                "start": {"x": start_x, "y": start_y},
                "end": {"x": end_x, "y": end_y}
            }
    
    @mcp_tool(
        name="browser_mouse_move_xy",
        description="Move mouse to specific coordinates without clicking"
    )
    async def mouse_move_xy(
        self,
        x: float,
        y: float,
        steps: int = 1
    ) -> Dict[str, Any]:
        """Move mouse to specific coordinates."""
        try:
            page = await self.get_current_page()
            
            if steps > 1:
                # Get current mouse position (approximate from last known)
                # In a real implementation, we'd track this
                current_x, current_y = 0, 0
                
                # Animate movement
                for i in range(1, steps + 1):
                    progress = i / steps
                    target_x = current_x + (x - current_x) * progress
                    target_y = current_y + (y - current_y) * progress
                    await page.mouse.move(target_x, target_y)
            else:
                await page.mouse.move(x, y)
            
            logger.info(f"Mouse moved to ({x}, {y})")
            
            return {
                "status": "success",
                "coordinates": {"x": x, "y": y},
                "steps": steps
            }
            
        except Exception as e:
            logger.error(f"Error moving mouse to ({x}, {y}): {e}")
            return {
                "status": "error",
                "message": str(e),
                "coordinates": {"x": x, "y": y}
            }
    
    @mcp_tool(
        name="browser_mouse_wheel",
        description="Scroll the mouse wheel at current position"
    )
    async def mouse_wheel(
        self,
        delta_x: float = 0,
        delta_y: float = 100
    ) -> Dict[str, Any]:
        """Scroll the mouse wheel."""
        try:
            page = await self.get_current_page()
            
            # Scroll wheel
            await page.mouse.wheel(delta_x, delta_y)
            
            logger.info(f"Mouse wheel scrolled: deltaX={delta_x}, deltaY={delta_y}")
            
            return {
                "status": "success",
                "delta": {"x": delta_x, "y": delta_y}
            }
            
        except Exception as e:
            logger.error(f"Error scrolling mouse wheel: {e}")
            return {
                "status": "error",
                "message": str(e),
                "delta": {"x": delta_x, "y": delta_y}
            }
    
    @mcp_tool(
        name="browser_get_element_bounds",
        description="Get the bounding box coordinates of an element",
        annotations={"readOnlyHint": True}
    )
    async def get_element_bounds(
        self,
        selector: str
    ) -> Dict[str, Any]:
        """Get bounding box of an element for coordinate-based interaction."""
        try:
            page = await self.get_current_page()
            
            # Get element bounding box
            element = await page.query_selector(selector)
            if not element:
                return {
                    "status": "error",
                    "message": f"Element not found: {selector}"
                }
            
            bounding_box = await element.bounding_box()
            if not bounding_box:
                return {
                    "status": "error",
                    "message": f"Could not get bounding box for: {selector}"
                }
            
            # Calculate center point
            center_x = bounding_box["x"] + bounding_box["width"] / 2
            center_y = bounding_box["y"] + bounding_box["height"] / 2
            
            return {
                "status": "success",
                "selector": selector,
                "bounds": {
                    "x": bounding_box["x"],
                    "y": bounding_box["y"],
                    "width": bounding_box["width"],
                    "height": bounding_box["height"]
                },
                "center": {
                    "x": center_x,
                    "y": center_y
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting element bounds: {e}")
            return {
                "status": "error",
                "message": str(e),
                "selector": selector
            }
    
    @mcp_tool(
        name="browser_draw_on_canvas",
        description="Draw on a canvas element using mouse movements"
    )
    async def draw_on_canvas(
        self,
        selector: str,
        points: List[Tuple[float, float]],
        draw_speed: int = 10
    ) -> Dict[str, Any]:
        """Draw on a canvas by moving the mouse through points."""
        try:
            if len(points) < 2:
                return {
                    "status": "error",
                    "message": "Need at least 2 points to draw"
                }
            
            # Get canvas bounds
            bounds_result = await self.get_element_bounds(selector)
            if bounds_result["status"] != "success":
                return bounds_result
            
            canvas_x = bounds_result["bounds"]["x"]
            canvas_y = bounds_result["bounds"]["y"]
            
            page = await self.get_current_page()
            
            # Move to first point
            first_x = canvas_x + points[0][0]
            first_y = canvas_y + points[0][1]
            await page.mouse.move(first_x, first_y)
            
            # Press mouse button to start drawing
            await page.mouse.down()
            
            # Draw through all points
            for i, (x, y) in enumerate(points[1:], 1):
                absolute_x = canvas_x + x
                absolute_y = canvas_y + y
                
                # Smooth movement between points
                if draw_speed > 1:
                    prev_x = canvas_x + points[i-1][0]
                    prev_y = canvas_y + points[i-1][1]
                    
                    for step in range(1, draw_speed + 1):
                        progress = step / draw_speed
                        current_x = prev_x + (absolute_x - prev_x) * progress
                        current_y = prev_y + (absolute_y - prev_y) * progress
                        await page.mouse.move(current_x, current_y)
                else:
                    await page.mouse.move(absolute_x, absolute_y)
            
            # Release mouse button
            await page.mouse.up()
            
            logger.info(f"Drew {len(points)} points on canvas")
            
            return {
                "status": "success",
                "selector": selector,
                "points_drawn": len(points),
                "canvas_bounds": bounds_result["bounds"]
            }
            
        except Exception as e:
            logger.error(f"Error drawing on canvas: {e}")
            return {
                "status": "error",
                "message": str(e),
                "selector": selector
            }


from typing import List, Tuple
