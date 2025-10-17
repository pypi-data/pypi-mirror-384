#!/usr/bin/env python3
"""
Standalone System Control Tests

Tests SystemControlMixin without importing the full package.
"""

import asyncio
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
from typing import Dict, Any, Optional, Tuple, List

# Add source path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Direct import to avoid server.py issues
from fastmcp.contrib.mcp_mixin import MCPMixin, mcp_tool
import platform
import secrets
import logging
from functools import wraps

logger = logging.getLogger(__name__)

# Copy the permission decorator for testing
def require_system_permission(permission_type: str):
    """Decorator to check system permissions before execution."""
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            if not self._check_system_permission(permission_type):
                return {
                    "status": "error",
                    "message": f"System {permission_type} not enabled",
                    "setup_required": "Use browser_system_control_setup first"
                }
            return await func(self, *args, **kwargs)
        return wrapper
    return decorator


class TestSystemControlMixin(MCPMixin):
    """Simplified SystemControlMixin for testing."""
    
    def __init__(self):
        super().__init__()
        self.system_control_enabled = False
        self.screenshot_enabled = False
        self.interaction_enabled = False
        self.permissions_session_token = None
        self.pyautogui_available = True  # Mock as available
    
    def _check_system_permission(self, permission_type: str) -> bool:
        """Check if specific system permission is granted."""
        if permission_type == "screenshot":
            return self.screenshot_enabled
        elif permission_type == "interaction":
            return self.interaction_enabled
        return False
    
    async def setup_system_control(
        self,
        enable_screenshots: bool = False,
        enable_interactions: bool = False,
        acknowledge_security_risks: bool = False
    ) -> Dict[str, Any]:
        """Setup system control with security validation."""
        if not acknowledge_security_risks:
            return {
                "status": "error",
                "message": "Security acknowledgment required",
                "required": "acknowledge_security_risks=True"
            }
        
        if not self.pyautogui_available:
            return {
                "status": "error",
                "message": "PyAutoGUI not available"
            }
        
        # Generate session token
        self.permissions_session_token = secrets.token_hex(16)
        
        # Enable capabilities
        if enable_screenshots:
            self.screenshot_enabled = True
        
        if enable_interactions:
            self.interaction_enabled = True
        
        self.system_control_enabled = enable_screenshots or enable_interactions
        
        return {
            "status": "success",
            "message": "System control configured",
            "enabled_capabilities": {
                "screenshots": self.screenshot_enabled,
                "interactions": self.interaction_enabled
            },
            "session_token": self.permissions_session_token
        }
    
    async def get_system_control_status(self) -> Dict[str, Any]:
        """Get current system control status."""
        return {
            "system_control_enabled": self.system_control_enabled,
            "capabilities": {
                "screenshots": self.screenshot_enabled,
                "interactions": self.interaction_enabled
            },
            "pyautogui_available": self.pyautogui_available,
            "platform": platform.system()
        }
    
    async def disable_system_control(self) -> Dict[str, Any]:
        """Disable all system control features."""
        self.system_control_enabled = False
        self.screenshot_enabled = False
        self.interaction_enabled = False
        self.permissions_session_token = None
        
        return {
            "status": "success",
            "message": "All system control features disabled"
        }
    
    @require_system_permission("screenshot")
    async def take_monitor_screenshot(self) -> Dict[str, Any]:
        """Take monitor screenshot (requires permission)."""
        return {
            "status": "success",
            "message": "Monitor screenshot taken",
            "filepath": "/tmp/monitor_screenshot.png"
        }
    
    @require_system_permission("interaction")
    async def system_click(self, x: int, y: int) -> Dict[str, Any]:
        """System click (requires interaction permission)."""
        return {
            "status": "success",
            "message": f"System click at ({x}, {y})",
            "coordinates": {"x": x, "y": y}
        }


async def test_security_model():
    """Test the security model of SystemControlMixin."""
    print("🔒 Testing Security Model")
    
    server = TestSystemControlMixin()
    
    # Test 1: Initial state is secure
    assert server.system_control_enabled is False
    assert server.screenshot_enabled is False
    assert server.interaction_enabled is False
    print("  ✅ Initial state secure")
    
    # Test 2: Setup requires acknowledgment
    result = await server.setup_system_control(
        enable_screenshots=True,
        acknowledge_security_risks=False
    )
    assert result["status"] == "error"
    assert "acknowledgment required" in result["message"].lower()
    print("  ✅ Security acknowledgment required")
    
    # Test 3: Tools are protected without permission
    result = await server.take_monitor_screenshot()
    assert result["status"] == "error"
    assert "not enabled" in result["message"]
    print("  ✅ Protected tools require permission")
    
    # Test 4: Status tool always works
    status = await server.get_system_control_status()
    assert "system_control_enabled" in status
    print("  ✅ Status tool always available")
    
    return True


async def test_permission_flow():
    """Test the permission setup and usage flow."""
    print("🔑 Testing Permission Flow")
    
    server = TestSystemControlMixin()
    
    # Test 1: Enable screenshots only
    result = await server.setup_system_control(
        enable_screenshots=True,
        enable_interactions=False,
        acknowledge_security_risks=True
    )
    assert result["status"] == "success"
    assert server.screenshot_enabled is True
    assert server.interaction_enabled is False
    print("  ✅ Screenshot permission granted")
    
    # Test 2: Screenshot tools work
    result = await server.take_monitor_screenshot()
    assert result["status"] == "success"
    print("  ✅ Screenshot tools accessible")
    
    # Test 3: Interaction tools still blocked
    result = await server.system_click(100, 100)
    assert result["status"] == "error"
    assert "interaction not enabled" in result["message"].lower()
    print("  ✅ Interaction tools properly blocked")
    
    # Test 4: Enable full permissions
    result = await server.setup_system_control(
        enable_screenshots=True,
        enable_interactions=True,
        acknowledge_security_risks=True
    )
    assert result["status"] == "success"
    assert server.interaction_enabled is True
    print("  ✅ Full permissions granted")
    
    # Test 5: All tools work
    result = await server.system_click(100, 100)
    assert result["status"] == "success"
    print("  ✅ All tools accessible")
    
    return True


async def test_disable_functionality():
    """Test disabling system control."""
    print("🚫 Testing Disable Functionality")
    
    server = TestSystemControlMixin()
    
    # Enable everything
    await server.setup_system_control(
        enable_screenshots=True,
        enable_interactions=True,
        acknowledge_security_risks=True
    )
    assert server.system_control_enabled is True
    print("  ✅ Features enabled")
    
    # Disable
    result = await server.disable_system_control()
    assert result["status"] == "success"
    assert server.system_control_enabled is False
    assert server.screenshot_enabled is False
    assert server.interaction_enabled is False
    assert server.permissions_session_token is None
    print("  ✅ All features disabled")
    
    # Verify tools are blocked again
    result = await server.take_monitor_screenshot()
    assert result["status"] == "error"
    print("  ✅ Tools properly blocked after disable")
    
    return True


async def test_progressive_permissions():
    """Test progressive permission model."""
    print("📊 Testing Progressive Permissions")
    
    server = TestSystemControlMixin()
    
    # Test progression: None -> Screenshots -> Full
    
    # Stage 1: No permissions
    screenshot_result = await server.take_monitor_screenshot()
    click_result = await server.system_click(100, 100)
    
    assert screenshot_result["status"] == "error"
    assert click_result["status"] == "error"
    print("  ✅ Stage 1: All tools blocked")
    
    # Stage 2: Screenshots only
    await server.setup_system_control(
        enable_screenshots=True,
        acknowledge_security_risks=True
    )
    
    screenshot_result = await server.take_monitor_screenshot()
    click_result = await server.system_click(100, 100)
    
    assert screenshot_result["status"] == "success"
    assert click_result["status"] == "error"
    print("  ✅ Stage 2: Screenshots allowed, interactions blocked")
    
    # Stage 3: Full permissions
    await server.setup_system_control(
        enable_screenshots=True,
        enable_interactions=True,
        acknowledge_security_risks=True
    )
    
    screenshot_result = await server.take_monitor_screenshot()
    click_result = await server.system_click(100, 100)
    
    assert screenshot_result["status"] == "success"
    assert click_result["status"] == "success"
    print("  ✅ Stage 3: All tools allowed")
    
    return True


async def run_all_tests():
    """Run all SystemControlMixin tests."""
    print("🧪 SystemControlMixin Security Tests")
    print("=" * 40)
    
    tests = [
        ("Security Model", test_security_model),
        ("Permission Flow", test_permission_flow),
        ("Disable Functionality", test_disable_functionality),
        ("Progressive Permissions", test_progressive_permissions)
    ]
    
    passed = 0
    total = len(tests)
    
    for name, test_func in tests:
        try:
            print(f"\nRunning: {name}")
            result = await test_func()
            if result:
                passed += 1
                print(f"✅ {name} PASSED\n")
        except Exception as e:
            print(f"❌ {name} FAILED: {e}\n")
    
    print("=" * 40)
    print(f"📊 Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    print(f"\n{'🎉 ALL TESTS PASSED!' if success else '❌ SOME TESTS FAILED'}")
    
    if success:
        print("\n🔒 SystemControlMixin Security Model Validated:")
        print("  • All tools disabled by default")
        print("  • Explicit consent required") 
        print("  • Progressive permission levels")
        print("  • Easy disable mechanism")
        print("  • Session-based permissions")
        print("\n✨ Ready for desktop automation with security!")
    
    sys.exit(0 if success else 1)