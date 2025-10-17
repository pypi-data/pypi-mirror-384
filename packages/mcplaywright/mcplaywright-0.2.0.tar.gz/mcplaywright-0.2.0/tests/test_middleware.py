#!/usr/bin/env python3
"""
Test script to validate dynamic tool visibility middleware
"""

import sys
import asyncio
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

async def test_middleware():
    """Test that middleware can be imported and instantiated"""
    
    try:
        # Test importing the middleware classes
        from middleware import (
            DynamicToolMiddleware, 
            SessionAwareMiddleware, 
            StateValidationMiddleware
        )
        print("✅ Successfully imported middleware classes")
        
        # Test instantiation
        dynamic_middleware = DynamicToolMiddleware()
        session_middleware = SessionAwareMiddleware()
        validation_middleware = StateValidationMiddleware()
        
        print("✅ Successfully instantiated middleware classes")
        
        # Test tool sets are configured
        print(f"✅ Video recording tools: {len(dynamic_middleware.video_recording_tools)} tools")
        print(f"✅ HTTP monitoring tools: {len(dynamic_middleware.http_monitoring_tools)} tools")
        print(f"✅ Session-required tools: {len(dynamic_middleware.session_required_tools)} tools")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Middleware test failed: {e}")
        return False

async def test_fastmcp_integration():
    """Test FastMCP integration"""
    
    try:
        from fastmcp import FastMCP
        from middleware import DynamicToolMiddleware
        
        # Create a test FastMCP app
        app = FastMCP("Test App")
        
        # Add middleware
        app.add_middleware(DynamicToolMiddleware())
        
        print("✅ Successfully added middleware to FastMCP app")
        return True
        
    except Exception as e:
        print(f"❌ FastMCP integration failed: {e}")
        return False

if __name__ == "__main__":
    async def main():
        print("Testing Dynamic Tool Visibility Middleware...\n")
        
        # Test basic middleware functionality
        middleware_ok = await test_middleware()
        
        # Test FastMCP integration
        fastmcp_ok = await test_fastmcp_integration()
        
        if middleware_ok and fastmcp_ok:
            print("\n🎉 All middleware tests passed!")
            return True
        else:
            print("\n❌ Some middleware tests failed")
            return False
    
    success = asyncio.run(main())
    sys.exit(0 if success else 1)