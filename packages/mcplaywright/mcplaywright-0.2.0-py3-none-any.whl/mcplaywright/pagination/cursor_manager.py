"""
Session-Scoped Cursor Manager for MCPlaywright Pagination

Manages cursor lifecycle, session isolation, and automatic cleanup.
Provides secure, efficient cursor-based pagination across multiple tools.
"""

import uuid
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Union
from threading import Lock
import logging

from .models import CursorState, QueryState, PaginationParams
from .storage import StorageBackend, InMemoryStorage, create_storage_backend

logger = logging.getLogger(__name__)


class CursorNotFoundError(Exception):
    """Raised when trying to access a non-existent cursor"""
    pass


class CursorExpiredError(Exception):
    """Raised when trying to access an expired cursor"""
    pass


class CrossSessionAccessError(Exception):
    """Raised when trying to access a cursor from different session"""
    pass


class SessionCursorManager:
    """
    Manages session-scoped cursors for pagination across MCPlaywright tools.
    
    Features:
    - Session isolation: Cursors only accessible within creating session
    - Pluggable storage: Memory, SQLite, Redis backends for cursor persistence
    - Automatic cleanup: Expired and abandoned cursors removed automatically
    - Query state tracking: Detects fresh queries vs cursor continuations
    - Thread-safe operations: Safe for concurrent access from multiple clients
    - Performance monitoring: Tracks cursor usage and performance metrics
    """
    
    def __init__(self, 
                 default_expiry_hours: int = 24,
                 cleanup_interval_minutes: int = 30,
                 max_cursors_per_session: int = 100,
                 storage_backend: Optional[Union[str, StorageBackend]] = None,
                 storage_config: Optional[Dict[str, Any]] = None):
        """
        Initialize cursor manager with configurable limits and storage backend.
        
        Args:
            default_expiry_hours: Default cursor expiration time
            cleanup_interval_minutes: How often to run cleanup
            max_cursors_per_session: Maximum cursors per session
            storage_backend: Storage backend ("memory", "sqlite", "redis") or StorageBackend instance
            storage_config: Configuration for storage backend
        """
        # Setup storage backend
        if isinstance(storage_backend, StorageBackend):
            self._storage = storage_backend
        elif isinstance(storage_backend, str):
            self._storage = create_storage_backend(storage_backend, **(storage_config or {}))
        else:
            # Default to in-memory storage
            self._storage = InMemoryStorage()
        
        # Session tracking (still keep in memory for fast access)
        self._session_cursors: Dict[str, Set[str]] = {}
        self._lock = Lock()
        
        # Configuration
        self._default_expiry_hours = default_expiry_hours
        self._cleanup_interval = timedelta(minutes=cleanup_interval_minutes)
        self._max_cursors_per_session = max_cursors_per_session
        
        # Metrics
        self._total_cursors_created = 0
        self._total_cursors_expired = 0
        self._total_cross_session_attempts = 0
        
        # Background cleanup task
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def start(self) -> None:
        """Start the cursor manager with background cleanup"""
        if self._running:
            return
        
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info(f"SessionCursorManager started (cleanup every {self._cleanup_interval})")
    
    async def stop(self) -> None:
        """Stop the cursor manager and cleanup tasks"""
        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # Clear storage backend
        await self._storage.close()
        
        # Clear session tracking
        with self._lock:
            self._session_cursors.clear()
        
        logger.info("SessionCursorManager stopped and cleaned up")
    
    async def create_cursor(self,
                     session_id: str,
                     tool_name: str,
                     query_state: QueryState,
                     initial_position: Dict[str, Any],
                     expiry_hours: Optional[int] = None,
                     direction: str = "forward",
                     enable_optimization: bool = True) -> str:
        """
        Create a new cursor for session-scoped pagination.
        
        Args:
            session_id: Session identifier
            tool_name: Name of the tool creating cursor
            query_state: Query parameters and filters
            initial_position: Starting position for pagination
            expiry_hours: Custom expiry time (uses default if None)
            direction: Navigation direction (forward, backward, both)
            enable_optimization: Enable adaptive performance optimization
        
        Returns:
            Unique cursor ID string
        
        Raises:
            ValueError: If session already has too many cursors
        """
        with self._lock:
            # Check session cursor limits
            session_cursor_count = len(self._session_cursors.get(session_id, set()))
            if session_cursor_count >= self._max_cursors_per_session:
                raise ValueError(f"Session {session_id} has reached maximum cursor limit ({self._max_cursors_per_session})")
            
            # Generate unique cursor ID
            cursor_id = f"cursor_{uuid.uuid4().hex[:16]}"
            
            # Calculate expiry time
            expiry_hours = expiry_hours or self._default_expiry_hours
            now = datetime.now()
            expires_at = now + timedelta(hours=expiry_hours)
            
            # Create cursor state with advanced features
            cursor = CursorState(
                id=cursor_id,
                session_id=session_id,
                tool_name=tool_name,
                query_state={"filters": query_state.filters, "parameters": query_state.parameters},
                position=initial_position,
                created_at=now,
                last_accessed=now,
                expires_at=expires_at,
                direction=direction,
                chunk_size_history=[],
                performance_metrics={},
                cached_positions={}
            )
            
            # Enable optimization features if requested
            if enable_optimization:
                cursor.metadata["optimization_enabled"] = True
                cursor.metadata["target_response_time_ms"] = 500
            
            # Store cursor in backend
            success = await self._storage.store_cursor(cursor_id, cursor)
            if not success:
                raise RuntimeError(f"Failed to store cursor {cursor_id}")
            
            # Track by session (keep in memory for fast access)
            if session_id not in self._session_cursors:
                self._session_cursors[session_id] = set()
            self._session_cursors[session_id].add(cursor_id)
            
            # Update metrics
            self._total_cursors_created += 1
            
            logger.debug(f"Created cursor {cursor_id} for session {session_id}, tool {tool_name}")
            return cursor_id
    
    async def get_cursor(self, cursor_id: str, session_id: str) -> CursorState:
        """
        Retrieve and validate cursor access.
        
        Args:
            cursor_id: Cursor identifier
            session_id: Requesting session identifier
        
        Returns:
            CursorState object
        
        Raises:
            CursorNotFoundError: Cursor doesn't exist
            CursorExpiredError: Cursor has expired
            CrossSessionAccessError: Session mismatch
        """
        # Retrieve cursor from storage backend
        cursor = await self._storage.retrieve_cursor(cursor_id)
        
        if cursor is None:
            raise CursorNotFoundError(f"Cursor {cursor_id} not found")
        
        # Check expiration
        if cursor.is_expired():
            await self._storage.delete_cursor(cursor_id)
            with self._lock:
                # Also remove from session tracking
                if cursor.session_id in self._session_cursors:
                    self._session_cursors[cursor.session_id].discard(cursor_id)
            self._total_cursors_expired += 1
            raise CursorExpiredError(f"Cursor {cursor_id} has expired")
        
        # Check session access
        if not cursor.verify_session_access(session_id):
            self._total_cross_session_attempts += 1
            raise CrossSessionAccessError(f"Cursor {cursor_id} not accessible from session {session_id}")
        
        # Refresh access time and store back
        cursor.refresh()
        await self._storage.store_cursor(cursor_id, cursor)
        
        logger.debug(f"Retrieved cursor {cursor_id} for session {session_id}")
        return cursor
    
    async def update_cursor_position(self,
                              cursor_id: str,
                              session_id: str,
                              new_position: Dict[str, Any],
                              result_count: int = 0) -> None:
        """
        Update cursor position after fetching results.
        
        Args:
            cursor_id: Cursor identifier
            session_id: Session identifier  
            new_position: New pagination position
            result_count: Number of items returned
        """
        cursor = await self.get_cursor(cursor_id, session_id)
        cursor.update_position(new_position, result_count)
        await self._storage.store_cursor(cursor_id, cursor)
        
        logger.debug(f"Updated cursor {cursor_id} position, +{result_count} results")
    
    async def invalidate_cursor(self, cursor_id: str, session_id: str) -> bool:
        """
        Manually invalidate a cursor.
        
        Args:
            cursor_id: Cursor identifier
            session_id: Session identifier
        
        Returns:
            True if cursor was removed, False if not found
        """
        try:
            # Verify session access first
            await self.get_cursor(cursor_id, session_id)
            
            # Remove from storage backend
            success = await self._storage.delete_cursor(cursor_id)
            
            # Remove from session tracking
            with self._lock:
                for session_cursors in self._session_cursors.values():
                    session_cursors.discard(cursor_id)
            
            return success
            
        except (CursorNotFoundError, CursorExpiredError, CrossSessionAccessError):
            return False
    
    async def invalidate_session_cursors(self, session_id: str) -> int:
        """
        Invalidate all cursors for a session.
        
        Args:
            session_id: Session identifier
        
        Returns:
            Number of cursors removed
        """
        with self._lock:
            if session_id not in self._session_cursors:
                return 0
            
            cursor_ids = self._session_cursors[session_id].copy()
        
        removed_count = 0
        for cursor_id in cursor_ids:
            if await self._storage.delete_cursor(cursor_id):
                removed_count += 1
                # Remove from session tracking
                with self._lock:
                    self._session_cursors[session_id].discard(cursor_id)
        
        # Clean up empty session
        with self._lock:
            if session_id in self._session_cursors and not self._session_cursors[session_id]:
                del self._session_cursors[session_id]
        
        logger.info(f"Invalidated {removed_count} cursors for session {session_id}")
        return removed_count
    
    async def detect_fresh_query(self,
                          session_id: str,
                          tool_name: str,
                          params: PaginationParams) -> bool:
        """
        Detect if this is a fresh query or cursor continuation.
        
        Args:
            session_id: Session identifier
            tool_name: Tool name
            params: Pagination parameters
        
        Returns:
            True if fresh query, False if continuation
        """
        # If cursor_id provided, it's a continuation (if valid)
        if params.cursor_id:
            try:
                cursor = await self.get_cursor(params.cursor_id, session_id)
                # Valid cursor = continuation
                return False
            except (CursorNotFoundError, CursorExpiredError, CrossSessionAccessError):
                # Invalid cursor = treat as fresh
                return True
        
        # No cursor_id = fresh query
        return True
    
    async def get_session_cursor_stats(self, session_id: str) -> Dict[str, Any]:
        """
        Get cursor statistics for a session.
        
        Args:
            session_id: Session identifier
        
        Returns:
            Dictionary with cursor statistics
        """
        with self._lock:
            session_cursors = self._session_cursors.get(session_id, set())
        
        active_cursors = []
        expired_count = 0
        stale_count = 0
        
        for cursor_id in session_cursors:
            cursor = await self._storage.retrieve_cursor(cursor_id)
            if cursor:
                if cursor.is_expired():
                    expired_count += 1
                elif cursor.is_stale():
                    stale_count += 1
                else:
                    active_cursors.append({
                        "cursor_id": cursor_id,
                        "tool_name": cursor.tool_name,
                        "created_at": cursor.created_at.isoformat(),
                        "last_accessed": cursor.last_accessed.isoformat(),
                        "result_count": cursor.result_count
                    })
        
        return {
            "session_id": session_id,
            "total_cursors": len(session_cursors),
            "active_cursors": active_cursors,
            "expired_count": expired_count,
            "stale_count": stale_count
        }
    
    async def navigate_backward(self,
                         cursor_id: str,
                         session_id: str,
                         steps: int = 1) -> Optional[Dict[str, Any]]:
        """
        Navigate backward in pagination history.
        
        Args:
            cursor_id: Cursor identifier
            session_id: Session identifier
            steps: Number of steps to go back
        
        Returns:
            Previous position or None if not available
        """
        cursor = await self.get_cursor(cursor_id, session_id)
        
        if not cursor.can_navigate_backward():
            return None
        
        # Get previous position (simplified - could support multiple steps)
        previous_pos = cursor.get_previous_position()
        
        # Update cursor to previous position
        cursor.position = previous_pos
        cursor.direction = "backward"
        cursor.refresh()
        await self._storage.store_cursor(cursor_id, cursor)
        
        logger.debug(f"Navigated cursor {cursor_id} backward {steps} step(s)")
        return previous_pos
    
    async def optimize_chunk_size(self,
                           cursor_id: str,
                           session_id: str,
                           last_fetch_time_ms: float,
                           result_count: int) -> int:
        """
        Calculate optimal chunk size based on performance history.
        
        Args:
            cursor_id: Cursor identifier
            session_id: Session identifier  
            last_fetch_time_ms: Time taken for last fetch
            result_count: Number of items in last fetch
        
        Returns:
            Recommended chunk size for next fetch
        """
        cursor = await self.get_cursor(cursor_id, session_id)
        
        # Record performance metrics
        cursor.record_performance(last_fetch_time_ms, result_count)
        cursor.record_chunk_size(result_count)
        
        # Get optimization target from metadata
        target_time_ms = cursor.metadata.get("target_response_time_ms", 500)
        
        # Calculate optimal chunk size
        optimal_size = cursor.get_optimal_chunk_size(target_time_ms)
        
        # Store updated cursor
        await self._storage.store_cursor(cursor_id, cursor)
        
        logger.debug(f"Optimized chunk size for cursor {cursor_id}: {optimal_size} (target: {target_time_ms}ms)")
        return optimal_size
    
    async def get_performance_insights(self, session_id: str) -> Dict[str, Any]:
        """Get performance insights for session cursors"""
        with self._lock:
            session_cursors = self._session_cursors.get(session_id, set())
        
        insights = {
            "session_id": session_id,
            "total_cursors": len(session_cursors),
            "performance_summary": {
                "avg_fetch_time_ms": 0,
                "avg_throughput": 0,
                "optimization_opportunities": []
            },
            "cursor_details": []
        }
        
        fetch_times = []
        throughputs = []
        
        for cursor_id in session_cursors:
            cursor = await self._storage.retrieve_cursor(cursor_id)
            if cursor:
                metrics = cursor.performance_metrics
                
                if metrics:
                    fetch_time = metrics.get("last_fetch_time_ms", 0)
                    throughput = metrics.get("last_throughput", 0)
                    
                    if fetch_time > 0:
                        fetch_times.append(fetch_time)
                    if throughput > 0:
                        throughputs.append(throughput)
                    
                    cursor_detail = {
                        "cursor_id": cursor_id,
                        "tool_name": cursor.tool_name,
                        "total_fetched": cursor.result_count,
                        "avg_chunk_size": sum(cursor.chunk_size_history) / len(cursor.chunk_size_history) if cursor.chunk_size_history else 0,
                        "last_fetch_time_ms": fetch_time,
                        "throughput": throughput
                    }
                    insights["cursor_details"].append(cursor_detail)
                    
                    # Identify optimization opportunities
                    if fetch_time > 1000:  # Slow fetches
                        insights["performance_summary"]["optimization_opportunities"].append(
                            f"Cursor {cursor_id} has slow fetch times ({fetch_time:.1f}ms) - consider smaller chunks"
                        )
        
        # Calculate averages
        if fetch_times:
            insights["performance_summary"]["avg_fetch_time_ms"] = sum(fetch_times) / len(fetch_times)
        if throughputs:
            insights["performance_summary"]["avg_throughput"] = sum(throughputs) / len(throughputs)
        
        return insights
    
    async def get_global_stats(self) -> Dict[str, Any]:
        """Get global cursor manager statistics"""
        with self._lock:
            total_sessions = len(self._session_cursors)
            total_session_cursors = sum(len(cursors) for cursors in self._session_cursors.values())
        
        # Get storage stats if available
        try:
            storage_stats = await self._storage.get_storage_stats()
        except Exception:
            storage_stats = {"type": "unknown", "total_cursors": total_session_cursors}
        
        return {
            "total_cursors": total_session_cursors,
            "total_sessions": total_sessions,
            "cursors_created": self._total_cursors_created,
            "cursors_expired": self._total_cursors_expired,
            "cross_session_attempts": self._total_cross_session_attempts,
            "max_cursors_per_session": self._max_cursors_per_session,
            "default_expiry_hours": self._default_expiry_hours,
            "storage_backend": storage_stats,
            "optimization_features": {
                "bidirectional_navigation": True,
                "adaptive_chunk_sizing": True,
                "performance_tracking": True
            }
        }
    
    # Removed _remove_cursor_unsafe method - now handled by storage backend
    
    async def _cleanup_loop(self) -> None:
        """Background task to clean up expired and stale cursors"""
        while self._running:
            try:
                await asyncio.sleep(self._cleanup_interval.total_seconds())
                
                if not self._running:
                    break
                
                removed_count = await self._cleanup_expired_cursors()
                if removed_count > 0:
                    logger.info(f"Cleanup removed {removed_count} expired/stale cursors")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cursor cleanup error: {e}")
    
    async def _cleanup_expired_cursors(self) -> int:
        """Clean up expired and stale cursors"""
        # Use storage backend's cleanup method
        removed_count = await self._storage.cleanup_expired(datetime.now())
        
        # Update session tracking by removing expired cursor IDs
        with self._lock:
            for session_id, cursor_ids in list(self._session_cursors.items()):
                # Check each cursor and remove if expired
                for cursor_id in list(cursor_ids):
                    cursor = await self._storage.retrieve_cursor(cursor_id)
                    if not cursor:  # Cursor was cleaned up
                        cursor_ids.discard(cursor_id)
                
                # Remove empty sessions
                if not cursor_ids:
                    del self._session_cursors[session_id]
        
        self._total_cursors_expired += removed_count
        return removed_count


# Global instance for session management
_cursor_manager: Optional[SessionCursorManager] = None


async def get_cursor_manager() -> SessionCursorManager:
    """Get the global cursor manager instance"""
    global _cursor_manager
    if _cursor_manager is None:
        _cursor_manager = SessionCursorManager()
        await _cursor_manager.start()
    return _cursor_manager


async def shutdown_cursor_manager() -> None:
    """Shutdown the global cursor manager"""
    global _cursor_manager
    if _cursor_manager is not None:
        await _cursor_manager.stop()
        _cursor_manager = None