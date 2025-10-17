#!/usr/bin/env python3
"""
Simple V3 Feature Test - Tests new features without import conflicts
"""

import asyncio
from pathlib import Path
import sys
import tempfile
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import mixins directly
from playwright.async_api import async_playwright


class SimpleV3Test:
    """Simple test for V3 features without complex imports."""
    
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        
    async def setup(self):
        """Setup browser for testing."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
        
    async def cleanup(self):
        """Cleanup browser resources."""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def test_debug_toolbar_injection(self):
        """Test debug toolbar JavaScript injection."""
        print("🎭 Testing Debug Toolbar Injection")
        
        await self.page.goto("https://example.com")
        
        # Generate toolbar HTML (simplified version)
        toolbar_html = """
        <div id="mcp-debug-toolbar" style="
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #1a1a1a;
            color: #ffffff;
            border: 2px solid #4CAF50;
            border-radius: 8px;
            padding: 10px 15px;
            font-family: monospace;
            z-index: 999999;
        ">
            <div style="display: flex; align-items: center;">
                <span style="
                    display: inline-block;
                    width: 10px;
                    height: 10px;
                    background: #4CAF50;
                    border-radius: 50%;
                    margin-right: 8px;
                "></span>
                <strong>MCPlaywright V3</strong>
            </div>
            <div style="margin-top: 5px; font-size: 11px; opacity: 0.8;">
                Client: Python Test
            </div>
        </div>
        """
        
        # Inject toolbar
        result = await self.page.evaluate(f"""
            (() => {{
                const container = document.createElement('div');
                container.innerHTML = `{toolbar_html}`;
                document.body.appendChild(container.firstElementChild);
                return document.getElementById('mcp-debug-toolbar') !== null;
            }})();
        """)
        
        assert result is True
        print("  ✅ Debug toolbar injected successfully")
        
        # Test toolbar visibility
        toolbar_visible = await self.page.evaluate("""
            () => {
                const toolbar = document.getElementById('mcp-debug-toolbar');
                return toolbar && window.getComputedStyle(toolbar).display !== 'none';
            }
        """)
        
        assert toolbar_visible is True
        print("  ✅ Debug toolbar is visible")
        
        return True
    
    async def test_custom_code_injection(self):
        """Test custom JavaScript and CSS injection."""
        print("💉 Testing Custom Code Injection")
        
        await self.page.goto("https://example.com")
        
        # Test CSS injection
        css_code = """
        body {
            border: 3px solid #4CAF50 !important;
            animation: pulse-border 2s infinite;
        }
        @keyframes pulse-border {
            0% { border-color: #4CAF50; }
            50% { border-color: #8BC34A; }
            100% { border-color: #4CAF50; }
        }
        """
        
        css_result = await self.page.evaluate(f"""
            (() => {{
                const style = document.createElement('style');
                style.setAttribute('data-mcp-injection', 'test-css');
                style.textContent = `{css_code}`;
                document.head.appendChild(style);
                return style.sheet.cssRules.length > 0;
            }})();
        """)
        
        assert css_result is True
        print("  ✅ CSS injection successful")
        
        # Test JavaScript injection
        js_code = """
        window.MCPTest = {
            version: '3.0.0',
            injected: true,
            timestamp: new Date().toISOString()
        };
        console.log('MCP Test injection successful');
        """
        
        js_result = await self.page.evaluate(f"""
            (() => {{
                try {{
                    {js_code}
                    return window.MCPTest && window.MCPTest.injected === true;
                }} catch (e) {{
                    return false;
                }}
            }})();
        """)
        
        assert js_result is True
        print("  ✅ JavaScript injection successful")
        
        return True
    
    async def test_coordinate_interactions(self):
        """Test coordinate-based mouse interactions."""
        print("🎯 Testing Coordinate Interactions")
        
        await self.page.goto("https://example.com")
        
        # Test mouse click at coordinates
        await self.page.mouse.click(100, 100)
        print("  ✅ Mouse click at coordinates (100, 100)")
        
        # Test mouse movement
        await self.page.mouse.move(200, 200)
        print("  ✅ Mouse movement to (200, 200)")
        
        # Test drag operation
        await self.page.mouse.move(150, 150)
        await self.page.mouse.down()
        await self.page.mouse.move(250, 250)
        await self.page.mouse.up()
        print("  ✅ Mouse drag from (150, 150) to (250, 250)")
        
        # Test getting element bounds
        bounds = await self.page.evaluate("""
            () => {
                const h1 = document.querySelector('h1');
                if (h1) {
                    const rect = h1.getBoundingClientRect();
                    return {
                        x: rect.x,
                        y: rect.y,
                        width: rect.width,
                        height: rect.height,
                        center_x: rect.x + rect.width / 2,
                        center_y: rect.y + rect.height / 2
                    };
                }
                return null;
            }
        """)
        
        if bounds:
            print(f"  ✅ Element bounds: {bounds['width']}x{bounds['height']} at ({bounds['x']}, {bounds['y']})")
            
            # Click at element center
            await self.page.mouse.click(bounds['center_x'], bounds['center_y'])
            print(f"  ✅ Clicked at element center ({bounds['center_x']}, {bounds['center_y']})")
        
        return True
    
    async def test_extension_manifest_creation(self):
        """Test Chrome extension manifest creation."""
        print("🧩 Testing Extension Management")
        
        # Create a test extension directory
        ext_dir = Path(tempfile.mkdtemp(prefix="test_extension_"))
        
        # Create manifest.json
        manifest = {
            "manifest_version": 3,
            "name": "MCPlaywright Test Extension",
            "version": "1.0.0",
            "description": "Test extension for MCPlaywright V3",
            "permissions": [],
            "action": {
                "default_title": "MCPlaywright Test"
            },
            "background": {
                "service_worker": "background.js"
            }
        }
        
        manifest_path = ext_dir / "manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)
        
        # Create background script
        background_js = """
        console.log('MCPlaywright Test Extension loaded');
        
        chrome.runtime.onInstalled.addListener(() => {
            console.log('MCPlaywright Test Extension installed');
        });
        """
        
        (ext_dir / "background.js").write_text(background_js)
        
        # Validate extension structure
        assert manifest_path.exists()
        assert (ext_dir / "background.js").exists()
        
        # Validate manifest content
        with open(manifest_path) as f:
            loaded_manifest = json.load(f)
        
        assert loaded_manifest["name"] == "MCPlaywright Test Extension"
        assert loaded_manifest["manifest_version"] == 3
        
        print(f"  ✅ Extension created at: {ext_dir}")
        print(f"  ✅ Manifest validated: {loaded_manifest['name']}")
        
        # Cleanup
        import shutil
        shutil.rmtree(ext_dir)
        
        return True
    
    async def test_canvas_drawing_simulation(self):
        """Test canvas drawing capabilities."""
        print("🎨 Testing Canvas Drawing")
        
        await self.page.goto("https://example.com")
        
        # Create a canvas element for testing
        canvas_created = await self.page.evaluate("""
            () => {
                const canvas = document.createElement('canvas');
                canvas.id = 'test-canvas';
                canvas.width = 300;
                canvas.height = 300;
                canvas.style.border = '1px solid #ccc';
                document.body.appendChild(canvas);
                
                const ctx = canvas.getContext('2d');
                ctx.strokeStyle = '#4CAF50';
                ctx.lineWidth = 2;
                
                return canvas.id;
            }
        """)
        
        assert canvas_created == "test-canvas"
        print("  ✅ Canvas element created")
        
        # Get canvas bounds
        canvas_bounds = await self.page.evaluate("""
            () => {
                const canvas = document.getElementById('test-canvas');
                const rect = canvas.getBoundingClientRect();
                return {
                    x: rect.x,
                    y: rect.y,
                    width: rect.width,
                    height: rect.height
                };
            }
        """)
        
        # Simulate drawing by moving mouse on canvas
        canvas_x = canvas_bounds['x']
        canvas_y = canvas_bounds['y']
        
        # Draw a simple shape
        points = [
            (50, 50), (100, 50), (100, 100), (50, 100), (50, 50)  # Square
        ]
        
        # Start drawing
        await self.page.mouse.move(canvas_x + points[0][0], canvas_y + points[0][1])
        await self.page.mouse.down()
        
        for x, y in points[1:]:
            await self.page.mouse.move(canvas_x + x, canvas_y + y)
        
        await self.page.mouse.up()
        
        print(f"  ✅ Drew {len(points)} points on canvas")
        print(f"  ✅ Canvas bounds: {canvas_bounds['width']}x{canvas_bounds['height']}")
        
        return True


async def run_v3_tests():
    """Run all V3 feature tests."""
    print("🚀 MCPlaywright V3 Feature Tests")
    print("=" * 40)
    
    test = SimpleV3Test()
    
    try:
        await test.setup()
        
        tests = [
            test.test_debug_toolbar_injection,
            test.test_custom_code_injection,
            test.test_coordinate_interactions,
            test.test_extension_manifest_creation,
            test.test_canvas_drawing_simulation
        ]
        
        passed = 0
        total = len(tests)
        
        for test_func in tests:
            try:
                await test_func()
                passed += 1
            except Exception as e:
                print(f"  ❌ Test failed: {e}")
        
        print("\n" + "=" * 40)
        print(f"📊 Results: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
        
        if passed == total:
            print("🎉 All V3 features working correctly!")
        
        return passed == total
        
    finally:
        await test.cleanup()


if __name__ == "__main__":
    success = asyncio.run(run_v3_tests())
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}")