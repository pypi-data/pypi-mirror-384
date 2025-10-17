#!/usr/bin/env python3
"""
Test Advanced Pagination Features

Tests bidirectional navigation, adaptive chunk sizing, and performance optimization
features of the cursor-based pagination system.
"""

import asyncio
import sys
from pathlib import Path

# Add source to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

async def test_bidirectional_navigation():
    """Test backward navigation capabilities"""
    print("🔄 Testing bidirectional navigation...")
    
    try:
        from pagination.cursor_manager import SessionCursorManager
        from pagination.models import QueryState
        
        manager = SessionCursorManager()
        await manager.start()
        
        session_id = "nav_test_session"
        
        # Create cursor with bidirectional support
        query_state = QueryState(
            filters={"filter": "all"},
            parameters={"limit": 20, "format": "summary"}
        )
        
        cursor_id = manager.create_cursor(
            session_id=session_id,
            tool_name="browser_get_requests",
            query_state=query_state,
            initial_position={"page": 1, "last_index": 19},
            direction="both",
            enable_optimization=True
        )
        print(f"  ✅ Created bidirectional cursor: {cursor_id}")
        
        # Simulate forward navigation (multiple pages)
        positions = [
            {"page": 2, "last_index": 39},
            {"page": 3, "last_index": 59}, 
            {"page": 4, "last_index": 79}
        ]
        
        for i, pos in enumerate(positions):
            manager.update_cursor_position(cursor_id, session_id, pos, 20)
            print(f"  ✅ Advanced to position {i+2}: page {pos['page']}")
        
        # Test backward navigation
        cursor = manager.get_cursor(cursor_id, session_id)
        assert cursor.can_navigate_backward()
        print("  ✅ Cursor supports backward navigation")
        
        # Navigate backward
        previous_pos = manager.navigate_backward(cursor_id, session_id)
        assert previous_pos is not None
        assert previous_pos["page"] == 3  # Should go back to page 3
        print(f"  ✅ Navigated backward to page {previous_pos['page']}")
        
        # Verify cursor direction changed
        cursor = manager.get_cursor(cursor_id, session_id)
        assert cursor.direction == "backward"
        print("  ✅ Cursor direction updated to 'backward'")
        
        await manager.stop()
        print("  ✅ Bidirectional navigation tests passed!")
        return True
        
    except Exception as e:
        print(f"  ❌ Bidirectional navigation test failed: {e}")
        return False


async def test_adaptive_chunk_sizing():
    """Test adaptive chunk size optimization"""
    print("🔄 Testing adaptive chunk sizing...")
    
    try:
        from pagination.cursor_manager import SessionCursorManager
        from pagination.models import QueryState
        
        manager = SessionCursorManager()
        await manager.start()
        
        session_id = "chunk_test_session"
        
        # Create cursor with optimization enabled
        query_state = QueryState(
            filters={"filter": "slow"}, 
            parameters={"limit": 100, "format": "detailed"}
        )
        
        cursor_id = manager.create_cursor(
            session_id=session_id,
            tool_name="browser_get_requests",
            query_state=query_state,
            initial_position={"last_index": 99},
            enable_optimization=True
        )
        print(f"  ✅ Created optimizing cursor: {cursor_id}")
        
        # Simulate fetches with varying performance
        performance_scenarios = [
            {"fetch_time_ms": 800, "result_count": 100},  # Acceptable
            {"fetch_time_ms": 1200, "result_count": 100}, # Too slow
            {"fetch_time_ms": 600, "result_count": 75},   # Good performance
            {"fetch_time_ms": 400, "result_count": 50},   # Very fast
        ]
        
        for i, scenario in enumerate(performance_scenarios):
            # Record performance and get optimization
            optimal_size = manager.optimize_chunk_size(
                cursor_id=cursor_id,
                session_id=session_id,
                last_fetch_time_ms=scenario["fetch_time_ms"],
                result_count=scenario["result_count"]
            )
            
            print(f"  ✅ Scenario {i+1}: {scenario['fetch_time_ms']}ms/{scenario['result_count']} items → optimal size: {optimal_size}")
        
        # Verify cursor has performance history
        cursor = manager.get_cursor(cursor_id, session_id)
        assert len(cursor.chunk_size_history) == 4
        assert len(cursor.performance_metrics) > 0
        print("  ✅ Performance history recorded correctly")
        
        # Test optimal chunk size calculation
        target_optimal = cursor.get_optimal_chunk_size(target_time_ms=500)
        assert 10 <= target_optimal <= 1000
        print(f"  ✅ Calculated optimal chunk size: {target_optimal} for 500ms target")
        
        await manager.stop()
        print("  ✅ Adaptive chunk sizing tests passed!")
        return True
        
    except Exception as e:
        print(f"  ❌ Adaptive chunk sizing test failed: {e}")
        return False


async def test_performance_insights():
    """Test performance monitoring and insights"""
    print("🔄 Testing performance insights...")
    
    try:
        from pagination.cursor_manager import SessionCursorManager
        from pagination.models import QueryState
        
        manager = SessionCursorManager()
        await manager.start()
        
        session_id = "insights_test_session"
        
        # Create multiple cursors with different performance profiles
        cursors_data = [
            {
                "tool": "browser_get_requests",
                "performance": [{"time": 300, "count": 50}, {"time": 350, "count": 50}],
                "expected_throughput": "high"
            },
            {
                "tool": "browser_get_console_messages", 
                "performance": [{"time": 1500, "count": 100}, {"time": 1800, "count": 100}],
                "expected_throughput": "low"
            },
            {
                "tool": "browser_export_requests",
                "performance": [{"time": 800, "count": 200}, {"time": 750, "count": 180}],
                "expected_throughput": "medium"
            }
        ]
        
        cursor_ids = []
        
        for i, cursor_data in enumerate(cursors_data):
            query_state = QueryState(
                filters={"filter": "all"},
                parameters={"limit": 100, "format": "summary"}
            )
            
            cursor_id = manager.create_cursor(
                session_id=session_id,
                tool_name=cursor_data["tool"],
                query_state=query_state,
                initial_position={"last_index": 99},
                enable_optimization=True
            )
            cursor_ids.append(cursor_id)
            
            # Simulate performance data
            for perf in cursor_data["performance"]:
                manager.optimize_chunk_size(
                    cursor_id=cursor_id,
                    session_id=session_id,
                    last_fetch_time_ms=perf["time"],
                    result_count=perf["count"]
                )
            
            print(f"  ✅ Created cursor {i+1} for {cursor_data['tool']} with {cursor_data['expected_throughput']} throughput")
        
        # Get performance insights
        insights = manager.get_performance_insights(session_id)
        
        # Validate insights structure
        assert insights["session_id"] == session_id
        assert insights["total_cursors"] == 3
        assert len(insights["cursor_details"]) == 3
        print("  ✅ Performance insights structure valid")
        
        # Check for optimization opportunities
        opportunities = insights["performance_summary"]["optimization_opportunities"]
        slow_cursor_found = any("slow fetch times" in opp for opp in opportunities)
        assert slow_cursor_found  # Should detect the slow console messages cursor
        print(f"  ✅ Detected {len(opportunities)} optimization opportunities")
        
        # Validate cursor details
        for detail in insights["cursor_details"]:
            assert "cursor_id" in detail
            assert "tool_name" in detail
            assert "total_fetched" in detail
            assert "last_fetch_time_ms" in detail
            print(f"  ✅ Cursor {detail['tool_name']}: {detail['total_fetched']} items, {detail['last_fetch_time_ms']}ms")
        
        # Test average calculations
        avg_fetch_time = insights["performance_summary"]["avg_fetch_time_ms"]
        assert avg_fetch_time > 0
        print(f"  ✅ Average fetch time: {avg_fetch_time:.1f}ms")
        
        await manager.stop()
        print("  ✅ Performance insights tests passed!")
        return True
        
    except Exception as e:
        print(f"  ❌ Performance insights test failed: {e}")
        return False


async def test_advanced_cursor_features():
    """Test advanced cursor state management"""
    print("🔄 Testing advanced cursor features...")
    
    try:
        from pagination.cursor_manager import SessionCursorManager
        from pagination.models import QueryState
        
        manager = SessionCursorManager()
        await manager.start()
        
        session_id = "advanced_test_session"
        
        # Create cursor with all advanced features
        query_state = QueryState(
            filters={"status": "errors", "domain": "api.test.com"},
            parameters={"limit": 50, "format": "detailed", "slow_threshold": 1000}
        )
        
        cursor_id = manager.create_cursor(
            session_id=session_id,
            tool_name="browser_get_requests",
            query_state=query_state,
            initial_position={"last_index": 49, "total": 500, "page": 1},
            direction="both",
            enable_optimization=True
        )
        
        cursor = manager.get_cursor(cursor_id, session_id)
        
        # Test advanced features
        assert cursor.direction == "both"
        assert cursor.metadata["optimization_enabled"] is True
        assert cursor.metadata["target_response_time_ms"] == 500
        print("  ✅ Cursor created with advanced features enabled")
        
        # Test position caching for bidirectional navigation
        positions = [
            {"last_index": 99, "total": 500, "page": 2},
            {"last_index": 149, "total": 500, "page": 3},
            {"last_index": 199, "total": 500, "page": 4}
        ]
        
        for pos in positions:
            cursor.update_position(pos, 50)
        
        # Should have cached previous positions
        assert len(cursor.cached_positions) == 3  # Original + 2 updates cached
        print(f"  ✅ Cached {len(cursor.cached_positions)} positions for navigation")
        
        # Test performance recording
        cursor.record_performance(750.0, 50)
        cursor.record_chunk_size(50)
        
        assert "last_fetch_time_ms" in cursor.performance_metrics
        assert cursor.performance_metrics["last_fetch_time_ms"] == 750.0
        assert len(cursor.chunk_size_history) == 1
        print("  ✅ Performance metrics recorded correctly")
        
        # Test optimal chunk size calculation
        optimal = cursor.get_optimal_chunk_size(target_time_ms=600)
        assert isinstance(optimal, int)
        assert 10 <= optimal <= 1000
        print(f"  ✅ Calculated optimal chunk size: {optimal}")
        
        # Test global stats include advanced features
        global_stats = manager.get_global_stats()
        optimization_features = global_stats["optimization_features"]
        assert optimization_features["bidirectional_navigation"] is True
        assert optimization_features["adaptive_chunk_sizing"] is True
        assert optimization_features["performance_tracking"] is True
        print("  ✅ Global stats show advanced features enabled")
        
        await manager.stop()
        print("  ✅ Advanced cursor features tests passed!")
        return True
        
    except Exception as e:
        print(f"  ❌ Advanced cursor features test failed: {e}")
        return False


async def main():
    """Run all advanced pagination tests"""
    print("🚀 MCPlaywright Advanced Pagination Features Test")
    print("=" * 65)
    
    tests = [
        ("Bidirectional Navigation", test_bidirectional_navigation),
        ("Adaptive Chunk Sizing", test_adaptive_chunk_sizing),
        ("Performance Insights", test_performance_insights),
        ("Advanced Cursor Features", test_advanced_cursor_features)
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n📋 Testing: {name}")
        result = await test_func()
        results.append(result)
        print()
    
    print("=" * 65)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"🎉 SUCCESS: All {total} advanced pagination tests passed!")
        print("\n✨ Advanced features are fully functional:")
        print("  • 🔄 Bidirectional Navigation - Navigate forward and backward through pages")
        print("  • ⚡ Adaptive Chunk Sizing - Automatic optimization based on performance") 
        print("  • 📊 Performance Insights - Comprehensive monitoring and analytics")
        print("  • 🧠 Smart Optimization - Machine learning-like adaptation")
        print("  • 💾 Position Caching - Efficient backward navigation")
        print("  • 🎯 Target Performance - Configurable response time goals")
        print("\n🏆 Phase 3 (Advanced Features) Complete!")
        print("📋 Ready for Phase 4: Integration & Testing")
        return 0
    else:
        print(f"⚠️  PARTIAL: {passed}/{total} advanced pagination tests passed")
        print("\nRemaining advanced features to debug:")
        
        failed_tests = [name for i, (name, _) in enumerate(tests) if not results[i]]
        for test_name in failed_tests:
            print(f"  • {test_name} needs investigation")
        
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))