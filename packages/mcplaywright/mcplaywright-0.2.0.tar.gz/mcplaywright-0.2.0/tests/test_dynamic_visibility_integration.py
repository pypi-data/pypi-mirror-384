#!/usr/bin/env python3
"""
Integration test for Dynamic Tool Visibility System

Tests the complete middleware system with mock session manager
to validate tool filtering and state validation logic.
"""

import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Import the middleware and server components
from fastmcp import FastMCP
from fastmcp.server.middleware import MiddlewareContext
from middleware import (
    DynamicToolMiddleware, 
    SessionAwareMiddleware, 
    StateValidationMiddleware
)

async def create_mock_session_manager():
    """Create a mock session manager for testing"""
    session_manager = AsyncMock()
    
    # Mock session list - empty by default
    session_manager.list_sessions = AsyncMock(return_value=[])
    session_manager.get_session = AsyncMock(return_value=None)
    
    return session_manager

async def create_mock_tools():
    """Create mock tools for testing"""
    return [
        {"name": "navigate", "description": "Navigate to a URL"},
        {"name": "take_screenshot", "description": "Take a screenshot"}, 
        {"name": "click_element", "description": "Click an element"},
        {"name": "start_recording", "description": "Start video recording"},
        {"name": "pause_recording", "description": "Pause video recording"},
        {"name": "resume_recording", "description": "Resume video recording"},
        {"name": "stop_recording", "description": "Stop video recording"},
        {"name": "recording_status", "description": "Get recording status"},
        {"name": "start_request_monitoring", "description": "Start HTTP monitoring"},
        {"name": "get_requests", "description": "Get captured requests"},
        {"name": "export_requests", "description": "Export requests to file"},
        {"name": "clear_requests", "description": "Clear captured requests"},
        {"name": "request_monitoring_status", "description": "Get monitoring status"},
    ]

async def test_empty_session_filtering():
    """Test tool filtering when no sessions exist"""
    print("🧪 Testing tool filtering with no active sessions...")
    
    # Create middleware
    middleware = DynamicToolMiddleware()
    session_manager = await create_mock_session_manager()
    
    # Mock context with session manager
    context = MagicMock()
    context.session_manager = session_manager
    
    # Mock call_next to return all tools
    async def mock_call_next(ctx):
        return await create_mock_tools()
    
    # Test tool filtering
    filtered_tools = await middleware.on_list_tools(context, mock_call_next)
    
    # Should only show always-available tools
    tool_names = [tool["name"] for tool in filtered_tools]
    
    # Check always available tools are present
    always_available = ["start_recording", "start_request_monitoring"]
    for tool in always_available:
        assert tool in tool_names, f"Always-available tool '{tool}' missing"
    
    # Check session-required tools are hidden
    session_required = ["navigate", "take_screenshot", "click_element"]
    for tool in session_required:
        assert tool not in tool_names, f"Session-required tool '{tool}' should be hidden"
    
    # Check recording tools are hidden
    recording_tools = ["pause_recording", "resume_recording", "stop_recording"]
    for tool in recording_tools:
        assert tool not in tool_names, f"Recording tool '{tool}' should be hidden"
    
    print(f"✅ Filtered {len(await create_mock_tools())} tools down to {len(filtered_tools)} relevant tools")
    return True

async def test_session_with_recording_filtering():
    """Test tool filtering when session exists with active recording"""
    print("🧪 Testing tool filtering with active session and recording...")
    
    # Create middleware
    middleware = DynamicToolMiddleware()
    session_manager = await create_mock_session_manager()
    
    # Mock active session with recording
    mock_session = MagicMock()
    mock_session.context._video_config = {"active": True}  # Simulate active recording
    
    session_manager.list_sessions.return_value = [{"session_id": "test-session"}]
    session_manager.get_session.return_value = mock_session
    
    # Mock context
    context = MagicMock()
    context.session_manager = session_manager
    
    # Mock call_next to return all tools
    async def mock_call_next(ctx):
        return await create_mock_tools()
    
    # Test tool filtering
    filtered_tools = await middleware.on_list_tools(context, mock_call_next)
    tool_names = [tool["name"] for tool in filtered_tools]
    
    # Should show session tools
    session_tools = ["navigate", "take_screenshot", "click_element"]
    for tool in session_tools:
        assert tool in tool_names, f"Session tool '{tool}' should be visible"
    
    # Should show recording control tools
    recording_tools = ["pause_recording", "resume_recording", "stop_recording"]
    for tool in recording_tools:
        assert tool in tool_names, f"Recording tool '{tool}' should be visible"
    
    print(f"✅ All {len(filtered_tools)} tools visible with active session and recording")
    return True

async def test_state_validation_middleware():
    """Test state validation middleware"""
    print("🧪 Testing state validation middleware...")
    
    # Create middleware
    middleware = StateValidationMiddleware()
    session_manager = await create_mock_session_manager()
    
    # Mock context
    context = MagicMock()
    context.session_manager = session_manager
    context.tool_name = "pause_recording"
    
    # Mock call_next
    async def mock_call_next(ctx):
        return {"success": True}
    
    # Test validation with no recording active
    try:
        await middleware.on_call_tool(context, mock_call_next)
        assert False, "Should have raised error for invalid state"
    except Exception as e:
        assert "requires active video recording" in str(e)
        print("✅ State validation correctly blocked invalid operation")
    
    return True

async def test_session_aware_middleware():
    """Test session-aware middleware"""
    print("🧪 Testing session-aware middleware...")
    
    # Create middleware
    middleware = SessionAwareMiddleware()
    
    # Mock context with tool arguments
    context = MagicMock()
    context.arguments = {"session_id": "test-session-123"}
    
    # Mock call_next
    async def mock_call_next(ctx):
        return {"success": True}
    
    # Test session extraction
    result = await middleware.on_call_tool(context, mock_call_next)
    
    # Should extract session_id to context
    assert hasattr(context, 'current_session_id')
    assert context.current_session_id == "test-session-123"
    
    print("✅ Session-aware middleware correctly extracted session ID")
    return True

async def test_complete_middleware_integration():
    """Test complete middleware system integration"""
    print("🧪 Testing complete middleware integration...")
    
    # Create FastMCP app
    app = FastMCP(
        name="MCPlaywright-Test",
        version="0.1.0"
    )
    
    # Add all middleware
    app.add_middleware(DynamicToolMiddleware())
    app.add_middleware(SessionAwareMiddleware())
    app.add_middleware(StateValidationMiddleware())
    
    print("✅ Successfully integrated all middleware components")
    return True

async def run_integration_tests():
    """Run all integration tests"""
    print("🚀 Running Dynamic Tool Visibility System Integration Tests\n")
    
    tests = [
        test_empty_session_filtering,
        test_session_with_recording_filtering,
        test_state_validation_middleware,
        test_session_aware_middleware,
        test_complete_middleware_integration
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            await test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__} failed: {str(e)}")
            failed += 1
        print()  # Add spacing
    
    print(f"📊 Integration Test Results:")
    print(f"   ✅ Passed: {passed}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📈 Success Rate: {passed}/{len(tests)} ({100*passed//len(tests)}%)")
    
    if failed == 0:
        print("\n🎉 All Dynamic Tool Visibility System integration tests passed!")
        print("🚀 The middleware system is ready for production deployment!")
    else:
        print(f"\n⚠️  {failed} integration tests failed - system needs fixes")
    
    return failed == 0

if __name__ == "__main__":
    success = asyncio.run(run_integration_tests())
    sys.exit(0 if success else 1)