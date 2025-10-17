#!/usr/bin/env python3
"""
Test Core Pagination Implementation

Tests the pagination infrastructure without requiring Playwright.
This validates the cursor management, models, and core functionality.
"""

import asyncio
import sys
from pathlib import Path

# Add source to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_cursor_manager_comprehensive():
    """Test SessionCursorManager with comprehensive scenarios"""
    print("🔄 Testing SessionCursorManager comprehensively...")
    
    try:
        from pagination.cursor_manager import SessionCursorManager
        from pagination.models import QueryState
        from datetime import datetime, timedelta
        
        # Initialize cursor manager
        manager = SessionCursorManager()
        await manager.start()
        
        # Test multiple sessions and cursors
        session_ids = ["session_1", "session_2", "session_3"]
        cursor_ids = []
        
        for i, session_id in enumerate(session_ids):
            query_state = QueryState(
                filters={"status": "all", "domain": f"example{i}.com"},
                parameters={"limit": 50, "format": "summary"}
            )
            
            cursor_id = manager.create_cursor(
                session_id=session_id,
                tool_name="browser_get_requests",
                query_state=query_state,
                initial_position={"last_index": i * 50, "filtered_total": 1000}
            )
            cursor_ids.append((cursor_id, session_id))
            print(f"  ✅ Created cursor {cursor_id} for session {session_id}")
        
        # Test session isolation - try cross-session access
        try:
            manager.get_cursor(cursor_ids[0][0], session_ids[1])
            print(f"  ❌ Cross-session access should have failed!")
            return False
        except Exception:
            print(f"  ✅ Cross-session access properly blocked")
        
        # Test cursor stats for each session
        for session_id in session_ids:
            stats = manager.get_session_cursor_stats(session_id)
            assert stats["total_cursors"] == 1
            print(f"  ✅ Session {session_id}: {stats['total_cursors']} cursors")
        
        # Test global stats
        global_stats = manager.get_global_stats()
        assert global_stats["total_cursors"] == 3
        assert global_stats["total_sessions"] == 3
        print(f"  ✅ Global stats: {global_stats['total_cursors']} cursors, {global_stats['total_sessions']} sessions")
        
        # Test session cleanup
        removed_count = manager.invalidate_session_cursors(session_ids[0])
        assert removed_count == 1
        print(f"  ✅ Cleaned up session {session_ids[0]}: {removed_count} cursors")
        
        # Cleanup
        await manager.stop()
        print("  ✅ Comprehensive SessionCursorManager tests passed!")
        return True
        
    except Exception as e:
        print(f"  ❌ SessionCursorManager comprehensive test failed: {e}")
        return False


async def test_pagination_models_advanced():
    """Test advanced pagination model scenarios"""
    print("🔄 Testing pagination models with advanced scenarios...")
    
    try:
        from pagination.models import (
            PaginationParams, RequestMonitoringParams, ConsoleMessagesParams,
            PaginatedResponse, QueryState
        )
        from datetime import timedelta
        import json
        
        # Test different parameter model types
        request_params = RequestMonitoringParams(
            limit=25,
            filter="errors", 
            domain="api.example.com",
            method="POST",
            status=404,
            slow_threshold=3000
        )
        
        console_params = ConsoleMessagesParams(
            limit=50,
            level_filter="error",
            source_filter="console"
        )
        
        print("  ✅ Created different parameter models")
        
        # Test QueryState consistency across different parameters
        query1 = QueryState.from_params(request_params)
        query2 = QueryState.from_params(console_params)
        
        # Should have different fingerprints due to different filters
        assert query1.fingerprint() != query2.fingerprint()
        print("  ✅ Different parameters produce different fingerprints")
        
        # Test QueryState equality
        query1_copy = QueryState(
            filters=query1.filters.copy(),
            parameters=query1.parameters.copy()
        )
        assert query1 == query1_copy
        print("  ✅ QueryState equality works correctly")
        
        # Test pagination response creation and serialization
        test_items = [
            {"id": f"item_{i}", "data": f"test_data_{i}"} for i in range(20)
        ]
        
        fresh_response = PaginatedResponse.create_fresh(
            items=test_items,
            cursor_id="cursor_fresh_123",
            estimated_total=200,
            fetch_time_ms=125.7,
            query_fingerprint=query1.fingerprint()
        )
        
        continuation_response = PaginatedResponse.create_continuation(
            items=test_items[10:],
            cursor_id="cursor_continue_456", 
            cursor_age=timedelta(minutes=5),
            total_fetched=50,
            fetch_time_ms=87.3
        )
        
        # Test response serialization (JSON compatibility)
        fresh_json = fresh_response.model_dump_json()
        continuation_json = continuation_response.model_dump_json()
        
        # Should be valid JSON
        json.loads(fresh_json)
        json.loads(continuation_json)
        print("  ✅ PaginatedResponse models serialize to valid JSON")
        
        # Test response metadata
        assert fresh_response.pagination.call_type == "fresh"
        assert fresh_response.has_more is True
        assert continuation_response.pagination.call_type == "continuation"
        
        print("  ✅ Advanced pagination model tests passed!")
        return True
        
    except Exception as e:
        print(f"  ❌ Advanced pagination models test failed: {e}")
        return False


async def test_query_state_robustness():
    """Test QueryState robustness with edge cases"""
    print("🔄 Testing QueryState robustness...")
    
    try:
        from pagination.models import QueryState, RequestMonitoringParams
        
        # Test with minimal parameters
        minimal_params = RequestMonitoringParams(limit=10)
        minimal_query = QueryState.from_params(minimal_params)
        
        # Test with all parameters
        full_params = RequestMonitoringParams(
            limit=100,
            cursor_id="test_cursor",
            session_id="test_session", 
            filter="slow",
            domain="complex-domain.example.com",
            method="PATCH",
            status=201,
            format="detailed",
            slow_threshold=5000
        )
        full_query = QueryState.from_params(full_params)
        
        # Fingerprints should be deterministic
        assert minimal_query.fingerprint() == minimal_query.fingerprint()
        assert full_query.fingerprint() == full_query.fingerprint()
        print("  ✅ QueryState fingerprints are deterministic")
        
        # Test with special characters and edge cases
        edge_params = RequestMonitoringParams(
            limit=1,
            filter="all",
            domain="test-with-special-chars.example.com",
            method="DELETE"
        )
        edge_query = QueryState.from_params(edge_params)
        
        # Should handle special characters in fingerprint
        fingerprint = edge_query.fingerprint()
        assert isinstance(fingerprint, str)
        assert len(fingerprint) > 0
        print("  ✅ QueryState handles edge cases and special characters")
        
        # Test query state filtering logic
        assert "cursor_id" not in full_query.parameters  # Should be excluded
        assert "session_id" not in full_query.parameters  # Should be excluded
        assert "filter" in full_query.filters  # Should be in filters
        assert "limit" in full_query.parameters  # Should be in parameters
        print("  ✅ QueryState correctly separates filters and parameters")
        
        print("  ✅ QueryState robustness tests passed!")
        return True
        
    except Exception as e:
        print(f"  ❌ QueryState robustness test failed: {e}")
        return False


async def test_cursor_lifecycle_simulation():
    """Simulate complete cursor lifecycle"""
    print("🔄 Testing complete cursor lifecycle simulation...")
    
    try:
        from pagination.cursor_manager import SessionCursorManager
        from pagination.models import QueryState, RequestMonitoringParams
        from datetime import datetime
        
        manager = SessionCursorManager()
        await manager.start()
        
        session_id = "lifecycle_test_session"
        
        # Simulate paginated query workflow
        params = RequestMonitoringParams(
            limit=20,
            filter="errors",
            domain="api.test.com",
            format="summary"
        )
        
        query_state = QueryState.from_params(params)
        
        # Step 1: Create cursor for first page
        cursor_id = manager.create_cursor(
            session_id=session_id,
            tool_name="browser_get_requests",
            query_state=query_state,
            initial_position={"last_index": 19, "filtered_total": 100, "current_page": 1}
        )
        print(f"  ✅ Step 1: Created cursor {cursor_id}")
        
        # Step 2: Fetch subsequent pages
        for page in range(2, 6):  # Pages 2-5
            cursor = manager.get_cursor(cursor_id, session_id)
            
            # Simulate fetching next page
            new_position = {
                "last_index": (page * 20) - 1,
                "filtered_total": 100,
                "current_page": page
            }
            
            manager.update_cursor_position(
                cursor_id, session_id, new_position, result_count=20
            )
            print(f"  ✅ Step 2.{page-1}: Updated cursor for page {page}")
        
        # Step 3: Verify cursor state
        final_cursor = manager.get_cursor(cursor_id, session_id)
        assert final_cursor.result_count == 80  # 20 results × 4 updates
        assert final_cursor.position["current_page"] == 5
        print("  ✅ Step 3: Cursor state correctly maintained")
        
        # Step 4: Simulate query change (should invalidate cursor)
        different_params = RequestMonitoringParams(
            limit=20,
            filter="success",  # Different filter
            domain="api.test.com",
            format="summary"
        )
        different_query = QueryState.from_params(different_params)
        
        # Cursor should not match the new query
        assert not final_cursor.matches_query_state({
            "filters": different_query.filters,
            "parameters": different_query.parameters
        })
        print("  ✅ Step 4: Query change detection works correctly")
        
        # Step 5: Cleanup
        removed = manager.invalidate_cursor(cursor_id, session_id)
        assert removed is True
        print("  ✅ Step 5: Cursor cleanup successful")
        
        await manager.stop()
        print("  ✅ Complete cursor lifecycle simulation passed!")
        return True
        
    except Exception as e:
        print(f"  ❌ Cursor lifecycle simulation failed: {e}")
        return False


async def main():
    """Run comprehensive pagination tests"""
    print("🧪 MCPlaywright Core Pagination Tests")
    print("=" * 60)
    
    tests = [
        ("SessionCursorManager Comprehensive", test_cursor_manager_comprehensive),
        ("Pagination Models Advanced", test_pagination_models_advanced),
        ("QueryState Robustness", test_query_state_robustness),
        ("Cursor Lifecycle Simulation", test_cursor_lifecycle_simulation)
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
        print(f"🎉 SUCCESS: All {total} core pagination tests passed!")
        print("\n✨ The core pagination implementation is fully functional:")
        print("  • Session-scoped cursor management with isolation")
        print("  • Robust QueryState fingerprinting and validation") 
        print("  • Comprehensive pagination model validation")
        print("  • Complete cursor lifecycle management")
        print("  • Cross-session security protection")
        print("  • Automatic cleanup and resource management")
        print("\n🚀 Ready for Phase 3: Advanced features and optimizations!")
        return 0
    else:
        print(f"⚠️  PARTIAL: {passed}/{total} core pagination tests passed")
        print("\nRemaining issues to investigate:")
        
        failed_tests = [name for i, (name, _) in enumerate(tests) if not results[i]]
        for test_name in failed_tests:
            print(f"  • {test_name} needs debugging")
        
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))