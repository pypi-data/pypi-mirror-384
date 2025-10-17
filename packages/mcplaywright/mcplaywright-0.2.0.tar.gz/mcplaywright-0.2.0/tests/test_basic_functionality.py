"""
Basic functionality tests for MCPlaywright

Tests the core FastMCP server functionality and health checks.
"""

import asyncio
import pytest
from unittest.mock import patch

# Import our server components
import sys
from pathlib import Path

# Add src to path for testing
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from server import app, health_check, server_info, test_playwright_installation

class TestBasicFunctionality:
    """Test basic server functionality"""
    
    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test the health check endpoint"""
        result = await health_check()
        
        assert result["status"] == "healthy"
        assert result["version"] == "0.1.0"
        assert "timestamp" in result
        assert "uptime" in result
        assert isinstance(result["active_sessions"], int)
        assert isinstance(result["playwright_available"], bool)
    
    @pytest.mark.asyncio 
    async def test_server_info(self):
        """Test the server info endpoint"""
        result = await server_info()
        
        assert result["name"] == "MCPlaywright"
        assert result["version"] == "0.1.0"
        assert "capabilities" in result
        assert "supported_browsers" in result
        assert "python_version" in result
        
        # Check expected capabilities
        capabilities = result["capabilities"]
        expected_capabilities = [
            "browser_automation",
            "screenshot_capture",
            "video_recording", 
            "request_monitoring",
            "ui_customization",
            "session_management"
        ]
        
        for capability in expected_capabilities:
            assert capability in capabilities
        
        # Check supported browsers
        supported_browsers = result["supported_browsers"]
        expected_browsers = ["chromium", "firefox", "webkit"]
        assert supported_browsers == expected_browsers
    
    @pytest.mark.asyncio
    async def test_playwright_installation_mock_success(self):
        """Test playwright installation check with mocked success"""
        
        # Mock successful playwright import and browser detection
        mock_browser = type('MockBrowser', (), {
            'executable_path': '/mock/path/to/chromium'
        })()
        
        mock_playwright = type('MockPlaywright', (), {
            'chromium': mock_browser,
            'firefox': mock_browser, 
            'webkit': mock_browser
        })()
        
        with patch('mcplaywright.server.async_playwright') as mock_async_playwright:
            with patch('pathlib.Path.exists', return_value=True):
                mock_async_playwright.return_value.__aenter__.return_value = mock_playwright
                
                result = await test_playwright_installation()
                
                assert result["success"] is True
                assert result["playwright_imported"] is True
                assert len(result["available_browsers"]) == 3
                assert "chromium" in result["available_browsers"]
                assert "firefox" in result["available_browsers"]  
                assert "webkit" in result["available_browsers"]
    
    @pytest.mark.asyncio
    async def test_playwright_installation_mock_failure(self):
        """Test playwright installation check with mocked failure"""
        
        # Mock ImportError for playwright
        with patch('mcplaywright.server.async_playwright', side_effect=ImportError("No module named 'playwright'")):
            result = await test_playwright_installation()
            
            assert result["success"] is False
            assert "Playwright not installed" in result["error"]
            assert "playwright install" in result["suggestion"]

class TestServerConfiguration:
    """Test server configuration and setup"""
    
    def test_app_metadata(self):
        """Test FastMCP app metadata"""
        assert app.name == "MCPlaywright"
        assert app.version == "0.1.0"
        assert "browser automation" in app.description.lower()
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling functionality"""
        
        # This will be expanded when we have more error cases
        # For now, just verify the basic structure works
        
        from fastmcp.exceptions import MCPError
        
        # Test that we can create MCP errors
        error = MCPError(code="TEST_ERROR", message="Test error message")
        assert error.code == "TEST_ERROR"
        assert error.message == "Test error message"

@pytest.mark.integration
class TestServerIntegration:
    """Integration tests for the complete server"""
    
    @pytest.mark.asyncio
    async def test_multiple_health_checks(self):
        """Test multiple sequential health checks"""
        
        # Run multiple health checks to ensure consistency
        results = []
        for i in range(3):
            result = await health_check()
            results.append(result)
            await asyncio.sleep(0.1)  # Small delay
        
        # All should succeed
        for result in results:
            assert result["status"] == "healthy"
        
        # Timestamps should be different (increasing)
        timestamps = [result["timestamp"] for result in results]
        assert len(set(timestamps)) == 3  # All unique
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test handling concurrent requests"""
        
        # Run multiple concurrent health checks
        tasks = [health_check() for _ in range(5)]
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        assert len(results) == 5
        for result in results:
            assert result["status"] == "healthy"
            assert result["version"] == "0.1.0"

if __name__ == "__main__":
    # Run basic tests when script is executed directly
    asyncio.run(test_health_check())
    print("✓ Basic health check test passed")
    
    asyncio.run(test_server_info()) 
    print("✓ Server info test passed")
    
    print("✓ All basic tests passed!")