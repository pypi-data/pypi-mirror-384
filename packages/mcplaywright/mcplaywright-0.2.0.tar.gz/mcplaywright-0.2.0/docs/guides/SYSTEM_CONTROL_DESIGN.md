# System Control & Monitor Screenshot Feature Design

## Overview
MCPlaywright System Control extends browser automation to full desktop automation using PyAutoGUI. This enables control of system browsers, native applications, and monitor screenshots for comprehensive testing and debugging.

## Security Architecture

### Core Security Principle: Disabled by Default
- **ALL system control tools are HIDDEN by default**
- **Explicit opt-in required** via setup tool
- **Progressive permission levels** with clear security boundaries
- **Easy disable mechanism** for security

### Permission Levels
```
Level 0: Browser Only (Default)
├── Standard MCPlaywright browser automation
├── Safe, sandboxed environment
└── No system access required

Level 1: Monitor Screenshots (screenshot_enabled = True)
├── Screen capture only (read-only)
├── Monitor information and debugging
├── Browser vs monitor comparison
└── Minimal security risk

Level 2: System Interaction (interaction_enabled = True)  
├── Mouse/keyboard control
├── Window management
├── System browser control
├── Application automation
└── Requires explicit security acknowledgment
```

## Implementation Strategy

### 1. SystemControlMixin Architecture
```python
class SystemControlMixin(MCPMixin):
    """System-level automation with security controls."""
    
    def __init__(self):
        super().__init__()
        # Security flags - all start False
        self.system_control_enabled = False
        self.screenshot_enabled = False  
        self.interaction_enabled = False
        self.permissions_session_token = None
        
    @require_system_permission("screenshot")
    async def take_monitor_screenshot(self, ...):
        """Hidden tool until screenshots enabled"""
        
    @require_system_permission("interaction") 
    async def system_click(self, ...):
        """Hidden tool until interaction enabled"""
```

### 2. Security Decorator Pattern
```python
def require_system_permission(permission_type: str):
    """Decorator to check permissions before execution."""
    def decorator(func):
        async def wrapper(self, *args, **kwargs):
            if not self._check_system_permission(permission_type):
                return {
                    "status": "error",
                    "message": f"System {permission_type} not enabled",
                    "setup_required": "Use browser_system_control_setup first",
                    "security_notice": "Desktop access requires explicit permission"
                }
            return await func(self, *args, **kwargs)
        return wrapper
    return decorator
```

## Tool Categories

### Always Available: Setup & Status Tools
```python
@mcp_tool(name="browser_system_control_setup")
async def setup_system_control(
    enable_screenshots: bool = False,
    enable_interactions: bool = False, 
    acknowledge_security_risks: bool = False
) -> Dict[str, Any]:
    """Enable system control with security validation."""

@mcp_tool(name="browser_system_control_status") 
async def get_system_control_status() -> Dict[str, Any]:
    """Get current permissions and available tools."""

@mcp_tool(name="browser_system_control_disable")
async def disable_system_control() -> Dict[str, Any]:
    """Disable all system control for security."""
```

### Hidden Until screenshot_enabled=True
```python
@mcp_tool(name="browser_take_monitor_screenshot", hidden=True)
@mcp_tool(name="browser_monitor_info", hidden=True)
@mcp_tool(name="browser_compare_browser_monitor", hidden=True)
```

### Hidden Until interaction_enabled=True  
```python
@mcp_tool(name="browser_system_click", hidden=True)
@mcp_tool(name="browser_system_type", hidden=True)
@mcp_tool(name="browser_system_hotkey", hidden=True)
@mcp_tool(name="browser_control_system_browser", hidden=True)
@mcp_tool(name="browser_focus_window", hidden=True)
@mcp_tool(name="browser_list_windows", hidden=True)
```

## Key Features

### 1. Monitor Screenshots & Debugging
- **Full desktop capture** for troubleshooting browser issues
- **Multi-monitor support** with monitor selection
- **Region-based screenshots** for specific areas
- **Browser vs monitor comparison** to debug rendering issues
- **Monitor information** for multi-display setups

### 2. System Browser Control
- **Control user's default browser** (Chrome, Firefox, Safari, Edge)
- **Multi-browser testing** - run same tests across different browsers
- **Browser window management** - focus, resize, position
- **Cross-browser automation** workflows

### 3. Desktop Application Integration
- **Window detection and focusing** by title
- **Mouse and keyboard control** at system level
- **Hotkey automation** for system shortcuts
- **File system interactions** (open files, handle downloads)

### 4. Advanced Use Cases
- **System dialog handling** - permission prompts, alerts
- **Cross-application workflows** - browser → native app → browser
- **Multi-window debugging** - see all browser windows
- **Desktop app testing** alongside web apps

## Security Implementation

### 1. Platform Permission Checks
```python
def check_platform_permissions() -> Dict[str, Any]:
    """Check platform-specific requirements."""
    system = platform.system()
    
    if system == "Darwin":  # macOS
        return check_macos_accessibility()
    elif system == "Linux": 
        return check_linux_display_access()
    elif system == "Windows":
        return {"available": True, "notes": "Usually works out of box"}
```

### 2. Safety Boundaries
```python
class SystemControlLimits:
    MAX_CLICK_RATE = 10  # clicks per second
    MAX_TYPE_RATE = 100  # characters per second
    SCREEN_BOUNDARY_CHECK = True
    PREVENT_SYSTEM_MODIFICATION = True
    
    @staticmethod
    def validate_coordinates(x: int, y: int) -> bool:
        """Ensure coordinates within screen bounds."""
```

### 3. User Consent Flow
```
1. User calls browser_system_control_setup
2. System shows security warnings
3. User must acknowledge_security_risks=True
4. Platform permission checks performed  
5. PyAutoGUI dependency validated
6. Session token generated
7. Specific tools enabled based on permissions
8. Hidden tools become visible in tool list
```

## Integration with Existing MCPlaywright

### 1. Server V3 Integration
```python
class MCPlaywrightServerV3(
    BrowserMixin,
    NavigationMixin, 
    InteractionMixin,
    ScreenshotMixin,
    SystemControlMixin,  # NEW
    ClientIdentificationMixin,
    ExtensionManagementMixin,
    CoordinateInteractionMixin,
    MediaStreamMixin
):
    """Complete server with system control capabilities."""
```

### 2. Dependency Management
```toml
# pyproject.toml
dependencies = [
    # ... existing dependencies
    "pyautogui>=0.9.54",  # NEW: System control
]
```

### 3. Testing Strategy
- **Unit tests** with PyAutoGUI mocking
- **Permission testing** for all platforms
- **Security validation** tests
- **Integration tests** with real desktop interaction (when available)

## Documentation & User Guidance

### 1. Security Documentation
- **Clear warnings** about desktop access implications
- **Platform-specific setup** instructions (macOS accessibility, etc.)
- **Use case examples** showing appropriate usage
- **Security best practices** for system control

### 2. Troubleshooting Guide
- **Permission issues** on different platforms
- **Headless environment** limitations
- **Multi-monitor setup** guidance
- **Performance considerations**

## Benefits

### 1. Enhanced Debugging
- **Complete visual context** - see entire desktop during automation
- **System-level issue detection** - catch problems outside browser
- **Multi-browser comparison** - test across different browsers
- **Integration testing** - browser + native app workflows

### 2. Advanced Automation
- **System browser control** - automate user's preferred browser
- **Cross-application testing** - comprehensive workflow testing
- **Desktop app integration** - test desktop + web combinations
- **File system automation** - handle downloads, file dialogs

### 3. Professional Testing
- **Enterprise environments** - integrate with existing desktop apps
- **Accessibility testing** - capture screen reader overlays
- **Performance monitoring** - visual confirmation of UI performance
- **Multi-display testing** - test responsive design across monitors

## Implementation Priority

### Phase 1: Security Foundation (Immediate)
1. Create SystemControlMixin with security architecture
2. Implement permission system and setup tools
3. Add PyAutoGUI dependency management
4. Platform permission validation

### Phase 2: Monitor Screenshots (Next)
1. Basic monitor screenshot functionality
2. Multi-monitor support
3. Browser vs monitor comparison
4. Monitor information tools

### Phase 3: System Interaction (Later)
1. Mouse and keyboard control
2. Window management
3. System browser control
4. Advanced automation features

This design provides powerful desktop automation capabilities while maintaining MCPlaywright's security and reliability through explicit consent, progressive enablement, and clear security boundaries.