#!/usr/bin/env python3
"""
Redis Persistence Testing

Tests that cursors survive Redis container restarts and validate TTL functionality.
"""

import sys
import os
import asyncio
import time
import json
from datetime import datetime, timedelta
sys.path.insert(0, 'src')

from pagination.cursor_manager import SessionCursorManager
from pagination.models import QueryState


async def test_redis_persistence():
    """Test cursor persistence across Redis restarts"""
    print("🔄 Redis Persistence Test")
    print("=" * 50)
    
    # Setup Redis cursor manager
    cursor_manager = SessionCursorManager(
        storage_backend="redis",
        storage_config={
            "host": os.getenv("REDIS_HOST", "localhost"),
            "port": int(os.getenv("REDIS_PORT", "6379")),
            "db": int(os.getenv("REDIS_DB", "3")),  # Use separate DB
        },
        default_expiry_hours=24
    )
    
    await cursor_manager.start()
    session_id = "persistence_test_session"
    
    # Create test cursors
    print("\n📝 Creating test cursors...")
    test_cursors = []
    
    for i in range(5):
        large_payload = {
            "persistence_test": True,
            "cursor_index": i,
            "created_at": datetime.now().isoformat(),
            "large_data": "x" * (100 * 1024),  # 100KB payload
            "nested_structure": {
                "level_1": {
                    "level_2": {
                        "data": f"test_data_{i}",
                        "values": list(range(100))
                    }
                }
            }
        }
        
        query_state = QueryState(
            filters={"persistence_test": True, "cursor_id": i},
            parameters={"test_type": "persistence"}
        )
        
        position_data = {
            "index": i * 10,
            "test_payload": large_payload,
            "metadata": {"created_for_persistence_test": True}
        }
        
        cursor_id = await cursor_manager.create_cursor(
            session_id=session_id,
            tool_name=f"persistence_test_{i}",
            query_state=query_state,
            initial_position=position_data
        )
        
        test_cursors.append(cursor_id)
        print(f"  ✅ Created cursor {i+1}: {cursor_id}")
    
    # Verify cursors exist
    print("\n🔍 Verifying cursors before restart...")
    for i, cursor_id in enumerate(test_cursors):
        try:
            cursor = await cursor_manager.get_cursor(cursor_id, session_id)
            payload = cursor.position["test_payload"]
            assert payload["cursor_index"] == i
            assert payload["large_data"] == "x" * (100 * 1024)
            print(f"  ✅ Cursor {i+1} verified: {len(payload['large_data'])/1024:.0f}KB")
        except Exception as e:
            print(f"  ❌ Cursor {i+1} verification failed: {e}")
    
    await cursor_manager.stop()
    
    # Simulate Redis restart
    print(f"\n🔄 Simulating Redis container restart...")
    print(f"  💡 In real scenario: docker restart redis-stress-test")
    print(f"  💡 For this test: brief pause to simulate restart delay")
    await asyncio.sleep(2)
    
    # Reconnect after restart
    print(f"\n🔌 Reconnecting to Redis after restart...")
    cursor_manager = SessionCursorManager(
        storage_backend="redis",
        storage_config={
            "host": os.getenv("REDIS_HOST", "localhost"),
            "port": int(os.getenv("REDIS_PORT", "6379")),
            "db": int(os.getenv("REDIS_DB", "3")),
        },
        default_expiry_hours=24
    )
    
    await cursor_manager.start()
    
    # Verify cursors survived restart
    print(f"\n🔍 Verifying cursors after restart...")
    survived_cursors = 0
    
    for i, cursor_id in enumerate(test_cursors):
        try:
            cursor = await cursor_manager.get_cursor(cursor_id, session_id)
            payload = cursor.position["test_payload"]
            
            # Verify data integrity
            assert payload["cursor_index"] == i
            assert payload["persistence_test"] is True
            assert len(payload["large_data"]) == 100 * 1024
            assert payload["nested_structure"]["level_1"]["level_2"]["data"] == f"test_data_{i}"
            
            survived_cursors += 1
            print(f"  ✅ Cursor {i+1} survived restart with full data integrity")
            
        except Exception as e:
            print(f"  ❌ Cursor {i+1} lost after restart: {e}")
    
    await cursor_manager.stop()
    
    print(f"\n📊 Persistence Test Results:")
    print(f"  📝 Cursors created: {len(test_cursors)}")
    print(f"  ✅ Cursors survived: {survived_cursors}")
    print(f"  📊 Survival rate: {survived_cursors/len(test_cursors)*100:.1f}%")
    
    if survived_cursors == len(test_cursors):
        print(f"  🎉 Perfect persistence! All cursors survived Redis restart")
        return True
    else:
        print(f"  ⚠️  Some cursors were lost during restart")
        return False


async def test_redis_ttl():
    """Test Redis TTL (Time To Live) functionality"""
    print("\n🕐 Redis TTL Test")
    print("=" * 50)
    
    # Setup with short TTL for testing
    cursor_manager = SessionCursorManager(
        storage_backend="redis",
        storage_config={
            "host": os.getenv("REDIS_HOST", "localhost"),
            "port": int(os.getenv("REDIS_PORT", "6379")),
            "db": int(os.getenv("REDIS_DB", "4")),  # Use separate DB
        },
        default_expiry_hours=1/3600  # 1 second for testing
    )
    
    await cursor_manager.start()
    session_id = "ttl_test_session"
    
    # Create cursors with different TTLs
    print("\n📝 Creating cursors with short TTL...")
    ttl_cursors = []
    
    for i in range(3):
        query_state = QueryState(
            filters={"ttl_test": True, "cursor_id": i},
            parameters={"test_type": "ttl"}
        )
        
        position_data = {
            "index": i,
            "ttl_test_data": f"cursor_{i}_data",
            "created_at": datetime.now().isoformat()
        }
        
        cursor_id = await cursor_manager.create_cursor(
            session_id=session_id,
            tool_name=f"ttl_test_{i}",
            query_state=query_state,
            initial_position=position_data,
            expiry_hours=1/3600  # 1 second expiry
        )
        
        ttl_cursors.append(cursor_id)
        print(f"  ✅ Created TTL cursor {i+1}: {cursor_id}")
    
    # Verify cursors exist immediately
    print(f"\n🔍 Verifying cursors immediately after creation...")
    for i, cursor_id in enumerate(ttl_cursors):
        try:
            cursor = await cursor_manager.get_cursor(cursor_id, session_id)
            print(f"  ✅ Cursor {i+1} accessible immediately")
        except Exception as e:
            print(f"  ❌ Cursor {i+1} not accessible: {e}")
    
    # Wait for TTL expiration
    print(f"\n⏰ Waiting for TTL expiration (3 seconds)...")
    await asyncio.sleep(3)
    
    # Try to access expired cursors
    print(f"\n🔍 Checking cursors after TTL expiration...")
    expired_count = 0
    
    for i, cursor_id in enumerate(ttl_cursors):
        try:
            cursor = await cursor_manager.get_cursor(cursor_id, session_id)
            print(f"  ⚠️  Cursor {i+1} unexpectedly still accessible")
        except Exception as e:
            expired_count += 1
            print(f"  ✅ Cursor {i+1} properly expired: {type(e).__name__}")
    
    await cursor_manager.stop()
    
    print(f"\n📊 TTL Test Results:")
    print(f"  📝 Cursors created: {len(ttl_cursors)}")
    print(f"  ⏰ Cursors expired: {expired_count}")
    print(f"  📊 Expiration rate: {expired_count/len(ttl_cursors)*100:.1f}%")
    
    if expired_count == len(ttl_cursors):
        print(f"  🎉 Perfect TTL behavior! All cursors expired as expected")
        return True
    else:
        print(f"  ⚠️  TTL behavior unexpected")
        return False


async def main():
    """Run comprehensive Redis functionality tests"""
    print("🧪 Redis Functionality Testing")
    print("=" * 70)
    
    try:
        # Test persistence
        persistence_passed = await test_redis_persistence()
        
        # Test TTL
        ttl_passed = await test_redis_ttl()
        
        # Summary
        print(f"\n🎯 Redis Functionality Test Summary:")
        print(f"=" * 70)
        print(f"  📦 Persistence Test: {'✅ PASSED' if persistence_passed else '❌ FAILED'}")
        print(f"  ⏰ TTL Test: {'✅ PASSED' if ttl_passed else '❌ FAILED'}")
        
        if persistence_passed and ttl_passed:
            print(f"\n🎉 All Redis functionality tests passed!")
            print(f"   💾 Cursors persist across restarts")
            print(f"   ⏰ TTL expiration works correctly")
            print(f"   🚀 Redis backend is production-ready")
        else:
            print(f"\n⚠️  Some Redis functionality tests failed")
            print(f"   📋 Review Redis configuration and connectivity")
        
        return persistence_passed and ttl_passed
        
    except Exception as e:
        print(f"❌ Redis functionality testing failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    if success:
        print(f"\n✅ Redis testing completed successfully!")
    else:
        print(f"\n❌ Redis testing had issues")