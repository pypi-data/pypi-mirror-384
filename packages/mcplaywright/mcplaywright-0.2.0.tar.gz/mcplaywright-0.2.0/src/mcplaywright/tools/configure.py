"""
Browser Configuration Tools for MCPlaywright

Tools for configuring browser behavior, UI customization, and session settings.
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

from pydantic import BaseModel, Field

from ..context import BrowserConfig, BrowserType
from ..session_manager import get_session_manager

logger = logging.getLogger(__name__)


class BrowserConfigureParams(BaseModel):
    """Parameters for browser configuration"""
    session_id: Optional[str] = Field(None, description="Session ID (auto-generated if not provided)")
    
    # Basic browser settings
    browser_type: Optional[str] = Field(None, description="Browser type: 'chromium', 'firefox', 'webkit'")
    headless: Optional[bool] = Field(None, description="Run browser in headless mode")
    
    # Viewport settings
    viewport_width: Optional[int] = Field(None, description="Browser viewport width")
    viewport_height: Optional[int] = Field(None, description="Browser viewport height")
    
    # UI Customization (ported from TypeScript implementation)
    slow_mo: Optional[int] = Field(None, description="Milliseconds delay between actions for visual demonstration")
    devtools: Optional[bool] = Field(None, description="Open Chrome DevTools automatically")
    args: Optional[List[str]] = Field(None, description="Custom browser launch arguments")
    chromium_sandbox: Optional[bool] = Field(None, description="Enable/disable Chromium sandbox")
    
    # Localization and preferences
    user_agent: Optional[str] = Field(None, description="Custom user agent string")
    locale: Optional[str] = Field(None, description="Browser locale (e.g., 'en-US', 'fr-FR')")
    timezone: Optional[str] = Field(None, description="Timezone ID (e.g., 'America/New_York')")
    color_scheme: Optional[str] = Field(None, description="Preferred color scheme: 'light', 'dark', 'no-preference'")
    
    # Geolocation
    latitude: Optional[float] = Field(None, description="Geolocation latitude")
    longitude: Optional[float] = Field(None, description="Geolocation longitude")
    accuracy: Optional[float] = Field(100, description="Geolocation accuracy in meters")
    
    # Permissions
    permissions: Optional[List[str]] = Field(None, description="Permissions to grant (e.g., ['geolocation', 'notifications'])")
    
    # Network settings
    offline: Optional[bool] = Field(None, description="Enable offline mode")


class SessionListParams(BaseModel):
    """Parameters for listing sessions"""
    include_details: Optional[bool] = Field(False, description="Include detailed session information")


async def browser_configure(params: BrowserConfigureParams) -> Dict[str, Any]:
    """
    Configure browser settings and behavior.
    
    Updates browser configuration including UI customization, viewport settings,
    localization, permissions, and other browser options. Creates a new session
    if none exists.
    
    Key Features:
    - UI customization (slowMo for demos, devtools, custom args)
    - Viewport and display settings
    - Localization and timezone configuration  
    - Geolocation and permissions management
    - Network settings (offline mode)
    - Browser type switching
    
    This tool ports the advanced configuration capabilities from the TypeScript
    implementation, including the novel UI customization features.
    
    Returns:
        Configuration update result with applied settings
    """
    try:
        # Get browser context (creates session if needed)
        session_manager = get_session_manager()
        context = await session_manager.get_or_create_session(params.session_id)
        
        # Build configuration updates
        config_updates = {}
        
        # Basic browser settings
        if params.browser_type is not None:
            try:
                browser_type = BrowserType(params.browser_type.lower())
                config_updates["browser_type"] = browser_type
            except ValueError:
                return {
                    "success": False,
                    "error": f"Invalid browser type: {params.browser_type}. Must be 'chromium', 'firefox', or 'webkit'",
                    "session_id": context.session_id
                }
        
        if params.headless is not None:
            config_updates["headless"] = params.headless
        
        # Viewport settings
        if params.viewport_width is not None or params.viewport_height is not None:
            current_viewport = context.config.viewport.copy()
            if params.viewport_width is not None:
                current_viewport["width"] = params.viewport_width
            if params.viewport_height is not None:
                current_viewport["height"] = params.viewport_height
            config_updates["viewport"] = current_viewport
        
        # UI Customization (novel features from TypeScript implementation)
        if params.slow_mo is not None:
            config_updates["slow_mo"] = params.slow_mo
            
        if params.devtools is not None:
            config_updates["devtools"] = params.devtools
            
        if params.args is not None:
            config_updates["args"] = params.args
            
        if params.chromium_sandbox is not None:
            config_updates["chromium_sandbox"] = params.chromium_sandbox
        
        # Localization
        if params.user_agent is not None:
            config_updates["user_agent"] = params.user_agent
            
        if params.locale is not None:
            config_updates["locale"] = params.locale
            
        if params.timezone is not None:
            config_updates["timezone"] = params.timezone
            
        if params.color_scheme is not None:
            config_updates["color_scheme"] = params.color_scheme
        
        # Geolocation
        if any([params.latitude is not None, params.longitude is not None]):
            if params.latitude is not None and params.longitude is not None:
                geolocation = {
                    "latitude": params.latitude,
                    "longitude": params.longitude,
                    "accuracy": params.accuracy or 100
                }
                config_updates["geolocation"] = geolocation
            else:
                return {
                    "success": False,
                    "error": "Both latitude and longitude must be provided for geolocation",
                    "session_id": context.session_id
                }
        
        # Permissions
        if params.permissions is not None:
            config_updates["permissions"] = params.permissions
        
        # Network settings
        if params.offline is not None:
            config_updates["offline"] = params.offline
        
        # Apply configuration updates
        if config_updates:
            logger.info(f"Updating browser config for session {context.session_id}: {list(config_updates.keys())}")
            await context.update_browser_config(config_updates)
        
        # Get current configuration for response
        current_config = {
            "browser_type": context.config.browser_type.value,
            "headless": context.config.headless,
            "viewport": context.config.viewport,
            "slow_mo": context.config.slow_mo,
            "devtools": context.config.devtools,
            "args": context.config.args,
            "chromium_sandbox": context.config.chromium_sandbox,
            "user_agent": context.config.user_agent,
            "locale": context.config.locale,
            "timezone": context.config.timezone,
            "color_scheme": context.config.color_scheme,
            "geolocation": context.config.geolocation,
            "permissions": context.config.permissions,
            "offline": context.config.offline
        }
        
        result = {
            "success": True,
            "session_id": context.session_id,
            "updates_applied": list(config_updates.keys()),
            "current_config": current_config,
            "timestamp": datetime.now().isoformat()
        }
        
        # Add helpful messages for UI customization features
        if "slow_mo" in config_updates:
            result["slow_mo_info"] = f"Actions will have {params.slow_mo}ms delays (great for demo recordings)"
        
        if "devtools" in config_updates and params.devtools:
            result["devtools_info"] = "Chrome DevTools will open automatically"
        
        if "args" in config_updates:
            result["args_info"] = f"Applied {len(params.args)} custom browser arguments"
        
        logger.info(f"Browser configuration updated for session {context.session_id}")
        return result
        
    except Exception as e:
        logger.error(f"Browser configuration failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "session_id": params.session_id,
            "timestamp": datetime.now().isoformat()
        }


async def browser_list_sessions(params: SessionListParams) -> Dict[str, Any]:
    """
    List all active browser sessions.
    
    Returns information about all active browser sessions including
    session IDs, creation times, activity status, and optionally
    detailed configuration and state information.
    
    Features:
    - Session overview with basic statistics
    - Optional detailed session information
    - Video recording and request monitoring status
    - Resource usage information
    
    Returns:
        List of active sessions with metadata
    """
    try:
        session_manager = get_session_manager()
        
        # Get session statistics
        stats = await session_manager.get_session_stats()
        
        # Get session list
        if params.include_details:
            sessions = await session_manager.list_sessions()
        else:
            # Basic session info only
            sessions = []
            for session_id in session_manager.sessions.keys():
                try:
                    context = session_manager.sessions[session_id]
                    sessions.append({
                        "session_id": session_id,
                        "created_at": context._created_at.isoformat(),
                        "last_activity": context._last_activity.isoformat(),
                        "browser_type": context.config.browser_type.value,
                        "headless": context.config.headless,
                        "pages": len(context._pages),
                        "video_recording": context._video_config is not None,
                        "request_monitoring": context._request_monitoring_enabled
                    })
                except Exception as e:
                    sessions.append({
                        "session_id": session_id,
                        "error": str(e),
                        "status": "error"
                    })
        
        result = {
            "success": True,
            "session_count": len(sessions),
            "sessions": sessions,
            "statistics": stats,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Listed {len(sessions)} active sessions")
        return result
        
    except Exception as e:
        logger.error(f"List sessions failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


async def browser_get_session_info(session_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific session.
    
    Returns comprehensive information about the browser session including
    configuration, state, video recording status, request monitoring,
    and resource usage.
    
    Returns:
        Detailed session information and metadata
    """
    try:
        session_manager = get_session_manager()
        
        # Check if session exists
        context = await session_manager.get_session(session_id)
        if not context:
            return {
                "success": False,
                "error": f"Session {session_id} not found",
                "session_id": session_id,
                "timestamp": datetime.now().isoformat()
            }
        
        # Get comprehensive session info
        session_info = context.get_session_info()
        
        # Add configuration details
        config_info = {
            "browser_type": context.config.browser_type.value,
            "headless": context.config.headless,
            "viewport": context.config.viewport,
            "slow_mo": context.config.slow_mo,
            "devtools": context.config.devtools,
            "args": context.config.args,
            "user_agent": context.config.user_agent,
            "locale": context.config.locale,
            "timezone": context.config.timezone,
            "permissions": context.config.permissions,
            "offline": context.config.offline
        }
        
        result = {
            "success": True,
            "session_info": session_info,
            "configuration": config_info,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"Retrieved session info for {session_id}")
        return result
        
    except Exception as e:
        logger.error(f"Get session info failed: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "session_id": session_id,
            "timestamp": datetime.now().isoformat()
        }