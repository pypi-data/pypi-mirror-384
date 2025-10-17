"""
MCP Response Pagination Manager

Advanced pagination system for managing large response datasets in MCP tools.
Provides cursor-based navigation with performance optimization and session isolation.
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, TypeVar, Generic, Callable
from pydantic import BaseModel
import asyncio

T = TypeVar('T')

class QueryState(BaseModel):
    """Represents the query parameters that define a dataset"""
    filters: Dict[str, Any] = {}
    parameters: Dict[str, Any] = {}
    
    @classmethod
    def from_params(cls, params: dict, exclude_keys: List[str] = None) -> "QueryState":
        """Extract query state from MCP tool parameters"""
        if exclude_keys is None:
            exclude_keys = ['limit', 'cursor_id', 'session_id', 'return_all']
            
        filters = {}
        parameters = {}
        
        for key, value in params.items():
            if key in exclude_keys:
                continue
                
            if 'filter' in key.lower() or key.endswith('_filter'):
                filters[key] = value
            else:
                parameters[key] = value
                
        return cls(filters=filters, parameters=parameters)
    
    def fingerprint(self) -> str:
        """Generate a unique fingerprint for this query state"""
        combined = {**self.filters, **self.parameters}
        sorted_dict = {k: combined[k] for k in sorted(combined.keys())}
        return json.dumps(sorted_dict, sort_keys=True, default=str)

class CursorState(BaseModel):
    """Represents a pagination cursor with performance metrics"""
    id: str
    session_id: str
    tool_name: str
    query_fingerprint: str
    position: Dict[str, Any]
    created_at: datetime
    expires_at: datetime
    last_accessed: datetime
    result_count: int = 0
    performance_metrics: Dict[str, Any] = {}
    
    def is_expired(self) -> bool:
        """Check if cursor has expired"""
        return datetime.now() > self.expires_at
    
    def update_access(self):
        """Update last accessed timestamp"""
        self.last_accessed = datetime.now()

class PaginatedResponse(BaseModel, Generic[T]):
    """Standardized paginated response structure"""
    items: List[T]
    total_count: Optional[int] = None
    has_more: bool
    cursor_id: Optional[str] = None
    metadata: Dict[str, Any] = {}
    
    class Config:
        arbitrary_types_allowed = True

class PaginationManager:
    """
    Manages pagination cursors and state across MCP tool invocations.
    
    Features:
    - Session-isolated cursor management
    - Automatic cursor expiration and cleanup
    - Performance metrics and optimization
    - Query state fingerprinting for consistency
    - Adaptive page sizing based on performance
    """
    
    def __init__(self):
        self.cursors: Dict[str, CursorState] = {}
        self.cleanup_task: Optional[asyncio.Task] = None
        self._start_cleanup_task()
    
    def _start_cleanup_task(self):
        """Start background task for cursor cleanup"""
        async def cleanup_expired():
            while True:
                try:
                    await asyncio.sleep(300)  # Clean up every 5 minutes
                    self.cleanup_expired_cursors()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    print(f"Cursor cleanup error: {e}")
        
        self.cleanup_task = asyncio.create_task(cleanup_expired())
    
    def cleanup_expired_cursors(self):
        """Remove expired cursors from memory"""
        expired_cursors = [
            cursor_id for cursor_id, cursor in self.cursors.items()
            if cursor.is_expired()
        ]
        
        for cursor_id in expired_cursors:
            del self.cursors[cursor_id]
            
        if expired_cursors:
            print(f"Cleaned up {len(expired_cursors)} expired cursors")
    
    async def create_cursor(
        self,
        session_id: str,
        tool_name: str,
        query_state: QueryState,
        initial_position: Dict[str, Any],
        ttl_hours: int = 24
    ) -> str:
        """Create a new pagination cursor"""
        
        cursor_id = str(uuid.uuid4())[:12]  # Short cursor ID
        now = datetime.now()
        
        cursor = CursorState(
            id=cursor_id,
            session_id=session_id,
            tool_name=tool_name,
            query_fingerprint=query_state.fingerprint(),
            position=initial_position,
            created_at=now,
            expires_at=now + timedelta(hours=ttl_hours),
            last_accessed=now,
            performance_metrics={
                'avg_fetch_time_ms': 0,
                'total_fetches': 0,
                'optimal_page_size': 50
            }
        )
        
        self.cursors[cursor_id] = cursor
        return cursor_id
    
    async def get_cursor(self, cursor_id: str, session_id: str) -> Optional[CursorState]:
        """Retrieve and validate a cursor"""
        cursor = self.cursors.get(cursor_id)
        
        if not cursor:
            return None
            
        if cursor.is_expired():
            del self.cursors[cursor_id]
            return None
            
        if cursor.session_id != session_id:
            raise ValueError(f"Cursor {cursor_id} not accessible from session {session_id}")
        
        cursor.update_access()
        return cursor
    
    async def update_cursor_position(
        self,
        cursor_id: str,
        new_position: Dict[str, Any],
        items_fetched: int
    ):
        """Update cursor position and metrics"""
        cursor = self.cursors.get(cursor_id)
        if not cursor:
            return
        
        cursor.position = new_position
        cursor.result_count += items_fetched
        cursor.update_access()
    
    async def record_performance(self, cursor_id: str, fetch_time_ms: float):
        """Record performance metrics for adaptive optimization"""
        cursor = self.cursors.get(cursor_id)
        if not cursor:
            return
        
        metrics = cursor.performance_metrics
        metrics['total_fetches'] += 1
        
        # Update average fetch time
        total_fetches = metrics['total_fetches']
        old_avg = metrics['avg_fetch_time_ms']
        metrics['avg_fetch_time_ms'] = (old_avg * (total_fetches - 1) + fetch_time_ms) / total_fetches
        
        # Adaptive page sizing for target 500ms response time
        target_time = 500
        current_size = metrics['optimal_page_size']
        
        if fetch_time_ms > target_time and current_size > 10:
            # Too slow, reduce page size
            metrics['optimal_page_size'] = max(10, int(current_size * 0.8))
        elif fetch_time_ms < target_time * 0.5 and current_size < 200:
            # Very fast, increase page size
            metrics['optimal_page_size'] = min(200, int(current_size * 1.2))
    
    async def invalidate_cursor(self, cursor_id: str):
        """Remove a cursor from the system"""
        self.cursors.pop(cursor_id, None)
    
    def get_cursor_stats(self) -> Dict[str, Any]:
        """Get statistics about active cursors"""
        now = datetime.now()
        active_cursors = len(self.cursors)
        expired_cursors = sum(1 for c in self.cursors.values() if c.is_expired())
        
        session_counts = {}
        for cursor in self.cursors.values():
            session_counts[cursor.session_id] = session_counts.get(cursor.session_id, 0) + 1
        
        return {
            'active_cursors': active_cursors,
            'expired_cursors': expired_cursors,
            'sessions_with_cursors': len(session_counts),
            'session_cursor_counts': session_counts,
            'cleanup_needed': expired_cursors > 0
        }
    
    async def cleanup(self):
        """Clean up pagination manager resources"""
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        
        self.cursors.clear()

# Global pagination manager instance
_pagination_manager: Optional[PaginationManager] = None

def get_pagination_manager() -> PaginationManager:
    """Get global pagination manager instance"""
    global _pagination_manager
    if _pagination_manager is None:
        _pagination_manager = PaginationManager()
    return _pagination_manager

async def cleanup_pagination_manager():
    """Clean up global pagination manager"""
    global _pagination_manager
    if _pagination_manager:
        await _pagination_manager.cleanup()
        _pagination_manager = None