#!/usr/bin/env python3
"""
Large Cursor Payload Testing

Test pagination system with extremely large cursor payloads (100KB+)
to validate memory management, serialization performance, and scalability.
"""

import sys
import os
import json
import time
import random
import string
import psutil
from typing import Dict, Any, List
sys.path.insert(0, 'src')

from pagination.cursor_manager import SessionCursorManager
from pagination.models import QueryState


def generate_large_payload(target_size_kb: int) -> Dict[str, Any]:
    """Generate a large data payload targeting specific size in KB"""
    
    # Calculate approximate size needed
    target_bytes = target_size_kb * 1024
    
    payload = {
        "metadata": {
            "timestamp": "2025-01-01T12:00:00Z",
            "version": "1.0.0",
            "generator": "large_cursor_test"
        },
        "large_arrays": [],
        "complex_objects": {},
        "text_data": "",
        "binary_simulation": []
    }
    
    # Add large text data (roughly 25% of target)
    text_size = target_bytes // 4
    payload["text_data"] = ''.join(random.choices(string.ascii_letters + string.digits + ' \n', k=text_size))
    
    # Add large arrays (roughly 35% of target)
    array_item_count = (target_bytes * 35 // 100) // 200  # ~200 bytes per item
    payload["large_arrays"] = [
        {
            "id": f"item_{i}",
            "data": ''.join(random.choices(string.ascii_letters, k=150)),
            "metadata": {
                "created": f"2025-01-{(i%30)+1:02d}T{(i%24):02d}:00:00Z",
                "tags": [f"tag_{j}" for j in range(5)],
                "properties": {f"prop_{k}": f"value_{k}_{i}" for k in range(3)}
            }
        }
        for i in range(array_item_count)
    ]
    
    # Add complex nested objects (roughly 25% of target)
    object_count = (target_bytes * 25 // 100) // 500  # ~500 bytes per object
    for i in range(object_count):
        payload["complex_objects"][f"object_{i}"] = {
            "nested_level_1": {
                "nested_level_2": {
                    "nested_level_3": {
                        "data": ''.join(random.choices(string.ascii_letters, k=200)),
                        "numbers": [random.randint(1, 1000) for _ in range(20)],
                        "config": {
                            f"setting_{j}": f"config_value_{j}_{i}"
                            for j in range(10)
                        }
                    }
                }
            }
        }
    
    # Add binary simulation data (roughly 15% of target)
    binary_size = target_bytes * 15 // 100
    payload["binary_simulation"] = [random.randint(0, 255) for _ in range(binary_size)]
    
    return payload


def measure_payload_size(payload: Dict[str, Any]) -> int:
    """Measure actual payload size in bytes"""
    json_str = json.dumps(payload, default=str)
    return len(json_str.encode('utf-8'))


async def main():
    print("🧪 Large Cursor Payload Testing")
    print("=" * 60)
    
    # Get storage backend from environment
    storage_backend = os.getenv("STORAGE_BACKEND", "memory")
    storage_config = {}
    
    if storage_backend == "redis":
        storage_config = {
            "host": os.getenv("REDIS_HOST", "localhost"),
            "port": int(os.getenv("REDIS_PORT", "6379")),
            "db": int(os.getenv("REDIS_DB", "0")),
            "password": os.getenv("REDIS_PASSWORD", None)
        }
        print(f"🔄 Using Redis backend: {storage_config['host']}:{storage_config['port']}/{storage_config['db']}")
    elif storage_backend == "sqlite":
        storage_config = {"db_path": "./data/large_cursor_test.db"}
        print(f"🔄 Using SQLite backend: {storage_config['db_path']}")
    else:
        print(f"🔄 Using Memory backend")
    
    # Initialize cursor manager with specified backend
    cursor_manager = SessionCursorManager(
        storage_backend=storage_backend,
        storage_config=storage_config
    )
    await cursor_manager.start()
    session_id = "large_cursor_session"
    
    # Get initial memory
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss
    print(f"📊 Initial memory: {initial_memory / (1024*1024):.2f}MB")
    
    # Test different cursor payload sizes
    test_sizes = [50, 100, 250, 500, 1000]  # KB
    results = []
    
    for target_size_kb in test_sizes:
        print(f"\n🔍 Testing {target_size_kb}KB cursor payloads...")
        
        # Generate large payload
        payload_start_time = time.time()
        large_payload = generate_large_payload(target_size_kb)
        payload_gen_time = time.time() - payload_start_time
        
        # Measure actual size
        actual_size_bytes = measure_payload_size(large_payload)
        actual_size_kb = actual_size_bytes / 1024
        
        print(f"  📦 Generated payload: {actual_size_kb:.1f}KB (target: {target_size_kb}KB)")
        print(f"  ⏱️  Generation time: {payload_gen_time:.3f}s")
        
        # Create query state with large payload
        query_state = QueryState(
            filters={"size_test": target_size_kb, "type": "large_cursor_test"},
            parameters={"limit": 100, "include_large_data": True}
        )
        
        # Create position data with the large payload
        position_data = {
            "index": 0,
            "last_id": f"large_item_0",
            "large_payload": large_payload,
            "cursor_metadata": {
                "size_kb": target_size_kb,
                "created_at": time.time(),
                "test_id": f"large_cursor_test_{target_size_kb}kb"
            }
        }
        
        # Test cursor creation with large payload
        creation_start_time = time.time()
        cursor_id = await cursor_manager.create_cursor(
            session_id=session_id,
            tool_name=f"large_cursor_test_{target_size_kb}kb",
            query_state=query_state,
            initial_position=position_data,
            enable_optimization=True
        )
        creation_time = time.time() - creation_start_time
        
        print(f"  ✅ Cursor created: {cursor_id}")
        print(f"  ⏱️  Creation time: {creation_time:.3f}s")
        
        # Test cursor retrieval
        retrieval_start_time = time.time()
        retrieved_cursor = await cursor_manager.get_cursor(cursor_id, session_id)
        retrieval_time = time.time() - retrieval_start_time
        
        print(f"  📖 Cursor retrieved successfully")
        print(f"  ⏱️  Retrieval time: {retrieval_time:.3f}s")
        
        # Validate data integrity
        retrieved_payload = retrieved_cursor.position["large_payload"]
        retrieved_size_bytes = measure_payload_size(retrieved_payload)
        retrieved_size_kb = retrieved_size_bytes / 1024
        
        integrity_check = (
            retrieved_payload["metadata"]["generator"] == "large_cursor_test" and
            len(retrieved_payload["large_arrays"]) > 0 and
            len(retrieved_payload["text_data"]) > 0
        )
        
        print(f"  🔍 Data integrity: {'✅ PASSED' if integrity_check else '❌ FAILED'}")
        print(f"  📏 Retrieved size: {retrieved_size_kb:.1f}KB")
        
        # Test cursor operations (update position)
        update_start_time = time.time()
        new_position = position_data.copy()
        new_position["index"] = 100
        new_position["last_id"] = f"large_item_100"
        # Keep the large payload
        await cursor_manager.update_cursor_position(cursor_id, session_id, new_position, 100)
        update_time = time.time() - update_start_time
        
        print(f"  🔄 Position updated in {update_time:.3f}s")
        
        # Check memory usage
        current_memory = process.memory_info().rss
        memory_diff_mb = (current_memory - initial_memory) / (1024 * 1024)
        # Get cursor count from session stats
        session_stats = await cursor_manager.get_session_cursor_stats(session_id)
        cursor_count = session_stats['total_cursors']
        memory_per_cursor_kb = memory_diff_mb * 1024 / cursor_count if cursor_count > 0 else 0
        
        print(f"  🧠 Memory per cursor: {memory_per_cursor_kb:.1f}KB")
        
        # Store results
        results.append({
            "target_size_kb": target_size_kb,
            "actual_size_kb": actual_size_kb,
            "creation_time": creation_time,
            "retrieval_time": retrieval_time,
            "update_time": update_time,
            "memory_per_cursor_kb": memory_per_cursor_kb,
            "integrity_check": integrity_check,
            "cursor_id": cursor_id
        })
    
    # Performance analysis
    print(f"\n📊 Large Cursor Performance Analysis:")
    print("-" * 60)
    
    for result in results:
        print(f"Size: {result['actual_size_kb']:6.1f}KB | "
              f"Create: {result['creation_time']:6.3f}s | "
              f"Retrieve: {result['retrieval_time']:6.3f}s | "
              f"Memory: {result['memory_per_cursor_kb']:6.1f}KB | "
              f"Integrity: {'✅' if result['integrity_check'] else '❌'}")
    
    # Test concurrent operations with large cursors
    print(f"\n🌪️ Concurrent Large Cursor Test...")
    concurrent_start_time = time.time()
    
    concurrent_cursors = []
    for i in range(5):  # Create 5 concurrent large cursors
        large_payload = generate_large_payload(200)  # 200KB each
        
        query_state = QueryState(
            filters={"concurrent_test": i},
            parameters={"worker_id": i}
        )
        
        position_data = {
            "worker_id": i,
            "large_payload": large_payload,
            "concurrent_test": True
        }
        
        cursor_id = await cursor_manager.create_cursor(
            session_id=f"concurrent_session_{i}",
            tool_name=f"concurrent_large_test_{i}",
            query_state=query_state,
            initial_position=position_data
        )
        
        concurrent_cursors.append(cursor_id)
    
    concurrent_time = time.time() - concurrent_start_time
    
    # Test retrieval of all concurrent cursors
    retrieval_start_time = time.time()
    for i, cursor_id in enumerate(concurrent_cursors):
        retrieved = await cursor_manager.get_cursor(cursor_id, f"concurrent_session_{i}")
        assert retrieved.position["worker_id"] == i
    
    concurrent_retrieval_time = time.time() - retrieval_start_time
    
    print(f"  ✅ Created {len(concurrent_cursors)} large cursors in {concurrent_time:.3f}s")
    print(f"  ✅ Retrieved all cursors in {concurrent_retrieval_time:.3f}s")
    
    # Final memory analysis
    final_memory = process.memory_info().rss
    total_memory_usage_mb = (final_memory - initial_memory) / (1024 * 1024)
    global_stats = await cursor_manager.get_global_stats()
    total_cursors = global_stats['total_cursors']
    
    print(f"\n🏁 Final Results:")
    print("-" * 60)
    print(f"  💾 Total cursors created: {total_cursors}")
    print(f"  🧠 Total memory increase: {total_memory_usage_mb:.2f}MB")
    print(f"  📏 Average memory per cursor: {total_memory_usage_mb*1024/total_cursors:.1f}KB")
    print(f"  ⚡ System performance: {'✅ EXCELLENT' if total_memory_usage_mb < 50 else '⚠️  HIGH' if total_memory_usage_mb < 100 else '❌ EXCESSIVE'}")
    
    # Performance thresholds validation
    print(f"\n🎯 Performance Threshold Validation:")
    print("-" * 60)
    
    thresholds = {
        "Creation time (100KB cursor)": (0.1, "s"),
        "Retrieval time (100KB cursor)": (0.05, "s"),
        "Memory efficiency": (150, "KB/cursor"),
        "Data integrity": (100, "% success rate")
    }
    
    # Get 100KB test result for threshold checking
    kb_100_result = next((r for r in results if abs(r["actual_size_kb"] - 100) < 20), None)
    
    if kb_100_result:
        actual_values = {
            "Creation time (100KB cursor)": kb_100_result["creation_time"],
            "Retrieval time (100KB cursor)": kb_100_result["retrieval_time"],
            "Memory efficiency": kb_100_result["memory_per_cursor_kb"],
            "Data integrity": 100 if all(r["integrity_check"] for r in results) else 0
        }
        
        for metric, (threshold, unit) in thresholds.items():
            actual = actual_values[metric]
            if metric == "Data integrity":
                status = "✅ PASSED" if actual == threshold else "❌ FAILED"
            elif metric == "Memory efficiency":
                status = "✅ PASSED" if actual <= threshold else "❌ FAILED"
            else:
                status = "✅ PASSED" if actual <= threshold else "❌ FAILED"
            
            print(f"  {metric}: {actual:.3f}{unit} (threshold: {threshold}{unit}) {status}")
    
    # Cleanup
    try:
        await cursor_manager.invalidate_session_cursors(session_id)
        for i in range(len(concurrent_cursors)):
            await cursor_manager.invalidate_session_cursors(f"concurrent_session_{i}")
        await cursor_manager.stop()
    except Exception as e:
        print(f"Cleanup error: {e}")
    
    print(f"\n✅ Large cursor payload testing complete!")
    print(f"🎉 System successfully handled cursors up to {max(r['actual_size_kb'] for r in results):.1f}KB!")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())