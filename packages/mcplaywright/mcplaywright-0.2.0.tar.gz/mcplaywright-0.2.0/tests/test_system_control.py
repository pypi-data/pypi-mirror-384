#!/usr/bin/env python3
"""
Tests for SystemControlMixin

Tests the security model and basic functionality of system control features.
"""

import pytest
import asyncio
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mixins.system_control_mixin import SystemControlMixin


class TestableSystemControlServer(SystemControlMixin):
    """Test server with only SystemControlMixin for isolation."""
    
    def __init__(self):
        super().__init__()
    
    async def get_current_page(self):
        """Mock page for screenshot tests."""
        mock_page = MagicMock()
        mock_page.screenshot.return_value = b"fake_screenshot_data"
        return mock_page
    
    async def take_screenshot(self, **kwargs):
        """Mock browser screenshot method."""
        return {
            "status": "success",
            "filepath": "/tmp/browser_screenshot.png",
            "format": "png"
        }


class TestSystemControlSecurity:
    """Test security model and permission system."""
    
    @pytest.fixture
    def server(self):
        """Create test server instance."""
        return TestableSystemControlServer()
    
    def test_initial_state_secure(self, server):
        """Test that all system control starts disabled."""
        assert server.system_control_enabled is False
        assert server.screenshot_enabled is False
        assert server.interaction_enabled is False
        assert server.permissions_session_token is None
    
    @pytest.mark.asyncio
    async def test_setup_requires_acknowledgment(self, server):
        """Test that setup requires security acknowledgment."""
        # Try without acknowledgment
        result = await server.setup_system_control(
            enable_screenshots=True,
            acknowledge_security_risks=False
        )
        
        assert result["status"] == "error"
        assert "acknowledgment required" in result["message"].lower()
        assert server.screenshot_enabled is False
    
    @pytest.mark.asyncio
    async def test_setup_with_acknowledgment(self, server):
        """Test successful setup with acknowledgment."""
        with patch.object(server, 'pyautogui_available', True):
            result = await server.setup_system_control(
                enable_screenshots=True,
                acknowledge_security_risks=True
            )
            
            assert result["status"] == "success"
            assert server.screenshot_enabled is True
            assert server.permissions_session_token is not None
    
    @pytest.mark.asyncio
    async def test_tools_hidden_without_permission(self, server):
        """Test that restricted tools return permission errors."""
        # Try screenshot without permission
        result = await server.take_monitor_screenshot()
        
        assert result["status"] == "error"
        assert "not enabled" in result["message"]
        assert "setup_required" in result
    
    @pytest.mark.asyncio
    async def test_progressive_permissions(self, server):
        """Test that interaction requires higher permission than screenshots."""
        with patch.object(server, 'pyautogui_available', True):
            # Enable only screenshots
            await server.setup_system_control(
                enable_screenshots=True,
                enable_interactions=False,
                acknowledge_security_risks=True
            )
            
            # Screenshot should work
            with patch('pyautogui.screenshot') as mock_screenshot:
                mock_screenshot.return_value = MagicMock(width=1920, height=1080, save=MagicMock())
                result = await server.take_monitor_screenshot()
                assert result["status"] == "success"
            
            # Interaction should fail
            result = await server.system_click(100, 100)
            assert result["status"] == "error"
            assert "interaction not enabled" in result["message"].lower()
    
    @pytest.mark.asyncio
    async def test_disable_system_control(self, server):
        """Test that disable clears all permissions."""
        with patch.object(server, 'pyautogui_available', True):
            # Enable features
            await server.setup_system_control(
                enable_screenshots=True,
                enable_interactions=True,
                acknowledge_security_risks=True
            )
            
            assert server.system_control_enabled is True
            
            # Disable
            result = await server.disable_system_control()
            
            assert result["status"] == "success"
            assert server.system_control_enabled is False
            assert server.screenshot_enabled is False
            assert server.interaction_enabled is False
            assert server.permissions_session_token is None
    
    @pytest.mark.asyncio
    async def test_status_tool_always_available(self, server):
        """Test that status tool works without permissions."""
        result = await server.get_system_control_status()
        
        assert "system_control_enabled" in result
        assert "capabilities" in result
        assert "pyautogui_available" in result
        # Should work even without permissions


class TestSystemControlFunctionality:
    """Test actual functionality when permissions are granted."""
    
    @pytest.fixture
    async def enabled_server(self):
        """Create server with system control enabled."""
        server = TestableSystemControlServer()
        
        with patch.object(server, 'pyautogui_available', True):
            await server.setup_system_control(
                enable_screenshots=True,
                enable_interactions=True,
                acknowledge_security_risks=True
            )
        
        return server
    
    @pytest.mark.asyncio
    async def test_monitor_screenshot(self, enabled_server):
        """Test monitor screenshot functionality."""
        with patch('pyautogui.screenshot') as mock_screenshot:
            mock_img = MagicMock()
            mock_img.width = 1920
            mock_img.height = 1080
            mock_img.save = MagicMock()
            mock_screenshot.return_value = mock_img
            
            result = await enabled_server.take_monitor_screenshot()
            
            assert result["status"] == "success"
            assert "filepath" in result
            assert result["size"]["width"] == 1920
            assert result["size"]["height"] == 1080
    
    @pytest.mark.asyncio
    async def test_monitor_info(self, enabled_server):
        """Test monitor information retrieval."""
        with patch('pyautogui.size') as mock_size:
            mock_size.return_value = MagicMock(width=1920, height=1080)
            
            result = await enabled_server.get_monitor_info()
            
            assert result["status"] == "success"
            assert result["primary_monitor"]["width"] == 1920
            assert result["primary_monitor"]["height"] == 1080
    
    @pytest.mark.asyncio
    async def test_system_click_with_validation(self, enabled_server):
        """Test system click with coordinate validation."""
        with patch('pyautogui.size') as mock_size, \
             patch('pyautogui.click') as mock_click:
            
            mock_size.return_value = MagicMock(width=1920, height=1080)
            
            # Valid coordinates
            result = await enabled_server.system_click(100, 100)
            assert result["status"] == "success"
            mock_click.assert_called_once()
            
            # Invalid coordinates
            result = await enabled_server.system_click(2000, 2000)
            assert result["status"] == "error"
            assert "out of bounds" in result["message"]
    
    @pytest.mark.asyncio
    async def test_system_type_with_limits(self, enabled_server):
        """Test system typing with safety limits."""
        with patch('pyautogui.typewrite') as mock_type:
            # Normal text
            result = await enabled_server.system_type("Hello World")
            assert result["status"] == "success"
            mock_type.assert_called_once()
            
            # Too long text
            long_text = "x" * 1001
            result = await enabled_server.system_type(long_text)
            assert result["status"] == "error"
            assert "too long" in result["message"]
    
    @pytest.mark.asyncio
    async def test_browser_monitor_comparison(self, enabled_server):
        """Test browser vs monitor screenshot comparison."""
        with patch('pyautogui.screenshot') as mock_screenshot:
            mock_img = MagicMock()
            mock_img.width = 1920
            mock_img.height = 1080
            mock_img.save = MagicMock()
            mock_screenshot.return_value = mock_img
            
            result = await enabled_server.compare_browser_and_monitor()
            
            assert result["status"] == "success"
            assert "comparison" in result
            assert "browser" in result["comparison"]
            assert "monitor" in result["comparison"]


class TestPyAutoGUIIntegration:
    """Test PyAutoGUI integration and error handling."""
    
    def test_pyautogui_unavailable_handling(self):
        """Test graceful handling when PyAutoGUI is unavailable."""
        with patch('pyautogui.FAILSAFE', side_effect=ImportError("No PyAutoGUI")):
            server = TestableSystemControlServer()
            assert server.pyautogui_available is False
    
    @pytest.mark.asyncio
    async def test_setup_without_pyautogui(self):
        """Test setup failure when PyAutoGUI unavailable."""
        server = TestableSystemControlServer()
        server.pyautogui_available = False
        
        result = await server.setup_system_control(
            enable_screenshots=True,
            acknowledge_security_risks=True
        )
        
        assert result["status"] == "error"
        assert "PyAutoGUI not available" in result["message"]


def test_permission_decorator():
    """Test the permission decorator functionality."""
    from mixins.system_control_mixin import require_system_permission
    
    # Create a mock method
    @require_system_permission("screenshot")
    async def mock_method(self):
        return {"status": "success"}
    
    # Test with permission denied
    mock_self = MagicMock()
    mock_self._check_system_permission.return_value = False
    
    result = asyncio.run(mock_method(mock_self))
    assert result["status"] == "error"
    assert "not enabled" in result["message"]


if __name__ == "__main__":
    # Run basic tests
    print("🧪 Testing SystemControlMixin Security Model")
    
    async def run_basic_tests():
        server = TestableSystemControlServer()
        
        # Test initial state
        assert server.system_control_enabled is False
        print("✅ Initial state secure")
        
        # Test permission requirement
        result = await server.take_monitor_screenshot()
        assert result["status"] == "error"
        print("✅ Tools properly protected")
        
        # Test status tool always works
        status = await server.get_system_control_status()
        assert "system_control_enabled" in status
        print("✅ Status tool available")
        
        print("🎉 Basic security tests passed!")
    
    asyncio.run(run_basic_tests())