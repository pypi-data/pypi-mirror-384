#!/usr/bin/env python3
"""
Test script to verify all imports work correctly
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def test_imports():
    """Test that all modules can be imported without Playwright dependency"""
    
    print("Testing FastMCP imports...")
    try:
        from fastmcp import FastMCP
        from fastmcp.exceptions import McpError
        print("✅ FastMCP imports successful")
    except ImportError as e:
        print(f"❌ FastMCP import failed: {e}")
        return False
    
    print("\nTesting Pydantic imports...")
    try:
        from pydantic import BaseModel, Field
        print("✅ Pydantic imports successful")
    except ImportError as e:
        print(f"❌ Pydantic import failed: {e}")
        return False
    
    print("\nTesting tool parameter classes...")
    try:
        # Test browser tools
        from tools.browser import NavigateParams, ScreenshotParams, ClickParams
        print("✅ Browser tool params imported")
        
        # Test video tools  
        from tools.video import StartRecordingParams, StopRecordingParams
        print("✅ Video tool params imported")
        
        # Test interaction tools
        from tools.interaction import TypeParams, FillParams, HoverParams
        print("✅ Interaction tool params imported")
        
        # Test tab tools
        from tools.tabs import NewTabParams, CloseTabParams, SwitchTabParams
        print("✅ Tab tool params imported")
        
        # Test dialog tools
        from tools.dialogs import FileUploadParams, HandleDialogParams
        print("✅ Dialog tool params imported")
        
        # Test wait tools
        from tools.wait import WaitForTextParams, WaitForElementParams
        print("✅ Wait tool params imported")
        
        # Test evaluation tools
        from tools.evaluation import EvaluateParams, ConsoleMessagesParams
        print("✅ Evaluation tool params imported")
        
        # Test monitoring tools
        from tools.monitoring import StartRequestMonitoringParams, GetRequestsParams
        print("✅ Monitoring tool params imported")
        
        # Test snapshot tools
        from tools.snapshots import SnapshotParams
        print("✅ Snapshot tool params imported")
        
    except ImportError as e:
        print(f"❌ Tool parameter import failed: {e}")
        return False
    
    print(f"\n🎉 All imports successful! MCPlaywright is ready for use.")
    print(f"📋 Note: Playwright must be installed separately with 'playwright install'")
    
    return True

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)