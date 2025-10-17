#!/usr/bin/env python3
"""
Memory Management Stress Test for Large Cursor Pagination

Tests cursor pagination system under memory pressure with resource limits.
Monitors memory usage, performance degradation, and cleanup efficiency.
"""

import sys
import os
import gc
import time
import json
import asyncio
import psutil
import resource
from typing import Dict, Any, List
from datetime import datetime, timedelta
sys.path.insert(0, 'src')

from pagination.cursor_manager import SessionCursorManager
from pagination.models import QueryState


def get_memory_usage() -> Dict[str, float]:
    """Get detailed memory usage information"""
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    
    try:
        # Get system memory info
        virtual_memory = psutil.virtual_memory()
        
        return {
            "process_rss_mb": memory_info.rss / (1024 * 1024),
            "process_vms_mb": memory_info.vms / (1024 * 1024),
            "system_available_mb": virtual_memory.available / (1024 * 1024),
            "system_used_percent": virtual_memory.percent,
            "system_total_mb": virtual_memory.total / (1024 * 1024)
        }
    except Exception:
        return {
            "process_rss_mb": memory_info.rss / (1024 * 1024),
            "process_vms_mb": memory_info.vms / (1024 * 1024),
            "system_available_mb": 0,
            "system_used_percent": 0,
            "system_total_mb": 0
        }


def set_memory_limit(limit_mb: int):
    """Set soft memory limit for the process"""
    try:
        limit_bytes = limit_mb * 1024 * 1024
        resource.setrlimit(resource.RLIMIT_AS, (limit_bytes, limit_bytes))
        print(f"💾 Memory limit set to {limit_mb}MB")
    except Exception as e:
        print(f"⚠️  Could not set memory limit: {e}")


def generate_stress_payload(size_kb: int, complexity: str = "high") -> Dict[str, Any]:
    """Generate varying complexity payloads for stress testing"""
    import random
    import string
    
    target_bytes = size_kb * 1024
    
    if complexity == "simple":
        # Simple payload: mostly text
        return {
            "type": "simple",
            "data": ''.join(random.choices(string.ascii_letters + string.digits, k=target_bytes))
        }
    
    elif complexity == "medium":
        # Medium payload: structured data
        return {
            "type": "medium",
            "metadata": {"created": datetime.now().isoformat(), "complexity": complexity},
            "text_data": ''.join(random.choices(string.ascii_letters, k=target_bytes // 2)),
            "structured_data": [
                {"id": i, "value": f"item_{i}", "tags": [f"tag_{j}" for j in range(5)]}
                for i in range(target_bytes // 400)
            ]
        }
    
    else:  # high complexity
        # High complexity: deeply nested structures
        return {
            "type": "high_complexity",
            "metadata": {
                "created": datetime.now().isoformat(),
                "complexity": complexity,
                "nested_config": {
                    "level_1": {
                        "level_2": {
                            "level_3": {
                                "settings": {f"setting_{i}": f"value_{i}" for i in range(20)},
                                "data": ''.join(random.choices(string.ascii_letters, k=target_bytes // 4))
                            }
                        }
                    }
                }
            },
            "large_arrays": [
                {
                    "array_id": i,
                    "nested_data": {
                        "coordinates": [random.random() for _ in range(10)],
                        "properties": {f"prop_{j}": random.randint(1, 1000) for j in range(10)},
                        "text": ''.join(random.choices(string.ascii_letters, k=100))
                    }
                }
                for i in range(target_bytes // 800)
            ],
            "binary_simulation": [random.randint(0, 255) for _ in range(target_bytes // 4)]
        }


class MemoryStressTest:
    """Stress test memory management with resource monitoring"""
    
    def __init__(self, storage_backend: str = "memory", memory_limit_mb: int = 512):
        self.storage_backend = storage_backend
        self.memory_limit_mb = memory_limit_mb
        self.cursor_manager = None
        self.created_cursors = []
        self.test_sessions = []
        self.memory_snapshots = []
        
    async def setup(self):
        """Setup stress test environment"""
        print(f"🔧 Setting up stress test environment...")
        print(f"   💾 Memory limit: {self.memory_limit_mb}MB")
        print(f"   🗄️  Storage backend: {self.storage_backend}")
        
        # Set memory limit for safety
        set_memory_limit(self.memory_limit_mb)
        
        # Configure storage backend
        storage_config = {}
        if self.storage_backend == "redis":
            storage_config = {
                "host": os.getenv("REDIS_HOST", "localhost"),
                "port": int(os.getenv("REDIS_PORT", "6379")),
                "db": int(os.getenv("REDIS_DB", "2")),  # Use separate DB for stress test
            }
        
        # Initialize cursor manager
        self.cursor_manager = SessionCursorManager(
            storage_backend=self.storage_backend,
            storage_config=storage_config,
            default_expiry_hours=1,  # Short expiry for stress test
            cleanup_interval_minutes=1,  # Frequent cleanup
            max_cursors_per_session=50  # Reasonable limit per session
        )
        
        await self.cursor_manager.start()
        
        # Take initial memory snapshot
        initial_memory = get_memory_usage()
        self.memory_snapshots.append({
            "timestamp": datetime.now(),
            "phase": "initial",
            "cursors_created": 0,
            **initial_memory
        })
        
        print(f"   📊 Initial memory: {initial_memory['process_rss_mb']:.1f}MB")
        
    async def create_cursor_batch(self, batch_size: int, cursor_size_kb: int, complexity: str = "medium") -> List[str]:
        """Create a batch of cursors and return their IDs"""
        batch_cursors = []
        
        # Use a single session for the entire batch to test session limits
        session_id = "stress_test_session"
        if session_id not in self.test_sessions:
            self.test_sessions.append(session_id)
        
        for i in range(batch_size):
            try:
                
                # Generate payload
                payload = generate_stress_payload(cursor_size_kb, complexity)
                
                # Create query state
                query_state = QueryState(
                    filters={"stress_test": True, "batch": len(self.created_cursors) // batch_size},
                    parameters={"complexity": complexity, "size_kb": cursor_size_kb}
                )
                
                # Create position data
                position_data = {
                    "index": i,
                    "batch_id": len(self.created_cursors) // batch_size,
                    "large_payload": payload,
                    "stress_test_metadata": {
                        "created_at": datetime.now().isoformat(),
                        "complexity": complexity,
                        "size_kb": cursor_size_kb
                    }
                }
                
                # Create cursor
                cursor_id = await self.cursor_manager.create_cursor(
                    session_id=session_id,
                    tool_name=f"stress_test_{complexity}_{cursor_size_kb}kb",
                    query_state=query_state,
                    initial_position=position_data
                )
                
                batch_cursors.append(cursor_id)
                self.created_cursors.append(cursor_id)
                
                # Session already tracked above
                
            except Exception as e:
                print(f"   ⚠️  Failed to create cursor {i}: {e}")
                break
        
        return batch_cursors
    
    async def test_memory_scaling(self) -> Dict[str, Any]:
        """Test memory usage as cursor count scales"""
        print(f"\n🔬 Memory Scaling Test...")
        
        test_phases = [
            {"batch_size": 5, "cursor_size_kb": 100, "complexity": "simple"},
            {"batch_size": 10, "cursor_size_kb": 100, "complexity": "medium"},
            {"batch_size": 20, "cursor_size_kb": 250, "complexity": "medium"},
            {"batch_size": 15, "cursor_size_kb": 500, "complexity": "high"},
            {"batch_size": 10, "cursor_size_kb": 1000, "complexity": "high"},
        ]
        
        for phase_idx, phase in enumerate(test_phases):
            print(f"\n  📋 Phase {phase_idx + 1}: {phase['batch_size']} cursors @ {phase['cursor_size_kb']}KB ({phase['complexity']})")
            
            # Create batch
            start_time = time.time()
            batch_cursors = await self.create_cursor_batch(
                phase["batch_size"],
                phase["cursor_size_kb"],
                phase["complexity"]
            )
            creation_time = time.time() - start_time
            
            # Take memory snapshot
            memory_info = get_memory_usage()
            self.memory_snapshots.append({
                "timestamp": datetime.now(),
                "phase": f"phase_{phase_idx + 1}",
                "cursors_created": len(self.created_cursors),
                "batch_size": len(batch_cursors),
                "cursor_size_kb": phase["cursor_size_kb"],
                "complexity": phase["complexity"],
                "creation_time": creation_time,
                **memory_info
            })
            
            print(f"     ✅ Created {len(batch_cursors)} cursors in {creation_time:.2f}s")
            print(f"     💾 Memory: {memory_info['process_rss_mb']:.1f}MB (Δ: {memory_info['process_rss_mb'] - self.memory_snapshots[0]['process_rss_mb']:+.1f}MB)")
            
            # Safety check: stop if memory usage is too high
            if memory_info['process_rss_mb'] > self.memory_limit_mb * 0.8:
                print(f"     ⚠️  Approaching memory limit ({memory_info['process_rss_mb']:.1f}MB), stopping phase creation")
                break
                
            # Brief pause between phases
            await asyncio.sleep(0.5)
        
        return {
            "total_cursors_created": len(self.created_cursors),
            "final_memory_mb": memory_info['process_rss_mb'],
            "memory_growth_mb": memory_info['process_rss_mb'] - self.memory_snapshots[0]['process_rss_mb']
        }
    
    async def test_cursor_retrieval_performance(self) -> Dict[str, Any]:
        """Test cursor retrieval performance under memory pressure"""
        print(f"\n🚀 Retrieval Performance Test...")
        
        if not self.created_cursors:
            print("     ⚠️  No cursors available for retrieval test")
            return {}
        
        # Sample cursors for testing
        test_cursor_count = min(20, len(self.created_cursors))
        test_cursors = self.created_cursors[-test_cursor_count:]  # Use most recent cursors
        
        retrieval_times = []
        memory_before = get_memory_usage()['process_rss_mb']
        
        for i, cursor_id in enumerate(test_cursors):
            try:
                session_id = "stress_test_session"  # Use the same session as creation
                
                start_time = time.time()
                cursor = await self.cursor_manager.get_cursor(cursor_id, session_id)
                retrieval_time = time.time() - start_time
                
                retrieval_times.append(retrieval_time)
                
                # Verify data integrity
                payload = cursor.position.get("large_payload", {})
                if not payload:
                    print(f"     ⚠️  Empty payload in cursor {cursor_id}")
                
            except Exception as e:
                print(f"     ❌ Failed to retrieve cursor {cursor_id}: {e}")
        
        memory_after = get_memory_usage()['process_rss_mb']
        
        if retrieval_times:
            avg_retrieval_time = sum(retrieval_times) / len(retrieval_times)
            max_retrieval_time = max(retrieval_times)
            print(f"     ✅ Retrieved {len(retrieval_times)} cursors")
            print(f"     ⏱️  Avg retrieval: {avg_retrieval_time*1000:.1f}ms, Max: {max_retrieval_time*1000:.1f}ms")
            print(f"     💾 Memory impact: {memory_after - memory_before:+.1f}MB")
            
            return {
                "cursors_tested": len(retrieval_times),
                "avg_retrieval_time_ms": avg_retrieval_time * 1000,
                "max_retrieval_time_ms": max_retrieval_time * 1000,
                "memory_impact_mb": memory_after - memory_before
            }
        
        return {}
    
    async def test_cleanup_efficiency(self) -> Dict[str, Any]:
        """Test automatic cleanup and memory recovery"""
        print(f"\n🧹 Cleanup Efficiency Test...")
        
        memory_before_cleanup = get_memory_usage()['process_rss_mb']
        
        # Trigger cleanup manually (simulates expired cursors)
        print(f"     🔄 Triggering manual cleanup...")
        cleanup_count = await self.cursor_manager._cleanup_expired_cursors()
        
        # Force garbage collection
        print(f"     🗑️  Running garbage collection...")
        gc.collect()
        
        await asyncio.sleep(1)  # Allow cleanup to complete
        
        memory_after_cleanup = get_memory_usage()['process_rss_mb']
        memory_recovered = memory_before_cleanup - memory_after_cleanup
        
        print(f"     ✅ Cleaned up {cleanup_count} cursors")
        print(f"     💾 Memory before: {memory_before_cleanup:.1f}MB, after: {memory_after_cleanup:.1f}MB")
        print(f"     ♻️  Memory recovered: {memory_recovered:.1f}MB")
        
        return {
            "cursors_cleaned": cleanup_count,
            "memory_before_mb": memory_before_cleanup,
            "memory_after_mb": memory_after_cleanup,
            "memory_recovered_mb": memory_recovered
        }
    
    async def run_stress_test(self) -> Dict[str, Any]:
        """Run complete stress test suite"""
        print(f"🧪 Memory Management Stress Test")
        print(f"=" * 60)
        
        try:
            # Setup
            await self.setup()
            
            # Run test phases
            scaling_results = await self.test_memory_scaling()
            retrieval_results = await self.test_cursor_retrieval_performance()
            cleanup_results = await self.test_cleanup_efficiency()
            
            # Final memory analysis
            final_memory = get_memory_usage()
            
            results = {
                "storage_backend": self.storage_backend,
                "memory_limit_mb": self.memory_limit_mb,
                "scaling_test": scaling_results,
                "retrieval_test": retrieval_results,
                "cleanup_test": cleanup_results,
                "final_memory": final_memory,
                "memory_snapshots": self.memory_snapshots,
                "total_test_time": (datetime.now() - self.memory_snapshots[0]["timestamp"]).total_seconds()
            }
            
            return results
            
        finally:
            # Cleanup
            if self.cursor_manager:
                await self.cursor_manager.stop()


async def run_containerized_stress_test():
    """Run stress test in various configurations"""
    
    # Test configurations
    test_configs = [
        {"backend": "memory", "limit_mb": 256, "name": "Memory Backend (256MB limit)"},
        {"backend": "redis", "limit_mb": 512, "name": "Redis Backend (512MB limit)"},
    ]
    
    all_results = {}
    
    for config in test_configs:
        print(f"\n{'=' * 80}")
        print(f"🔬 {config['name']}")
        print(f"{'=' * 80}")
        
        try:
            # Create stress test instance
            stress_test = MemoryStressTest(
                storage_backend=config["backend"],
                memory_limit_mb=config["limit_mb"]
            )
            
            # Run test
            results = await stress_test.run_stress_test()
            all_results[config["backend"]] = results
            
            # Summary
            print(f"\n📊 {config['name']} Results:")
            print(f"   💾 Total cursors created: {results['scaling_test'].get('total_cursors_created', 0)}")
            print(f"   🧠 Final memory usage: {results['final_memory']['process_rss_mb']:.1f}MB")
            print(f"   📈 Memory growth: {results['scaling_test'].get('memory_growth_mb', 0):.1f}MB")
            print(f"   ⏱️  Test duration: {results['total_test_time']:.1f}s")
            
            if results['cleanup_test']:
                print(f"   ♻️  Memory recovered: {results['cleanup_test']['memory_recovered_mb']:.1f}MB")
        
        except Exception as e:
            print(f"   ❌ Stress test failed: {e}")
            all_results[config["backend"]] = {"error": str(e)}
    
    return all_results


if __name__ == "__main__":
    # Check if Redis is available
    storage_backend = os.getenv("STORAGE_BACKEND", "memory")
    
    if storage_backend == "redis":
        print("🔄 Testing with Redis backend...")
    else:
        print("🔄 Testing with Memory backend...")
    
    results = asyncio.run(run_containerized_stress_test())
    
    print(f"\n🎯 Stress Test Complete!")
    print(f"=" * 60)
    
    # Generate efficiency recommendations
    for backend, result in results.items():
        if "error" not in result:
            scaling = result["scaling_test"]
            memory_per_cursor = scaling["memory_growth_mb"] / max(scaling["total_cursors_created"], 1)
            
            print(f"\n{backend.upper()} Backend Efficiency:")
            print(f"  📊 Memory per cursor: {memory_per_cursor:.1f}MB")
            print(f"  🎯 Recommended max cursors (500MB): {int(500 / memory_per_cursor)}")
            print(f"  ⚡ Performance rating: {'🟢 EXCELLENT' if memory_per_cursor < 2 else '🟡 GOOD' if memory_per_cursor < 5 else '🔴 HIGH OVERHEAD'}")