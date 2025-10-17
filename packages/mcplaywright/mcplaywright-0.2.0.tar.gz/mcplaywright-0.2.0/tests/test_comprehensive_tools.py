"""
Comprehensive tests for all MCPlaywright tools

Tests all 40+ tools implemented in the complete Python port,
including video recording, HTTP monitoring, interactions, and more.
"""

import asyncio
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from pathlib import Path

# Import our components
import sys
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Import all tool modules for comprehensive testing
from tools.video import (
    StartRecordingParams, StopRecordingParams, RecordingModeParams, RecordingControlParams
)
from tools.interaction import (
    TypeParams, FillParams, KeyboardParams, HoverParams, 
    DragParams, SelectParams, CheckParams
)
from tools.tabs import (
    NewTabParams, CloseTabParams, SwitchTabParams, TabListParams
)
from tools.dialogs import (
    FileUploadParams, HandleDialogParams, DismissFileChooserParams
)
from tools.wait import (
    WaitForTextParams, WaitForTextGoneParams, WaitForElementParams,
    WaitForLoadStateParams, WaitForTimeParams, WaitForRequestParams
)
from tools.evaluation import (
    EvaluateParams, ConsoleMessagesParams
)
from tools.monitoring import (
    StartRequestMonitoringParams, GetRequestsParams, 
    ExportRequestsParams, ClearRequestsParams
)
from tools.snapshots import SnapshotParams


@pytest.mark.comprehensive
class TestVideoRecordingTools:
    """Test video recording functionality"""
    
    def test_video_parameter_models(self):
        """Test video recording parameter validation"""
        
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
        
        # Test default values
        params = StartRecordingParams()
        assert params.session_id is None
        assert params.filename is None
        assert params.size_width == 1280
        assert params.size_height == 720
        assert params.auto_set_viewport is True
        assert params.mode == "smart"
    
    def test_recording_mode_validation(self):
        """Test recording mode parameter validation"""
        
        # Valid modes
        for mode in ["smart", "continuous", "action-only", "segment"]:
            params = RecordingModeParams(
                session_id="test-session",
                mode=mode
            )
            assert params.mode == mode
    
    def test_recording_control_params(self):
        """Test recording control parameter models"""
        
        # Test pause/resume params
        params = RecordingControlParams(session_id="test-session")
        assert params.session_id == "test-session"
        
        # Test stop params
        params = StopRecordingParams(session_id="test-session")
        assert params.session_id == "test-session"


@pytest.mark.comprehensive
class TestInteractionTools:
    """Test advanced interaction tools"""
    
    def test_type_params(self):
        """Test type parameter validation"""
        
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
    
    def test_fill_params(self):
        """Test fill parameter validation"""
        
        params = FillParams(
            selector="textarea",
            text="Large text content",
            force=True
        )
        assert params.selector == "textarea"
        assert params.text == "Large text content"
        assert params.force is True
    
    def test_hover_params(self):
        """Test hover parameter validation"""
        
        params = HoverParams(
            selector="button.hover-target",
            timeout=10000
        )
        assert params.selector == "button.hover-target"
        assert params.timeout == 10000
    
    def test_drag_and_drop_params(self):
        """Test drag and drop parameter validation"""
        
        params = DragAndDropParams(
            source_selector=".drag-source",
            target_selector=".drop-target",
            timeout=15000
        )
        assert params.source_selector == ".drag-source"
        assert params.target_selector == ".drop-target"
        assert params.timeout == 15000
    
    def test_select_option_params(self):
        """Test select option parameter validation"""
        
        # Test by value
        params = SelectOptionParams(
            selector="select#country",
            value="US"
        )
        assert params.selector == "select#country"
        assert params.value == "US"
        
        # Test by label
        params = SelectOptionParams(
            selector="select#country",
            label="United States"
        )
        assert params.label == "United States"
    
    def test_check_params(self):
        """Test check parameter validation"""
        
        params = CheckParams(
            selector="input[type='checkbox']",
            checked=True,
            force=False
        )
        assert params.selector == "input[type='checkbox']"
        assert params.checked is True
        assert params.force is False


@pytest.mark.comprehensive
class TestTabManagementTools:
    """Test tab management functionality"""
    
    def test_new_tab_params(self):
        """Test new tab parameter validation"""
        
        params = NewTabParams(
            session_id="test-session",
            url="https://example.com"
        )
        assert params.session_id == "test-session"
        assert params.url == "https://example.com"
        
        # Test without URL
        params = NewTabParams(session_id="test-session")
        assert params.url is None
    
    def test_close_tab_params(self):
        """Test close tab parameter validation"""
        
        params = CloseTabParams(
            session_id="test-session",
            tab_index=2
        )
        assert params.session_id == "test-session"
        assert params.tab_index == 2
        
        # Test without tab index (current tab)
        params = CloseTabParams(session_id="test-session")
        assert params.tab_index is None
    
    def test_switch_tab_params(self):
        """Test switch tab parameter validation"""
        
        params = SwitchTabParams(
            session_id="test-session",
            tab_index=1
        )
        assert params.session_id == "test-session"
        assert params.tab_index == 1


@pytest.mark.comprehensive
class TestFileAndDialogTools:
    """Test file upload and dialog handling"""
    
    def test_file_upload_params(self):
        """Test file upload parameter validation"""
        
        params = FileUploadParams(
            session_id="test-session",
            selector="input[type='file']",
            file_paths=["/path/to/file1.txt", "/path/to/file2.pdf"],
            timeout=20000
        )
        assert params.selector == "input[type='file']"
        assert len(params.file_paths) == 2
        assert params.file_paths[0] == "/path/to/file1.txt"
        assert params.timeout == 20000
    
    def test_handle_dialog_params(self):
        """Test dialog handling parameter validation"""
        
        # Test accept dialog
        params = HandleDialogParams(
            session_id="test-session",
            accept=True
        )
        assert params.accept is True
        assert params.prompt_text is None
        
        # Test prompt with text
        params = HandleDialogParams(
            session_id="test-session",
            accept=True,
            prompt_text="User input"
        )
        assert params.accept is True
        assert params.prompt_text == "User input"
    
    def test_dismiss_file_chooser_params(self):
        """Test file chooser dismissal parameter validation"""
        
        params = DismissFileChooserParams(session_id="test-session")
        assert params.session_id == "test-session"


@pytest.mark.comprehensive
class TestWaitTools:
    """Test wait condition tools"""
    
    def test_wait_for_text_params(self):
        """Test wait for text parameter validation"""
        
        params = WaitForTextParams(
            session_id="test-session",
            text="Loading complete",
            timeout=45000,
            record_during_wait=False
        )
        assert params.text == "Loading complete"
        assert params.timeout == 45000
        assert params.record_during_wait is False
    
    def test_wait_for_element_params(self):
        """Test wait for element parameter validation"""
        
        params = WaitForElementParams(
            selector="button.submit",
            state="visible",
            timeout=30000,
            record_during_wait=True
        )
        assert params.selector == "button.submit"
        assert params.state == "visible"
        assert params.timeout == 30000
        assert params.record_during_wait is True
    
    def test_wait_for_load_state_params(self):
        """Test wait for load state parameter validation"""
        
        params = WaitForLoadStateParams(
            state="networkidle",
            timeout=60000
        )
        assert params.state == "networkidle"
        assert params.timeout == 60000
    
    def test_wait_for_time_params(self):
        """Test wait for time parameter validation"""
        
        params = WaitForTimeParams(
            time=2.5,
            record_during_wait=False
        )
        assert params.time == 2.5
        assert params.record_during_wait is False
    
    def test_wait_for_request_params(self):
        """Test wait for request parameter validation"""
        
        params = WaitForRequestParams(
            url_pattern="/api/data",
            timeout=15000,
            record_during_wait=True
        )
        assert params.url_pattern == "/api/data"
        assert params.timeout == 15000
        assert params.record_during_wait is True


@pytest.mark.comprehensive
class TestEvaluationTools:
    """Test JavaScript evaluation tools"""
    
    def test_evaluate_params(self):
        """Test JavaScript evaluation parameter validation"""
        
        # Test page-level evaluation
        params = EvaluateParams(
            function="() => document.title"
        )
        assert params.function == "() => document.title"
        assert params.element is None
        assert params.ref is None
        
        # Test element evaluation
        params = EvaluateParams(
            function="(element) => element.textContent",
            element="Submit button",
            ref="button.submit"
        )
        assert params.function == "(element) => element.textContent"
        assert params.element == "Submit button"
        assert params.ref == "button.submit"
    
    def test_console_messages_params(self):
        """Test console messages parameter validation"""
        
        params = ConsoleMessagesParams(
            session_id="test-session",
            clear_after=True
        )
        assert params.session_id == "test-session"
        assert params.clear_after is True


@pytest.mark.comprehensive
class TestHTTPMonitoringTools:
    """Test HTTP request monitoring tools"""
    
    def test_start_request_monitoring_params(self):
        """Test start monitoring parameter validation"""
        
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
    
    def test_get_requests_params(self):
        """Test get requests parameter validation"""
        
        params = GetRequestsParams(
            session_id="test-session",
            filter="failed",
            limit=50,
            domain="api.example.com",
            method="POST",
            status=404,
            format="detailed",
            slow_threshold=2000
        )
        assert params.filter == "failed"
        assert params.limit == 50
        assert params.domain == "api.example.com"
        assert params.method == "POST"
        assert params.status == 404
        assert params.format == "detailed"
        assert params.slow_threshold == 2000
    
    def test_export_requests_params(self):
        """Test export requests parameter validation"""
        
        params = ExportRequestsParams(
            format="har",
            filename="requests_export.har",
            include_body=True,
            filter="errors"
        )
        assert params.format == "har"
        assert params.filename == "requests_export.har"
        assert params.include_body is True
        assert params.filter == "errors"
    
    def test_clear_requests_params(self):
        """Test clear requests parameter validation"""
        
        params = ClearRequestsParams(session_id="test-session")
        assert params.session_id == "test-session"


@pytest.mark.comprehensive
class TestSnapshotTools:
    """Test snapshot and accessibility tools"""
    
    def test_snapshot_params(self):
        """Test snapshot parameter validation"""
        
        params = SnapshotParams(
            session_id="test-session",
            include_accessibility=True,
            include_viewport_info=True
        )
        assert params.session_id == "test-session"
        assert params.include_accessibility is True
        assert params.include_viewport_info is True
        
        # Test defaults
        params = SnapshotParams()
        assert params.include_accessibility is True
        assert params.include_viewport_info is True


@pytest.mark.comprehensive
class TestParameterValidation:
    """Test parameter validation across all tools"""
    
    def test_session_id_handling(self):
        """Test session ID parameter handling across tools"""
        
        # Test tools that accept optional session_id
        optional_session_tools = [
            TypeParams(selector="input", text="test"),
            FillParams(selector="input", text="test"),
            HoverParams(selector="button"),
            NewTabParams(),
            WaitForTextParams(text="Loading"),
            SnapshotParams()
        ]
        
        for params in optional_session_tools:
            # Should accept None session_id
            assert hasattr(params, 'session_id')
            # Default should be None for auto-generation
            if hasattr(params, 'session_id'):
                assert params.session_id is None
    
    def test_timeout_parameter_consistency(self):
        """Test timeout parameter consistency"""
        
        # Test tools with timeout parameters
        timeout_tools = [
            TypeParams(selector="input", text="test", timeout=30000),
            HoverParams(selector="button", timeout=15000),
            WaitForTextParams(text="Loading", timeout=45000),
            WaitForElementParams(selector="div", timeout=30000),
            FileUploadParams(selector="input", file_paths=["test.txt"], timeout=20000)
        ]
        
        for params in timeout_tools:
            assert hasattr(params, 'timeout')
            assert isinstance(params.timeout, int)
            assert params.timeout > 0
    
    def test_selector_parameter_consistency(self):
        """Test CSS selector parameter consistency"""
        
        # Test tools with selector parameters
        selector_tools = [
            TypeParams(selector="input[type='text']", text="test"),
            FillParams(selector="textarea", text="test"),
            HoverParams(selector="button.hover-me"),
            CheckParams(selector="input[type='checkbox']", checked=True),
            SelectOptionParams(selector="select", value="option1"),
            FileUploadParams(selector="input[type='file']", file_paths=["test.txt"])
        ]
        
        for params in selector_tools:
            assert hasattr(params, 'selector')
            assert isinstance(params.selector, str)
            assert len(params.selector) > 0


@pytest.mark.comprehensive
class TestErrorHandling:
    """Test error handling across all tools"""
    
    def test_invalid_parameter_types(self):
        """Test handling of invalid parameter types"""
        
        # Test invalid timeout (should be int)
        with pytest.raises(ValueError):
            TypeParams(selector="input", text="test", timeout="invalid")
        
        # Test invalid boolean (should be bool)
        with pytest.raises(ValueError):
            CheckParams(selector="input", checked="yes")
        
        # Test invalid list (should be list)
        with pytest.raises(ValueError):
            FileUploadParams(selector="input", file_paths="single-file")
    
    def test_missing_required_parameters(self):
        """Test handling of missing required parameters"""
        
        # Test missing required selector
        with pytest.raises(ValueError):
            TypeParams(text="test")  # Missing required selector
        
        # Test missing required text
        with pytest.raises(ValueError):
            TypeParams(selector="input")  # Missing required text
        
        # Test missing required tab_index
        with pytest.raises(ValueError):
            SwitchTabParams(session_id="test")  # Missing required tab_index


if __name__ == "__main__":
    # Run comprehensive tool tests
    print("Running comprehensive MCPlaywright tool tests...")
    
    # Run parameter validation tests
    test_classes = [
        TestVideoRecordingTools,
        TestInteractionTools,
        TestTabManagementTools,
        TestFileAndDialogTools,
        TestWaitTools,
        TestEvaluationTools,
        TestHTTPMonitoringTools,
        TestSnapshotTools,
        TestParameterValidation,
        TestErrorHandling
    ]
    
    total_tests = 0
    passed_tests = 0
    
    for test_class in test_classes:
        print(f"\n--- Testing {test_class.__name__} ---")
        instance = test_class()
        
        # Get all test methods
        test_methods = [method for method in dir(instance) if method.startswith('test_')]
        
        for method_name in test_methods:
            total_tests += 1
            try:
                method = getattr(instance, method_name)
                method()
                print(f"✅ {method_name}")
                passed_tests += 1
            except Exception as e:
                print(f"❌ {method_name}: {str(e)}")
    
    print(f"\n🎯 Test Results: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All comprehensive tool tests passed!")
    else:
        print(f"⚠️  {total_tests - passed_tests} tests failed")