#!/usr/bin/env python3
"""
MCPlaywright V3 Feature Parity Test Suite

Comprehensive tests for all new features:
- MCP Client Identification System
- Chrome Extension Management
- Coordinate-Based Interactions
"""

import asyncio
import pytest
from pathlib import Path
import json
from typing import Dict, Any
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from mixins.client_identification_mixin import ClientIdentificationMixin
from mixins.extension_mixin import ExtensionManagementMixin
from mixins.coordinate_mixin import CoordinateInteractionMixin
from mixins.browser_mixin import BrowserMixin
from mixins.navigation_mixin import NavigationMixin


class TestableServer(
    BrowserMixin,
    NavigationMixin,
    ClientIdentificationMixin,
    ExtensionManagementMixin,
    CoordinateInteractionMixin
):
    """Test server combining all new mixins."""
    pass


class TestClientIdentification:
    """Test MCP Client Identification System."""
    
    @pytest.fixture
    async def server(self):
        server = TestableServer()
        yield server
        await server.close_browser()
    
    @pytest.mark.asyncio
    async def test_debug_toolbar_enable(self, server):
        """Test enabling the debug toolbar."""
        # Navigate to a page
        await server.navigate_to_url("https://example.com")
        
        # Enable toolbar
        result = await server.enable_debug_toolbar(
            project_name="Test Client",
            theme="dark",
            position="bottom-right"
        )
        
        assert result["status"] == "success"
        assert "session" in result
        assert server.toolbar_enabled is True
        assert "debug_toolbar" in server.injections
    
    @pytest.mark.asyncio
    async def test_custom_code_injection(self, server):
        """Test JavaScript and CSS injection."""
        await server.navigate_to_url("https://example.com")
        
        # Test JavaScript injection
        js_result = await server.inject_custom_code(
            name="test_js",
            code="console.log('Test injection');",
            type="javascript"
        )
        
        assert js_result["status"] == "success"
        assert "test_js" in server.injections
        
        # Test CSS injection
        css_result = await server.inject_custom_code(
            name="test_css",
            code="body { border: 1px solid red; }",
            type="css"
        )
        
        assert css_result["status"] == "success"
        assert "test_css" in server.injections
    
    @pytest.mark.asyncio
    async def test_list_injections(self, server):
        """Test listing active injections."""
        await server.navigate_to_url("https://example.com")
        
        # Add some injections
        await server.enable_debug_toolbar()
        await server.inject_custom_code("test1", "// test", "javascript")
        await server.inject_custom_code("test2", "/* test */", "css")
        
        # List injections
        result = await server.list_injections()
        
        assert result["status"] == "success"
        assert result["injection_count"] == 3  # toolbar + 2 custom
        assert len(result["injections"]) == 3
    
    @pytest.mark.asyncio
    async def test_clear_injections(self, server):
        """Test clearing injections."""
        await server.navigate_to_url("https://example.com")
        
        # Add injections
        await server.inject_custom_code("test1", "// test", "javascript")
        await server.inject_custom_code("test2", "/* test */", "css")
        
        # Clear injections (not toolbar)
        result = await server.clear_injections(include_toolbar=False)
        
        assert result["status"] == "success"
        assert result["message"] == "Cleared 2 injections"
        
        # Clear all including toolbar
        await server.enable_debug_toolbar()
        result = await server.clear_injections(include_toolbar=True)
        
        assert server.toolbar_enabled is False
    
    @pytest.mark.asyncio
    async def test_disable_toolbar(self, server):
        """Test disabling the debug toolbar."""
        await server.navigate_to_url("https://example.com")
        
        # Enable then disable
        await server.enable_debug_toolbar()
        assert server.toolbar_enabled is True
        
        result = await server.disable_debug_toolbar()
        
        assert result["status"] == "success"
        assert server.toolbar_enabled is False
        assert "debug_toolbar" not in server.injections


class TestExtensionManagement:
    """Test Chrome Extension Management."""
    
    @pytest.fixture
    async def server(self):
        server = TestableServer()
        yield server
        await server.close_browser()
    
    @pytest.mark.asyncio
    async def test_install_extension(self, server):
        """Test installing an extension."""
        # Create a test extension directory
        test_ext_dir = Path("/tmp/test_extension")
        test_ext_dir.mkdir(exist_ok=True)
        
        # Create manifest.json
        manifest = {
            "manifest_version": 3,
            "name": "Test Extension",
            "version": "1.0.0"
        }
        (test_ext_dir / "manifest.json").write_text(json.dumps(manifest))
        
        # Install extension
        result = await server.install_extension(
            path=str(test_ext_dir),
            name="Test Extension"
        )
        
        assert result["status"] == "success"
        assert result["name"] == "Test Extension"
        assert str(test_ext_dir) in server.installed_extensions
    
    @pytest.mark.asyncio
    async def test_install_popular_extension(self, server):
        """Test installing a popular extension."""
        result = await server.install_popular_extension("react-devtools")
        
        assert result["status"] == "success"
        assert result["extension"] == "react-devtools"
        assert result["name"] == "React Developer Tools"
        assert result["restart_required"] is True
    
    @pytest.mark.asyncio
    async def test_list_extensions(self, server):
        """Test listing extensions."""
        # Install some extensions
        await server.install_popular_extension("react-devtools")
        await server.install_popular_extension("vue-devtools")
        
        # List extensions
        result = await server.list_extensions()
        
        assert result["status"] == "success"
        assert result["count"] == 2
        assert len(result["extensions"]) == 2
        assert "react-devtools" in result["popular_available"]
    
    @pytest.mark.asyncio
    async def test_uninstall_extension(self, server):
        """Test uninstalling an extension."""
        # Install then uninstall
        test_ext_dir = Path("/tmp/test_ext_uninstall")
        test_ext_dir.mkdir(exist_ok=True)
        (test_ext_dir / "manifest.json").write_text('{"manifest_version": 3, "name": "Test", "version": "1.0"}')
        
        await server.install_extension(str(test_ext_dir))
        
        result = await server.uninstall_extension(str(test_ext_dir))
        
        assert result["status"] == "success"
        assert str(test_ext_dir) not in server.installed_extensions


class TestCoordinateInteractions:
    """Test Coordinate-Based Interactions."""
    
    @pytest.fixture
    async def server(self):
        server = TestableServer()
        yield server
        await server.close_browser()
    
    @pytest.mark.asyncio
    async def test_mouse_click_xy(self, server):
        """Test clicking at specific coordinates."""
        await server.navigate_to_url("https://example.com")
        
        result = await server.mouse_click_xy(100, 200, button="left")
        
        assert result["status"] == "success"
        assert result["coordinates"] == {"x": 100, "y": 200}
        assert result["button"] == "left"
    
    @pytest.mark.asyncio
    async def test_mouse_drag_xy(self, server):
        """Test dragging between coordinates."""
        await server.navigate_to_url("https://example.com")
        
        result = await server.mouse_drag_xy(
            start_x=100, start_y=100,
            end_x=300, end_y=300,
            steps=5
        )
        
        assert result["status"] == "success"
        assert result["start"] == {"x": 100, "y": 100}
        assert result["end"] == {"x": 300, "y": 300}
        assert result["steps"] == 5
    
    @pytest.mark.asyncio
    async def test_mouse_move_xy(self, server):
        """Test moving mouse to coordinates."""
        await server.navigate_to_url("https://example.com")
        
        result = await server.mouse_move_xy(250, 250, steps=3)
        
        assert result["status"] == "success"
        assert result["coordinates"] == {"x": 250, "y": 250}
        assert result["steps"] == 3
    
    @pytest.mark.asyncio
    async def test_mouse_wheel(self, server):
        """Test mouse wheel scrolling."""
        await server.navigate_to_url("https://example.com")
        
        result = await server.mouse_wheel(delta_x=0, delta_y=100)
        
        assert result["status"] == "success"
        assert result["delta"] == {"x": 0, "y": 100}
    
    @pytest.mark.asyncio
    async def test_get_element_bounds(self, server):
        """Test getting element bounding box."""
        await server.navigate_to_url("https://example.com")
        
        result = await server.get_element_bounds("h1")
        
        if result["status"] == "success":
            assert "bounds" in result
            assert "center" in result
            assert "x" in result["bounds"]
            assert "y" in result["bounds"]
            assert "width" in result["bounds"]
            assert "height" in result["bounds"]
    
    @pytest.mark.asyncio
    async def test_draw_on_canvas(self, server):
        """Test drawing on canvas (if canvas exists)."""
        # Navigate to a page with canvas (or create one)
        await server.navigate_to_url("https://example.com")
        
        # Inject a canvas for testing
        page = await server.get_current_page()
        await page.evaluate("""
            () => {
                const canvas = document.createElement('canvas');
                canvas.id = 'test-canvas';
                canvas.width = 400;
                canvas.height = 400;
                document.body.appendChild(canvas);
            }
        """)
        
        # Draw on canvas
        points = [(10, 10), (50, 50), (100, 50), (100, 100)]
        result = await server.draw_on_canvas(
            selector="#test-canvas",
            points=points,
            draw_speed=2
        )
        
        assert result["status"] == "success"
        assert result["points_drawn"] == len(points)


class TestIntegration:
    """Integration tests for V3 features working together."""
    
    @pytest.fixture
    async def server(self):
        server = TestableServer()
        yield server
        await server.close_browser()
    
    @pytest.mark.asyncio
    async def test_toolbar_with_navigation(self, server):
        """Test toolbar persistence across navigation."""
        # Enable toolbar
        await server.navigate_to_url("https://example.com")
        await server.enable_debug_toolbar(project_name="Integration Test")
        
        # Navigate to another page
        await server.navigate_to_url("https://example.org")
        
        # Toolbar should still be in injections
        assert server.toolbar_enabled is True
        assert "debug_toolbar" in server.injections
    
    @pytest.mark.asyncio
    async def test_coordinate_interaction_with_bounds(self, server):
        """Test coordinate interactions using element bounds."""
        await server.navigate_to_url("https://example.com")
        
        # Get element bounds
        bounds_result = await server.get_element_bounds("h1")
        
        if bounds_result["status"] == "success":
            center = bounds_result["center"]
            
            # Click at element center
            click_result = await server.mouse_click_xy(center["x"], center["y"])
            
            assert click_result["status"] == "success"
            assert click_result["coordinates"]["x"] == center["x"]
            assert click_result["coordinates"]["y"] == center["y"]
    
    @pytest.mark.asyncio
    async def test_extension_browser_args(self, server):
        """Test browser arguments for extensions."""
        # Install extensions
        await server.install_popular_extension("react-devtools")
        await server.install_popular_extension("vue-devtools")
        
        # Get browser args
        args = server._get_browser_args_for_extensions()
        
        assert len(args) >= 2  # At least load-extension args
        assert any("--load-extension" in arg for arg in args)


async def run_all_v3_tests():
    """Run all V3 feature tests."""
    print("🧪 MCPlaywright V3 Feature Parity Test Suite")
    print("=" * 50)
    
    test_classes = [
        TestClientIdentification,
        TestExtensionManagement,
        TestCoordinateInteractions,
        TestIntegration
    ]
    
    total_tests = 0
    passed_tests = 0
    failed_tests = []
    
    for test_class in test_classes:
        print(f"\n📋 Testing {test_class.__name__}")
        
        test_instance = test_class()
        server = TestableServer()
        
        # Get all test methods
        test_methods = [m for m in dir(test_instance) if m.startswith("test_")]
        
        for method_name in test_methods:
            total_tests += 1
            try:
                method = getattr(test_instance, method_name)
                await method(server)
                passed_tests += 1
                print(f"  ✅ {method_name}")
            except Exception as e:
                failed_tests.append((test_class.__name__, method_name, str(e)))
                print(f"  ❌ {method_name}: {e}")
        
        await server.close_browser()
    
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print(f"  Total: {total_tests}")
    print(f"  Passed: {passed_tests}")
    print(f"  Failed: {len(failed_tests)}")
    print(f"  Success Rate: {(passed_tests/total_tests*100):.1f}%")
    
    if failed_tests:
        print("\n❌ Failed Tests:")
        for class_name, method, error in failed_tests:
            print(f"  {class_name}.{method}: {error}")
    
    return passed_tests == total_tests


if __name__ == "__main__":
    success = asyncio.run(run_all_v3_tests())
    sys.exit(0 if success else 1)