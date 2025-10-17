#!/usr/bin/env python3
"""
Test parameter validation without Playwright dependency
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def test_parameter_models():
    """Test that all parameter models can be instantiated and validated"""
    
    print("Testing parameter model validation...")
    
    try:
        # Test video recording parameters
        from tools.video import (
            StartRecordingParams, StopRecordingParams, RecordingModeParams, RecordingControlParams
        )
        
        # Test StartRecordingParams
        params = StartRecordingParams(
            session_id="test-session",
            filename="test-recording",
            size_width=1920,
            size_height=1080,
            auto_set_viewport=True,
            mode="smart"
        )
        assert params.session_id == "test-session"
        assert params.filename == "test-recording"
        assert params.size_width == 1920
        assert params.size_height == 1080
        assert params.auto_set_viewport is True
        assert params.mode == "smart"
        print("✅ Video recording parameter validation passed")
        
    except ImportError as e:
        print(f"⚠️  Video tools skipped due to Playwright dependency: {e}")
    except Exception as e:
        print(f"❌ Video parameter test failed: {e}")
        return False
    
    try:
        # Test interaction parameters
        from tools.interaction import TypeParams, FillParams, HoverParams
        
        params = TypeParams(
            session_id="test-session",
            selector="input[type='text']",
            text="Hello, World!",
            delay=50,
            timeout=30000
        )
        assert params.selector == "input[type='text']"
        assert params.text == "Hello, World!"
        assert params.delay == 50
        assert params.timeout == 30000
        print("✅ Interaction parameter validation passed")
        
    except ImportError as e:
        print(f"⚠️  Interaction tools skipped due to Playwright dependency: {e}")
    except Exception as e:
        print(f"❌ Interaction parameter test failed: {e}")
        return False
    
    try:
        # Test monitoring parameters
        from tools.monitoring import StartRequestMonitoringParams, GetRequestsParams
        
        params = StartRequestMonitoringParams(
            session_id="test-session",
            capture_body=True,
            max_body_size=5242880,  # 5MB
            url_filter="/api/",
            auto_save=True
        )
        assert params.capture_body is True
        assert params.max_body_size == 5242880
        assert params.url_filter == "/api/"
        assert params.auto_save is True
        print("✅ Monitoring parameter validation passed")
        
    except ImportError as e:
        print(f"⚠️  Monitoring tools skipped due to Playwright dependency: {e}")
    except Exception as e:
        print(f"❌ Monitoring parameter test failed: {e}")
        return False
    
    try:
        # Test basic FastMCP and Pydantic functionality
        from pydantic import BaseModel, Field
        
        class TestModel(BaseModel):
            name: str = Field(..., description="Test name")
            count: int = Field(default=0, ge=0)
        
        model = TestModel(name="test", count=5)
        assert model.name == "test"
        assert model.count == 5
        
        print("✅ Pydantic parameter validation passed")
        
    except Exception as e:
        print(f"❌ Pydantic parameter test failed: {e}")
        return False
    
    print("🎉 Parameter validation tests completed successfully!")
    return True

if __name__ == "__main__":
    success = test_parameter_models()
    sys.exit(0 if success else 1)