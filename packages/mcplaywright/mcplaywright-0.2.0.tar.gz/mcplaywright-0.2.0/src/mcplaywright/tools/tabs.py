"""
Tab Management Tools for MCPlaywright

Advanced tab management with session isolation and smart recording integration.
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ..session_manager import get_session_manager
from .video import begin_video_action_for_session, end_video_action_for_session

logger = logging.getLogger(__name__)


class NewTabParams(BaseModel):
    """Parameters for opening new tabs"""
    session_id: Optional[str] = Field(None, description="Session ID")
    url: Optional[str] = Field(None, description="URL to navigate to in new tab")


class CloseTabParams(BaseModel):
    """Parameters for closing tabs"""
    session_id: Optional[str] = Field(None, description="Session ID")
    tab_index: Optional[int] = Field(None, description="Tab index to close (current tab if not specified)")


class SwitchTabParams(BaseModel):
    """Parameters for switching tabs"""
    session_id: Optional[str] = Field(None, description="Session ID")
    tab_index: int = Field(description="Tab index to switch to")


class TabListParams(BaseModel):
    """Parameters for listing tabs"""
    session_id: Optional[str] = Field(None, description="Session ID")


async def browser_new_tab(params: NewTabParams) -> Dict[str, Any]:
    """
    Open a new tab and optionally navigate to URL.
    
    Creates a new page in the current browser context and switches to it.
    Supports optional navigation to a specific URL after creation.
    
    Features:
    - New page creation with automatic focus switching
    - Optional URL navigation in new tab
    - Session-based tab management
    - Video recording integration
    
    Returns:
        New tab creation result with tab information
    """
    try:
        session_manager = get_session_manager()
        context = await session_manager.get_or_create_session(params.session_id)
        
        # Begin video action
        await context.begin_video_action("new_tab")
        
        # Create new page
        logger.info(f"Creating new tab (session: {context.session_id})")
        page = await context.browser_context.new_page()
        
        # Set as current page
        context.set_current_page(page)
        
        # Navigate to URL if provided
        page_info = {"url": "about:blank", "title": "New Tab"}
        if params.url:
            logger.info(f"Navigating new tab to {params.url}")
            response = await page.goto(params.url, wait_until="load")
            page_info = {
                "url": page.url,
                "title": await page.title(),
                "status": response.status if response else None
            }
        
        # Get all pages for tab list
        all_pages = context.browser_context.pages
        tab_index = len(all_pages) - 1
        
        # End video action
        await context.end_video_action("new_tab")
        
        result = {
            "success": True,
            "tab_index": tab_index,
            "tab_count": len(all_pages),
            "page_info": page_info,
            "session_id": context.session_id,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"New tab created: index {tab_index}, URL {page_info['url']}")
        return result
        
    except Exception as e:
        logger.error(f"New tab creation failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "session_id": params.session_id,
            "timestamp": datetime.now().isoformat()
        }


async def browser_close_tab(params: CloseTabParams) -> Dict[str, Any]:
    """
    Close a browser tab by index.
    
    Closes the specified tab or current tab if no index provided.
    Automatically switches to another tab if the current tab is closed.
    
    Features:
    - Close specific tab by index or current tab
    - Automatic tab switching when current tab is closed
    - Session state management
    - Video recording integration
    
    Returns:
        Tab closure result with updated tab information
    """
    try:
        session_manager = get_session_manager()
        context = await session_manager.get_session(params.session_id)
        
        if not context:
            return {
                "success": False,
                "error": f"Session {params.session_id} not found",
                "session_id": params.session_id,
                "timestamp": datetime.now().isoformat()
            }
        
        # Begin video action
        await context.begin_video_action("close_tab")
        
        all_pages = context.browser_context.pages
        
        if not all_pages:
            return {
                "success": False,
                "error": "No tabs available to close",
                "session_id": context.session_id,
                "timestamp": datetime.now().isoformat()
            }
        
        # Determine which tab to close
        if params.tab_index is not None:
            if params.tab_index < 0 or params.tab_index >= len(all_pages):
                return {
                    "success": False,
                    "error": f"Tab index {params.tab_index} out of range (0-{len(all_pages)-1})",
                    "session_id": context.session_id,
                    "timestamp": datetime.now().isoformat()
                }
            page_to_close = all_pages[params.tab_index]
            closed_index = params.tab_index
        else:
            # Close current page
            page_to_close = await context.get_current_page()
            closed_index = all_pages.index(page_to_close)
        
        # Get page info before closing
        closed_page_info = {
            "url": page_to_close.url,
            "title": await page_to_close.title(),
            "index": closed_index
        }
        
        # Close the page
        logger.info(f"Closing tab {closed_index}: {closed_page_info['title']}")
        await page_to_close.close()
        
        # Update page list
        remaining_pages = context.browser_context.pages
        
        # Switch to another page if we closed the current page
        if remaining_pages and page_to_close == context._current_page:
            # Switch to the next available tab (or previous if we closed the last one)
            new_index = min(closed_index, len(remaining_pages) - 1)
            new_current_page = remaining_pages[new_index]
            context.set_current_page(new_current_page)
            
            new_page_info = {
                "url": new_current_page.url,
                "title": await new_current_page.title(),
                "index": new_index
            }
        else:
            new_page_info = None
        
        # End video action
        await context.end_video_action("close_tab")
        
        result = {
            "success": True,
            "closed_tab": closed_page_info,
            "current_tab": new_page_info,
            "remaining_tabs": len(remaining_pages),
            "session_id": context.session_id,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Tab closed: {closed_page_info['title']}, {len(remaining_pages)} tabs remaining")
        return result
        
    except Exception as e:
        logger.error(f"Close tab failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "session_id": params.session_id,
            "timestamp": datetime.now().isoformat()
        }


async def browser_switch_tab(params: SwitchTabParams) -> Dict[str, Any]:
    """
    Switch to a different browser tab by index.
    
    Changes the active tab to the specified index and updates the current page.
    Provides information about the newly active tab.
    
    Features:
    - Switch to tab by index
    - Automatic current page updating
    - Tab state validation
    - Video recording integration
    
    Returns:
        Tab switching result with new active tab information
    """
    try:
        session_manager = get_session_manager()
        context = await session_manager.get_session(params.session_id)
        
        if not context:
            return {
                "success": False,
                "error": f"Session {params.session_id} not found",
                "session_id": params.session_id,
                "timestamp": datetime.now().isoformat()
            }
        
        # Begin video action
        await context.begin_video_action("switch_tab")
        
        all_pages = context.browser_context.pages
        
        if not all_pages:
            return {
                "success": False,
                "error": "No tabs available",
                "session_id": context.session_id,
                "timestamp": datetime.now().isoformat()
            }
        
        # Validate tab index
        if params.tab_index < 0 or params.tab_index >= len(all_pages):
            return {
                "success": False,
                "error": f"Tab index {params.tab_index} out of range (0-{len(all_pages)-1})",
                "session_id": context.session_id,
                "timestamp": datetime.now().isoformat()
            }
        
        # Get the target page
        target_page = all_pages[params.tab_index]
        
        # Update current page
        context.set_current_page(target_page)
        
        # Bring the page to front
        await target_page.bring_to_front()
        
        # Get page information
        page_info = {
            "url": target_page.url,
            "title": await target_page.title(),
            "index": params.tab_index,
            "ready_state": await target_page.evaluate("() => document.readyState")
        }
        
        # End video action
        await context.end_video_action("switch_tab")
        
        result = {
            "success": True,
            "active_tab": page_info,
            "total_tabs": len(all_pages),
            "session_id": context.session_id,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Switched to tab {params.tab_index}: {page_info['title']}")
        return result
        
    except Exception as e:
        logger.error(f"Switch tab failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "session_id": params.session_id,
            "timestamp": datetime.now().isoformat()
        }


async def browser_list_tabs(params: TabListParams) -> Dict[str, Any]:
    """
    List all open browser tabs with detailed information.
    
    Returns comprehensive information about all tabs in the current session,
    including URLs, titles, and current active tab.
    
    Features:
    - Complete tab inventory
    - Active tab identification
    - Page state information
    - Session context awareness
    
    Returns:
        Tab list with detailed information for each tab
    """
    try:
        session_manager = get_session_manager()
        context = await session_manager.get_session(params.session_id)
        
        if not context:
            return {
                "success": False,
                "error": f"Session {params.session_id} not found",
                "session_id": params.session_id,
                "timestamp": datetime.now().isoformat()
            }
        
        all_pages = context.browser_context.pages
        current_page = context._current_page
        
        # Gather information about each tab
        tab_list = []
        current_tab_index = -1
        
        for index, page in enumerate(all_pages):
            try:
                tab_info = {
                    "index": index,
                    "url": page.url,
                    "title": await page.title(),
                    "ready_state": await page.evaluate("() => document.readyState"),
                    "is_current": page == current_page
                }
                
                if page == current_page:
                    current_tab_index = index
                
                tab_list.append(tab_info)
                
            except Exception as e:
                # Handle closed or invalid pages
                tab_list.append({
                    "index": index,
                    "url": "about:blank",
                    "title": "Closed Tab",
                    "ready_state": "complete",
                    "is_current": False,
                    "error": str(e)
                })
        
        result = {
            "success": True,
            "tabs": tab_list,
            "total_tabs": len(all_pages),
            "current_tab_index": current_tab_index,
            "session_id": context.session_id,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Listed {len(tab_list)} tabs, current tab: {current_tab_index}")
        return result
        
    except Exception as e:
        logger.error(f"List tabs failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "session_id": params.session_id,
            "timestamp": datetime.now().isoformat()
        }