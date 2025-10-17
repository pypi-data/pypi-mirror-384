"""
Pytest configuration and fixtures for MCPlaywright tests
"""

import asyncio
import os
import sys
import tempfile
from pathlib import Path
from typing import AsyncGenerator, Dict, Any
from unittest.mock import patch

import pytest

# Add src to path for testing
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


@pytest.fixture(scope="session") 
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_artifacts_dir():
    """Create temporary artifacts directory for tests"""
    with tempfile.TemporaryDirectory(prefix="mcplaywright-test-") as temp_dir:
        artifacts_dir = Path(temp_dir) / "artifacts"
        artifacts_dir.mkdir()
        
        # Create subdirectories
        (artifacts_dir / "videos").mkdir()
        (artifacts_dir / "screenshots").mkdir()
        (artifacts_dir / "requests").mkdir()
        (artifacts_dir / "logs").mkdir()
        
        yield artifacts_dir


@pytest.fixture
def mock_playwright_success():
    """Mock successful Playwright installation and browser availability"""
    
    class MockBrowser:
        def __init__(self, name: str):
            self.name = name
            self.executable_path = f"/mock/path/to/{name}"
    
    class MockPlaywright:
        def __init__(self):
            self.chromium = MockBrowser("chromium")
            self.firefox = MockBrowser("firefox") 
            self.webkit = MockBrowser("webkit")
    
    mock_pw = MockPlaywright()
    
    with patch('mcplaywright.server.async_playwright') as mock_async_pw:
        with patch('pathlib.Path.exists', return_value=True):
            mock_async_pw.return_value.__aenter__.return_value = mock_pw
            yield mock_pw


@pytest.fixture 
def mock_playwright_not_installed():
    """Mock Playwright not being installed"""
    
    with patch('mcplaywright.server.async_playwright', side_effect=ImportError("No module named 'playwright'")):
        yield


@pytest.fixture
def test_config():
    """Test configuration dictionary"""
    return {
        "browser_type": "chromium",
        "headless": True,
        "viewport": {"width": 1280, "height": 720},
        "timeout": 30000,
        "artifacts_dir": "./test-artifacts"
    }


@pytest.fixture
def sample_health_response():
    """Sample health check response for testing"""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "timestamp": "2024-01-01T12:00:00Z",
        "active_sessions": 0,
        "playwright_available": True,
        "uptime": "1h 30m"
    }


@pytest.fixture
def sample_server_info():
    """Sample server info response for testing"""
    return {
        "name": "MCPlaywright",
        "version": "0.1.0",
        "capabilities": [
            "browser_automation",
            "screenshot_capture",
            "video_recording",
            "request_monitoring", 
            "ui_customization",
            "session_management"
        ],
        "supported_browsers": ["chromium", "firefox", "webkit"],
        "python_version": "3.11.0"
    }


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """Set up test environment variables"""
    monkeypatch.setenv("DEVELOPMENT_MODE", "true")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("ARTIFACT_STORAGE_DIR", "./test-artifacts")
    

@pytest.fixture
def caplog_debug(caplog):
    """Configure caplog for debug level logging"""
    caplog.set_level("DEBUG")
    return caplog


# Async test helpers
@pytest.fixture
async def async_test_timeout():
    """Provide reasonable timeout for async tests"""
    return 10.0  # 10 seconds


# Mock browser fixtures for when we implement browser functionality
@pytest.fixture
def mock_browser_context():
    """Mock browser context for testing browser operations"""
    
    class MockPage:
        def __init__(self):
            self.url = "about:blank"
            self.title_value = "Test Page"
            
        async def goto(self, url: str):
            self.url = url
            
        async def title(self):
            return self.title_value
            
        async def screenshot(self, **kwargs):
            return b"fake-screenshot-data"
    
    class MockBrowserContext:
        def __init__(self):
            self.pages = []
            
        async def new_page(self):
            page = MockPage()
            self.pages.append(page)
            return page
            
        async def close(self):
            self.pages.clear()
    
    return MockBrowserContext()


# Test data fixtures
@pytest.fixture
def sample_video_config():
    """Sample video recording configuration"""
    return {
        "filename": "test-recording",
        "size": {"width": 1280, "height": 720},
        "mode": "smart",
        "auto_set_viewport": True
    }


@pytest.fixture
def sample_request_data():
    """Sample HTTP request data for testing"""
    return {
        "id": "req-123",
        "timestamp": "2024-01-01T12:00:00Z",
        "url": "https://example.com/api/test",
        "method": "GET",
        "headers": {"Content-Type": "application/json"},
        "resource_type": "xhr",
        "response": {
            "status": 200,
            "status_text": "OK",
            "headers": {"Content-Type": "application/json"},
            "from_cache": False,
            "duration": 150.5
        }
    }


# Performance test fixtures
@pytest.fixture
def performance_baseline():
    """Performance baseline metrics for comparison"""
    return {
        "health_check_time": 0.05,  # 50ms
        "server_info_time": 0.03,   # 30ms
        "playwright_test_time": 2.0  # 2 seconds
    }


# Report generation fixtures
@pytest.fixture
def test_reporter():
    """Test reporter for enhanced test output"""
    
    class TestReporter:
        def __init__(self):
            self.test_results = []
            
        def log_test_start(self, test_name: str):
            self.test_results.append({
                "name": test_name,
                "start_time": asyncio.get_event_loop().time()
            })
            
        def log_test_end(self, test_name: str, success: bool):
            for result in self.test_results:
                if result["name"] == test_name:
                    result["end_time"] = asyncio.get_event_loop().time()
                    result["success"] = success
                    result["duration"] = result["end_time"] - result["start_time"]
                    break
                    
        def get_summary(self):
            return {
                "total_tests": len(self.test_results),
                "passed": len([r for r in self.test_results if r.get("success", False)]),
                "failed": len([r for r in self.test_results if not r.get("success", True)]),
                "avg_duration": sum(r.get("duration", 0) for r in self.test_results) / len(self.test_results) if self.test_results else 0
            }
    
    return TestReporter()


# Cleanup fixture
@pytest.fixture(autouse=True, scope="session")
def cleanup_test_artifacts():
    """Clean up test artifacts after test session"""
    yield
    
    # Clean up any test artifacts
    test_dirs = ["test-artifacts", "reports", ".pytest_cache"]
    for test_dir in test_dirs:
        if Path(test_dir).exists():
            import shutil
            shutil.rmtree(test_dir, ignore_errors=True)