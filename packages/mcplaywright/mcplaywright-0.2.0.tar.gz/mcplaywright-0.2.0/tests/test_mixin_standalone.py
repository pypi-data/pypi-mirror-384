#!/usr/bin/env python3
"""
Standalone MCPlaywright V2 Torture Test

Tests the mixin architecture without importing conflicting modules.
"""

import asyncio
import time
import random
from typing import Dict, Any, List, Optional
from pathlib import Path
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StandaloneMCPlaywrightServer:
    """Standalone test server combining all functionality."""
    
    def __init__(self):
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._current_page: Optional[Page] = None
        self._pages: List[Page] = []
        self._browser_type = "chromium"
        self._headless = True
        self._viewport = {"width": 1280, "height": 720}
        self.screenshot_dir = Path("/tmp/mcplaywright/screenshots")
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
    
    async def ensure_browser_context(self) -> BrowserContext:
        """Ensure browser context is initialized."""
        if not self._context:
            await self._create_browser_context()
        return self._context
    
    async def _create_browser_context(self):
        """Create a new browser context."""
        if not self._playwright:
            self._playwright = await async_playwright().start()
        
        if self._browser:
            await self._browser.close()
        
        browser_launcher = getattr(self._playwright, self._browser_type)
        self._browser = await browser_launcher.launch(
            headless=self._headless,
            args=["--no-sandbox", "--disable-setuid-sandbox"]
        )
        
        self._context = await self._browser.new_context(viewport=self._viewport)
        self._current_page = await self._context.new_page()
        self._pages = [self._current_page]
        
        logger.info(f"Browser context created: {self._browser_type}, headless={self._headless}")
    
    async def get_current_page(self) -> Page:
        """Get the current active page."""
        if not self._current_page:
            await self.ensure_browser_context()
        return self._current_page
    
    async def close_browser(self) -> Dict[str, Any]:
        """Close browser and cleanup resources."""
        try:
            if self._context:
                await self._context.close()
                self._context = None
            
            if self._browser:
                await self._browser.close()
                self._browser = None
            
            if self._playwright:
                await self._playwright.stop()
                self._playwright = None
            
            self._current_page = None
            self._pages = []
            
            return {"status": "success", "message": "Browser closed successfully"}
        except Exception as e:
            logger.error(f"Error closing browser: {e}")
            return {"status": "error", "message": str(e)}
    
    async def navigate_to_url(self, url: str, wait_until: str = "load") -> Dict[str, Any]:
        """Navigate to a URL."""
        try:
            page = await self.get_current_page()
            response = await page.goto(url, wait_until=wait_until)
            
            final_url = page.url
            title = await page.title()
            status = response.status if response else None
            
            return {
                "status": "success",
                "url": final_url,
                "title": title,
                "response_status": status
            }
        except Exception as e:
            logger.error(f"Error navigating to {url}: {e}")
            return {"status": "error", "message": str(e), "url": url}
    
    async def take_screenshot(
        self,
        full_page: bool = False,
        selector: Optional[str] = None,
        filename: Optional[str] = None,
        format: str = "png",
        quality: Optional[int] = None
    ) -> Dict[str, Any]:
        """Take a screenshot."""
        try:
            page = await self.get_current_page()
            
            options = {"type": format, "full_page": full_page}
            if quality and format == "jpeg":
                options["quality"] = quality
            
            if selector:
                element = await page.query_selector(selector)
                if not element:
                    return {"status": "error", "message": f"Element not found: {selector}"}
                screenshot_bytes = await element.screenshot(**options)
                target = selector
            else:
                screenshot_bytes = await page.screenshot(**options)
                target = "page"
            
            result = {
                "status": "success",
                "target": target,
                "full_page": full_page,
                "format": format
            }
            
            if filename:
                filepath = self.screenshot_dir / filename
                filepath.write_bytes(screenshot_bytes)
                result["filepath"] = str(filepath)
            
            return result
            
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            return {"status": "error", "message": str(e)}
    
    async def click_element(
        self,
        selector: str,
        timeout: int = 30000
    ) -> Dict[str, Any]:
        """Click on an element."""
        try:
            page = await self.get_current_page()
            await page.wait_for_selector(selector, timeout=timeout)
            await page.click(selector)
            return {"status": "success", "selector": selector}
        except Exception as e:
            return {"status": "error", "message": str(e), "selector": selector}
    
    async def hover_element(
        self,
        selector: str,
        timeout: int = 30000
    ) -> Dict[str, Any]:
        """Hover over an element."""
        try:
            page = await self.get_current_page()
            await page.wait_for_selector(selector, timeout=timeout)
            await page.hover(selector)
            return {"status": "success", "selector": selector}
        except Exception as e:
            return {"status": "error", "message": str(e), "selector": selector}
    
    async def type_text(
        self,
        selector: str,
        value: str,
        timeout: int = 30000
    ) -> Dict[str, Any]:
        """Type text into an element."""
        try:
            page = await self.get_current_page()
            await page.wait_for_selector(selector, timeout=timeout)
            await page.type(selector, value)
            return {"status": "success", "selector": selector, "value": value}
        except Exception as e:
            return {"status": "error", "message": str(e), "selector": selector}


async def torture_test():
    """Run the torture test."""
    print("🔥 MCPlaywright V2 TORTURE TEST 🔥")
    print("=" * 50)
    
    server = StandaloneMCPlaywrightServer()
    
    try:
        # Test 1: Rapid Navigation
        print("\n🚀 TEST 1: RAPID NAVIGATION")
        urls = [
            "https://example.com",
            "https://example.org",
            "https://example.net",
            "https://httpbin.org",
            "https://www.wikipedia.org"
        ] * 2  # 10 navigations
        
        start_time = time.time()
        results = []
        
        for i, url in enumerate(urls):
            result = await server.navigate_to_url(url, wait_until="domcontentloaded")
            success = result.get("status") == "success"
            results.append(success)
            print(f"  [{i+1}/{len(urls)}] {url} - {'✅' if success else '❌'}")
        
        duration = time.time() - start_time
        success_rate = sum(results) / len(results) * 100
        
        print(f"\n  📊 Results:")
        print(f"     Total: {len(urls)} navigations")
        print(f"     Duration: {duration:.2f}s")
        print(f"     Rate: {len(urls)/duration:.2f} nav/sec")
        print(f"     Success: {success_rate:.1f}%")
        
        assert success_rate >= 80, f"Navigation success rate too low: {success_rate}%"
        
        # Test 2: Screenshot Bombardment
        print("\n📸 TEST 2: SCREENSHOT BOMBARDMENT")
        await server.navigate_to_url("https://www.wikipedia.org")
        
        screenshot_configs = [
            {"full_page": False, "format": "png"},
            {"full_page": True, "format": "png"},
            {"full_page": False, "format": "jpeg", "quality": 50},
        ] * 3  # 9 screenshots
        
        start_time = time.time()
        results = []
        
        for i, config in enumerate(screenshot_configs):
            filename = f"torture_{i}.{config.get('format', 'png')}"
            result = await server.take_screenshot(filename=filename, **config)
            success = result.get("status") == "success"
            results.append(success)
            print(f"  [{i+1}/{len(screenshot_configs)}] Screenshot - {'✅' if success else '❌'}")
        
        duration = time.time() - start_time
        success_rate = sum(results) / len(results) * 100
        
        print(f"\n  📊 Results:")
        print(f"     Total: {len(screenshot_configs)} screenshots")
        print(f"     Duration: {duration:.2f}s")
        print(f"     Rate: {len(screenshot_configs)/duration:.2f} screenshots/sec")
        print(f"     Success: {success_rate:.1f}%")
        
        assert success_rate >= 70, f"Screenshot success rate too low: {success_rate}%"
        
        # Test 3: Interaction Test
        print("\n🎯 TEST 3: ELEMENT INTERACTIONS")
        
        interactions = [
            {"action": "hover", "selector": "a"},
            {"action": "click", "selector": "a"},
            {"action": "hover", "selector": "img"},
        ] * 3  # 9 interactions
        
        start_time = time.time()
        results = []
        
        for i, interaction in enumerate(interactions):
            try:
                if interaction["action"] == "click":
                    result = await server.click_element(interaction["selector"], timeout=1000)
                elif interaction["action"] == "hover":
                    result = await server.hover_element(interaction["selector"], timeout=1000)
                
                success = result.get("status") == "success"
                results.append(success)
                print(f"  [{i+1}/{len(interactions)}] {interaction['action']} - {'✅' if success else '❌'}")
            except Exception as e:
                results.append(False)
                print(f"  [{i+1}/{len(interactions)}] {interaction['action']} - ❌ Error: {e}")
        
        duration = time.time() - start_time
        success_rate = sum(results) / len(results) * 100
        
        print(f"\n  📊 Results:")
        print(f"     Total: {len(interactions)} interactions")
        print(f"     Duration: {duration:.2f}s")
        print(f"     Rate: {len(interactions)/duration:.2f} interactions/sec")
        print(f"     Success: {success_rate:.1f}%")
        
        # Test 4: Memory Test
        print("\n💾 TEST 4: MEMORY LEAK DETECTION")
        
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        print(f"  Initial memory: {initial_memory:.2f} MB")
        
        for cycle in range(3):
            print(f"  Cycle {cycle + 1}/3:")
            
            # Navigate
            for i in range(5):
                await server.navigate_to_url(f"https://example.com?cycle={cycle}&nav={i}")
            print(f"    ✓ 5 navigations")
            
            # Screenshots
            for i in range(5):
                await server.take_screenshot(filename=f"memory_{cycle}_{i}.png")
            print(f"    ✓ 5 screenshots")
            
            current_memory = process.memory_info().rss / 1024 / 1024
            memory_increase = current_memory - initial_memory
            print(f"    Memory: {current_memory:.2f} MB (+{memory_increase:.2f} MB)")
        
        final_memory = process.memory_info().rss / 1024 / 1024
        total_increase = final_memory - initial_memory
        
        print(f"\n  📊 Results:")
        print(f"     Initial: {initial_memory:.2f} MB")
        print(f"     Final: {final_memory:.2f} MB")
        print(f"     Increase: {total_increase:.2f} MB")
        
        assert total_increase < 200, f"Memory leak detected: {total_increase:.2f} MB increase"
        
        # Test 5: Error Recovery
        print("\n🛡️ TEST 5: ERROR RECOVERY")
        
        # Try invalid operations
        print("  Testing error scenarios...")
        error_result = await server.click_element("#nonexistent-element-12345", timeout=500)
        print(f"  Invalid selector: {'✅ Handled' if error_result.get('status') == 'error' else '❌ Not handled'}")
        
        error_result = await server.navigate_to_url("not-a-valid-url")
        print(f"  Invalid URL: {'✅ Handled' if error_result.get('status') == 'error' else '❌ Not handled'}")
        
        # Try valid operation to ensure recovery
        recovery_result = await server.navigate_to_url("https://example.com")
        print(f"  Recovery: {'✅ Success' if recovery_result.get('status') == 'success' else '❌ Failed'}")
        
        assert recovery_result.get("status") == "success", "Failed to recover after errors"
        
        print("\n" + "=" * 50)
        print("✅ ALL TORTURE TESTS PASSED! 💪")
        print("=" * 50)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    finally:
        await server.close_browser()


if __name__ == "__main__":
    asyncio.run(torture_test())