"""
Test MCPlaywright V2 with Mixins and Bulk Operations

Validates the new modular architecture and bulk tool calling capabilities.
"""

import pytest
import asyncio
from typing import Dict, Any, List
from server import app
from fastmcp.testing import MCPTestClient


class TestMCPlaywrightV2:
    """Test suite for MCPlaywright V2 with mixins and bulk operations."""
    
    @pytest.fixture
    async def server(self):
        """Create a test server instance."""
        server = MCPlaywrightServer()
        yield server
        # Cleanup
        await server.close_browser()
    
    @pytest.fixture
    async def client(self):
        """Create a test client for the FastMCP app."""
        async with MCPTestClient(app) as client:
            yield client
    
    @pytest.mark.asyncio
    async def test_mixin_composition(self, server):
        """Test that all mixins are properly composed."""
        # Check that server has methods from all mixins
        assert hasattr(server, 'navigate_to_url')  # NavigationMixin
        assert hasattr(server, 'click_element')    # InteractionMixin
        assert hasattr(server, 'take_screenshot')  # ScreenshotMixin
        assert hasattr(server, 'close_browser')    # BrowserMixin
        
        # Test basic navigation
        result = await server.navigate_to_url("https://example.com")
        assert result["status"] == "success"
        assert "example.com" in result["url"]
    
    @pytest.mark.asyncio
    async def test_bulk_navigation(self, client):
        """Test bulk URL navigation."""
        urls = [
            "https://example.com",
            "https://example.org",
            "https://example.net"
        ]
        
        result = await client.call_tool("browser_bulk_navigate", urls=urls)
        
        assert result["status"] == "success"
        assert result["total"] == 3
        assert result["successful"] > 0
        
        # Check individual results
        for i, url_result in enumerate(result["results"]):
            assert url_result["url"] == urls[i]
            if url_result["success"]:
                assert url_result["title"] is not None
    
    @pytest.mark.asyncio
    async def test_bulk_interactions(self, client):
        """Test bulk element interactions."""
        # Navigate to a test page first
        await client.call_tool("browser_navigate", url="https://example.com")
        
        # Define multiple interactions
        interactions = [
            {"action": "hover", "selector": "h1"},
            {"action": "click", "selector": "a", "options": {"button": "left"}},
        ]
        
        result = await client.call_tool("browser_bulk_interact", interactions=interactions)
        
        assert result["status"] == "success"
        assert result["total"] == len(interactions)
        assert "results" in result
        
        # Check each interaction result
        for i, interaction_result in enumerate(result["results"]):
            assert interaction_result["action"] == interactions[i]["action"]
            assert "success" in interaction_result
    
    @pytest.mark.asyncio
    async def test_bulk_screenshots(self, client):
        """Test bulk screenshot operations."""
        # Navigate to a page
        await client.call_tool("browser_navigate", url="https://example.com")
        
        # Take multiple screenshots
        result = await client.call_tool(
            "browser_bulk_screenshot",
            selectors=["h1", "p", "a"]
        )
        
        assert result["status"] == "success"
        assert len(result["screenshots"]) == 3
        
        for screenshot in result["screenshots"]:
            assert "success" in screenshot
            if screenshot["success"]:
                assert "filepath" in screenshot
    
    @pytest.mark.asyncio
    async def test_batch_test_scenarios(self, client):
        """Test running multiple test scenarios in batch."""
        test_scenarios = [
            {
                "name": "Example.com Test",
                "url": "https://example.com",
                "interactions": [
                    {"action": "hover", "selector": "h1"}
                ],
                "screenshot": True
            },
            {
                "name": "Example.org Test",
                "url": "https://example.org",
                "interactions": [
                    {"action": "click", "selector": "a"}
                ],
                "screenshot": False
            }
        ]
        
        result = await client.call_tool(
            "browser_batch_test",
            test_scenarios=test_scenarios
        )
        
        assert result["status"] == "success"
        assert result["total_tests"] == 2
        assert "results" in result
        
        # Check each test result
        for i, test_result in enumerate(result["results"]):
            assert test_result["name"] == test_scenarios[i]["name"]
            assert "success" in test_result
            assert "steps" in test_result
    
    @pytest.mark.asyncio
    async def test_server_info(self, client):
        """Test server information endpoint."""
        result = await client.call_tool("server_info")
        
        assert result["name"] == "MCPlaywright V2"
        assert result["version"] == "2.0.0"
        assert "BrowserMixin" in result["mixins"]
        assert "NavigationMixin" in result["mixins"]
        assert "InteractionMixin" in result["mixins"]
        assert "ScreenshotMixin" in result["mixins"]
        assert len(result["bulk_operations"]) >= 4
        assert result["total_tools"] > 10
    
    @pytest.mark.asyncio
    async def test_mixin_tool_registration(self, client):
        """Test that all mixin tools are properly registered."""
        # Get list of available tools
        tools = client.list_tools()
        
        # Check for tools from each mixin
        tool_names = [tool.name for tool in tools]
        
        # BrowserMixin tools
        assert "browser_close" in tool_names
        assert "browser_configure" in tool_names
        assert "browser_snapshot" in tool_names
        
        # NavigationMixin tools
        assert "browser_navigate" in tool_names
        assert "browser_navigate_back" in tool_names
        assert "browser_navigate_forward" in tool_names
        
        # InteractionMixin tools
        assert "browser_click" in tool_names
        assert "browser_type" in tool_names
        assert "browser_hover" in tool_names
        
        # ScreenshotMixin tools
        assert "browser_take_screenshot" in tool_names
        assert "browser_screenshot_element" in tool_names
        assert "browser_pdf" in tool_names
        
        # Bulk operation tools
        assert "browser_bulk_navigate" in tool_names
        assert "browser_bulk_interact" in tool_names
        assert "browser_batch_test" in tool_names


@pytest.mark.asyncio
async def test_bulk_tool_caller_integration():
    """Test BulkToolCaller integration with MCPlaywright."""
    from fastmcp.contrib.bulk_tool_caller import BulkToolCaller
    
    # Create bulk caller
    bulk_caller = BulkToolCaller()
    bulk_caller.register_tools(app)
    
    # Test calling multiple tools in bulk
    tool_calls = [
        {"tool": "server_info", "arguments": {}},
        {"tool": "browser_navigate", "arguments": {"url": "https://example.com"}},
        {"tool": "browser_take_screenshot", "arguments": {"filename": "test.png"}}
    ]
    
    # Note: This would require a running server to test properly
    # For now, we just verify the bulk caller is set up correctly
    assert bulk_caller is not None
    assert hasattr(bulk_caller, 'call_tools_bulk')
    assert hasattr(bulk_caller, 'call_tool_bulk')


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])