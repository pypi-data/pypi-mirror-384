"""
Advanced Coordinate-Based Mouse Tools with Mathematical Precision

Implements sophisticated mouse automation with subpixel precision, mathematical
interpolation, bezier curves, and complex gesture patterns.
"""

import math
from typing import Dict, Any, List, Optional, Literal
from pydantic import BaseModel, Field
from playwright.async_api import Page

from ..context import Context

# Mathematical interpolation functions
def smooth_step(t: float) -> float:
    """Hermite interpolation for smooth easing"""
    return t * t * (3.0 - 2.0 * t)

def cubic_bezier(t: float, p0: float, p1: float, p2: float, p3: float) -> float:
    """Cubic bezier curve interpolation"""
    u = 1 - t
    return (u**3 * p0 + 3 * u**2 * t * p1 + 3 * u * t**2 * p2 + t**3 * p3)

def quadratic_bezier(t: float, p0: float, p1: float, p2: float) -> float:
    """Quadratic bezier curve interpolation"""
    u = 1 - t
    return u**2 * p0 + 2 * u * t * p1 + t**2 * p2

class MousePoint(BaseModel):
    """Advanced mouse point with action and timing control"""
    x: float = Field(description="X coordinate (supports subpixel precision)")
    y: float = Field(description="Y coordinate (supports subpixel precision)")
    delay: int = Field(default=0, ge=0, le=5000, description="Delay at this point in milliseconds")
    action: Literal['move', 'click', 'down', 'up'] = Field(default='move', description="Action to perform at this point")

class AdvancedMouseMoveParams(BaseModel):
    """Parameters for advanced mouse movement with precision control"""
    x: float = Field(description="Target X coordinate")
    y: float = Field(description="Target Y coordinate")
    precision: Literal['pixel', 'subpixel'] = Field(default='pixel', description="Coordinate precision level")
    delay: int = Field(default=0, ge=0, le=5000, description="Delay before movement in milliseconds")
    easing: Literal['linear', 'smooth', 'ease_in', 'ease_out'] = Field(default='linear', description="Movement easing function")
    duration: int = Field(default=0, ge=0, le=5000, description="Movement duration in milliseconds (0 = instant)")

class AdvancedMouseClickParams(BaseModel):
    """Parameters for advanced mouse clicking with timing and precision"""
    x: float = Field(description="Click X coordinate")
    y: float = Field(description="Click Y coordinate")
    button: Literal['left', 'right', 'middle'] = Field(default='left', description="Mouse button to click")
    click_count: int = Field(default=1, ge=1, le=3, description="Number of clicks (1=single, 2=double, 3=triple)")
    precision: Literal['pixel', 'subpixel'] = Field(default='pixel', description="Coordinate precision level")
    hold_time: int = Field(default=0, ge=0, le=2000, description="How long to hold button down in milliseconds")
    delay: int = Field(default=0, ge=0, le=5000, description="Delay before click in milliseconds")

class AdvancedMouseDragParams(BaseModel):
    """Parameters for advanced mouse dragging with mathematical interpolation"""
    start_x: float = Field(description="Start X coordinate")
    start_y: float = Field(description="Start Y coordinate")
    end_x: float = Field(description="End X coordinate")
    end_y: float = Field(description="End Y coordinate")
    button: Literal['left', 'right', 'middle'] = Field(default='left', description="Mouse button to drag with")
    precision: Literal['pixel', 'subpixel'] = Field(default='pixel', description="Coordinate precision level")
    pattern: Literal['direct', 'smooth', 'bezier', 'arc'] = Field(default='direct', description="Drag movement pattern")
    steps: int = Field(default=10, ge=1, le=50, description="Number of intermediate steps for smooth patterns")
    duration: Optional[int] = Field(default=None, ge=100, le=10000, description="Total drag duration in milliseconds")
    delay: int = Field(default=0, ge=0, le=5000, description="Delay before starting drag")
    control_point_offset: float = Field(default=0.2, ge=0.0, le=1.0, description="Control point offset for bezier curves")

class MouseScrollParams(BaseModel):
    """Parameters for precise mouse scrolling"""
    x: float = Field(description="Scroll X coordinate")
    y: float = Field(description="Scroll Y coordinate")
    delta_x: float = Field(default=0, description="Horizontal scroll amount (positive = right, negative = left)")
    delta_y: float = Field(description="Vertical scroll amount (positive = down, negative = up)")
    precision: Literal['pixel', 'subpixel'] = Field(default='pixel', description="Coordinate precision level")
    smooth: bool = Field(default=False, description="Use smooth scrolling animation")
    delay: int = Field(default=0, ge=0, le=5000, description="Delay before scrolling")

class MouseGestureParams(BaseModel):
    """Parameters for complex mouse gestures with multiple waypoints"""
    points: List[MousePoint] = Field(min_length=2, description="Array of points defining the gesture path")
    button: Literal['left', 'right', 'middle'] = Field(default='left', description="Mouse button for click actions")
    precision: Literal['pixel', 'subpixel'] = Field(default='pixel', description="Coordinate precision level")
    smooth_path: bool = Field(default=False, description="Smooth the path between points")
    interpolation_steps: int = Field(default=5, ge=1, le=20, description="Steps for path smoothing")

async def browser_advanced_mouse_move(
    context: Context,
    params: AdvancedMouseMoveParams
) -> Dict[str, Any]:
    """
    Advanced mouse movement with subpixel precision and mathematical easing.
    
    Features mathematical interpolation for natural movement patterns including
    linear, smooth hermite, ease-in, and ease-out transitions. Supports both
    pixel and subpixel coordinate precision for ultra-accurate positioning.
    """
    
    page = await context.get_current_page()
    
    # Apply delay if specified
    if params.delay > 0:
        await page.wait_for_timeout(params.delay)
    
    # Get current mouse position for easing calculations
    current_pos = await page.evaluate("() => ({ x: 0, y: 0 })") # Playwright doesn't expose current position
    
    if params.duration > 0 and params.easing != 'linear':
        # Perform smooth movement with easing
        steps = max(5, params.duration // 50)  # ~20 FPS for smooth movement
        step_delay = params.duration / steps
        
        for i in range(1, steps + 1):
            t = i / steps
            
            # Apply easing function
            if params.easing == 'smooth':
                t = smooth_step(t)
            elif params.easing == 'ease_in':
                t = t * t
            elif params.easing == 'ease_out':
                t = 1 - (1 - t) ** 2
            
            # Calculate intermediate position
            x = current_pos.get('x', 0) + (params.x - current_pos.get('x', 0)) * t
            y = current_pos.get('y', 0) + (params.y - current_pos.get('y', 0)) * t
            
            # Move to intermediate position
            await page.mouse.move(x, y)
            
            if step_delay > 0:
                await page.wait_for_timeout(int(step_delay))
    else:
        # Direct movement
        await page.mouse.move(params.x, params.y)
    
    # Format coordinates for response
    coords = f"{params.x:.2f}, {params.y:.2f}" if params.precision == 'subpixel' else f"{round(params.x)}, {round(params.y)}"
    easing_info = f" with {params.easing} easing" if params.duration > 0 and params.easing != 'linear' else ""
    
    return {
        "status": "mouse_moved",
        "coordinates": {"x": params.x, "y": params.y},
        "precision": params.precision,
        "easing": params.easing,
        "duration": params.duration,
        "description": f"Moved mouse to ({coords}){easing_info}"
    }

async def browser_advanced_mouse_click(
    context: Context,
    params: AdvancedMouseClickParams
) -> Dict[str, Any]:
    """
    Advanced mouse clicking with precision timing and multi-click support.
    
    Supports single, double, and triple clicks with configurable hold times,
    subpixel coordinate precision, and advanced timing control for complex
    interaction patterns.
    """
    
    page = await context.get_current_page()
    
    # Apply delay if specified
    if params.delay > 0:
        await page.wait_for_timeout(params.delay)
    
    # Move to position first
    await page.mouse.move(params.x, params.y)
    
    # Perform click action based on type
    if params.click_count == 1:
        # Single click with optional hold time
        await page.mouse.down(button=params.button)
        if params.hold_time > 0:
            await page.wait_for_timeout(params.hold_time)
        await page.mouse.up(button=params.button)
    else:
        # Multi-click (double/triple)
        await page.mouse.click(params.x, params.y, button=params.button, click_count=params.click_count)
    
    # Format response
    coords = f"{params.x:.2f}, {params.y:.2f}" if params.precision == 'subpixel' else f"{round(params.x)}, {round(params.y)}"
    click_type = {1: 'single', 2: 'double', 3: 'triple'}[params.click_count]
    hold_info = f" (held {params.hold_time}ms)" if params.hold_time > 0 else ""
    
    return {
        "status": "mouse_clicked",
        "coordinates": {"x": params.x, "y": params.y},
        "button": params.button,
        "click_count": params.click_count,
        "hold_time": params.hold_time,
        "precision": params.precision,
        "description": f"{click_type.capitalize()} {params.button} click at ({coords}){hold_info}"
    }

async def browser_advanced_mouse_drag(
    context: Context,
    params: AdvancedMouseDragParams
) -> Dict[str, Any]:
    """
    Advanced mouse dragging with mathematical interpolation patterns.
    
    Supports multiple drag patterns including direct, smooth hermite interpolation,
    bezier curves, and arc movements. Features subpixel precision and configurable
    timing for natural, human-like mouse movements.
    """
    
    page = await context.get_current_page()
    
    # Apply delay if specified
    if params.delay > 0:
        await page.wait_for_timeout(params.delay)
    
    # Move to start position and begin drag
    await page.mouse.move(params.start_x, params.start_y)
    await page.mouse.down(button=params.button)
    
    if params.pattern == 'direct':
        # Direct drag to end position
        await page.mouse.move(params.end_x, params.end_y)
    else:
        # Advanced interpolated drag
        step_delay = (params.duration or 500) / params.steps
        
        for i in range(1, params.steps + 1):
            t = i / params.steps
            x, y = params.start_x, params.start_y
            
            if params.pattern == 'smooth':
                # Smooth hermite interpolation
                t_smooth = smooth_step(t)
                x = params.start_x + (params.end_x - params.start_x) * t_smooth
                y = params.start_y + (params.end_y - params.start_y) * t_smooth
                
            elif params.pattern == 'bezier':
                # Quadratic bezier curve with automatic control point
                control_x = (params.start_x + params.end_x) / 2
                control_y = min(params.start_y, params.end_y) - abs(params.end_x - params.start_x) * params.control_point_offset
                
                x = quadratic_bezier(t, params.start_x, control_x, params.end_x)
                y = quadratic_bezier(t, params.start_y, control_y, params.end_y)
                
            elif params.pattern == 'arc':
                # Arc movement using trigonometric functions
                center_x = (params.start_x + params.end_x) / 2
                center_y = (params.start_y + params.end_y) / 2
                radius = math.sqrt((params.end_x - params.start_x)**2 + (params.end_y - params.start_y)**2) / 2
                
                start_angle = math.atan2(params.start_y - center_y, params.start_x - center_x)
                end_angle = math.atan2(params.end_y - center_y, params.end_x - center_x)
                angle = start_angle + (end_angle - start_angle) * t
                
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
            
            # Move to calculated position
            await page.mouse.move(x, y)
            
            if step_delay > 0:
                await page.wait_for_timeout(int(step_delay))
    
    # Release mouse button
    await page.mouse.up(button=params.button)
    
    # Format response
    start_coords = f"{params.start_x:.2f}, {params.start_y:.2f}" if params.precision == 'subpixel' else f"{round(params.start_x)}, {round(params.start_y)}"
    end_coords = f"{params.end_x:.2f}, {params.end_y:.2f}" if params.precision == 'subpixel' else f"{round(params.end_x)}, {round(params.end_y)}"
    
    return {
        "status": "mouse_dragged",
        "start_coordinates": {"x": params.start_x, "y": params.start_y},
        "end_coordinates": {"x": params.end_x, "y": params.end_y},
        "button": params.button,
        "pattern": params.pattern,
        "steps": params.steps,
        "duration": params.duration,
        "precision": params.precision,
        "description": f"Dragged {params.button} mouse from ({start_coords}) to ({end_coords}) using {params.pattern} pattern"
    }

async def browser_advanced_mouse_scroll(
    context: Context,
    params: MouseScrollParams
) -> Dict[str, Any]:
    """
    Precise mouse scrolling with smooth animation support.
    
    Provides accurate scrolling control with optional smooth animation for
    large scroll distances. Supports both horizontal and vertical scrolling
    with subpixel coordinate precision.
    """
    
    page = await context.get_current_page()
    
    # Apply delay if specified
    if params.delay > 0:
        await page.wait_for_timeout(params.delay)
    
    # Move to scroll position
    await page.mouse.move(params.x, params.y)
    
    if params.smooth and abs(params.delta_y) > 100:
        # Break large scrolls into smooth steps
        steps = min(10, int(abs(params.delta_y) / 50))
        step_x = params.delta_x / steps
        step_y = params.delta_y / steps
        
        for _ in range(steps):
            await page.mouse.wheel(step_x, step_y)
            await page.wait_for_timeout(50)  # Small delay for smoothness
    else:
        # Direct scroll
        await page.mouse.wheel(params.delta_x, params.delta_y)
    
    # Format response
    coords = f"{params.x:.2f}, {params.y:.2f}" if params.precision == 'subpixel' else f"{round(params.x)}, {round(params.y)}"
    scroll_info = f"deltaX={params.delta_x}, deltaY={params.delta_y}"
    smooth_info = " (smooth)" if params.smooth else ""
    
    return {
        "status": "mouse_scrolled",
        "coordinates": {"x": params.x, "y": params.y},
        "delta": {"x": params.delta_x, "y": params.delta_y},
        "smooth": params.smooth,
        "precision": params.precision,
        "description": f"Scrolled at ({coords}): {scroll_info}{smooth_info}"
    }

async def browser_advanced_mouse_gesture(
    context: Context,
    params: MouseGestureParams
) -> Dict[str, Any]:
    """
    Complex mouse gestures with multiple waypoints and path smoothing.
    
    Enables sophisticated mouse automation with custom gesture patterns,
    multiple action points, and optional path interpolation for natural
    movement between waypoints.
    """
    
    page = await context.get_current_page()
    
    gesture_actions = []
    
    for i, point in enumerate(params.points):
        if params.smooth_path and i > 0:
            # Smooth path between previous and current point
            prev_point = params.points[i - 1]
            
            for step in range(1, params.interpolation_steps + 1):
                t = step / params.interpolation_steps
                t_smooth = smooth_step(t)
                
                x = prev_point.x + (point.x - prev_point.x) * t_smooth
                y = prev_point.y + (point.y - prev_point.y) * t_smooth
                
                await page.mouse.move(x, y)
                await page.wait_for_timeout(20)  # Small delay for smooth movement
        else:
            # Direct movement to point
            await page.mouse.move(point.x, point.y)
        
        # Perform action at this point
        coords = f"{point.x:.2f}, {point.y:.2f}" if params.precision == 'subpixel' else f"{round(point.x)}, {round(point.y)}"
        
        if point.action == 'click':
            await page.mouse.click(point.x, point.y, button=params.button)
            gesture_actions.append(f"Point {i + 1}: Click at ({coords})")
        elif point.action == 'down':
            await page.mouse.down(button=params.button)
            gesture_actions.append(f"Point {i + 1}: Mouse down at ({coords})")
        elif point.action == 'up':
            await page.mouse.up(button=params.button)
            gesture_actions.append(f"Point {i + 1}: Mouse up at ({coords})")
        else:  # 'move'
            gesture_actions.append(f"Point {i + 1}: Move to ({coords})")
        
        # Apply point-specific delay
        if point.delay > 0:
            await page.wait_for_timeout(point.delay)
    
    return {
        "status": "gesture_completed",
        "point_count": len(params.points),
        "button": params.button,
        "smooth_path": params.smooth_path,
        "precision": params.precision,
        "actions": gesture_actions,
        "description": f"Completed gesture with {len(params.points)} points{' (smooth path)' if params.smooth_path else ''}"
    }