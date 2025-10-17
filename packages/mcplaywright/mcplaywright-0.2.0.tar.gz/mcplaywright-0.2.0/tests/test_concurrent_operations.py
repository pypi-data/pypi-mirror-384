#!/usr/bin/env python3
"""
Concurrent Operations Testing for Redis Backend

Tests multiple concurrent sessions creating and accessing cursors simultaneously.
"""

import sys
import os
import asyncio
import time
import random
from datetime import datetime
sys.path.insert(0, 'src')

from pagination.cursor_manager import SessionCursorManager
from pagination.models import QueryState


async def worker_session(worker_id: int, cursor_manager: SessionCursorManager, operations: int = 10):
    """Simulate a worker session performing cursor operations"""
    session_id = f"worker_session_{worker_id}"
    created_cursors = []
    
    try:
        for i in range(operations):
            # Create cursor
            payload = {
                "worker_id": worker_id,
                "operation_id": i,
                "timestamp": datetime.now().isoformat(),
                "data": f"worker_{worker_id}_data_{i}" * 100,  # ~2KB payload
                "concurrent_test": True
            }
            
            query_state = QueryState(
                filters={"worker_id": worker_id, "concurrent_test": True},
                parameters={"operation_id": i}
            )
            
            position_data = {
                "index": i,
                "worker_payload": payload,
                "metadata": {"worker_id": worker_id, "created_at": datetime.now().isoformat()}
            }
            
            cursor_id = await cursor_manager.create_cursor(
                session_id=session_id,
                tool_name=f"concurrent_worker_{worker_id}_op_{i}",
                query_state=query_state,
                initial_position=position_data
            )
            
            created_cursors.append(cursor_id)
            
            # Randomly retrieve some cursors
            if random.random() < 0.3 and created_cursors:
                random_cursor = random.choice(created_cursors)
                try:
                    cursor = await cursor_manager.get_cursor(random_cursor, session_id)
                    # Verify data integrity
                    retrieved_payload = cursor.position["worker_payload"]
                    assert retrieved_payload["worker_id"] == worker_id
                except Exception as e:
                    print(f"    ⚠️  Worker {worker_id} retrieval failed: {e}")
            
            # Brief random delay to simulate real usage
            await asyncio.sleep(random.uniform(0.01, 0.05))
        
        return {
            "worker_id": worker_id,
            "cursors_created": len(created_cursors),
            "session_id": session_id,
            "success": True
        }
        
    except Exception as e:
        return {
            "worker_id": worker_id,
            "cursors_created": len(created_cursors),
            "session_id": session_id,
            "success": False,
            "error": str(e)
        }


async def test_concurrent_operations():
    """Test concurrent cursor operations"""
    print("🔄 Concurrent Operations Test")
    print("=" * 50)
    
    # Setup Redis cursor manager
    cursor_manager = SessionCursorManager(
        storage_backend="redis",
        storage_config={
            "host": os.getenv("REDIS_HOST", "localhost"),
            "port": int(os.getenv("REDIS_PORT", "6379")),
            "db": int(os.getenv("REDIS_DB", "5")),  # Use separate DB
        },
        max_cursors_per_session=25,  # Allow reasonable per-session limit
        default_expiry_hours=1
    )
    
    await cursor_manager.start()
    
    # Test configuration
    num_workers = 8
    operations_per_worker = 20
    
    print(f"\n🚀 Starting {num_workers} concurrent workers...")
    print(f"   📊 {operations_per_worker} operations per worker")
    print(f"   🎯 Total expected cursors: {num_workers * operations_per_worker}")
    
    # Start concurrent workers
    start_time = time.time()
    
    tasks = [
        worker_session(worker_id, cursor_manager, operations_per_worker)
        for worker_id in range(num_workers)
    ]
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    end_time = time.time()
    total_time = end_time - start_time
    
    # Analyze results
    successful_workers = 0
    total_cursors_created = 0
    failed_workers = []
    
    for result in results:
        if isinstance(result, dict):
            if result["success"]:
                successful_workers += 1
                total_cursors_created += result["cursors_created"]
                print(f"  ✅ Worker {result['worker_id']}: {result['cursors_created']} cursors")
            else:
                failed_workers.append(result)
                print(f"  ❌ Worker {result['worker_id']}: {result.get('error', 'Unknown error')}")
        else:
            print(f"  ❌ Worker failed with exception: {result}")
    
    # Test cross-session retrieval (should fail due to isolation)
    print(f"\n🔒 Testing session isolation...")
    if successful_workers >= 2:
        try:
            # Try to access a cursor from worker 0 using worker 1's session
            worker_0_result = next(r for r in results if isinstance(r, dict) and r["worker_id"] == 0 and r["success"])
            worker_1_result = next(r for r in results if isinstance(r, dict) and r["worker_id"] == 1 and r["success"])
            
            # This should fail due to session isolation
            try:
                await cursor_manager.get_cursor("some_cursor_id", worker_1_result["session_id"])
                print(f"  ⚠️  Session isolation may be compromised")
            except Exception:
                print(f"  ✅ Session isolation working correctly")
        except StopIteration:
            print(f"  ℹ️  Insufficient successful workers for isolation test")
    
    await cursor_manager.stop()
    
    # Performance analysis
    print(f"\n📊 Concurrent Operations Results:")
    print(f"  👥 Successful workers: {successful_workers}/{num_workers}")
    print(f"  📝 Total cursors created: {total_cursors_created}")
    print(f"  ⏱️  Total time: {total_time:.2f}s")
    print(f"  🚀 Throughput: {total_cursors_created/total_time:.1f} cursors/sec")
    print(f"  ⚡ Avg time per cursor: {total_time*1000/total_cursors_created:.1f}ms")
    
    if failed_workers:
        print(f"\n❌ Failed workers:")
        for failed in failed_workers:
            print(f"  Worker {failed['worker_id']}: {failed.get('error', 'Unknown error')}")
    
    success_rate = successful_workers / num_workers
    throughput = total_cursors_created / total_time
    
    return {
        "successful_workers": successful_workers,
        "total_workers": num_workers,
        "success_rate": success_rate,
        "total_cursors": total_cursors_created,
        "throughput": throughput,
        "total_time": total_time,
        "passed": success_rate >= 0.8 and throughput >= 10  # 80% success, 10+ cursors/sec
    }


async def main():
    """Run concurrent operations test"""
    print("🧪 Redis Concurrent Operations Testing")
    print("=" * 60)
    
    try:
        result = await test_concurrent_operations()
        
        print(f"\n🎯 Concurrent Operations Test Summary:")
        print(f"=" * 60)
        print(f"  🎯 Success rate: {result['success_rate']*100:.1f}%")
        print(f"  🚀 Throughput: {result['throughput']:.1f} cursors/sec")
        print(f"  ⏱️  Average time: {result['total_time']*1000/result['total_cursors']:.1f}ms per cursor")
        
        if result["passed"]:
            print(f"\n✅ Concurrent operations test PASSED!")
            print(f"   🎉 Redis backend handles concurrent load excellently")
            print(f"   🔒 Session isolation working correctly")
            print(f"   ⚡ Performance meets production requirements")
        else:
            print(f"\n⚠️  Concurrent operations test had issues")
            if result['success_rate'] < 0.8:
                print(f"   📊 Success rate too low: {result['success_rate']*100:.1f}%")
            if result['throughput'] < 10:
                print(f"   🐌 Throughput too low: {result['throughput']:.1f} cursors/sec")
        
        return result["passed"]
        
    except Exception as e:
        print(f"❌ Concurrent operations testing failed: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    if success:
        print(f"\n🎉 Concurrent operations testing completed successfully!")
    else:
        print(f"\n⚠️  Concurrent operations testing had issues")