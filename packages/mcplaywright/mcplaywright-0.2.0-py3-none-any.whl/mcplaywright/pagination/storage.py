"""
Pluggable Storage Backends for Cursor Persistence

Provides multiple storage options for cursor data with automatic cleanup
of abandoned cursors and efficient memory management.
"""

import json
import time
import sqlite3
import tempfile
import threading
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from pathlib import Path
import logging

from .models import CursorState

logger = logging.getLogger(__name__)


class StorageBackend(ABC):
    """Abstract base class for cursor storage backends"""
    
    @abstractmethod
    async def store_cursor(self, cursor_id: str, cursor_state: CursorState) -> bool:
        """Store cursor state"""
        pass
    
    @abstractmethod
    async def retrieve_cursor(self, cursor_id: str) -> Optional[CursorState]:
        """Retrieve cursor state"""
        pass
    
    @abstractmethod
    async def delete_cursor(self, cursor_id: str) -> bool:
        """Delete cursor state"""
        pass
    
    @abstractmethod
    async def cleanup_expired(self, older_than: datetime) -> int:
        """Remove expired cursors, return count removed"""
        pass
    
    @abstractmethod
    async def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage backend statistics"""
        pass
    
    @abstractmethod
    async def close(self):
        """Close storage backend and cleanup resources"""
        pass


class InMemoryStorage(StorageBackend):
    """In-memory storage backend (current implementation)"""
    
    def __init__(self):
        self._cursors: Dict[str, CursorState] = {}
        self._lock = threading.RLock()
    
    async def store_cursor(self, cursor_id: str, cursor_state: CursorState) -> bool:
        """Store cursor in memory"""
        try:
            with self._lock:
                self._cursors[cursor_id] = cursor_state
            return True
        except Exception as e:
            logger.error(f"Failed to store cursor {cursor_id}: {e}")
            return False
    
    async def retrieve_cursor(self, cursor_id: str) -> Optional[CursorState]:
        """Retrieve cursor from memory"""
        with self._lock:
            return self._cursors.get(cursor_id)
    
    async def delete_cursor(self, cursor_id: str) -> bool:
        """Delete cursor from memory"""
        try:
            with self._lock:
                if cursor_id in self._cursors:
                    del self._cursors[cursor_id]
                    return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete cursor {cursor_id}: {e}")
            return False
    
    async def cleanup_expired(self, older_than: datetime) -> int:
        """Remove expired cursors from memory"""
        removed_count = 0
        
        with self._lock:
            expired_ids = [
                cursor_id for cursor_id, cursor_state in self._cursors.items()
                if cursor_state.expires_at < older_than
            ]
            
            for cursor_id in expired_ids:
                del self._cursors[cursor_id]
                removed_count += 1
        
        return removed_count
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """Get memory storage statistics"""
        with self._lock:
            cursor_count = len(self._cursors)
            
            # Estimate memory usage
            import sys
            total_size = sum(sys.getsizeof(cursor) for cursor in self._cursors.values())
            
            return {
                "backend_type": "in_memory",
                "cursor_count": cursor_count,
                "estimated_memory_bytes": total_size,
                "estimated_memory_mb": total_size / (1024 * 1024)
            }
    
    async def close(self):
        """Close in-memory storage"""
        with self._lock:
            self._cursors.clear()


class SQLiteStorage(StorageBackend):
    """SQLite-based cursor storage with automatic cleanup"""
    
    def __init__(self, db_path: Optional[str] = None, cleanup_interval_minutes: int = 30):
        self.db_path = db_path or str(Path(tempfile.gettempdir()) / "mcplaywright_cursors.db")
        self.cleanup_interval_minutes = cleanup_interval_minutes
        self._connection: Optional[sqlite3.Connection] = None
        self._lock = threading.RLock()
        
    async def _ensure_connection(self):
        """Ensure database connection is established"""
        if self._connection is None:
            with self._lock:
                if self._connection is None:
                    self._connection = sqlite3.connect(
                        self.db_path,
                        check_same_thread=False,
                        timeout=30.0
                    )
                    
                    # Enable WAL mode for better concurrent access
                    self._connection.execute("PRAGMA journal_mode=WAL")
                    self._connection.execute("PRAGMA synchronous=NORMAL")
                    
                    # Create cursors table
                    self._connection.execute("""
                        CREATE TABLE IF NOT EXISTS cursors (
                            cursor_id TEXT PRIMARY KEY,
                            session_id TEXT NOT NULL,
                            tool_name TEXT NOT NULL,
                            cursor_data TEXT NOT NULL,
                            created_at REAL NOT NULL,
                            expires_at REAL NOT NULL,
                            last_accessed REAL NOT NULL,
                            data_size_bytes INTEGER NOT NULL
                        )
                    """)
                    
                    # Create indexes separately
                    self._connection.execute("CREATE INDEX IF NOT EXISTS idx_session_id ON cursors(session_id)")
                    self._connection.execute("CREATE INDEX IF NOT EXISTS idx_expires_at ON cursors(expires_at)")
                    self._connection.execute("CREATE INDEX IF NOT EXISTS idx_last_accessed ON cursors(last_accessed)")
                    
                    self._connection.commit()
    
    def _serialize_cursor(self, cursor_state: CursorState) -> str:
        """Serialize cursor state to JSON"""
        cursor_dict = {
            "id": cursor_state.id,
            "session_id": cursor_state.session_id,
            "tool_name": cursor_state.tool_name,
            "query_state": cursor_state.query_state,
            "position": cursor_state.position,
            "created_at": cursor_state.created_at.timestamp(),
            "last_accessed": cursor_state.last_accessed.timestamp(),
            "expires_at": cursor_state.expires_at.timestamp(),
            "direction": cursor_state.direction,
            "chunk_size_history": cursor_state.chunk_size_history,
            "performance_metrics": cursor_state.performance_metrics,
            "cached_positions": cursor_state.cached_positions,
            "result_count": cursor_state.result_count,
            "metadata": cursor_state.metadata
        }
        return json.dumps(cursor_dict, default=str)
    
    def _deserialize_cursor(self, cursor_data: str) -> CursorState:
        """Deserialize cursor state from JSON"""
        cursor_dict = json.loads(cursor_data)
        
        cursor_state = CursorState(
            id=cursor_dict["id"],
            session_id=cursor_dict["session_id"],
            tool_name=cursor_dict["tool_name"],
            query_state=cursor_dict["query_state"],
            position=cursor_dict["position"],
            created_at=datetime.fromtimestamp(cursor_dict["created_at"]),
            last_accessed=datetime.fromtimestamp(cursor_dict["last_accessed"]),
            expires_at=datetime.fromtimestamp(cursor_dict["expires_at"]),
            direction=cursor_dict.get("direction", "forward"),
            chunk_size_history=cursor_dict.get("chunk_size_history", []),
            performance_metrics=cursor_dict.get("performance_metrics", {}),
            cached_positions=cursor_dict.get("cached_positions", {}),
            result_count=cursor_dict.get("result_count", 0),
            metadata=cursor_dict.get("metadata", {})
        )
        
        return cursor_state
    
    async def store_cursor(self, cursor_id: str, cursor_state: CursorState) -> bool:
        """Store cursor in SQLite"""
        try:
            await self._ensure_connection()
            
            cursor_data = self._serialize_cursor(cursor_state)
            data_size = len(cursor_data.encode('utf-8'))
            
            with self._lock:
                self._connection.execute("""
                    INSERT OR REPLACE INTO cursors 
                    (cursor_id, session_id, tool_name, cursor_data, created_at, 
                     expires_at, last_accessed, data_size_bytes)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    cursor_id,
                    cursor_state.session_id,
                    cursor_state.tool_name,
                    cursor_data,
                    cursor_state.created_at.timestamp(),
                    cursor_state.expires_at.timestamp(),
                    cursor_state.last_accessed.timestamp(),
                    data_size
                ))
                
                self._connection.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to store cursor {cursor_id} in SQLite: {e}")
            return False
    
    async def retrieve_cursor(self, cursor_id: str) -> Optional[CursorState]:
        """Retrieve cursor from SQLite"""
        try:
            await self._ensure_connection()
            
            with self._lock:
                cursor = self._connection.execute(
                    "SELECT cursor_data FROM cursors WHERE cursor_id = ?",
                    (cursor_id,)
                ).fetchone()
                
                if cursor:
                    cursor_state = self._deserialize_cursor(cursor[0])
                    
                    # Update last accessed time
                    now = datetime.now()
                    cursor_state.last_accessed = now
                    
                    self._connection.execute(
                        "UPDATE cursors SET last_accessed = ? WHERE cursor_id = ?",
                        (now.timestamp(), cursor_id)
                    )
                    self._connection.commit()
                    
                    return cursor_state
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to retrieve cursor {cursor_id} from SQLite: {e}")
            return None
    
    async def delete_cursor(self, cursor_id: str) -> bool:
        """Delete cursor from SQLite"""
        try:
            await self._ensure_connection()
            
            with self._lock:
                cursor = self._connection.execute(
                    "DELETE FROM cursors WHERE cursor_id = ?",
                    (cursor_id,)
                )
                self._connection.commit()
                
                return cursor.rowcount > 0
                
        except Exception as e:
            logger.error(f"Failed to delete cursor {cursor_id} from SQLite: {e}")
            return False
    
    async def cleanup_expired(self, older_than: datetime) -> int:
        """Remove expired cursors from SQLite"""
        try:
            await self._ensure_connection()
            
            with self._lock:
                cursor = self._connection.execute(
                    "DELETE FROM cursors WHERE expires_at < ?",
                    (older_than.timestamp(),)
                )
                self._connection.commit()
                
                return cursor.rowcount
                
        except Exception as e:
            logger.error(f"Failed to cleanup expired cursors from SQLite: {e}")
            return 0
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """Get SQLite storage statistics"""
        try:
            await self._ensure_connection()
            
            with self._lock:
                # Get cursor count and total data size
                stats = self._connection.execute("""
                    SELECT 
                        COUNT(*) as cursor_count,
                        SUM(data_size_bytes) as total_data_bytes,
                        AVG(data_size_bytes) as avg_cursor_size,
                        MIN(created_at) as oldest_cursor,
                        MAX(last_accessed) as most_recent_access
                    FROM cursors
                """).fetchone()
                
                # Get database file size
                db_path = Path(self.db_path)
                file_size_bytes = db_path.stat().st_size if db_path.exists() else 0
                
                return {
                    "backend_type": "sqlite",
                    "db_path": self.db_path,
                    "cursor_count": stats[0] or 0,
                    "total_data_bytes": stats[1] or 0,
                    "total_data_mb": (stats[1] or 0) / (1024 * 1024),
                    "avg_cursor_size_bytes": stats[2] or 0,
                    "avg_cursor_size_kb": (stats[2] or 0) / 1024,
                    "db_file_size_bytes": file_size_bytes,
                    "db_file_size_mb": file_size_bytes / (1024 * 1024),
                    "oldest_cursor": datetime.fromtimestamp(stats[3]) if stats[3] else None,
                    "most_recent_access": datetime.fromtimestamp(stats[4]) if stats[4] else None
                }
                
        except Exception as e:
            logger.error(f"Failed to get SQLite storage stats: {e}")
            return {"backend_type": "sqlite", "error": str(e)}
    
    async def close(self):
        """Close SQLite connection"""
        with self._lock:
            if self._connection:
                self._connection.close()
                self._connection = None


class RedisStorage(StorageBackend):
    """Redis-based cursor storage with TTL support"""
    
    def __init__(self, 
                 host: str = "localhost", 
                 port: int = 6379, 
                 db: int = 0,
                 password: Optional[str] = None,
                 key_prefix: str = "mcplaywright:cursor:",
                 default_ttl_hours: int = 24):
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.key_prefix = key_prefix
        self.default_ttl_seconds = default_ttl_hours * 3600
        self._redis = None
        
    async def _ensure_connection(self):
        """Ensure Redis connection is established"""
        if self._redis is None:
            try:
                import redis.asyncio as redis
                
                self._redis = redis.Redis(
                    host=self.host,
                    port=self.port,
                    db=self.db,
                    password=self.password,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                
                # Test connection
                await self._redis.ping()
                
            except ImportError:
                raise ImportError("redis package required for Redis storage. Install with: pip install redis")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                self._redis = None
                raise
    
    def _get_key(self, cursor_id: str) -> str:
        """Get Redis key for cursor"""
        return f"{self.key_prefix}{cursor_id}"
    
    async def store_cursor(self, cursor_id: str, cursor_state: CursorState) -> bool:
        """Store cursor in Redis with TTL"""
        try:
            await self._ensure_connection()
            
            # Serialize cursor state
            cursor_data = {
                "id": cursor_state.id,
                "session_id": cursor_state.session_id,
                "tool_name": cursor_state.tool_name,
                "query_state": json.dumps(cursor_state.query_state, default=str),
                "position": json.dumps(cursor_state.position, default=str),
                "created_at": cursor_state.created_at.timestamp(),
                "last_accessed": cursor_state.last_accessed.timestamp(),
                "expires_at": cursor_state.expires_at.timestamp(),
                "direction": cursor_state.direction,
                "chunk_size_history": json.dumps(cursor_state.chunk_size_history),
                "performance_metrics": json.dumps(cursor_state.performance_metrics),
                "cached_positions": json.dumps(cursor_state.cached_positions),
                "result_count": cursor_state.result_count,
                "metadata": json.dumps(cursor_state.metadata, default=str)
            }
            
            # Calculate TTL based on expiration time
            ttl_seconds = max(1, int((cursor_state.expires_at - datetime.now()).total_seconds()))
            
            # Store with TTL
            key = self._get_key(cursor_id)
            await self._redis.hset(key, mapping=cursor_data)
            await self._redis.expire(key, ttl_seconds)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to store cursor {cursor_id} in Redis: {e}")
            return False
    
    async def retrieve_cursor(self, cursor_id: str) -> Optional[CursorState]:
        """Retrieve cursor from Redis"""
        try:
            await self._ensure_connection()
            
            key = self._get_key(cursor_id)
            cursor_data = await self._redis.hgetall(key)
            
            if not cursor_data:
                return None
            
            # Deserialize cursor state
            cursor_state = CursorState(
                id=cursor_data["id"],
                session_id=cursor_data["session_id"],
                tool_name=cursor_data["tool_name"],
                query_state=json.loads(cursor_data["query_state"]),
                position=json.loads(cursor_data["position"]),
                created_at=datetime.fromtimestamp(float(cursor_data["created_at"])),
                last_accessed=datetime.fromtimestamp(float(cursor_data["last_accessed"])),
                expires_at=datetime.fromtimestamp(float(cursor_data["expires_at"])),
                direction=cursor_data.get("direction", "forward"),
                chunk_size_history=json.loads(cursor_data.get("chunk_size_history", "[]")),
                performance_metrics=json.loads(cursor_data.get("performance_metrics", "{}")),
                cached_positions=json.loads(cursor_data.get("cached_positions", "{}")),
                result_count=int(cursor_data.get("result_count", 0)),
                metadata=json.loads(cursor_data.get("metadata", "{}"))
            )
            
            # Update last accessed time
            now = datetime.now()
            cursor_state.last_accessed = now
            await self._redis.hset(key, "last_accessed", now.timestamp())
            
            return cursor_state
            
        except Exception as e:
            logger.error(f"Failed to retrieve cursor {cursor_id} from Redis: {e}")
            return None
    
    async def delete_cursor(self, cursor_id: str) -> bool:
        """Delete cursor from Redis"""
        try:
            await self._ensure_connection()
            
            key = self._get_key(cursor_id)
            deleted_count = await self._redis.delete(key)
            
            return deleted_count > 0
            
        except Exception as e:
            logger.error(f"Failed to delete cursor {cursor_id} from Redis: {e}")
            return False
    
    async def cleanup_expired(self, older_than: datetime) -> int:
        """Redis automatically expires keys with TTL, return 0"""
        # Redis handles TTL automatically, but we can check for any lingering keys
        try:
            await self._ensure_connection()
            
            pattern = f"{self.key_prefix}*"
            keys = await self._redis.keys(pattern)
            
            expired_count = 0
            for key in keys:
                cursor_data = await self._redis.hgetall(key)
                if cursor_data and "expires_at" in cursor_data:
                    expires_at = datetime.fromtimestamp(float(cursor_data["expires_at"]))
                    if expires_at < older_than:
                        await self._redis.delete(key)
                        expired_count += 1
            
            return expired_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired cursors from Redis: {e}")
            return 0
    
    async def get_storage_stats(self) -> Dict[str, Any]:
        """Get Redis storage statistics"""
        try:
            await self._ensure_connection()
            
            # Get cursor keys count
            pattern = f"{self.key_prefix}*"
            keys = await self._redis.keys(pattern)
            cursor_count = len(keys)
            
            # Get Redis info
            redis_info = await self._redis.info()
            
            # Estimate cursor data size
            total_memory_usage = 0
            for key in keys[:10]:  # Sample first 10 for estimation
                memory_usage = await self._redis.memory_usage(key)
                if memory_usage:
                    total_memory_usage += memory_usage
            
            avg_cursor_memory = total_memory_usage / min(10, cursor_count) if cursor_count > 0 else 0
            estimated_total_memory = avg_cursor_memory * cursor_count
            
            return {
                "backend_type": "redis",
                "host": self.host,
                "port": self.port,
                "db": self.db,
                "cursor_count": cursor_count,
                "estimated_memory_bytes": estimated_total_memory,
                "estimated_memory_mb": estimated_total_memory / (1024 * 1024),
                "avg_cursor_memory_bytes": avg_cursor_memory,
                "redis_used_memory": redis_info.get("used_memory", 0),
                "redis_used_memory_mb": redis_info.get("used_memory", 0) / (1024 * 1024),
                "redis_version": redis_info.get("redis_version", "unknown")
            }
            
        except Exception as e:
            logger.error(f"Failed to get Redis storage stats: {e}")
            return {"backend_type": "redis", "error": str(e)}
    
    async def close(self):
        """Close Redis connection"""
        if self._redis:
            await self._redis.close()
            self._redis = None


def create_storage_backend(backend_type: str, **kwargs) -> StorageBackend:
    """Factory function to create storage backends"""
    
    if backend_type == "memory":
        return InMemoryStorage()
    elif backend_type == "sqlite":
        return SQLiteStorage(**kwargs)
    elif backend_type == "redis":
        return RedisStorage(**kwargs)
    else:
        raise ValueError(f"Unknown storage backend: {backend_type}")