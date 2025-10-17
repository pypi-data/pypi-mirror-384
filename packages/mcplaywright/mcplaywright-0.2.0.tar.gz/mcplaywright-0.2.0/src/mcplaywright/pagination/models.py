"""
Pagination Models for MCPlaywright

Core data models for session-scoped cursor pagination system.
"""

import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


@dataclass
class CursorState:
    """
    Represents the state of a pagination cursor within a session.
    
    Each cursor is tied to a specific session and tool, maintaining
    query state and current position for resumable pagination.
    Enhanced with bidirectional navigation and performance tracking.
    """
    id: str
    session_id: str
    tool_name: str
    query_state: Dict[str, Any]
    position: Dict[str, Any]
    created_at: datetime
    last_accessed: datetime
    expires_at: datetime
    result_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Advanced pagination features
    direction: str = "forward"  # forward, backward, both
    chunk_size_history: List[int] = field(default_factory=list)
    performance_metrics: Dict[str, float] = field(default_factory=dict)
    cached_positions: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """Check if cursor has expired"""
        return datetime.now() > self.expires_at
    
    def is_stale(self) -> bool:
        """Check if cursor hasn't been accessed recently (30 minutes)"""
        return datetime.now() - self.last_accessed > timedelta(minutes=30)
    
    def refresh(self, extend_hours: int = 1):
        """Refresh cursor access time and extend expiration"""
        self.last_accessed = datetime.now()
        self.expires_at = datetime.now() + timedelta(hours=extend_hours)
    
    def verify_session_access(self, requesting_session_id: str) -> bool:
        """Verify cursor can be accessed by requesting session"""
        return self.session_id == requesting_session_id
    
    def matches_query_state(self, current_query: Dict[str, Any]) -> bool:
        """Check if current query matches cursor's stored query state"""
        return self.query_state == current_query
    
    def update_position(self, new_position: Dict[str, Any], result_count: int = 0):
        """Update cursor position and increment result count"""
        # Cache previous position for bidirectional navigation
        if self.position:
            position_key = f"pos_{len(self.cached_positions)}"
            self.cached_positions[position_key] = self.position.copy()
        
        self.position = new_position
        self.result_count += result_count
        self.refresh()
    
    def record_chunk_size(self, chunk_size: int):
        """Record chunk size for adaptive pagination"""
        self.chunk_size_history.append(chunk_size)
        # Keep only last 10 chunk sizes for analysis
        if len(self.chunk_size_history) > 10:
            self.chunk_size_history = self.chunk_size_history[-10:]
    
    def record_performance(self, fetch_time_ms: float, result_count: int):
        """Record performance metrics for optimization"""
        self.performance_metrics.update({
            "last_fetch_time_ms": fetch_time_ms,
            "avg_time_per_item": fetch_time_ms / result_count if result_count > 0 else 0,
            "last_throughput": result_count / (fetch_time_ms / 1000) if fetch_time_ms > 0 else 0
        })
    
    def get_optimal_chunk_size(self, target_time_ms: float = 500) -> int:
        """Calculate optimal chunk size based on performance history"""
        if not self.performance_metrics or not self.chunk_size_history:
            return 100  # Default chunk size
        
        avg_time_per_item = self.performance_metrics.get("avg_time_per_item", 5.0)
        if avg_time_per_item <= 0:
            return 100
        
        # Calculate optimal size to hit target fetch time
        optimal_size = int(target_time_ms / avg_time_per_item)
        
        # Clamp between reasonable bounds
        return max(10, min(optimal_size, 1000))
    
    def can_navigate_backward(self) -> bool:
        """Check if backward navigation is possible"""
        return len(self.cached_positions) > 0
    
    def get_previous_position(self) -> Optional[Dict[str, Any]]:
        """Get previous position for backward navigation"""
        if not self.cached_positions:
            return None
        
        # Get most recent cached position
        latest_key = max(self.cached_positions.keys())
        return self.cached_positions[latest_key]


@dataclass
class QueryState:
    """
    Represents a query's filter and parameter state.
    Used to determine if a cursor can be reused or needs to be invalidated.
    """
    filters: Dict[str, Any]
    parameters: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.now)
    
    @classmethod
    def from_params(cls, params: BaseModel) -> "QueryState":
        """Create QueryState from Pydantic model parameters"""
        param_dict = params.model_dump(exclude={'cursor_id', 'session_id'})
        filters = {}
        parameters = {}
        
        # Separate filters from other parameters
        filter_keys = {'filter', 'domain', 'method', 'status', 'priority_filter', 'tool_filter'}
        for key, value in param_dict.items():
            if key in filter_keys or key.endswith('_filter'):
                filters[key] = value
            else:
                parameters[key] = value
        
        return cls(filters=filters, parameters=parameters)
    
    def fingerprint(self) -> str:
        """Generate a stable fingerprint for this query state"""
        combined = {**self.filters, **self.parameters}
        return str(hash(json.dumps(combined, sort_keys=True)))
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, QueryState):
            return False
        return self.filters == other.filters and self.parameters == other.parameters


class PaginationParams(BaseModel):
    """
    Base pagination parameters for all paginated tools.
    
    Tools should inherit from this and add their specific parameters.
    """
    limit: Optional[int] = Field(
        default=100, 
        ge=1, 
        le=1000,
        description="Maximum number of items to return per page (1-1000)"
    )
    cursor_id: Optional[str] = Field(
        default=None,
        description="Session-scoped cursor ID for continuation"
    )
    session_id: Optional[str] = Field(
        default=None,
        description="Session ID (usually auto-detected)"
    )


class PaginationMetadata(BaseModel):
    """Metadata about pagination state and performance"""
    call_type: str = Field(description="'fresh' or 'continuation'")
    cursor_age: Optional[timedelta] = Field(default=None, description="Age of cursor if continuation")
    total_fetched: Optional[int] = Field(default=None, description="Total items fetched via this cursor")
    query_fingerprint: Optional[str] = Field(default=None, description="Fingerprint of query state")
    estimated_total: Optional[int] = Field(default=None, description="Estimated total items available")
    fetch_time_ms: Optional[float] = Field(default=None, description="Time taken to fetch results")
    
    class Config:
        # Allow timedelta serialization
        json_encoders = {
            timedelta: lambda v: v.total_seconds()
        }


class PaginatedResponse(BaseModel):
    """
    Standard response format for all paginated tools.
    
    Provides consistent interface for cursor-based pagination.
    """
    items: List[Any] = Field(description="The actual data items")
    cursor_id: Optional[str] = Field(
        default=None, 
        description="Cursor ID for next page (null if no more data)"
    )
    has_more: bool = Field(description="Whether more data is available")
    pagination: PaginationMetadata = Field(description="Pagination metadata")
    
    @classmethod
    def create_fresh(
        cls,
        items: List[Any],
        cursor_id: Optional[str] = None,
        estimated_total: Optional[int] = None,
        fetch_time_ms: Optional[float] = None,
        query_fingerprint: Optional[str] = None
    ) -> "PaginatedResponse":
        """Create response for fresh query"""
        return cls(
            items=items,
            cursor_id=cursor_id,
            has_more=cursor_id is not None,
            pagination=PaginationMetadata(
                call_type="fresh",
                estimated_total=estimated_total,
                fetch_time_ms=fetch_time_ms,
                query_fingerprint=query_fingerprint
            )
        )
    
    @classmethod 
    def create_continuation(
        cls,
        items: List[Any],
        cursor_id: Optional[str] = None,
        cursor_age: Optional[timedelta] = None,
        total_fetched: Optional[int] = None,
        fetch_time_ms: Optional[float] = None
    ) -> "PaginatedResponse":
        """Create response for cursor continuation"""
        return cls(
            items=items,
            cursor_id=cursor_id,
            has_more=cursor_id is not None,
            pagination=PaginationMetadata(
                call_type="continuation",
                cursor_age=cursor_age,
                total_fetched=total_fetched,
                fetch_time_ms=fetch_time_ms
            )
        )


# Tool-specific parameter models
class RequestMonitoringParams(PaginationParams):
    """Parameters for HTTP request monitoring pagination with ripgrep filtering"""
    filter: Optional[str] = Field("all", description="Filter requests: 'all', 'failed', 'slow', 'errors', 'success'")
    domain: Optional[str] = Field(None, description="Filter requests by domain hostname")
    method: Optional[str] = Field(None, description="Filter requests by HTTP method")
    status: Optional[int] = Field(None, description="Filter requests by HTTP status code")
    format: Optional[str] = Field("summary", description="Response format: 'summary', 'detailed', 'stats'")
    slow_threshold: Optional[int] = Field(1000, description="Threshold in milliseconds for 'slow' requests")
    
    # Universal ripgrep filtering parameters
    filter_pattern: Optional[str] = Field(None, description="Ripgrep pattern to search for (supports regex)")
    filter_fields: Optional[List[str]] = Field(None, description="Fields to search: url, method, status, headers, request_body, response_body")
    filter_mode: Optional[str] = Field("content", description="Filter mode: content, files, count")
    case_sensitive: Optional[bool] = Field(False, description="Case sensitive pattern matching")
    whole_words: Optional[bool] = Field(False, description="Match whole words only")
    context_lines: Optional[int] = Field(None, description="Context lines before/after matches")
    invert_match: Optional[bool] = Field(False, description="Invert match (show non-matching)")
    max_matches: Optional[int] = Field(None, description="Maximum matches to return")


class ConsoleMessagesParams(PaginationParams):
    """Parameters for console message pagination with ripgrep filtering"""
    level_filter: Optional[str] = Field(None, description="Filter by log level: error, warn, info, debug")
    source_filter: Optional[str] = Field(None, description="Filter by source: console, network, security")
    
    # Universal ripgrep filtering parameters
    filter_pattern: Optional[str] = Field(None, description="Ripgrep pattern to search for (supports regex)")
    filter_fields: Optional[List[str]] = Field(None, description="Fields to search: message, level, source, stack_trace, timestamp")
    filter_mode: Optional[str] = Field("content", description="Filter mode: content, files, count")
    case_sensitive: Optional[bool] = Field(False, description="Case sensitive pattern matching")
    whole_words: Optional[bool] = Field(False, description="Match whole words only")
    context_lines: Optional[int] = Field(None, description="Context lines before/after matches")
    invert_match: Optional[bool] = Field(False, description="Invert match (show non-matching)")
    max_matches: Optional[int] = Field(None, description="Maximum matches to return")


class MessageQueueParams(PaginationParams):
    """Parameters for message queue pagination"""
    priority_filter: Optional[str] = Field(None, description="Filter by priority: low, normal, high, urgent, critical")
    client_filter: Optional[str] = Field(None, description="Filter by client ID")


class TestReportParams(PaginationParams):
    """Parameters for test report pagination"""
    test_type_filter: Optional[str] = Field(None, description="Filter by test type")
    status_filter: Optional[str] = Field(None, description="Filter by test status: passed, failed")
    date_range: Optional[str] = Field(None, description="Date range filter: last_hour, last_day, last_week")