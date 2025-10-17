"""
MCPlaywright Context Management

Core context class that manages browser sessions, video recording, 
request monitoring, and session state across MCP calls.

This is the heart of the MCPlaywright system, providing persistent
browser contexts that survive across multiple MCP tool invocations.
"""

import asyncio
import logging
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from dataclasses import dataclass, field

from pydantic import BaseModel, Field
from playwright.async_api import Browser, BrowserContext, Page, async_playwright

# Import pagination components
from .pagination.cursor_manager import SessionCursorManager, get_cursor_manager
from .pagination.models import CursorState, QueryState

logger = logging.getLogger(__name__)


class VideoMode(Enum):
    """Video recording modes with different behavior patterns"""
    CONTINUOUS = "continuous"    # Record everything including waits
    SMART = "smart"             # Auto-pause during waits, resume on actions
    ACTION_ONLY = "action-only"  # Only record during active interactions  
    SEGMENT = "segment"         # Separate video files per action sequence


class BrowserType(Enum):
    """Supported browser types"""
    CHROMIUM = "chromium"
    FIREFOX = "firefox"
    WEBKIT = "webkit"


@dataclass
class VideoConfig:
    """Video recording configuration"""
    directory: Path
    size: Dict[str, int] = field(default_factory=lambda: {"width": 1280, "height": 720})
    mode: VideoMode = VideoMode.SMART
    base_filename: str = ""
    auto_set_viewport: bool = True


@dataclass
class ClientVersion:
    """MCP client version information"""
    name: str
    version: str


class BrowserConfig(BaseModel):
    """Browser configuration model"""
    browser_type: BrowserType = BrowserType.CHROMIUM
    headless: bool = True
    viewport: Dict[str, int] = Field(default_factory=lambda: {"width": 1280, "height": 720})
    user_agent: Optional[str] = None
    locale: Optional[str] = None
    timezone: Optional[str] = None
    geolocation: Optional[Dict[str, float]] = None
    permissions: Optional[List[str]] = None
    color_scheme: Optional[str] = None
    
    # UI Customization options (ported from TypeScript)
    slow_mo: Optional[int] = None  # Milliseconds between actions
    devtools: Optional[bool] = None  # Open Chrome DevTools
    args: Optional[List[str]] = None  # Custom browser arguments
    chromium_sandbox: Optional[bool] = None  # Sandbox control
    
    # Network options
    offline: Optional[bool] = None


class Context:
    """
    Core browser context manager for MCPlaywright.
    
    Manages persistent browser sessions, video recording state,
    HTTP request monitoring, and session-based operations across
    multiple MCP tool invocations.
    
    This class is the heart of the system and handles:
    - Browser context lifecycle management
    - Video recording with multiple modes and smart pause/resume
    - HTTP request interception and monitoring  
    - Session persistence across MCP calls
    - Artifact management and storage
    - UI customization and configuration
    """
    
    def __init__(
        self,
        session_id: str,
        config: Optional[BrowserConfig] = None,
        artifacts_dir: Optional[Path] = None
    ):
        self.session_id = session_id
        self.config = config or BrowserConfig()
        self.artifacts_dir = artifacts_dir or Path("./artifacts")
        
        # Browser management
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._browser_context: Optional[BrowserContext] = None
        self._pages: List[Page] = []
        self._current_page: Optional[Page] = None
        
        # Video recording state
        self._video_config: Optional[VideoConfig] = None
        self._active_pages_with_videos: Set[Page] = set()
        self._video_recording_paused: bool = False
        self._pausedpage_videos: Dict[Page, Any] = {}  # Page -> Video mapping
        self._video_recording_mode: VideoMode = VideoMode.SMART
        self._current_video_segment: int = 1
        self._auto_recording_enabled: bool = True
        
        # HTTP request monitoring
        self._request_interceptor = None
        self._request_monitoring_enabled: bool = False
        
        # Session state
        self.client_version: Optional[ClientVersion] = None
        self._created_at = datetime.now()
        self._last_activity = datetime.now()
        
        # Pagination cursor management
        self._cursor_manager: Optional[SessionCursorManager] = None
        
        logger.info(f"Created Context for session {session_id}")
    
    async def initialize(self) -> None:
        """Initialize the browser context and Playwright"""
        try:
            self._playwright = await async_playwright().start()
            
            # Initialize cursor manager for pagination
            self._cursor_manager = await get_cursor_manager()
            
            logger.info(f"Playwright and cursor manager initialized for session {self.session_id}")
        except Exception as e:
            logger.error(f"Failed to initialize Playwright: {str(e)}")
            raise
    
    async def cleanup(self) -> None:
        """
        Clean up all browser resources and session state.
        
        Comprehensive cleanup to prevent memory leaks on MCP client disconnection:
        - HTTP request monitoring data
        - Video recording state and references
        - Page references and event handlers
        - Browser contexts and processes
        - Cursor pagination state
        - Session tracking data structures
        """
        cleanup_summary = {
            "cursors_cleaned": 0,
            "requests_cleaned": 0,
            "video_pages_cleaned": 0,
            "pages_closed": 0,
            "errors": []
        }
        
        try:
            # 1. Clean up HTTP request monitoring data
            try:
                captured_requests = getattr(self, '_captured_requests', [])
                if captured_requests:
                    cleanup_summary["requests_cleaned"] = len(captured_requests)
                    self._captured_requests = []  # Clear request monitoring data
                    logger.info(f"Cleaned up {cleanup_summary['requests_cleaned']} captured HTTP requests")
            except Exception as e:
                cleanup_summary["errors"].append(f"Request cleanup: {str(e)}")
                logger.warning(f"Failed to cleanup HTTP requests: {str(e)}")
            
            # 2. Clean up video recording state and references
            try:
                video_cleanup_count = 0
                
                # Clear active video recordings
                if self._active_pages_with_videos:
                    video_cleanup_count += len(self._active_pages_with_videos)
                    self._active_pages_with_videos.clear()
                
                # Clear paused video references
                if self._pausedpage_videos:
                    video_cleanup_count += len(self._pausedpage_videos)
                    self._pausedpage_videos.clear()
                
                # Reset video state
                self._video_recording_paused = False
                self._current_video_segment = 1
                self._video_config = None
                
                cleanup_summary["video_pages_cleaned"] = video_cleanup_count
                if video_cleanup_count > 0:
                    logger.info(f"Cleaned up {video_cleanup_count} video recording references")
                    
            except Exception as e:
                cleanup_summary["errors"].append(f"Video cleanup: {str(e)}")
                logger.warning(f"Failed to cleanup video state: {str(e)}")
            
            # 3. Clean up session cursors for pagination
            try:
                if self._cursor_manager:
                    cursor_count = await self._cursor_manager.invalidate_session_cursors(self.session_id)
                    cleanup_summary["cursors_cleaned"] = cursor_count
                    if cursor_count > 0:
                        logger.info(f"Cleaned up {cursor_count} pagination cursors")
            except Exception as e:
                cleanup_summary["errors"].append(f"Cursor cleanup: {str(e)}")
                logger.warning(f"Failed to cleanup cursors: {str(e)}")
            
            # 4. Close all pages and clear references
            try:
                pages_to_close = self._pages.copy()  # Copy to avoid modification during iteration
                for page in pages_to_close:
                    try:
                        if not page.is_closed():
                            await page.close()
                            cleanup_summary["pages_closed"] += 1
                    except Exception as page_error:
                        logger.warning(f"Failed to close page: {str(page_error)}")
                
                # Clear page references
                self._pages.clear()
                self._current_page = None
                
                if cleanup_summary["pages_closed"] > 0:
                    logger.info(f"Closed {cleanup_summary['pages_closed']} browser pages")
                    
            except Exception as e:
                cleanup_summary["errors"].append(f"Page cleanup: {str(e)}")
                logger.warning(f"Failed to cleanup pages: {str(e)}")
            
            # 5. Close browser context
            try:
                if self._browser_context:
                    await self._browser_context.close()
                    self._browser_context = None
            except Exception as e:
                cleanup_summary["errors"].append(f"Browser context: {str(e)}")
                logger.warning(f"Failed to close browser context: {str(e)}")
            
            # 6. Close browser
            try:
                if self._browser:
                    await self._browser.close()
                    self._browser = None
            except Exception as e:
                cleanup_summary["errors"].append(f"Browser: {str(e)}")
                logger.warning(f"Failed to close browser: {str(e)}")
            
            # 7. Stop Playwright
            try:
                if self._playwright:
                    await self._playwright.stop()
                    self._playwright = None
            except Exception as e:
                cleanup_summary["errors"].append(f"Playwright: {str(e)}")
                logger.warning(f"Failed to stop Playwright: {str(e)}")
            
            # 8. Clear remaining session state
            try:
                self._request_interceptor = None
                self._request_monitoring_enabled = False
                self._cursor_manager = None
            except Exception as e:
                cleanup_summary["errors"].append(f"Session state: {str(e)}")
                logger.warning(f"Failed to clear session state: {str(e)}")
            
            # Log cleanup summary
            total_cleaned = (cleanup_summary["cursors_cleaned"] + 
                           cleanup_summary["requests_cleaned"] + 
                           cleanup_summary["video_pages_cleaned"] + 
                           cleanup_summary["pages_closed"])
            
            if cleanup_summary["errors"]:
                logger.warning(f"Context cleanup completed with {len(cleanup_summary['errors'])} errors: {cleanup_summary}")
            else:
                logger.info(f"Context cleanup successful - cleaned {total_cleaned} resources for session {self.session_id}")
            
        except Exception as e:
            logger.error(f"Critical error during cleanup: {str(e)}")
            # Even if cleanup fails, ensure references are cleared to prevent memory leaks
            try:
                self._pages.clear()
                self._current_page = None
                self._browser_context = None
                self._browser = None
                self._playwright = None
                self._captured_requests = []
                self._active_pages_with_videos.clear()
                self._pausedpage_videos.clear()
                self._cursor_manager = None
            except:
                pass  # Ignore errors in emergency cleanup
    
    async def ensure_browser_context(self) -> BrowserContext:
        """Ensure browser context exists, create if needed"""
        if self._browser_context is None:
            await self._create_browser_context()
        return self._browser_context
    
    async def _create_browser_context(self) -> None:
        """Create browser context with current configuration"""
        if not self._playwright:
            await self.initialize()
        
        # Get browser type
        browser_type = getattr(self._playwright, self.config.browser_type.value)
        
        # Prepare launch options
        launch_options = {
            "headless": self.config.headless
        }
        
        # Add UI customization options
        if self.config.slow_mo is not None:
            launch_options["slow_mo"] = self.config.slow_mo
            
        if self.config.devtools is not None:
            launch_options["devtools"] = self.config.devtools
            
        if self.config.chromium_sandbox is not None:
            launch_options["chromium_sandbox"] = self.config.chromium_sandbox
            
        if self.config.args:
            launch_options["args"] = self.config.args
        
        # Launch browser
        self._browser = await browser_type.launch(**launch_options)
        
        # Prepare context options
        context_options = {
            "viewport": self.config.viewport
        }
        
        if self.config.user_agent:
            context_options["user_agent"] = self.config.user_agent
            
        if self.config.locale:
            context_options["locale"] = self.config.locale
            
        if self.config.timezone:
            context_options["timezone_id"] = self.config.timezone
            
        if self.config.geolocation:
            context_options["geolocation"] = self.config.geolocation
            
        if self.config.permissions:
            context_options["permissions"] = self.config.permissions
            
        if self.config.color_scheme:
            context_options["color_scheme"] = self.config.color_scheme
        
        # Add video recording if configured
        if self._video_config:
            context_options["record_video"] = {
                "dir": str(self._video_config.directory),
                "size": self._video_config.size
            }
        
        # Create context
        self._browser_context = await self._browser.new_context(**context_options)
        
        # Set offline mode if configured
        if self.config.offline is not None:
            await self._browser_context.set_offline(self.config.offline)
        
        logger.info(f"Created browser context for session {self.session_id}")
    
    async def get_current_page(self) -> Page:
        """Get current page, create one if none exists"""
        if self._current_page is None or self._current_page.is_closed():
            context = await self.ensure_browser_context()
            self._current_page = await context.new_page()
            self._pages.append(self._current_page)
            
            # Set up request monitoring if enabled
            if self._request_monitoring_enabled:
                await self._setup_request_monitoring(self._current_page)
            
            # Track for video recording if configured
            if self._video_config:
                self._active_pages_with_videos.add(self._current_page)
        
        self._last_activity = datetime.now()
        return self._current_page
    
    async def update_browser_config(self, updates: Dict[str, Any]) -> None:
        """Update browser configuration and recreate context if needed"""
        config_changed = False
        
        # Update configuration
        for key, value in updates.items():
            if hasattr(self.config, key):
                current_value = getattr(self.config, key)
                if current_value != value:
                    setattr(self.config, key, value)
                    config_changed = True
                    logger.info(f"Updated config {key}: {current_value} -> {value}")
        
        # Recreate browser context if configuration changed
        if config_changed:
            logger.info("Browser configuration changed, recreating context")
            
            # Close current context
            if self._browser_context:
                await self._browser_context.close()
            
            # Clear state
            self._browser_context = None
            self._pages.clear()
            self._current_page = None
            
            # Will be recreated on next access
    
    # Video Recording Methods
    
    def set_video_recording(self, config: VideoConfig) -> None:
        """Configure video recording for browser contexts"""
        self._video_config = config
        
        # Force recreation of browser context to include video recording
        if self._browser_context:
            asyncio.create_task(self._recreate_context_with_video())
        
        logger.info(f"Video recording configured: {config.directory}, mode: {config.mode}")
    
    async def _recreate_context_with_video(self) -> None:
        """Recreate browser context with video recording enabled"""
        if self._browser_context:
            await self._browser_context.close()
        
        self._browser_context = None
        self._pages.clear()
        self._current_page = None
        # Will be recreated with video recording on next access
    
    def get_video_recording_info(self) -> Dict[str, Any]:
        """Get current video recording information"""
        return {
            "enabled": self._video_config is not None,
            "config": self._video_config.__dict__ if self._video_config else None,
            "active_recordings": len(self._active_pages_with_videos),
            "paused": self._video_recording_paused,
            "paused_recordings": len(self._pausedpage_videos),
            "mode": self._video_recording_mode.value,
            "current_segment": self._current_video_segment,
            "auto_recording_enabled": self._auto_recording_enabled
        }
    
    async def pause_video_recording(self) -> Dict[str, Any]:
        """Pause video recording on all active pages"""
        if not self._video_config or self._video_recording_paused:
            return {"paused": 0, "message": "No active recording to pause"}
        
        paused_count = 0
        for page in self._active_pages_with_videos:
            try:
                if not page.is_closed():
                    video = page.video()
                    if video and video not in self._pausedpage_videos.values():
                        # Store video reference for resuming
                        self._pausedpage_videos[page] = video
                        paused_count += 1
            except Exception as e:
                logger.warning(f"Error pausing video for page: {str(e)}")
        
        if paused_count > 0:
            self._video_recording_paused = True
            logger.info(f"Paused video recording on {paused_count} pages")
        
        return {"paused": paused_count, "message": f"Paused recording on {paused_count} pages"}
    
    async def resume_video_recording(self) -> Dict[str, Any]:
        """Resume video recording on paused pages"""
        if not self._video_recording_paused:
            return {"resumed": 0, "message": "Recording not paused"}
        
        resumed_count = len(self._pausedpage_videos)
        
        # Clear paused videos (recording continues automatically)
        self._pausedpage_videos.clear()
        self._video_recording_paused = False
        
        logger.info(f"Resumed video recording on {resumed_count} pages")
        
        return {"resumed": resumed_count, "message": f"Resumed recording on {resumed_count} pages"}
    
    def set_video_recording_mode(self, mode: VideoMode) -> None:
        """Set video recording mode"""
        self._video_recording_mode = mode
        logger.info(f"Video recording mode set to: {mode.value}")
    
    async def begin_video_action(self, action_name: str) -> None:
        """Called before browser actions to handle smart recording"""
        if (self._video_recording_mode == VideoMode.SMART and 
            self._video_recording_paused):
            await self.resume_video_recording()
            logger.debug(f"Auto-resumed recording for action: {action_name}")
    
    async def end_video_action(self, action_name: str) -> None:
        """Called after browser actions to handle smart recording"""
        if (self._video_recording_mode == VideoMode.SMART and 
            not self._video_recording_paused):
            # Pause after a short delay to allow action to complete
            await asyncio.sleep(0.1)
            await self.pause_video_recording()
            logger.debug(f"Auto-paused recording after action: {action_name}")
    
    async def stop_video_recording(self) -> List[str]:
        """Stop video recording and return video file paths"""
        if not self._video_config:
            logger.info("No video recording to stop")
            return []
        
        video_paths = []
        
        # Collect video paths from all pages
        for page in self._active_pages_with_videos:
            try:
                if not page.is_closed():
                    video = page.video()
                    if video:
                        video_path = await video.path()
                        video_paths.append(video_path)
            except Exception as e:
                logger.error(f"Error getting video path: {str(e)}")
        
        # Clear video recording state
        self.clear_video_recording_state()
        
        logger.info(f"Stopped video recording, collected {len(video_paths)} videos")
        return video_paths
    
    def clear_video_recording_state(self) -> None:
        """Clear video recording state"""
        self._video_config = None
        self._active_pages_with_videos.clear()
        self._video_recording_paused = False
        self._pausedpage_videos.clear()
        self._current_video_segment = 1
    
    # Request Monitoring Methods
    
    async def _setup_request_monitoring(self, page: Page) -> None:
        """Set up HTTP request monitoring on a page"""
        # This will be implemented when we add the request interceptor
        pass
    
    async def enable_request_monitoring(self, options: Optional[Dict[str, Any]] = None) -> None:
        """Enable HTTP request monitoring"""
        self._request_monitoring_enabled = True
        
        # Apply to current page if exists
        if self._current_page:
            await self._setup_request_monitoring(self._current_page)
        
        logger.info("HTTP request monitoring enabled")
    
    async def disable_request_monitoring(self) -> None:
        """Disable HTTP request monitoring"""
        self._request_monitoring_enabled = False
        logger.info("HTTP request monitoring disabled")
    
    # Pagination Cursor Methods
    
    async def create_pagination_cursor(self,
                                      tool_name: str,
                                      query_state: QueryState,
                                      initial_position: Dict[str, Any],
                                      expiry_hours: Optional[int] = None) -> str:
        """
        Create a pagination cursor for the session.
        
        Args:
            tool_name: Name of the tool creating cursor
            query_state: Query parameters and filters
            initial_position: Starting position for pagination
            expiry_hours: Custom expiry time (uses default if None)
        
        Returns:
            Unique cursor ID string
        """
        if not self._cursor_manager:
            self._cursor_manager = await get_cursor_manager()
        
        cursor_id = self._cursor_manager.create_cursor(
            session_id=self.session_id,
            tool_name=tool_name,
            query_state=query_state,
            initial_position=initial_position,
            expiry_hours=expiry_hours
        )
        
        self.update_last_activity()
        logger.debug(f"Created pagination cursor {cursor_id} for tool {tool_name}")
        return cursor_id
    
    async def get_pagination_cursor(self, cursor_id: str) -> CursorState:
        """
        Retrieve and validate cursor access for the session.
        
        Args:
            cursor_id: Cursor identifier
        
        Returns:
            CursorState object
        
        Raises:
            CursorNotFoundError: Cursor doesn't exist
            CursorExpiredError: Cursor has expired
            CrossSessionAccessError: Session mismatch
        """
        if not self._cursor_manager:
            self._cursor_manager = await get_cursor_manager()
        
        cursor = self._cursor_manager.get_cursor(cursor_id, self.session_id)
        self.update_last_activity()
        return cursor
    
    async def update_cursor_position(self,
                                   cursor_id: str,
                                   new_position: Dict[str, Any],
                                   result_count: int = 0) -> None:
        """
        Update cursor position after fetching results.
        
        Args:
            cursor_id: Cursor identifier
            new_position: New pagination position
            result_count: Number of items returned
        """
        if not self._cursor_manager:
            self._cursor_manager = await get_cursor_manager()
        
        self._cursor_manager.update_cursor_position(
            cursor_id=cursor_id,
            session_id=self.session_id,
            new_position=new_position,
            result_count=result_count
        )
        
        self.update_last_activity()
    
    async def invalidate_cursor(self, cursor_id: str) -> bool:
        """
        Manually invalidate a cursor for the session.
        
        Args:
            cursor_id: Cursor identifier
        
        Returns:
            True if cursor was removed, False if not found
        """
        if not self._cursor_manager:
            return False
        
        result = self._cursor_manager.invalidate_cursor(cursor_id, self.session_id)
        self.update_last_activity()
        return result
    
    async def detect_fresh_pagination_query(self,
                                          tool_name: str,
                                          params: Any) -> bool:
        """
        Detect if this is a fresh query or cursor continuation.
        
        Args:
            tool_name: Tool name
            params: Pagination parameters (should have cursor_id attribute)
        
        Returns:
            True if fresh query, False if continuation
        """
        if not self._cursor_manager:
            return True
        
        result = self._cursor_manager.detect_fresh_query(
            session_id=self.session_id,
            tool_name=tool_name,
            params=params
        )
        
        self.update_last_activity()
        return result
    
    async def get_cursor_stats(self) -> Dict[str, Any]:
        """Get cursor statistics for this session"""
        if not self._cursor_manager:
            return {"session_id": self.session_id, "total_cursors": 0}
        
        return self._cursor_manager.get_session_cursor_stats(self.session_id)
    
    # Utility Methods
    
    def get_session_info(self) -> Dict[str, Any]:
        """Get session information"""
        return {
            "session_id": self.session_id,
            "created_at": self._created_at.isoformat(),
            "last_activity": self._last_activity.isoformat(),
            "client_version": self.client_version.__dict__ if self.client_version else None,
            "browser_type": self.config.browser_type.value,
            "headless": self.config.headless,
            "pages": len(self._pages),
            "video_recording": self.get_video_recording_info(),
            "request_monitoring": self._request_monitoring_enabled,
            "cursor_manager_active": self._cursor_manager is not None
        }
    
    def update_last_activity(self) -> None:
        """Update last activity timestamp"""
        self._last_activity = datetime.now()
    
    def __repr__(self) -> str:
        return f"Context(session_id='{self.session_id}', browser='{self.config.browser_type.value}')"