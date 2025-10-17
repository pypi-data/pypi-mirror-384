"""
Pagination utility functions for common operations.
"""

from typing import List, Dict, Any, TypeVar, Optional
from pydantic import BaseModel, Field

T = TypeVar('T')

class PaginationParams(BaseModel):
    """Standard pagination parameters"""
    limit: int = Field(default=50, ge=1, le=1000)
    cursor_id: Optional[str] = Field(default=None)
    session_id: Optional[str] = Field(default=None)
    return_all: bool = Field(default=False)

def paginate_list(
    data: List[T], 
    page_size: int = 50, 
    page_number: int = 1
) -> Dict[str, Any]:
    """
    Simple list pagination for basic use cases.
    
    Args:
        data: List of items to paginate
        page_size: Number of items per page
        page_number: Page number (1-based)
    
    Returns:
        Dict with items, pagination info, and metadata
    """
    
    total_items = len(data)
    total_pages = (total_items + page_size - 1) // page_size
    
    # Validate page number
    if page_number < 1:
        page_number = 1
    elif page_number > total_pages:
        page_number = total_pages
    
    # Calculate slice boundaries
    start_index = (page_number - 1) * page_size
    end_index = min(start_index + page_size, total_items)
    
    page_items = data[start_index:end_index]
    
    return {
        "items": page_items,
        "pagination": {
            "current_page": page_number,
            "page_size": page_size,
            "total_items": total_items,
            "total_pages": total_pages,
            "has_previous": page_number > 1,
            "has_next": page_number < total_pages,
            "start_index": start_index,
            "end_index": end_index
        }
    }

def create_pagination_params(**kwargs) -> PaginationParams:
    """Create pagination parameters with validation"""
    return PaginationParams(**kwargs)

def estimate_response_tokens(text: str, chars_per_token: float = 4.0) -> int:
    """Estimate token count for response text"""
    return int(len(text) / chars_per_token)

def should_paginate(
    data: List[Any], 
    formatter: callable,
    max_tokens: int = 8000,
    chars_per_token: float = 4.0
) -> bool:
    """
    Determine if data should be paginated based on estimated response size.
    
    Args:
        data: List of items to check
        formatter: Function to format items for response
        max_tokens: Maximum tokens before pagination recommended
        chars_per_token: Ratio for token estimation
    
    Returns:
        True if pagination is recommended
    """
    
    if len(data) <= 10:
        return False  # Always show small datasets
    
    # Sample first few items to estimate size
    sample_size = min(5, len(data))
    sample_text = '\n'.join(formatter(item) for item in data[:sample_size])
    
    # Estimate full response size
    avg_chars_per_item = len(sample_text) / sample_size
    estimated_total_chars = avg_chars_per_item * len(data)
    estimated_tokens = estimated_total_chars / chars_per_token
    
    return estimated_tokens > max_tokens

def format_pagination_summary(
    current_page: int,
    total_pages: int,
    items_on_page: int,
    total_items: int,
    tool_name: str,
    cursor_id: Optional[str] = None
) -> str:
    """Format a standard pagination summary"""
    
    summary = f"**📄 Page {current_page} of {total_pages}** ({items_on_page} items)\n"
    summary += f"Total: {total_items} items\n"
    
    if cursor_id:
        summary += f"Next: `{tool_name}({{...same_params, cursor_id: \"{cursor_id}\"}})`"
    else:
        summary += "✅ End of results"
    
    return summary

def create_large_response_warning(
    item_count: int,
    estimated_tokens: int,
    tool_name: str,
    recommended_limit: int = 50
) -> str:
    """Create a warning message for large responses"""
    
    if estimated_tokens > 50000:
        level = "🚨 EXTREMELY LARGE"
    elif estimated_tokens > 20000:
        level = "⚠️ VERY LARGE"
    elif estimated_tokens > 8000:
        level = "⚠️ LARGE"
    else:
        level = "💡 LARGE"
    
    warning = f"""{level} response (~{estimated_tokens:,} tokens)

**⚠️ This response may:**
• Fill up context rapidly
• Cause performance issues
• Be truncated by client limits

**💡 Recommendations:**
• Use pagination: `{tool_name}({{...same_params, limit: {recommended_limit}}})`
• Apply filters to reduce data
• Use cursor navigation: `return_all: false`

**📊 Dataset:** {item_count} items
"""
    
    return warning