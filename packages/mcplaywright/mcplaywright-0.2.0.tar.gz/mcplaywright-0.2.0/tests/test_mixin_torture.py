#!/usr/bin/env python3
"""
MCPlaywright V2 Torture Test Suite

Comprehensive stress testing for the mixin architecture and bulk operations.
This will test the absolute limits of the system.
"""

import asyncio
import time
import random
from typing import Dict, Any, List
import pytest
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import mixins directly to avoid conflicts
from mixins.browser_mixin import BrowserMixin
from mixins.navigation_mixin import NavigationMixin
from mixins.interaction_mixin import InteractionMixin
from mixins.screenshot_mixin import ScreenshotMixin

# Create a test server class combining mixins
class MCPlaywrightServer(BrowserMixin, NavigationMixin, InteractionMixin, ScreenshotMixin):
    def __init__(self):
        super().__init__()


class TestMCPlaywrightTorture:
    """Torture test suite - push everything to the limit."""
    
    @pytest.fixture
    async def server(self):
        """Create a test server instance."""
        server = MCPlaywrightServer()
        yield server
        await server.close_browser()
    
    @pytest.mark.asyncio
    async def test_rapid_navigation_stress(self, server):
        """Hammer the navigation system with rapid-fire requests."""
        print("\n🔥 RAPID NAVIGATION STRESS TEST")
        
        urls = [
            "https://example.com",
            "https://example.org", 
            "https://example.net",
            "https://httpbin.org",
            "https://www.wikipedia.org",
            "https://archive.org",
        ] * 5  # 30 navigations
        
        start_time = time.time()
        results = []
        
        for i, url in enumerate(urls):
            try:
                result = await server.navigate_to_url(url, wait_until="domcontentloaded")
                results.append({
                    "url": url,
                    "success": result.get("status") == "success",
                    "time": time.time() - start_time
                })
                print(f"  [{i+1}/{len(urls)}] {url} - {'✅' if result.get('status') == 'success' else '❌'}")
            except Exception as e:
                print(f"  [{i+1}/{len(urls)}] {url} - ❌ ERROR: {e}")
                results.append({
                    "url": url,
                    "success": False,
                    "error": str(e)
                })
        
        duration = time.time() - start_time
        success_rate = sum(1 for r in results if r["success"]) / len(results) * 100
        
        print(f"\n  📊 Results:")
        print(f"     Total: {len(urls)} navigations")
        print(f"     Duration: {duration:.2f}s")
        print(f"     Rate: {len(urls)/duration:.2f} nav/sec")
        print(f"     Success: {success_rate:.1f}%")
        
        assert success_rate >= 80, f"Navigation success rate too low: {success_rate}%"
    
    @pytest.mark.asyncio
    async def test_screenshot_bombardment(self, server):
        """Take screenshots as fast as possible."""
        print("\n📸 SCREENSHOT BOMBARDMENT TEST")
        
        # Navigate to a content-rich page
        await server.navigate_to_url("https://www.wikipedia.org")
        
        screenshot_types = [
            {"full_page": False, "format": "png"},
            {"full_page": True, "format": "png"},
            {"full_page": False, "format": "jpeg", "quality": 50},
            {"selector": "img", "format": "png"},
            {"selector": "a", "format": "jpeg"},
        ] * 10  # 50 screenshots
        
        start_time = time.time()
        results = []
        
        for i, config in enumerate(screenshot_types):
            try:
                filename = f"torture_test_{i}.{config.get('format', 'png')}"
                result = await server.take_screenshot(filename=filename, **config)
                success = result.get("status") == "success"
                results.append(success)
                print(f"  [{i+1}/{len(screenshot_types)}] Screenshot - {'✅' if success else '❌'}")
            except Exception as e:
                print(f"  [{i+1}/{len(screenshot_types)}] Screenshot - ❌ ERROR: {e}")
                results.append(False)
        
        duration = time.time() - start_time
        success_rate = sum(results) / len(results) * 100
        
        print(f"\n  📊 Results:")
        print(f"     Total: {len(screenshot_types)} screenshots")
        print(f"     Duration: {duration:.2f}s")
        print(f"     Rate: {len(screenshot_types)/duration:.2f} screenshots/sec")
        print(f"     Success: {success_rate:.1f}%")
        
        assert success_rate >= 70, f"Screenshot success rate too low: {success_rate}%"
    
    @pytest.mark.asyncio
    async def test_interaction_chaos(self, server):
        """Perform chaotic interactions on a page."""
        print("\n🎯 INTERACTION CHAOS TEST")
        
        # Navigate to a page with interactive elements
        await server.navigate_to_url("https://www.wikipedia.org")
        
        # Generate random interactions
        interactions = []
        selectors = ["input", "a", "button", "img", "h1", "h2", "p", "div"]
        actions = ["click", "hover", "type"]
        
        for i in range(100):  # 100 random interactions
            selector = random.choice(selectors)
            action = random.choice(actions)
            
            interaction = {"action": action, "selector": selector}
            if action == "type":
                interaction["value"] = f"test_{i}"
            
            interactions.append(interaction)
        
        start_time = time.time()
        results = []
        
        for i, interaction in enumerate(interactions):
            try:
                if interaction["action"] == "click":
                    result = await server.click_element(
                        interaction["selector"],
                        timeout=1000  # Short timeout for speed
                    )
                elif interaction["action"] == "hover":
                    result = await server.hover_element(
                        interaction["selector"],
                        timeout=1000
                    )
                elif interaction["action"] == "type":
                    result = await server.type_text(
                        interaction["selector"],
                        interaction["value"],
                        timeout=1000
                    )
                
                success = result.get("status") == "success"
                results.append(success)
                
                if (i + 1) % 10 == 0:
                    print(f"  [{i+1}/{len(interactions)}] Interactions completed...")
                    
            except Exception as e:
                results.append(False)
        
        duration = time.time() - start_time
        success_rate = sum(results) / len(results) * 100
        
        print(f"\n  📊 Results:")
        print(f"     Total: {len(interactions)} interactions")
        print(f"     Duration: {duration:.2f}s")
        print(f"     Rate: {len(interactions)/duration:.2f} interactions/sec")
        print(f"     Success: {success_rate:.1f}%")
        
        # Lower threshold since many selectors might not exist
        assert success_rate >= 20, f"Interaction success rate too low: {success_rate}%"
    
    @pytest.mark.asyncio
    async def test_memory_leak_detection(self, server):
        """Test for memory leaks with repeated operations."""
        print("\n💾 MEMORY LEAK DETECTION TEST")
        
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        print(f"  Initial memory: {initial_memory:.2f} MB")
        
        # Perform many operations
        for cycle in range(5):
            print(f"\n  Cycle {cycle + 1}/5:")
            
            # Navigate
            for i in range(10):
                await server.navigate_to_url(f"https://example.com?cycle={cycle}&nav={i}")
            print(f"    ✓ 10 navigations")
            
            # Screenshots
            for i in range(10):
                await server.take_screenshot(filename=f"leak_test_{cycle}_{i}.png")
            print(f"    ✓ 10 screenshots")
            
            # Check memory
            current_memory = process.memory_info().rss / 1024 / 1024
            memory_increase = current_memory - initial_memory
            print(f"    Memory: {current_memory:.2f} MB (+{memory_increase:.2f} MB)")
        
        final_memory = process.memory_info().rss / 1024 / 1024
        total_increase = final_memory - initial_memory
        
        print(f"\n  📊 Results:")
        print(f"     Initial: {initial_memory:.2f} MB")
        print(f"     Final: {final_memory:.2f} MB")
        print(f"     Increase: {total_increase:.2f} MB")
        
        # Allow up to 100MB increase
        assert total_increase < 100, f"Memory leak detected: {total_increase:.2f} MB increase"
    
    @pytest.mark.asyncio
    async def test_concurrent_operations(self, server):
        """Test concurrent operations."""
        print("\n⚡ CONCURRENT OPERATIONS TEST")
        
        async def navigate_task(url: str) -> Dict[str, Any]:
            return await server.navigate_to_url(url)
        
        async def screenshot_task(filename: str) -> Dict[str, Any]:
            return await server.take_screenshot(filename=filename)
        
        # Create concurrent tasks
        tasks = []
        
        # Mix different operations
        for i in range(20):
            if i % 2 == 0:
                tasks.append(navigate_task(f"https://example.com?task={i}"))
            else:
                tasks.append(screenshot_task(f"concurrent_{i}.png"))
        
        print(f"  Running {len(tasks)} concurrent operations...")
        start_time = time.time()
        
        # Run all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        duration = time.time() - start_time
        
        # Count successes
        successes = sum(
            1 for r in results 
            if isinstance(r, dict) and r.get("status") == "success"
        )
        errors = sum(1 for r in results if isinstance(r, Exception))
        
        print(f"\n  📊 Results:")
        print(f"     Total: {len(tasks)} operations")
        print(f"     Duration: {duration:.2f}s")
        print(f"     Successes: {successes}")
        print(f"     Errors: {errors}")
        print(f"     Rate: {len(tasks)/duration:.2f} ops/sec")
        
        assert successes >= len(tasks) * 0.5, f"Too many concurrent failures: {errors}/{len(tasks)}"
    
    @pytest.mark.asyncio
    async def test_error_recovery(self, server):
        """Test error handling and recovery."""
        print("\n🛡️ ERROR RECOVERY TEST")
        
        error_scenarios = [
            # Invalid selectors
            {"action": "click", "selector": "#definitely-does-not-exist-12345"},
            {"action": "type", "selector": "#nonexistent-input", "value": "test"},
            
            # Invalid URLs
            {"action": "navigate", "url": "not-a-valid-url"},
            {"action": "navigate", "url": "https://definitely-not-a-real-domain-12345.com"},
            
            # Invalid screenshot configs
            {"action": "screenshot", "selector": "#nonexistent", "format": "invalid"},
            
            # Recovery - valid operations
            {"action": "navigate", "url": "https://example.com"},
            {"action": "screenshot", "filename": "recovery.png"},
        ]
        
        results = []
        for i, scenario in enumerate(error_scenarios):
            try:
                if scenario["action"] == "click":
                    result = await server.click_element(scenario["selector"], timeout=1000)
                elif scenario["action"] == "type":
                    result = await server.type_text(
                        scenario["selector"], 
                        scenario["value"],
                        timeout=1000
                    )
                elif scenario["action"] == "navigate":
                    result = await server.navigate_to_url(scenario["url"])
                elif scenario["action"] == "screenshot":
                    result = await server.take_screenshot(**{k: v for k, v in scenario.items() if k != "action"})
                
                success = result.get("status") == "success"
                results.append({
                    "scenario": scenario,
                    "success": success,
                    "result": result
                })
                
                print(f"  [{i+1}/{len(error_scenarios)}] {scenario['action']} - {'✅ Recovered' if success else '❌ Failed (expected)'}")
                
            except Exception as e:
                print(f"  [{i+1}/{len(error_scenarios)}] {scenario['action']} - ⚠️ Exception: {e}")
                results.append({
                    "scenario": scenario,
                    "success": False,
                    "error": str(e)
                })
        
        # Check that we recovered after errors
        recovery_successful = any(
            r["success"] for r in results[-2:]  # Last 2 should be valid
        )
        
        print(f"\n  📊 Results:")
        print(f"     Total scenarios: {len(error_scenarios)}")
        print(f"     Expected failures: 5")
        print(f"     Recovery successful: {'✅' if recovery_successful else '❌'}")
        
        assert recovery_successful, "Failed to recover after errors"


async def run_torture_tests():
    """Run all torture tests."""
    print("🔥 MCPlaywright V2 TORTURE TEST SUITE 🔥")
    print("=" * 50)
    
    test = TestMCPlaywrightTorture()
    server = MCPlaywrightServer()
    
    try:
        # Run each test
        await test.test_rapid_navigation_stress(server)
        await test.test_screenshot_bombardment(server)
        await test.test_interaction_chaos(server)
        await test.test_memory_leak_detection(server)
        await test.test_concurrent_operations(server)
        await test.test_error_recovery(server)
        
        print("\n" + "=" * 50)
        print("✅ ALL TORTURE TESTS PASSED! 💪")
        print("=" * 50)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        raise
    finally:
        await server.close_browser()


if __name__ == "__main__":
    # Run the torture tests
    asyncio.run(run_torture_tests())