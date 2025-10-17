"""
Pagination decorators and utilities for MCP tools.

Provides easy-to-use decorators for adding pagination support to any MCP tool.
"""

from functools import wraps
from typing import Dict, Any, List, TypeVar, Callable, Optional, Union
from pydantic import BaseModel, Field

from .pagination_manager import (
    get_pagination_manager, 
    QueryState, 
    PaginatedResponse
)

T = TypeVar('T')

class PaginationParams(BaseModel):
    """Standard pagination parameters for MCP tools"""
    limit: int = Field(default=50, ge=1, le=1000, description="Maximum items per page (1-1000)")
    cursor_id: Optional[str] = Field(default=None, description="Continue from previous page using cursor ID")
    session_id: Optional[str] = Field(default=None, description="Session identifier for cursor isolation")
    return_all: bool = Field(default=False, description="Return entire response bypassing pagination (WARNING: may produce very large responses)")

class PaginationConfig(BaseModel):
    """Configuration for pagination behavior"""
    max_response_tokens: int = 8000
    default_page_size: int = 50
    enable_performance_optimization: bool = True
    token_estimation_ratio: float = 4.0  # Roughly 4 chars per token

def with_pagination(
    data_extractor: Callable[[Any], List[T]],
    item_formatter: Callable[[T], str],
    tool_name: str,
    config: Optional[PaginationConfig] = None
):
    """
    Decorator to add pagination support to MCP tools.
    
    Args:
        data_extractor: Function that extracts the full dataset from tool parameters
        item_formatter: Function that formats individual items for response
        tool_name: Name of the tool (for cursor tracking)
        config: Pagination configuration options
    
    Usage:
        @with_pagination(
            data_extractor=lambda params: get_all_requests(params),
            item_formatter=lambda req: f"Request: {req.url} - {req.status}",
            tool_name="browser_get_requests"
        )
        async def browser_get_requests(params: RequestParams) -> Dict[str, Any]:
            # Tool implementation - data extraction and formatting handled by decorator
            pass
    """
    
    if config is None:
        config = PaginationConfig()
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Dict[str, Any]:
            # Extract parameters - assume first arg after context is params
            context = args[0] if args else None
            params_obj = args[1] if len(args) > 1 else kwargs.get('params')
            
            if not params_obj:
                # Fall back to original function if no params
                return await func(*args, **kwargs)
            
            # Convert params to dict if it's a Pydantic model
            if hasattr(params_obj, 'dict'):
                params_dict = params_obj.dict()
            else:
                params_dict = dict(params_obj)
            
            # Extract pagination parameters
            pagination_params = PaginationParams(
                limit=params_dict.get('limit', config.default_page_size),
                cursor_id=params_dict.get('cursor_id'),
                session_id=params_dict.get('session_id', 'default'),
                return_all=params_dict.get('return_all', False)
            )
            
            # Extract all data using provided extractor
            start_time = time.time()
            all_data = data_extractor(params_dict)
            fetch_time_ms = (time.time() - start_time) * 1000
            
            # Handle bypass option
            if pagination_params.return_all:
                return await _handle_bypass_pagination(
                    all_data, 
                    item_formatter, 
                    tool_name, 
                    config,
                    fetch_time_ms
                )
            
            # Handle pagination
            return await _handle_paginated_response(
                all_data,
                item_formatter,
                tool_name,
                pagination_params,
                config,
                fetch_time_ms
            )
        
        return wrapper
    return decorator

async def _handle_bypass_pagination(
    all_data: List[T],
    item_formatter: Callable[[T], str],
    tool_name: str,
    config: PaginationConfig,
    fetch_time_ms: float
) -> Dict[str, Any]:
    """Handle return_all bypass option with warnings"""
    
    # Format all items for token estimation
    formatted_items = [item_formatter(item) for item in all_data]
    full_response = '\n'.join(formatted_items)
    estimated_tokens = len(full_response) / config.token_estimation_ratio
    
    # Generate warnings based on response size
    warning_level = "💡"
    warning_text = "Large response"
    
    if estimated_tokens > 50000:
        warning_level = "🚨"
        warning_text = "EXTREMELY LARGE response"
    elif estimated_tokens > 20000:
        warning_level = "⚠️"
        warning_text = "VERY LARGE response"
    elif estimated_tokens > config.max_response_tokens:
        warning_level = "⚠️"
        warning_text = "Large response"
    
    # Build comprehensive warning
    warning_message = f"""{warning_level} **PAGINATION BYPASSED** - {warning_text} (~{int(estimated_tokens):,} tokens)

**⚠️ WARNING: This response may:**
• Fill up context rapidly ({estimated_tokens/1000:.1f}k+ tokens)
• Cause client performance issues
• Be truncated by MCP client limits
• Impact subsequent conversation quality

**📊 Dataset: {len(all_data)} items** ({fetch_time_ms:.0f}ms fetch time)
"""
    
    if estimated_tokens > config.max_response_tokens:
        recommended_limit = max(10, int(config.default_page_size * config.max_response_tokens / estimated_tokens))
        warning_message += f"""
**💡 RECOMMENDATION:**
• Use pagination: `{tool_name}({{...same_params, return_all: false, limit: {recommended_limit}}})`
• Apply filters to reduce dataset size
• Consider using cursor navigation for exploration
"""
    
    # Combine warning with data
    result = [warning_message] + formatted_items
    
    # Add summary footer
    result.append(f"""
**📋 COMPLETE DATASET DELIVERED**
• Items: {len(all_data)} (all)
• Tokens: ~{int(estimated_tokens):,}
• Fetch Time: {fetch_time_ms:.0f}ms
• Status: ✅ No pagination applied

💡 **Next time**: Use `return_all: false` for paginated navigation""")
    
    return {
        "status": "complete_dataset",
        "items": result,
        "total_count": len(all_data),
        "estimated_tokens": int(estimated_tokens),
        "fetch_time_ms": fetch_time_ms,
        "bypassed_pagination": True
    }

async def _handle_paginated_response(
    all_data: List[T],
    item_formatter: Callable[[T], str],
    tool_name: str,
    pagination_params: PaginationParams,
    config: PaginationConfig,
    fetch_time_ms: float
) -> Dict[str, Any]:
    """Handle normal paginated response"""
    
    pagination_mgr = get_pagination_manager()
    
    # Detect fresh query vs cursor continuation
    if not pagination_params.cursor_id:
        return await _handle_fresh_query(
            all_data, item_formatter, tool_name, pagination_params, 
            config, fetch_time_ms, pagination_mgr
        )
    else:
        return await _handle_cursor_continuation(
            all_data, item_formatter, tool_name, pagination_params,
            config, fetch_time_ms, pagination_mgr
        )

async def _handle_fresh_query(
    all_data: List[T],
    item_formatter: Callable[[T], str],
    tool_name: str,
    pagination_params: PaginationParams,
    config: PaginationConfig,
    fetch_time_ms: float,
    pagination_mgr
) -> Dict[str, Any]:
    """Handle fresh query (no cursor)"""
    
    limit = pagination_params.limit
    page_items = all_data[:limit]
    
    # Format page items
    formatted_items = [item_formatter(item) for item in page_items]
    
    # Check if more pages available
    has_more = len(all_data) > limit
    cursor_id = None
    
    if has_more:
        # Create cursor for continuation
        query_state = QueryState.from_params({})  # Simplified for demo
        initial_position = {
            'last_index': limit - 1,
            'total_items': len(all_data)
        }
        
        cursor_id = await pagination_mgr.create_cursor(
            session_id=pagination_params.session_id,
            tool_name=tool_name,
            query_state=query_state,
            initial_position=initial_position
        )
        
        # Record performance
        await pagination_mgr.record_performance(cursor_id, fetch_time_ms)
    
    # Build response
    total_pages = (len(all_data) + limit - 1) // limit if has_more else 1
    
    result = []
    
    # Add header
    if has_more:
        result.append(f"**Results: {len(page_items)} of {len(all_data)} items** ({fetch_time_ms:.0f}ms) • [Next page available]")
    else:
        result.append(f"**Results: {len(page_items)} items** ({fetch_time_ms:.0f}ms)")
    
    # Add formatted items
    result.extend(formatted_items)
    
    # Add pagination footer
    if has_more:
        result.append(f"""
**📄 Pagination**
• Page: 1 of {total_pages}
• Next: `{tool_name}({{...same_params, cursor_id: "{cursor_id}"}})`
• Items: {len(page_items)}/{len(all_data)}""")
    
    return {
        "status": "paginated_response",
        "items": result,
        "page_count": len(page_items),
        "total_count": len(all_data),
        "has_more": has_more,
        "cursor_id": cursor_id,
        "current_page": 1,
        "total_pages": total_pages,
        "fetch_time_ms": fetch_time_ms
    }

async def _handle_cursor_continuation(
    all_data: List[T],
    item_formatter: Callable[[T], str],
    tool_name: str,
    pagination_params: PaginationParams,
    config: PaginationConfig,
    fetch_time_ms: float,
    pagination_mgr
) -> Dict[str, Any]:
    """Handle cursor continuation (existing cursor)"""
    
    # Get cursor
    cursor = await pagination_mgr.get_cursor(
        pagination_params.cursor_id, 
        pagination_params.session_id
    )
    
    if not cursor:
        # Cursor expired or invalid, fall back to fresh query
        return await _handle_fresh_query(
            all_data, item_formatter, tool_name, pagination_params,
            config, fetch_time_ms, pagination_mgr
        )
    
    # Calculate page boundaries
    limit = pagination_params.limit
    start_index = cursor.position.get('last_index', 0) + 1
    end_index = start_index + limit
    
    page_items = all_data[start_index:end_index]
    formatted_items = [item_formatter(item) for item in page_items]
    
    # Check if more pages available
    has_more = end_index < len(all_data)
    new_cursor_id = None
    
    if has_more:
        # Update cursor position
        new_position = {
            'last_index': end_index - 1,
            'total_items': len(all_data)
        }
        await pagination_mgr.update_cursor_position(
            cursor.id, new_position, len(page_items)
        )
        new_cursor_id = cursor.id
    else:
        # No more pages, invalidate cursor
        await pagination_mgr.invalidate_cursor(cursor.id)
    
    # Record performance
    await pagination_mgr.record_performance(cursor.id, fetch_time_ms)
    
    # Calculate page numbers
    current_page = (start_index // limit) + 1
    total_pages = (len(all_data) + limit - 1) // limit
    
    result = []
    
    # Add header
    result.append(
        f"**Results: {len(page_items)} items** ({fetch_time_ms:.0f}ms) • "
        f"Page {current_page}/{total_pages} • Total fetched: {cursor.result_count + len(page_items)}/{len(all_data)}"
    )
    
    # Add formatted items
    result.extend(formatted_items)
    
    # Add pagination footer
    next_info = f'Next: `{tool_name}({{...same_params, cursor_id: "{new_cursor_id}"}})`' if new_cursor_id else "✅ End of results"
    
    result.append(f"""
**📄 Pagination**
• Page: {current_page} of {total_pages}
• {next_info}
• Progress: {cursor.result_count + len(page_items)}/{len(all_data)} items fetched""")
    
    return {
        "status": "cursor_continuation",
        "items": result,
        "page_count": len(page_items),
        "total_count": len(all_data),
        "has_more": has_more,
        "cursor_id": new_cursor_id,
        "current_page": current_page,
        "total_pages": total_pages,
        "fetch_time_ms": fetch_time_ms,
        "total_fetched": cursor.result_count + len(page_items)
    }

# Import time for performance measurements
import time