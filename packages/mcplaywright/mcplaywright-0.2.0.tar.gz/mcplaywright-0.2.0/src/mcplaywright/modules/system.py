"""
Provides desktop automation capabilities using PyAutoGUI.
SECURITY: All tools are disabled by default and require explicit permission.
"""

from typing import Dict, Any, Optional, Tuple, List
from fastmcp.contrib.mcp_mixin import MCPMixin, mcp_tool
from pathlib import Path
import platform
import logging
import secrets
import asyncio
from functools import wraps

logger = logging.getLogger(__name__)


def require_system_permission(permission_type: str):
    """
    Decorator to check system permissions before execution.
    
    Args:
        permission_type: "screenshot" or "interaction"
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            if not self._check_system_permission(permission_type):
                return {
                    "status": "error",
                    "message": f"System {permission_type} not enabled",
                    "setup_required": "Use browser_system_control_setup first",
                    "security_notice": f"Desktop {permission_type} requires explicit permission",
                    "available_setup": "browser_system_control_setup"
                }
            return await func(self, *args, **kwargs)
        return wrapper
    return decorator


class SystemControl(MCPMixin):
    """
    system-level automation with security controls.
    
    SECURITY MODEL:
    - All system tools are disabled by default
    - Explicit opt-in required via setup tool
    - Progressive permission levels (screenshot < interaction)
    - Session-based permissions (don't persist)
    - Platform permission validation
    """
    
    def __init__(self):
        super().__init__()
        # Security flags - all start False
        self.system_control_enabled = False
        self.screenshot_enabled = False
        self.interaction_enabled = False
        self.permissions_session_token = None
        self.pyautogui_available = False
        
        # Try to import PyAutoGUI
        self._initialize_pyautogui()
        
        # Setup screenshot directory
        self.screenshot_dir = Path("/tmp/mcplaywright/screenshots")
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
    
    def _initialize_pyautogui(self):
        """Initialize PyAutoGUI with safety settings."""
        try:
            import pyautogui
            # Disable failsafe for headless environments
            pyautogui.FAILSAFE = False
            # Set pause between actions for safety
            pyautogui.PAUSE = 0.1
            self.pyautogui_available = True
            logger.info("PyAutoGUI initialized successfully")
        except ImportError:
            logger.warning("PyAutoGUI not available - system control features disabled")
            self.pyautogui_available = False
        except Exception as e:
            logger.error(f"Error initializing PyAutoGUI: {e}")
            self.pyautogui_available = False
    
    def _check_system_permission(self, permission_type: str) -> bool:
        """Check if specific system permission is granted."""
        if not self.pyautogui_available:
            return False
        
        if permission_type == "screenshot":
            return self.screenshot_enabled
        elif permission_type == "interaction":
            return self.interaction_enabled
        
        return False
    
    def _check_platform_permissions(self) -> Dict[str, Any]:
        """Check platform-specific permissions and requirements."""
        system = platform.system()
        result = {"platform": system, "checks": []}
        
        if system == "Darwin":  # macOS
            result["checks"].append({
                "name": "Accessibility Permissions",
                "required": True,
                "status": "unknown",
                "note": "May require enabling accessibility permissions in System Preferences"
            })
        elif system == "Linux":
            result["checks"].append({
                "name": "Display Server Access", 
                "required": True,
                "status": "unknown",
                "note": "Requires X11 or Wayland display server access"
            })
        elif system == "Windows":
            result["checks"].append({
                "name": "User Interface Privilege",
                "required": False,
                "status": "available",
                "note": "Usually works out of the box"
            })
        
        return result
    
    # ALWAYS AVAILABLE: Setup and Status Tools
    
    @mcp_tool(
        name="browser_system_control_setup",
        description="""Enable system control features for desktop automation beyond the browser.
        
        This will make the following tools available when enabled:
        • browser_system_control_disable - Disable system control features for security
        • browser_take_monitor_screenshot - Screenshot entire monitor/desktop (not just browser)
        • browser_monitor_info - Get information about connected displays and screen resolution
        • browser_compare_browser_monitor - Compare browser screenshot with desktop screenshot
        • browser_system_click - Click at system coordinates outside browser window
        • browser_system_type - Type text at system level (works outside browser)
        • browser_system_hotkey - Send keyboard shortcuts and system hotkeys
        • browser_focus_window - Focus windows by title or application name
        • browser_list_windows - List all open windows and applications
        
        WARNING: Grants control over your entire desktop, not just the browser. Use with caution!
        Requires explicit security acknowledgment due to powerful system access capabilities."""
    )
    async def setup_system_control(
        self,
        enable_screenshots: bool = False,
        enable_interactions: bool = False,
        acknowledge_security_risks: bool = False
    ) -> Dict[str, Any]:
        """
        Enable system control features with explicit security consent.
        
        WARNING: This enables control of your entire desktop, not just the browser.
        Use with caution and only when necessary for testing/debugging.
        
        Args:
            enable_screenshots: Allow monitor screenshots (lower risk)
            enable_interactions: Allow mouse/keyboard control (higher risk)
            acknowledge_security_risks: Must be True to enable any features
        
        Returns:
            Setup result with enabled capabilities
        """
        try:
            # Security validation
            if not acknowledge_security_risks:
                return {
                    "status": "error",
                    "message": "Security acknowledgment required",
                    "required": "acknowledge_security_risks=True",
                    "warning": "System control provides desktop automation capabilities beyond browser"
                }
            
            # Check PyAutoGUI availability
            if not self.pyautogui_available:
                return {
                    "status": "error", 
                    "message": "PyAutoGUI not available",
                    "solution": "Install with: pip install pyautogui",
                    "note": "Required for system control features"
                }
            
            # Platform permission checks
            platform_info = self._check_platform_permissions()
            
            # Generate session token
            self.permissions_session_token = secrets.token_hex(16)
            
            # Enable requested capabilities
            if enable_screenshots:
                self.screenshot_enabled = True
                logger.info("System screenshots enabled")
            
            if enable_interactions:
                self.interaction_enabled = True
                logger.warning("System interactions enabled - full desktop access granted")
            
            self.system_control_enabled = enable_screenshots or enable_interactions
            
            # Test basic functionality
            test_results = {}
            if enable_screenshots:
                test_results["screenshot_test"] = await self._test_screenshot_capability()
            
            return {
                "status": "success",
                "message": "System control configured",
                "enabled_capabilities": {
                    "screenshots": self.screenshot_enabled,
                    "interactions": self.interaction_enabled
                },
                "session_token": self.permissions_session_token,
                "platform_info": platform_info,
                "test_results": test_results,
                "security_notice": "System control enabled for this session only",
                "available_tools": self._list_available_tools()
            }
            
        except Exception as e:
            logger.error(f"Error setting up system control: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    @mcp_tool(
        name="browser_system_control_status",
        description="Get current system control permissions and status"
    )
    async def get_system_control_status(self) -> Dict[str, Any]:
        """Get current system control status and available capabilities."""
        return {
            "system_control_enabled": self.system_control_enabled,
            "capabilities": {
                "screenshots": self.screenshot_enabled,
                "interactions": self.interaction_enabled
            },
            "pyautogui_available": self.pyautogui_available,
            "session_token": self.permissions_session_token is not None,
            "platform": platform.system(),
            "available_tools": self._list_available_tools(),
            "setup_required": not self.system_control_enabled
        }
    
    @mcp_tool(
        name="browser_system_control_disable",
        description="Disable all system control features for security"
    )
    async def disable_system_control(self) -> Dict[str, Any]:
        """Disable all system control features and clear permissions."""
        self.system_control_enabled = False
        self.screenshot_enabled = False
        self.interaction_enabled = False
        self.permissions_session_token = None
        
        logger.info("System control disabled")
        
        return {
            "status": "success",
            "message": "All system control features disabled",
            "security_notice": "Desktop access permissions revoked"
        }
    
    def _list_available_tools(self) -> List[str]:
        """List tools available based on current permissions."""
        tools = ["browser_system_control_setup", "browser_system_control_status", "browser_system_control_disable"]
        
        if self.screenshot_enabled:
            tools.extend([
                "browser_take_monitor_screenshot",
                "browser_monitor_info", 
                "browser_compare_browser_monitor"
            ])
        
        if self.interaction_enabled:
            tools.extend([
                "browser_system_click",
                "browser_system_type",
                "browser_system_hotkey",
                "browser_focus_window",
                "browser_list_windows"
            ])
        
        return tools
    
    async def _test_screenshot_capability(self) -> Dict[str, Any]:
        """Test basic screenshot functionality."""
        try:
            import pyautogui
            size = pyautogui.size()
            return {
                "success": True,
                "screen_size": {"width": size.width, "height": size.height},
                "monitors": 1  # Basic test, will enhance for multi-monitor
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    # HIDDEN TOOLS: Monitor Screenshots (require screenshot permission)
    
    @mcp_tool(
        name="browser_take_monitor_screenshot",
        description="Take a screenshot of the monitor/desktop",
        annotations={"hidden": True}
    )
    @require_system_permission("screenshot")
    async def take_monitor_screenshot(
        self,
        monitor: int = 0,
        region: Optional[Tuple[int, int, int, int]] = None,
        filename: Optional[str] = None,
        format: str = "png"
    ) -> Dict[str, Any]:
        """
        Take a screenshot of the monitor for debugging.
        
        Args:
            monitor: Monitor number (0 = primary, 1 = secondary, etc.)
            region: Optional (x, y, width, height) region to capture
            filename: Optional filename to save screenshot
            format: Image format ("png" or "jpeg")
        
        Returns:
            Screenshot result with path and metadata
        """
        try:
            import pyautogui
            
            # Take screenshot
            if region:
                x, y, width, height = region
                screenshot = pyautogui.screenshot(region=(x, y, width, height))
                target = f"region_{x}_{y}_{width}_{height}"
            else:
                screenshot = pyautogui.screenshot()
                target = f"monitor_{monitor}"
            
            # Save screenshot
            if filename:
                filepath = self.screenshot_dir / filename
            else:
                import datetime
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                filepath = self.screenshot_dir / f"monitor_{timestamp}.{format}"
            
            screenshot.save(filepath, format.upper())
            
            return {
                "status": "success",
                "target": target,
                "filepath": str(filepath),
                "format": format,
                "size": {
                    "width": screenshot.width,
                    "height": screenshot.height
                },
                "monitor": monitor,
                "region": region
            }
            
        except Exception as e:
            logger.error(f"Error taking monitor screenshot: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    @mcp_tool(
        name="browser_monitor_info",
        description="Get information about connected monitors",
        annotations={"hidden": True}
    )
    @require_system_permission("screenshot")
    async def get_monitor_info(self) -> Dict[str, Any]:
        """Get information about connected monitors and display setup."""
        try:
            import pyautogui
            
            # Get primary monitor info
            size = pyautogui.size()
            
            return {
                "status": "success",
                "primary_monitor": {
                    "width": size.width,
                    "height": size.height,
                    "index": 0
                },
                "total_monitors": 1,  # Will enhance for multi-monitor
                "platform": platform.system(),
                "pyautogui_version": pyautogui.__version__
            }
            
        except Exception as e:
            logger.error(f"Error getting monitor info: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    @mcp_tool(
        name="browser_compare_browser_monitor",
        description="Compare browser screenshot with monitor screenshot",
        annotations={"hidden": True}
    )
    @require_system_permission("screenshot")
    async def compare_browser_and_monitor(
        self,
        filename_prefix: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Take both browser and monitor screenshots for comparison.
        Useful for debugging rendering issues, dialogs, or positioning problems.
        
        Args:
            filename_prefix: Optional prefix for saved files
        
        Returns:
            Paths to both screenshots and comparison metadata
        """
        try:
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if filename_prefix:
                browser_filename = f"{filename_prefix}_browser_{timestamp}.png"
                monitor_filename = f"{filename_prefix}_monitor_{timestamp}.png"
            else:
                browser_filename = f"compare_browser_{timestamp}.png"
                monitor_filename = f"compare_monitor_{timestamp}.png"
            
            # Take browser screenshot
            browser_result = await self.take_screenshot(filename=browser_filename)
            
            # Take monitor screenshot
            monitor_result = await self.take_monitor_screenshot(filename=monitor_filename)
            
            return {
                "status": "success",
                "comparison": {
                    "browser": browser_result,
                    "monitor": monitor_result
                },
                "timestamp": timestamp,
                "note": "Use for debugging rendering issues, dialogs, or positioning"
            }
            
        except Exception as e:
            logger.error(f"Error comparing screenshots: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    # HIDDEN TOOLS: System Interaction (require interaction permission)
    
    @mcp_tool(
        name="browser_system_click",
        description="Click at system coordinates (outside browser)",
        annotations={"hidden": True}
    )
    @require_system_permission("interaction")
    async def system_click(
        self,
        x: int,
        y: int,
        button: str = "left",
        clicks: int = 1,
        interval: float = 0.0
    ) -> Dict[str, Any]:
        """
        Click at system-level coordinates.
        
        WARNING: This clicks outside the browser at desktop level.
        
        Args:
            x: X coordinate on screen
            y: Y coordinate on screen  
            button: Mouse button ("left", "right", "middle")
            clicks: Number of clicks
            interval: Interval between clicks
        
        Returns:
            Click result
        """
        try:
            import pyautogui
            
            # Validate coordinates
            size = pyautogui.size()
            if not (0 <= x <= size.width and 0 <= y <= size.height):
                return {
                    "status": "error",
                    "message": f"Coordinates out of bounds: ({x}, {y})",
                    "screen_size": {"width": size.width, "height": size.height}
                }
            
            # Perform click
            pyautogui.click(x, y, clicks=clicks, interval=interval, button=button)
            
            logger.warning(f"System click performed at ({x}, {y}) with {button} button")
            
            return {
                "status": "success",
                "action": "system_click",
                "coordinates": {"x": x, "y": y},
                "button": button,
                "clicks": clicks,
                "warning": "Desktop-level click performed"
            }
            
        except Exception as e:
            logger.error(f"Error performing system click: {e}")
            return {
                "status": "error", 
                "message": str(e)
            }
    
    @mcp_tool(
        name="browser_system_type",
        description="Type text at system level",
        annotations={"hidden": True}
    )
    @require_system_permission("interaction")
    async def system_type(
        self,
        text: str,
        interval: float = 0.0
    ) -> Dict[str, Any]:
        """
        Type text at system level (wherever focus is).
        
        WARNING: This types at desktop level, not in browser.
        
        Args:
            text: Text to type
            interval: Interval between keystrokes
        
        Returns:
            Typing result
        """
        try:
            import pyautogui
            
            # Safety check for text length
            if len(text) > 1000:
                return {
                    "status": "error",
                    "message": "Text too long (max 1000 characters)",
                    "length": len(text)
                }
            
            # Type text
            pyautogui.typewrite(text, interval=interval)
            
            logger.warning(f"System typing performed: {len(text)} characters")
            
            return {
                "status": "success",
                "action": "system_type",
                "text_length": len(text),
                "interval": interval,
                "warning": "Desktop-level typing performed"
            }
            
        except Exception as e:
            logger.error(f"Error performing system typing: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    @mcp_tool(
        name="browser_system_hotkey",
        description="Send system hotkey combination",
        annotations={"hidden": True}
    )
    @require_system_permission("interaction")
    async def system_hotkey(
        self,
        keys: List[str]
    ) -> Dict[str, Any]:
        """
        Send hotkey combination at system level.
        
        WARNING: This sends hotkeys at desktop level.
        
        Args:
            keys: List of keys to press together (e.g., ["cmd", "tab"])
        
        Returns:
            Hotkey result
        """
        try:
            import pyautogui
            
            # Safety check
            if len(keys) > 5:
                return {
                    "status": "error",
                    "message": "Too many keys in combination (max 5)"
                }
            
            # Send hotkey
            pyautogui.hotkey(*keys)
            
            logger.warning(f"System hotkey performed: {'+'.join(keys)}")
            
            return {
                "status": "success",
                "action": "system_hotkey",
                "keys": keys,
                "warning": "Desktop-level hotkey performed"
            }
            
        except Exception as e:
            logger.error(f"Error performing system hotkey: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    @mcp_tool(
        name="browser_focus_window",
        description="Focus a window by title",
        annotations={"hidden": True}
    )
    @require_system_permission("interaction")
    async def focus_window(
        self,
        window_title: str,
        partial_match: bool = True
    ) -> Dict[str, Any]:
        """
        Focus a window by its title.
        
        Args:
            window_title: Title of window to focus
            partial_match: Allow partial title matching
        
        Returns:
            Focus result
        """
        try:
            # This is a placeholder - full implementation would use
            # platform-specific window management APIs
            return {
                "status": "info",
                "message": "Window focusing not yet implemented",
                "requested_title": window_title,
                "note": "Feature planned for future release"
            }
            
        except Exception as e:
            logger.error(f"Error focusing window: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
    
    @mcp_tool(
        name="browser_list_windows",
        description="List all open windows",
        annotations={"hidden": True}
    )
    @require_system_permission("interaction")
    async def list_windows(self) -> Dict[str, Any]:
        """
        List all open windows for debugging.
        
        Returns:
            List of open windows
        """
        try:
            # This is a placeholder - full implementation would use
            # platform-specific window enumeration APIs
            return {
                "status": "info",
                "message": "Window listing not yet implemented",
                "note": "Feature planned for future release",
                "platform": platform.system()
            }
            
        except Exception as e:
            logger.error(f"Error listing windows: {e}")
            return {
                "status": "error",
                "message": str(e)
            }
