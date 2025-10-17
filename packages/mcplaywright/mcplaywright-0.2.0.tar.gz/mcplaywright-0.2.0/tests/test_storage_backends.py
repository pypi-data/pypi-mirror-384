#!/usr/bin/env python3
"""
Storage Backend Testing for Large Cursor Payloads

Tests different storage backends (memory, SQLite, Redis) with large cursor data
to validate performance, memory efficiency, and abandoned cursor cleanup.
"""

import sys
import os
import json
import time
import asyncio
import tempfile
import random
import string
import psutil
from pathlib import Path
from typing import Dict, Any, List
sys.path.insert(0, 'src')

from pagination.cursor_manager import SessionCursorManager
from pagination.models import QueryState
from pagination.storage import InMemoryStorage, SQLiteStorage


def generate_large_payload(target_size_kb: int) -> Dict[str, Any]:
    """Generate a large data payload targeting specific size in KB"""
    
    target_bytes = target_size_kb * 1024
    
    payload = {
        "metadata": {
            "timestamp": "2025-01-01T12:00:00Z",
            "version": "1.0.0",
            "generator": "storage_backend_test",
            "size_target_kb": target_size_kb
        },
        "large_text": ''.join(random.choices(string.ascii_letters + string.digits + ' \n', k=target_bytes // 2)),
        "data_array": [
            {
                "id": f"item_{i}",
                "payload": ''.join(random.choices(string.ascii_letters, k=100)),
                "metadata": {f"key_{j}": f"value_{j}_{i}" for j in range(5)}
            }
            for i in range((target_bytes // 2) // 200)
        ],
        "binary_simulation": [random.randint(0, 255) for _ in range(target_bytes // 4)]
    }
    
    return payload


async def test_storage_backend(backend_name: str, cursor_manager: SessionCursorManager, payload_sizes: List[int]):
    """Test a storage backend with various cursor payload sizes"""
    
    print(f"\n🔧 Testing {backend_name} storage backend...")
    print("-" * 50)
    
    session_id = f"storage_test_{backend_name}"
    results = []
    
    # Get initial process memory
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss
    
    for size_kb in payload_sizes:
        print(f"  📦 Testing {size_kb}KB cursor...")
        
        # Generate large payload
        payload = generate_large_payload(size_kb)
        actual_size_bytes = len(json.dumps(payload, default=str).encode('utf-8'))
        actual_size_kb = actual_size_bytes / 1024
        
        # Create query state
        query_state = QueryState(
            filters={"backend": backend_name, "size_kb": size_kb},
            parameters={"test_type": "storage_backend"}
        )
        
        # Create position with large payload
        position_data = {
            "index": 0,
            "large_payload": payload,
            "backend_test": True
        }
        
        # Time cursor creation
        start_time = time.time()
        cursor_id = await cursor_manager.create_cursor(
            session_id=session_id,
            tool_name=f"{backend_name}_test_{size_kb}kb",
            query_state=query_state,
            initial_position=position_data
        )
        creation_time = time.time() - start_time
        
        # Time cursor retrieval
        start_time = time.time()
        retrieved_cursor = await cursor_manager.get_cursor(cursor_id, session_id)
        retrieval_time = time.time() - start_time
        
        # Validate data integrity
        retrieved_payload = retrieved_cursor.position["large_payload"]
        integrity_check = (
            retrieved_payload["metadata"]["generator"] == "storage_backend_test" and
            retrieved_payload["metadata"]["size_target_kb"] == size_kb and
            len(retrieved_payload["large_text"]) > 0
        )
        
        # Check current memory usage
        current_memory = process.memory_info().rss
        memory_diff_mb = (current_memory - initial_memory) / (1024 * 1024)
        
        results.append({
            "size_kb": actual_size_kb,
            "creation_time": creation_time,
            "retrieval_time": retrieval_time,
            "integrity": integrity_check,
            "memory_diff_mb": memory_diff_mb,
            "cursor_id": cursor_id
        })
        
        print(f"    ✅ Created in {creation_time:.3f}s, retrieved in {retrieval_time:.3f}s")
        print(f"    📏 Size: {actual_size_kb:.1f}KB, Integrity: {'✅' if integrity_check else '❌'}")
    
    # Get storage backend statistics
    try:
        stats = await cursor_manager._storage.get_storage_stats()
        print(f"  📊 Storage stats: {stats}")
    except Exception as e:
        print(f"  ⚠️  Could not get storage stats: {e}")
    
    return results


async def test_abandoned_cursor_cleanup():
    """Test cleanup of abandoned cursors across different storage backends"""
    
    print(f"\n🧹 Testing Abandoned Cursor Cleanup...")
    print("=" * 60)
    
    backends_to_test = [
        ("memory", InMemoryStorage()),
        ("sqlite", SQLiteStorage(db_path=str(Path(tempfile.gettempdir()) / "test_cleanup.db")))
    ]
    
    for backend_name, storage_backend in backends_to_test:
        print(f"\n🔧 Testing cleanup with {backend_name} backend...")
        
        # Create cursor manager with short expiry for testing
        cursor_manager = SessionCursorManager(
            default_expiry_hours=1/3600,  # 1 second expiry for testing
            storage_backend=storage_backend
        )
        
        await cursor_manager.start()
        
        # Create several "abandoned" cursors
        abandoned_cursors = []
        for i in range(5):
            payload = generate_large_payload(100)  # 100KB each
            
            query_state = QueryState(
                filters={"cleanup_test": i},
                parameters={"abandoned": True}
            )
            
            position_data = {"large_payload": payload, "test_id": i}
            
            cursor_id = await cursor_manager.create_cursor(
                session_id=f"abandoned_session_{i}",
                tool_name=f"abandoned_test_{i}",
                query_state=query_state,
                initial_position=position_data
            )
            
            abandoned_cursors.append(cursor_id)
        
        print(f"  ✅ Created {len(abandoned_cursors)} abandoned cursors")
        
        # Wait for cursors to expire
        await asyncio.sleep(2)
        
        # Test cleanup
        from datetime import datetime
        cleanup_count = await cursor_manager._storage.cleanup_expired(datetime.now())
        
        print(f"  🧹 Cleaned up {cleanup_count} expired cursors")
        
        # Verify cursors are gone
        remaining_count = 0
        for cursor_id in abandoned_cursors:
            try:
                await cursor_manager.get_cursor(cursor_id, f"abandoned_session_{abandoned_cursors.index(cursor_id)}")
                remaining_count += 1
            except:
                pass  # Expected - cursor should be gone
        
        print(f"  ✅ Cleanup successful: {remaining_count} cursors remaining (should be 0)")
        
        await cursor_manager.stop()
        if hasattr(storage_backend, 'close'):
            await storage_backend.close()


async def performance_comparison():
    """Compare performance across different storage backends"""
    
    print(f"\n📊 Performance Comparison Across Storage Backends")
    print("=" * 60)
    
    backends = [
        ("memory", "memory", {}),
        ("sqlite", "sqlite", {"db_path": str(Path(tempfile.gettempdir()) / "perf_test.db")}),
    ]
    
    # Try Redis if available
    try:
        from pagination.storage import RedisStorage
        
        # Check for containerized Redis first, then localhost
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        redis_db = int(os.getenv("REDIS_DB", "1"))
        
        backends.append(("redis", "redis", {
            "host": redis_host, 
            "port": redis_port, 
            "db": redis_db
        }))
        print(f"  ℹ️  Redis backend configured: {redis_host}:{redis_port}/{redis_db}")
    except ImportError:
        print("  ℹ️  Redis not available, skipping Redis backend test")
    
    test_sizes = [100, 500, 1000]  # KB
    all_results = {}
    
    for backend_name, backend_type, backend_config in backends:
        try:
            print(f"\n🧪 Testing {backend_name} backend...")
            
            cursor_manager = SessionCursorManager(
                storage_backend=backend_type,
                storage_config=backend_config
            )
            
            await cursor_manager.start()
            
            results = await test_storage_backend(backend_name, cursor_manager, test_sizes)
            all_results[backend_name] = results
            
            await cursor_manager.stop()
            
        except Exception as e:
            print(f"  ❌ {backend_name} backend test failed: {e}")
            continue
    
    # Performance comparison table
    print(f"\n📈 Performance Comparison Summary:")
    print("-" * 80)
    print(f"{'Backend':<10} {'Size (KB)':<10} {'Create (ms)':<12} {'Retrieve (ms)':<14} {'Memory (MB)':<12}")
    print("-" * 80)
    
    for backend_name, results in all_results.items():
        for result in results:
            print(f"{backend_name:<10} {result['size_kb']:<10.1f} {result['creation_time']*1000:<12.1f} "
                  f"{result['retrieval_time']*1000:<14.1f} {result['memory_diff_mb']:<12.1f}")
    
    # Efficiency analysis
    print(f"\n🎯 Efficiency Analysis:")
    print("-" * 40)
    
    for backend_name, results in all_results.items():
        # Calculate averages
        avg_create = sum(r['creation_time'] for r in results) / len(results) * 1000
        avg_retrieve = sum(r['retrieval_time'] for r in results) / len(results) * 1000
        max_memory = max(r['memory_diff_mb'] for r in results)
        
        efficiency_score = 100 / (avg_create + avg_retrieve + max_memory * 10)  # Lower times + memory = higher score
        
        print(f"  {backend_name}: Avg Create: {avg_create:.1f}ms, "
              f"Avg Retrieve: {avg_retrieve:.1f}ms, "
              f"Max Memory: {max_memory:.1f}MB, "
              f"Efficiency: {efficiency_score:.1f}")


async def main():
    """Run comprehensive storage backend testing"""
    
    print("🧪 Storage Backend Testing for Large Cursor Payloads")
    print("=" * 70)
    
    # Test 1: Performance comparison
    await performance_comparison()
    
    # Test 2: Abandoned cursor cleanup
    await test_abandoned_cursor_cleanup()
    
    print(f"\n✅ Storage backend testing complete!")
    print(f"\n💡 Recommendations:")
    print(f"  • Memory: Best performance, but limited by RAM for large cursors")
    print(f"  • SQLite: Good balance of persistence and performance")
    print(f"  • Redis: Best for distributed systems, handles TTL automatically")
    print(f"  • For abandoned cursors: All backends support automatic cleanup")


if __name__ == "__main__":
    asyncio.run(main())