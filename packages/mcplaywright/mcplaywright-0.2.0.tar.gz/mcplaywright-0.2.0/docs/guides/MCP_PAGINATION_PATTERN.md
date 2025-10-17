# MCP Pagination Pattern for Long Tool Responses

## Overview

This document describes a comprehensive pagination pattern for Model Context Protocol (MCP) servers that need to return large datasets from tool calls. Unlike standard MCP pagination which only works for "list" commands, this pattern enables cursor-based pagination for any tool that returns substantial data.

## Problem Statement

**Challenge**: MCP's built-in pagination only supports list operations, but many practical tools return large datasets:
- HTTP request monitoring (thousands of captured requests)
- Console message logs (extensive browser console output)
- Test results and reports (comprehensive testing data)
- DevTools profiling data (detailed performance metrics)

**Current Limitation**: Without pagination, these tools must either:
- Truncate results (losing important data)
- Return massive responses (overwhelming the client)
- Implement ad-hoc pagination (inconsistent user experience)

## Solution Architecture

### Core Components

#### 1. Session-Scoped Cursor Management
```python
@dataclass
class CursorState:
    """Session-isolated cursor with security and lifecycle management"""
    id: str                    # Unique cursor identifier
    session_id: str           # Session isolation
    tool_name: str            # Tool that created cursor
    query_state: Dict         # Parameters that created this cursor
    position: Dict            # Current pagination position
    created_at: datetime      # Creation timestamp
    expires_at: datetime      # Automatic cleanup
    result_count: int         # Total items fetched
    direction: str            # Navigation direction support
    performance_metrics: Dict # Adaptive optimization data
```

#### 2. Query State Fingerprinting
```python
class QueryState:
    """Detects parameter changes that invalidate cursors"""
    filters: Dict[str, Any]     # Filter parameters
    parameters: Dict[str, Any]  # Other parameters
    
    def fingerprint(self) -> str:
        """Stable hash for detecting query changes"""
        combined = {**self.filters, **self.parameters}
        return str(hash(json.dumps(combined, sort_keys=True)))
```

#### 3. Standardized Response Format
```python
class PaginatedResponse:
    """Consistent pagination response across all tools"""
    items: List[Any]                    # Actual data
    cursor_id: Optional[str]            # Next page cursor
    has_more: bool                      # More data available
    pagination: PaginationMetadata      # Performance/debug info
    
    @classmethod
    def create_fresh(cls, items, cursor_id=None, **kwargs):
        """Factory for fresh queries"""
    
    @classmethod 
    def create_continuation(cls, items, cursor_id=None, **kwargs):
        """Factory for cursor continuations"""
```

## Implementation Pattern

### Step 1: Tool Parameter Model
```python
class ToolPaginationParams(PaginationParams):
    """Inherit from base pagination parameters"""
    # Tool-specific parameters
    filter: Optional[str] = Field("all", description="Data filter")
    format: Optional[str] = Field("summary", description="Output format")
    
    # Inherited pagination parameters:
    # - limit: Maximum items per page
    # - cursor_id: Continuation cursor
    # - session_id: Session identifier
```

### Step 2: Fresh vs Continuation Detection
```python
async def paginated_tool(params: ToolPaginationParams) -> PaginatedResponse:
    """Standard pagination implementation pattern"""
    start_time = datetime.now()
    context = await get_session_context(params.session_id)
    
    # Detect fresh query vs cursor continuation
    is_fresh = await context.detect_fresh_pagination_query(
        tool_name="tool_name", 
        params=params
    )
    
    if is_fresh:
        return await handle_fresh_query(context, params, start_time)
    else:
        return await handle_cursor_continuation(context, params, start_time)
```

### Step 3: Fresh Query Handling
```python
async def handle_fresh_query(context, params, start_time):
    """Handle new pagination query"""
    # Apply filters and get dataset
    filtered_data = apply_filters(raw_data, params)
    
    # Get page of results
    page_items = filtered_data[:params.limit]
    
    # Create cursor if more data available
    cursor_id = None
    if len(filtered_data) > params.limit:
        query_state = QueryState.from_params(params)
        cursor_id = await context.create_pagination_cursor(
            tool_name="tool_name",
            query_state=query_state,
            initial_position={
                "last_index": params.limit - 1,
                "filtered_total": len(filtered_data)
            }
        )
    
    return PaginatedResponse.create_fresh(
        items=format_items(page_items, params.format),
        cursor_id=cursor_id,
        estimated_total=len(filtered_data),
        fetch_time_ms=(datetime.now() - start_time).total_seconds() * 1000
    )
```

### Step 4: Cursor Continuation Handling
```python
async def handle_cursor_continuation(context, params, start_time):
    """Handle cursor-based continuation"""
    try:
        cursor = await context.get_pagination_cursor(params.cursor_id)
        
        # Verify query consistency
        current_query = QueryState.from_params(params)
        if not cursor.matches_query_state(current_query.dict()):
            # Parameters changed, treat as fresh query
            return await handle_fresh_query(context, params, start_time)
        
        # Get next page from cursor position
        position = cursor.position
        start_index = position["last_index"] + 1
        end_index = start_index + params.limit
        
        # Re-apply filters (data may have changed)
        filtered_data = apply_filters(raw_data, params)
        page_items = filtered_data[start_index:end_index]
        
        # Update cursor or invalidate if no more data
        new_cursor_id = None
        if end_index < len(filtered_data):
            new_position = {"last_index": end_index - 1, ...}
            await context.update_cursor_position(
                params.cursor_id, new_position, len(page_items)
            )
            new_cursor_id = params.cursor_id
        else:
            await context.invalidate_cursor(params.cursor_id)
        
        return PaginatedResponse.create_continuation(
            items=format_items(page_items, params.format),
            cursor_id=new_cursor_id,
            cursor_age=datetime.now() - cursor.last_accessed,
            total_fetched=cursor.result_count + len(page_items)
        )
        
    except (CursorNotFoundError, CursorExpiredError, CrossSessionAccessError):
        # Cursor issues, fallback to fresh query
        return await handle_fresh_query(context, params, start_time)
```

## Advanced Features

### Bidirectional Navigation
```python
# Enable backward navigation
cursor.direction = "both"
cursor.cached_positions = {}  # Store previous positions

# Navigate backward
if cursor.can_navigate_backward():
    previous_pos = cursor.get_previous_position()
    # Fetch previous page using cached position
```

### Adaptive Chunk Sizing
```python
# Record performance metrics
cursor.record_performance(fetch_time_ms=125.5, result_count=50)
cursor.record_chunk_size(50)

# Calculate optimal chunk size for target response time
optimal_size = cursor.get_optimal_chunk_size(target_time_ms=500)
# Automatically adjusts based on performance history
```

### Query State Validation
```python
# Automatic detection of parameter changes
current_fingerprint = QueryState.from_params(params).fingerprint()
cached_fingerprint = cursor.query_state_fingerprint

if current_fingerprint != cached_fingerprint:
    # Parameters changed, invalidate cursor and start fresh
    logger.warning("Query parameters changed, starting fresh pagination")
    return handle_fresh_query(context, params, start_time)
```

## Security Features

### Session Isolation
```python
class SessionCursorManager:
    """Ensures cursors are only accessible within creating session"""
    
    def get_cursor(self, cursor_id: str, session_id: str) -> CursorState:
        cursor = self._cursors[cursor_id]
        
        # Verify session access
        if not cursor.verify_session_access(session_id):
            raise CrossSessionAccessError(
                f"Cursor {cursor_id} not accessible from session {session_id}"
            )
        
        return cursor
```

### Automatic Cleanup
```python
# Cursors automatically expire and are cleaned up
cursor.expires_at = datetime.now() + timedelta(hours=24)

# Background cleanup task removes expired cursors
async def cleanup_expired_cursors():
    for cursor_id, cursor in self._cursors.items():
        if cursor.is_expired() or cursor.is_stale():
            self._remove_cursor(cursor_id)
```

## Usage Examples

### HTTP Request Monitoring
```python
# First page
response = await browser_get_requests(RequestMonitoringParams(
    limit=50,
    filter="errors",
    domain="api.example.com"
))
# Returns: 50 error requests + cursor_id for next page

# Next page  
response = await browser_get_requests(RequestMonitoringParams(
    limit=50,
    cursor_id="cursor_abc123",  # Continue from previous page
    filter="errors",            # Same parameters
    domain="api.example.com"
))
# Returns: Next 50 error requests + updated cursor_id
```

### Console Message Pagination
```python
# Large console log pagination
response = await browser_get_console_messages(ConsoleMessagesParams(
    limit=100,
    level_filter="error",
    source_filter="console"
))

# Continue with cursor
response = await browser_get_console_messages(ConsoleMessagesParams(
    limit=100,
    cursor_id=response.cursor_id,  # Continue from where we left off
    level_filter="error",
    source_filter="console"
))
```

## Benefits

### Performance
- **Efficient Memory Usage**: Only load data pages as needed
- **Fast Response Times**: Consistent response times regardless of dataset size
- **Adaptive Optimization**: Automatic chunk size tuning based on performance

### User Experience
- **Consistent Interface**: Same pagination pattern across all tools
- **Resumable Navigation**: Pick up where you left off across sessions
- **Progress Tracking**: Total items fetched and remaining estimates

### Security
- **Session Isolation**: Cursors cannot be accessed across sessions
- **Automatic Cleanup**: Expired cursors removed automatically
- **Parameter Validation**: Detect and handle parameter changes gracefully

### Developer Experience
- **Easy Integration**: Simple pattern to add pagination to new tools
- **Comprehensive Testing**: Full test coverage with edge case handling
- **Rich Metadata**: Performance metrics and debugging information

## Implementation Checklist

### For New Paginated Tools:
- [ ] Create tool-specific parameter model inheriting from `PaginationParams`
- [ ] Implement fresh query detection logic
- [ ] Add cursor creation for multi-page datasets
- [ ] Handle cursor continuation with consistency validation
- [ ] Add error handling for invalid/expired cursors
- [ ] Include performance metrics and optimization
- [ ] Write comprehensive tests for edge cases

### For MCP Server Integration:
- [ ] Initialize SessionCursorManager on server startup
- [ ] Register paginated tools with FastMCP
- [ ] Configure cursor cleanup intervals
- [ ] Set appropriate cursor expiration times
- [ ] Monitor cursor usage and performance metrics
- [ ] Document pagination usage for API consumers

## Best Practices

1. **Always validate query consistency** between cursor creation and continuation
2. **Implement graceful fallbacks** when cursors are invalid or expired
3. **Record performance metrics** for optimization and monitoring
4. **Use appropriate expiration times** based on data volatility
5. **Test with large datasets** to ensure performance at scale
6. **Document pagination behavior** for API consumers
7. **Monitor cursor usage patterns** for optimization opportunities

This pagination pattern provides a robust, secure, and efficient solution for handling large datasets in MCP tools while maintaining a consistent user experience across different data types and use cases.