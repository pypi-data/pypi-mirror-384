#!/usr/bin/env python3
"""
Isolated test for middleware classes without Playwright dependencies
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def test_middleware_structure():
    """Test middleware structure without importing session manager"""
    
    try:
        # Test direct middleware import by copying the classes
        from typing import List, Dict, Any
        from fastmcp.server.middleware import Middleware, MiddlewareContext
        from fastmcp.exceptions import ToolError
        
        class TestDynamicToolMiddleware(Middleware):
            """Test version of DynamicToolMiddleware"""
            
            def __init__(self):
                self.video_recording_tools = {
                    "pause_recording",
                    "resume_recording", 
                    "stop_recording",
                    "set_recording_mode",
                    "recording_status"
                }
                
                self.http_monitoring_tools = {
                    "get_requests",
                    "export_requests", 
                    "clear_requests",
                    "request_monitoring_status"
                }
                
                self.session_required_tools = {
                    "navigate", "click_element", "take_screenshot",
                    "type_text", "fill_element", "hover_element",
                    "press_key", "snapshot", "drag_and_drop",
                    "select_option", "check_element", "file_upload",
                    "handle_dialog", "dismiss_file_chooser",
                    "wait_for_text", "wait_for_element", 
                    "wait_for_load_state", "wait_for_request",
                    "wait_for_text_gone", "wait_for_time",
                    "evaluate", "console_messages",
                    "new_tab", "close_tab", "switch_tab", "list_tabs",
                    "get_page_info"
                }
            
            async def on_list_tools(self, context: MiddlewareContext, call_next):
                """Filter tools based on current session state"""
                # This is just a test - real implementation would call session manager
                all_tools = await call_next(context)
                return all_tools  # For test, return all tools unchanged
        
        class TestSessionAwareMiddleware(Middleware):
            """Test version of SessionAwareMiddleware"""
            
            async def on_call_tool(self, context: MiddlewareContext, call_next):
                """Add session context to tool calls"""
                return await call_next(context)
        
        class TestStateValidationMiddleware(Middleware):
            """Test version of StateValidationMiddleware"""
            
            async def on_call_tool(self, context: MiddlewareContext, call_next):
                """Validate tool calls against current server state"""
                return await call_next(context)
        
        # Test instantiation
        dynamic_middleware = TestDynamicToolMiddleware()
        session_middleware = TestSessionAwareMiddleware()
        validation_middleware = TestStateValidationMiddleware()
        
        print("✅ Successfully imported FastMCP middleware base classes")
        print("✅ Successfully instantiated test middleware classes")
        print(f"✅ Video recording tools: {len(dynamic_middleware.video_recording_tools)} tools")
        print(f"✅ HTTP monitoring tools: {len(dynamic_middleware.http_monitoring_tools)} tools") 
        print(f"✅ Session-required tools: {len(dynamic_middleware.session_required_tools)} tools")
        
        # Test FastMCP integration
        from fastmcp import FastMCP
        
        app = FastMCP("Test App")
        app.add_middleware(dynamic_middleware)
        app.add_middleware(session_middleware)
        app.add_middleware(validation_middleware)
        
        print("✅ Successfully added middleware to FastMCP app")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Middleware test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing Dynamic Tool Visibility Middleware Structure...\n")
    
    success = test_middleware_structure()
    
    if success:
        print("\n🎉 Middleware structure test passed!")
        print("\n💡 Next steps:")
        print("  1. Install Playwright: playwright install")
        print("  2. Test full middleware with session manager integration")
        print("  3. Test dynamic tool filtering in real server")
    else:
        print("\n❌ Middleware structure test failed")
    
    sys.exit(0 if success else 1)