"""
Unit tests for the Universal Ripgrep Filtering System.

Tests the filtering engine, decorators, and integration with MCPlaywright tools.
"""

import asyncio
import pytest
import tempfile
from pathlib import Path
from typing import List, Dict, Any

from mcplaywright.filters.engine import RipgrepFilterEngine
from mcplaywright.filters.models import UniversalFilterParams, FilterMode
from mcplaywright.filters.decorators import filter_response


class TestRipgrepFilterEngine:
    """Test the core ripgrep filtering engine"""
    
    @pytest.fixture
    def engine(self):
        """Create a filter engine instance"""
        return RipgrepFilterEngine()
    
    @pytest.fixture
    def sample_requests(self):
        """Sample HTTP request data for testing"""
        return [
            {
                "url": "https://api.example.com/v1/users",
                "method": "GET",
                "status": 200,
                "headers": {"content-type": "application/json"},
                "response_body": '{"users": [{"id": 1, "name": "John"}]}'
            },
            {
                "url": "https://api.example.com/v1/login",
                "method": "POST", 
                "status": 401,
                "headers": {"content-type": "application/json"},
                "response_body": '{"error": "Invalid credentials"}'
            },
            {
                "url": "https://cdn.example.com/images/logo.png",
                "method": "GET",
                "status": 200,
                "headers": {"content-type": "image/png"},
                "response_body": "<binary data>"
            }
        ]
    
    @pytest.fixture
    def sample_console_messages(self):
        """Sample console message data for testing"""
        return [
            {
                "message": "User login successful",
                "level": "info",
                "source": "console",
                "timestamp": "2024-01-15T10:30:00Z"
            },
            {
                "message": "TypeError: Cannot read property 'id' of undefined",
                "level": "error",
                "source": "javascript",
                "timestamp": "2024-01-15T10:31:00Z",
                "stack_trace": "at UserComponent.render:15:3"
            },
            {
                "message": "React warning: prop validation failed",
                "level": "warning",
                "source": "console",
                "timestamp": "2024-01-15T10:32:00Z"
            }
        ]
    
    @pytest.mark.asyncio
    async def test_basic_pattern_filtering(self, engine, sample_requests):
        """Test basic pattern filtering functionality"""
        filter_params = UniversalFilterParams(
            filter_pattern="api.*users",
            filter_mode=FilterMode.CONTENT
        )
        
        result = await engine.filter_response(
            data=sample_requests,
            filter_params=filter_params,
            filterable_fields=["url", "method", "status"],
            content_fields=["url"]
        )
        
        assert result.match_count > 0
        assert len(result.filtered_data) == 1
        assert "users" in result.filtered_data[0]["url"]
        assert result.pattern_used == "api.*users"
    
    @pytest.mark.asyncio
    async def test_field_specific_filtering(self, engine, sample_requests):
        """Test filtering specific fields only"""
        filter_params = UniversalFilterParams(
            filter_pattern="POST",
            filter_fields=["method"],
            filter_mode=FilterMode.CONTENT
        )
        
        result = await engine.filter_response(
            data=sample_requests,
            filter_params=filter_params,
            filterable_fields=["url", "method", "status"],
            content_fields=["method"]
        )
        
        assert result.match_count > 0
        assert len(result.filtered_data) == 1
        assert result.filtered_data[0]["method"] == "POST"
        assert "method" in result.fields_searched
    
    @pytest.mark.asyncio
    async def test_case_insensitive_filtering(self, engine, sample_console_messages):
        """Test case insensitive pattern matching"""
        filter_params = UniversalFilterParams(
            filter_pattern="TYPEERROR",
            case_sensitive=False,
            filter_mode=FilterMode.CONTENT
        )
        
        result = await engine.filter_response(
            data=sample_console_messages,
            filter_params=filter_params,
            filterable_fields=["message", "level", "source"],
            content_fields=["message"]
        )
        
        assert result.match_count > 0
        assert len(result.filtered_data) == 1
        assert "TypeError" in result.filtered_data[0]["message"]
    
    @pytest.mark.asyncio
    async def test_inverted_filtering(self, engine, sample_requests):
        """Test inverted matching (show non-matches)"""
        filter_params = UniversalFilterParams(
            filter_pattern="200",
            invert_match=True,
            filter_mode=FilterMode.CONTENT
        )
        
        result = await engine.filter_response(
            data=sample_requests,
            filter_params=filter_params,
            filterable_fields=["url", "method", "status"],
            content_fields=["status"]
        )
        
        # Should return items that don't have status 200
        assert result.match_count > 0
        for item in result.filtered_data:
            assert item["status"] != 200
    
    @pytest.mark.asyncio
    async def test_count_mode_filtering(self, engine, sample_requests):
        """Test count mode returns match statistics only"""
        filter_params = UniversalFilterParams(
            filter_pattern="api",
            filter_mode=FilterMode.COUNT
        )
        
        result = await engine.filter_response(
            data=sample_requests,
            filter_params=filter_params,
            filterable_fields=["url", "method", "status"],
            content_fields=["url"]
        )
        
        assert isinstance(result.filtered_data, dict)
        assert "total_matches" in result.filtered_data
        assert result.filtered_data["total_matches"] > 0
    
    @pytest.mark.asyncio
    async def test_max_matches_limiting(self, engine, sample_requests):
        """Test max matches parameter limits results"""
        filter_params = UniversalFilterParams(
            filter_pattern="example\\.com",
            max_matches=1,
            filter_mode=FilterMode.CONTENT
        )
        
        result = await engine.filter_response(
            data=sample_requests,
            filter_params=filter_params,
            filterable_fields=["url", "method", "status"],
            content_fields=["url"]
        )
        
        # Should respect max_matches limit
        assert len(result.filtered_data) <= 1
    
    @pytest.mark.asyncio
    async def test_no_matches_handling(self, engine, sample_requests):
        """Test behavior when no matches are found"""
        filter_params = UniversalFilterParams(
            filter_pattern="nonexistent_pattern_xyz123",
            filter_mode=FilterMode.CONTENT
        )
        
        result = await engine.filter_response(
            data=sample_requests,
            filter_params=filter_params,
            filterable_fields=["url", "method", "status"],
            content_fields=["url"]
        )
        
        assert result.match_count == 0
        assert len(result.filtered_data) == 0
        assert result.execution_time_ms >= 0  # Should still track timing


class TestFilterDecorator:
    """Test the filter_response decorator"""
    
    @pytest.mark.asyncio
    async def test_decorator_with_filtering(self):
        """Test decorator applies filtering when filter_pattern provided"""
        
        @filter_response(
            filterable_fields=["name", "email", "role"],
            content_fields=["name", "email"],
            default_fields=["name"]
        )
        async def mock_tool(**kwargs):
            """Mock tool function that returns user data"""
            return [
                {"name": "John Doe", "email": "john@example.com", "role": "admin"},
                {"name": "Jane Smith", "email": "jane@example.com", "role": "user"},
                {"name": "Bob Johnson", "email": "bob@corp.com", "role": "admin"}
            ]
        
        # Test with filtering
        result = await mock_tool(
            filter_pattern="corp\\.com",
            filter_fields=["email"]
        )
        
        # Should return filtered results with metadata
        assert isinstance(result, dict)
        assert "data" in result or "filtered_data" in result
        assert "filter_applied" in result or "filter_metadata" in result
    
    @pytest.mark.asyncio
    async def test_decorator_without_filtering(self):
        """Test decorator passes through when no filtering requested"""
        
        @filter_response(
            filterable_fields=["name", "email"],
            content_fields=["name"]
        )
        async def mock_tool(**kwargs):
            return {"users": ["alice", "bob"]}
        
        # Test without filtering
        result = await mock_tool()
        
        # Should return original result unchanged
        assert result == {"users": ["alice", "bob"]}
    
    @pytest.mark.asyncio
    async def test_decorator_handles_errors_gracefully(self):
        """Test decorator handles filtering errors gracefully"""
        
        @filter_response(
            filterable_fields=["field1"],
            content_fields=["field1"]
        )
        async def mock_tool(**kwargs):
            return {"data": "test"}
        
        # Test with invalid regex pattern
        result = await mock_tool(
            filter_pattern="[invalid regex",  # Invalid regex
            filter_fields=["field1"]
        )
        
        # Should return original result when filtering fails
        assert result == {"data": "test"}


class TestIntegrationScenarios:
    """Test real-world integration scenarios"""
    
    @pytest.mark.asyncio
    async def test_http_request_filtering_scenario(self):
        """Test realistic HTTP request filtering scenario"""
        
        # Simulate large HTTP request dataset
        requests_data = []
        for i in range(100):
            if i % 10 == 0:
                # Add some error requests
                requests_data.append({
                    "url": f"https://api.example.com/v1/endpoint{i}",
                    "method": "POST",
                    "status": 500,
                    "response_body": '{"error": "Internal server error"}'
                })
            else:
                requests_data.append({
                    "url": f"https://api.example.com/v1/endpoint{i}",
                    "method": "GET", 
                    "status": 200,
                    "response_body": '{"success": true}'
                })
        
        engine = RipgrepFilterEngine()
        
        # Filter for error requests
        filter_params = UniversalFilterParams(
            filter_pattern="error|500",
            filter_fields=["status", "response_body"],
            filter_mode=FilterMode.CONTENT
        )
        
        result = await engine.filter_response(
            data=requests_data,
            filter_params=filter_params,
            filterable_fields=["url", "method", "status", "response_body"],
            content_fields=["response_body"]
        )
        
        # Should find all error requests
        assert result.match_count > 0
        assert len(result.filtered_data) == 10  # Every 10th request is an error
        
        for item in result.filtered_data:
            assert item["status"] == 500 or "error" in item["response_body"]
    
    @pytest.mark.asyncio
    async def test_console_messages_filtering_scenario(self):
        """Test realistic console message filtering scenario"""
        
        # Simulate console messages with various patterns
        console_data = []
        error_patterns = [
            "TypeError: Cannot read property",
            "ReferenceError: variable is not defined", 
            "SyntaxError: Unexpected token",
            "Network error: Failed to fetch"
        ]
        
        for i in range(50):
            if i % 5 == 0:
                # Add error messages
                pattern = error_patterns[i % len(error_patterns)]
                console_data.append({
                    "message": f"{pattern} at line {i}",
                    "level": "error",
                    "source": "javascript",
                    "stack_trace": f"at Component.render:{i}:3"
                })
            else:
                console_data.append({
                    "message": f"Debug info {i}",
                    "level": "info",
                    "source": "console",
                    "stack_trace": None
                })
        
        engine = RipgrepFilterEngine()
        
        # Filter for JavaScript errors
        filter_params = UniversalFilterParams(
            filter_pattern="(TypeError|ReferenceError|SyntaxError)",
            filter_fields=["message"],
            filter_mode=FilterMode.CONTENT
        )
        
        result = await engine.filter_response(
            data=console_data,
            filter_params=filter_params,
            filterable_fields=["message", "level", "source", "stack_trace"],
            content_fields=["message", "stack_trace"]
        )
        
        # Should find JavaScript error messages
        assert result.match_count > 0
        assert len(result.filtered_data) == 8  # Only matches TypeError, ReferenceError, SyntaxError (not Network error)
        
        for item in result.filtered_data:
            assert any(error in item["message"] for error in ["TypeError", "ReferenceError", "SyntaxError"])


@pytest.mark.integration
class TestFilteringPerformance:
    """Test filtering performance with larger datasets"""
    
    @pytest.mark.asyncio
    async def test_large_dataset_filtering_performance(self):
        """Test filtering performance with large datasets"""
        
        # Create large dataset (1000 items)
        large_dataset = []
        for i in range(1000):
            large_dataset.append({
                "id": i,
                "url": f"https://api{i % 10}.example.com/endpoint{i}",
                "method": "GET" if i % 2 == 0 else "POST",
                "status": 200 if i % 20 != 0 else 500,
                "body": f"Response data for request {i}"
            })
        
        engine = RipgrepFilterEngine()
        
        # Filter for specific pattern
        filter_params = UniversalFilterParams(
            filter_pattern="api[0-5].*endpoint",
            filter_mode=FilterMode.CONTENT
        )
        
        import time
        start_time = time.time()
        
        result = await engine.filter_response(
            data=large_dataset,
            filter_params=filter_params,
            filterable_fields=["url", "method", "status", "body"],
            content_fields=["url", "body"]
        )
        
        end_time = time.time()
        execution_time = (end_time - start_time) * 1000  # Convert to ms
        
        # Performance assertions
        assert execution_time < 5000  # Should complete within 5 seconds
        assert result.execution_time_ms > 0
        assert result.match_count > 0
        assert len(result.filtered_data) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])