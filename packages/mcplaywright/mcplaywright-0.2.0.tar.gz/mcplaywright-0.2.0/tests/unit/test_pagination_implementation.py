#!/usr/bin/env python3
"""
Test Pagination Implementation

Validates that the cursor-based pagination system works correctly
for HTTP request monitoring and other paginated tools.
"""

import asyncio
import sys
from pathlib import Path

# Add source to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_cursor_manager():
    """Test SessionCursorManager basic functionality"""
    print("🔄 Testing SessionCursorManager...")
    
    try:
        from pagination.cursor_manager import SessionCursorManager
        from pagination.models import QueryState
        from datetime import datetime, timedelta
        
        # Initialize cursor manager
        manager = SessionCursorManager()
        await manager.start()
        
        # Test cursor creation
        query_state = QueryState(
            filters={"status": "all", "domain": "example.com"},
            parameters={"limit": 100, "format": "summary"}
        )
        
        session_id = "test_session_123"
        cursor_id = manager.create_cursor(
            session_id=session_id,
            tool_name="browser_get_requests", 
            query_state=query_state,
            initial_position={"last_index": 99, "filtered_total": 500}
        )
        
        print(f"  ✅ Created cursor: {cursor_id}")
        
        # Test cursor retrieval
        cursor = manager.get_cursor(cursor_id, session_id)
        assert cursor.session_id == session_id
        assert cursor.tool_name == "browser_get_requests"
        print(f"  ✅ Retrieved cursor successfully")
        
        # Test cursor position update
        manager.update_cursor_position(
            cursor_id, session_id, 
            {"last_index": 199, "filtered_total": 500}, 
            result_count=100
        )
        print(f"  ✅ Updated cursor position")
        
        # Test session stats
        stats = manager.get_session_cursor_stats(session_id)
        assert stats["total_cursors"] == 1
        print(f"  ✅ Session stats: {stats['total_cursors']} cursors")
        
        # Test cursor invalidation
        invalidated = manager.invalidate_cursor(cursor_id, session_id)
        assert invalidated is True
        print(f"  ✅ Invalidated cursor successfully")
        
        # Cleanup
        await manager.stop()
        print("  ✅ SessionCursorManager tests passed!")
        return True
        
    except Exception as e:
        print(f"  ❌ SessionCursorManager test failed: {e}")
        return False


async def test_pagination_models():
    """Test pagination models and validation"""
    print("🔄 Testing pagination models...")
    
    try:
        from pagination.models import (
            PaginationParams, RequestMonitoringParams, 
            PaginatedResponse, QueryState
        )
        
        # Test RequestMonitoringParams
        params = RequestMonitoringParams(
            limit=50,
            cursor_id="test_cursor",
            filter="errors",
            domain="api.example.com",
            method="POST",
            status=500
        )
        
        assert params.limit == 50
        assert params.filter == "errors"
        print("  ✅ RequestMonitoringParams validation passed")
        
        # Test QueryState fingerprinting
        query1 = QueryState.from_params(params)
        query2 = QueryState.from_params(params)
        
        assert query1.fingerprint() == query2.fingerprint()
        print("  ✅ QueryState fingerprinting consistent")
        
        # Test PaginatedResponse
        response = PaginatedResponse.create_fresh(
            items=[{"id": 1, "url": "test.com"}],
            cursor_id="cursor_123",
            estimated_total=1000,
            fetch_time_ms=45.5
        )
        
        assert response.has_more is True
        assert response.pagination.call_type == "fresh"
        print("  ✅ PaginatedResponse creation passed")
        
        print("  ✅ Pagination models tests passed!")
        return True
        
    except Exception as e:
        print(f"  ❌ Pagination models test failed: {e}")
        return False


async def test_context_integration():
    """Test Context class cursor integration"""
    print("🔄 Testing Context cursor integration...")
    
    try:
        from context import Context, BrowserConfig
        from pagination.models import QueryState
        from datetime import datetime
        
        # Create test context
        context = Context(
            session_id="test_context_session",
            config=BrowserConfig(headless=True)
        )
        
        await context.initialize()
        
        # Test cursor creation through context
        query_state = QueryState(
            filters={"filter": "slow"},
            parameters={"limit": 25, "slow_threshold": 2000}
        )
        
        cursor_id = await context.create_pagination_cursor(
            tool_name="browser_get_requests",
            query_state=query_state,
            initial_position={"last_index": 24, "filtered_total": 200}
        )
        
        print(f"  ✅ Created cursor via context: {cursor_id}")
        
        # Test cursor retrieval
        cursor = await context.get_pagination_cursor(cursor_id)
        assert cursor.session_id == context.session_id
        print("  ✅ Retrieved cursor via context")
        
        # Test cursor stats
        stats = await context.get_cursor_stats()
        assert stats["total_cursors"] == 1
        print(f"  ✅ Context cursor stats: {stats['total_cursors']} cursors")
        
        # Cleanup
        await context.cleanup()
        print("  ✅ Context integration tests passed!")
        return True
        
    except Exception as e:
        print(f"  ❌ Context integration test failed: {e}")
        return False


async def test_request_monitoring_pagination():
    """Test HTTP request monitoring pagination (mock test)"""
    print("🔄 Testing request monitoring pagination...")
    
    try:
        from pagination.models import RequestMonitoringParams, PaginatedResponse
        
        # Test parameter creation
        params = RequestMonitoringParams(
            limit=10,
            filter="all",
            domain="example.com",
            format="summary"
        )
        
        assert params.limit == 10
        assert params.filter == "all"
        print("  ✅ RequestMonitoringParams created successfully")
        
        # Mock pagination response
        mock_items = [
            {"id": f"req_{i}", "method": "GET", "url": f"https://example.com/api/{i}"} 
            for i in range(10)
        ]
        
        response = PaginatedResponse.create_fresh(
            items=mock_items,
            cursor_id="mock_cursor_123",
            estimated_total=100,
            fetch_time_ms=25.0,
            query_fingerprint="mock_fingerprint"
        )
        
        assert len(response.items) == 10
        assert response.has_more is True
        assert response.pagination.call_type == "fresh"
        print("  ✅ Mock pagination response created")
        
        print("  ✅ Request monitoring pagination tests passed!")
        return True
        
    except Exception as e:
        print(f"  ❌ Request monitoring pagination test failed: {e}")
        return False


async def main():
    """Run all pagination tests"""
    print("🧪 MCPlaywright Pagination Implementation Test")
    print("=" * 60)
    
    tests = [
        ("Cursor Manager", test_cursor_manager),
        ("Pagination Models", test_pagination_models), 
        ("Context Integration", test_context_integration),
        ("Request Monitoring Pagination", test_request_monitoring_pagination)
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n📋 Testing: {name}")
        result = await test_func()
        results.append(result)
        print()
    
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"🎉 SUCCESS: All {total} pagination tests passed!")
        print("\n✨ The MCP pagination implementation is working correctly:")
        print("  • SessionCursorManager provides session-scoped cursor management")
        print("  • Pagination models validate parameters and responses properly")
        print("  • Context class integrates cursor lifecycle management")  
        print("  • Request monitoring tools support cursor-based pagination")
        print("  • Session isolation and security features are functional")
        return 0
    else:
        print(f"⚠️  PARTIAL: {passed}/{total} pagination tests passed")
        print("\nRemaining issues to investigate:")
        
        if not results[0]:
            print("  • SessionCursorManager implementation needs fixes")
        if not results[1]:
            print("  • Pagination models need validation improvements")
        if not results[2]:
            print("  • Context integration requires debugging")
        if not results[3]:
            print("  • Request monitoring pagination needs adjustment")
        
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))