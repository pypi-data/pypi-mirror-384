"""
Core Browser Tools for MCPlaywright

Basic browser automation tools with session management and advanced features.
"""

import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime

from pydantic import BaseModel, Field

from ..context import Context
from ..session_manager import get_session_manager
from .video import begin_video_action_for_session, end_video_action_for_session

logger = logging.getLogger(__name__)


# Pydantic models for tool parameters
class NavigateParams(BaseModel):
    """Parameters for browser navigation"""
    url: str = Field(description="URL to navigate to")
    session_id: Optional[str] = Field(None, description="Session ID (auto-generated if not provided)")
    wait_until: Optional[str] = Field("load", description="When to consider navigation complete: 'load', 'domcontentloaded', 'networkidle'")
    timeout: Optional[int] = Field(30000, description="Timeout in milliseconds")


class ScreenshotParams(BaseModel):
    """Parameters for taking screenshots"""
    session_id: Optional[str] = Field(None, description="Session ID")
    filename: Optional[str] = Field(None, description="Screenshot filename (auto-generated if not provided)")
    full_page: Optional[bool] = Field(False, description="Capture full scrollable page")
    clip: Optional[Dict[str, int]] = Field(None, description="Clip region: {x, y, width, height}")
    quality: Optional[int] = Field(None, description="JPEG quality 0-100 (only for JPEG)")
    format: Optional[str] = Field("png", description="Image format: 'png' or 'jpeg'")


class ClickParams(BaseModel):
    """Parameters for clicking elements"""
    session_id: Optional[str] = Field(None, description="Session ID")
    selector: str = Field(description="CSS selector for element to click")
    button: Optional[str] = Field("left", description="Mouse button: 'left', 'right', 'middle'")
    click_count: Optional[int] = Field(1, description="Number of clicks")
    delay: Optional[int] = Field(0, description="Delay between clicks in milliseconds")
    timeout: Optional[int] = Field(30000, description="Timeout waiting for element")


class CloseSessionParams(BaseModel):
    """Parameters for closing browser sessions"""
    session_id: str = Field(description="Session ID to close")


async def get_context_for_session(session_id: Optional[str] = None) -> Context:
    """Helper to get or create browser context for a session"""
    session_manager = get_session_manager()
    context = await session_manager.get_or_create_session(session_id)
    return context


async def browser_navigate(params: NavigateParams) -> Dict[str, Any]:
    """
    Navigate to a URL in the browser.
    
    Navigates to the specified URL and waits for the page to load.
    Creates a new browser session if none exists for the session_id.
    
    Features:
    - Automatic session management
    - Configurable wait conditions  
    - Video recording integration (auto-resume for smart mode)
    - Request monitoring integration
    
    Returns:
        Navigation result with URL, title, and status information
    """
    try:
        # Get browser context
        context = await get_context_for_session(params.session_id)
        
        # Begin video action if recording
        await context.begin_video_action("navigate")
        
        # Get current page
        page = await context.get_current_page()
        
        # Navigate to URL
        logger.info(f"Navigating to {params.url} (session: {context.session_id})")
        
        response = await page.goto(
            params.url,
            wait_until=params.wait_until,
            timeout=params.timeout
        )
        
        # Get page information
        title = await page.title()
        final_url = page.url
        
        # End video action
        await context.end_video_action("navigate")
        
        result = {
            "success": True,
            "url": final_url,
            "requested_url": params.url,
            "title": title,
            "status": response.status if response else None,
            "session_id": context.session_id,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Navigation successful: {title} ({final_url})")
        return result
        
    except Exception as e:
        logger.error(f"Navigation failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "url": params.url,
            "session_id": params.session_id,
            "timestamp": datetime.now().isoformat()
        }


async def browser_screenshot(params: ScreenshotParams) -> Dict[str, Any]:
    """
    Take a screenshot of the current page.
    
    Captures a screenshot of the current page or a specified region.
    Supports full-page screenshots and custom clipping regions.
    
    Features:
    - Full-page or viewport screenshots
    - Custom clip regions
    - Multiple image formats (PNG, JPEG)
    - Automatic filename generation
    - Session-based artifact storage
    
    Returns:
        Screenshot information with file path and metadata
    """
    try:
        # Get browser context
        context = await get_context_for_session(params.session_id)
        
        # Begin video action
        await context.begin_video_action("screenshot")
        
        # Get current page
        page = await context.get_current_page()
        
        # Generate filename if not provided
        if params.filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            params.filename = f"screenshot_{timestamp}.{params.format}"
        
        # Ensure filename has correct extension
        if not params.filename.endswith(f".{params.format}"):
            params.filename += f".{params.format}"
        
        # Create screenshots directory in session artifacts
        screenshots_dir = context.artifacts_dir / "screenshots"
        screenshots_dir.mkdir(exist_ok=True)
        screenshot_path = screenshots_dir / params.filename
        
        # Prepare screenshot options
        screenshot_options = {
            "path": str(screenshot_path),
            "full_page": params.full_page,
            "type": params.format
        }
        
        if params.clip:
            screenshot_options["clip"] = params.clip
            
        if params.quality and params.format == "jpeg":
            screenshot_options["quality"] = params.quality
        
        # Take screenshot
        logger.info(f"Taking screenshot: {params.filename} (session: {context.session_id})")
        
        await page.screenshot(**screenshot_options)
        
        # Get file size
        file_size = screenshot_path.stat().st_size
        
        # End video action
        await context.end_video_action("screenshot")
        
        result = {
            "success": True,
            "filename": params.filename,
            "path": str(screenshot_path),
            "size_bytes": file_size,
            "format": params.format,
            "full_page": params.full_page,
            "session_id": context.session_id,
            "timestamp": datetime.now().isoformat(),
            "page_title": await page.title(),
            "page_url": page.url
        }
        
        logger.info(f"Screenshot saved: {screenshot_path} ({file_size} bytes)")
        return result
        
    except Exception as e:
        logger.error(f"Screenshot failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "filename": params.filename,
            "session_id": params.session_id,
            "timestamp": datetime.now().isoformat()
        }


async def browser_click(params: ClickParams) -> Dict[str, Any]:
    """
    Click on an element in the page.
    
    Clicks on the first element matching the CSS selector.
    Supports different mouse buttons, multiple clicks, and custom delays.
    
    Features:
    - CSS selector-based element targeting
    - Multiple mouse buttons (left, right, middle)
    - Multiple clicks with configurable delays
    - Element visibility and actionability checks
    - Video recording integration
    
    Returns:
        Click result with element information and action status
    """
    try:
        # Get browser context
        context = await get_context_for_session(params.session_id)
        
        # Begin video action
        await context.begin_video_action("click")
        
        # Get current page
        page = await context.get_current_page()
        
        # Find and click element
        logger.info(f"Clicking element '{params.selector}' (session: {context.session_id})")
        
        # Wait for element to be visible and actionable
        await page.wait_for_selector(params.selector, timeout=params.timeout)
        
        # Get element information before clicking
        element = page.locator(params.selector).first
        element_text = await element.text_content() if await element.count() > 0 else ""
        element_tag = await element.evaluate("el => el.tagName.toLowerCase()") if await element.count() > 0 else ""
        
        # Perform click
        await element.click(
            button=params.button,
            click_count=params.click_count,
            delay=params.delay
        )
        
        # Small delay to let any resulting navigation/changes complete
        await asyncio.sleep(0.1)
        
        # End video action
        await context.end_video_action("click")
        
        result = {
            "success": True,
            "selector": params.selector,
            "button": params.button,
            "click_count": params.click_count,
            "element_text": element_text,
            "element_tag": element_tag,
            "session_id": context.session_id,
            "timestamp": datetime.now().isoformat(),
            "page_url": page.url
        }
        
        logger.info(f"Click successful on {element_tag} element: '{element_text[:50]}'")
        return result
        
    except Exception as e:
        logger.error(f"Click failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "selector": params.selector,
            "session_id": params.session_id,
            "timestamp": datetime.now().isoformat()
        }


async def browser_close_session(params: CloseSessionParams) -> Dict[str, Any]:
    """
    Close a browser session and clean up resources.
    
    Closes the browser context, stops any video recordings,
    and cleans up all associated resources for the session.
    
    Features:
    - Complete resource cleanup
    - Video recording finalization
    - Session artifact preservation
    - Graceful error handling
    
    Returns:
        Session closure result with cleanup information
    """
    try:
        session_manager = get_session_manager()
        
        # Check if session exists
        if params.session_id not in session_manager:
            return {
                "success": False,
                "error": f"Session {params.session_id} not found",
                "session_id": params.session_id,
                "timestamp": datetime.now().isoformat()
            }
        
        # Get context for final video/artifact handling
        context = await session_manager.get_session(params.session_id)
        video_files = []
        
        if context:
            # Stop video recording if active
            if context._video_config:
                video_files = await context.stop_video_recording()
            
            # Get session info for response
            session_info = context.get_session_info()
        else:
            session_info = {"session_id": params.session_id}
        
        # Remove session (this handles cleanup)
        cleanup_success = await session_manager.remove_session(params.session_id)
        
        result = {
            "success": cleanup_success,
            "session_id": params.session_id,
            "session_info": session_info,
            "video_files": video_files,
            "timestamp": datetime.now().isoformat()
        }
        
        if cleanup_success:
            logger.info(f"Session closed successfully: {params.session_id}")
        else:
            logger.warning(f"Session cleanup had issues: {params.session_id}")
            result["warning"] = "Session cleanup had issues but session was removed"
        
        return result
        
    except Exception as e:
        logger.error(f"Session close failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "session_id": params.session_id,
            "timestamp": datetime.now().isoformat()
        }


async def browser_get_page_info(session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Get information about the current page.
    
    Returns comprehensive information about the current page
    including title, URL, viewport size, and loading state.
    
    Returns:
        Page information and metadata
    """
    try:
        context = await get_context_for_session(session_id)
        page = await context.get_current_page()
        
        # Get page information
        title = await page.title()
        url = page.url
        
        # Get viewport size
        viewport = await page.evaluate("() => ({width: window.innerWidth, height: window.innerHeight})")
        
        # Get loading state
        ready_state = await page.evaluate("() => document.readyState")
        
        result = {
            "success": True,
            "title": title,
            "url": url,
            "viewport": viewport,
            "ready_state": ready_state,
            "session_id": context.session_id,
            "timestamp": datetime.now().isoformat()
        }
        
        return result
        
    except Exception as e:
        logger.error(f"Get page info failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }